import os
import shutil
import stat
from flask import Blueprint, request, redirect, jsonify, send_from_directory
from config import HTDOCS_FOLDER, login_required

files_bp = Blueprint("files", __name__)


def handle_remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


@files_bp.route("/htdocs/<path:filename>")
def serve_file(filename):
    return send_from_directory(HTDOCS_FOLDER, filename)


@files_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    requested_path = request.form.get("path", "/htdocs")

    if not file or not file.filename:
        return jsonify({
            "success": False,
            "error": "Nenhum arquivo foi enviado."
        }), 400

    from werkzeug.utils import secure_filename

    filename = secure_filename(file.filename)

    if not filename:
        return jsonify({
            "success": False,
            "error": "Nome de arquivo inválido."
        }), 400

    base_path = os.path.realpath(HTDOCS_FOLDER)

    relative_path = requested_path.replace("\\", "/").strip("/")

    if relative_path == "htdocs":
        relative_path = ""
    elif relative_path.startswith("htdocs/"):
        relative_path = relative_path[len("htdocs/"):]

    destination_dir = os.path.realpath(
        os.path.join(base_path, relative_path)
    )

    try:
        if os.path.commonpath([base_path, destination_dir]) != base_path:
            return jsonify({
                "success": False,
                "error": "Caminho de destino inválido."
            }), 403
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Caminho de destino inválido."
        }), 403

    if not os.path.isdir(destination_dir):
        return jsonify({
            "success": False,
            "error": "A pasta de destino não existe."
        }), 404

    destination = os.path.join(destination_dir, filename)

    if os.path.islink(destination):
        return jsonify({
            "success": False,
            "error": "O destino não pode ser um link simbólico."
        }), 403

    try:
        file.save(destination)

        return jsonify({
            "success": True,
            "filename": filename,
            "path": os.path.relpath(
                destination, base_path
            ).replace("\\", "/")
        }), 201

    except OSError as error:
        print(
            f"ERRO UPLOAD: {type(error).__name__}: {error}",
            flush=True
        )

        return jsonify({
            "success": False,
            "error": "Não foi possível salvar o arquivo no destino."
        }), 500


@files_bp.route("/delete/<path:filename>", methods=["GET", "POST", "DELETE"])
@login_required
def delete(filename):
    try:
        base_path = os.path.realpath(HTDOCS_FOLDER)
        requested_path = os.path.join(base_path, filename)
        path = os.path.realpath(requested_path)

        # Impede exclusão fora da pasta permitida.
        if os.path.commonpath([base_path, path]) != base_path:
            return "invalid path", 400

        if path == base_path:
            return "cannot delete root folder", 400

        if not os.path.lexists(path):
            return "not found", 404

        # Remove links simbólicos sem seguir o destino.
        if os.path.islink(requested_path):
            os.remove(requested_path)

        elif os.path.isfile(path):
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)

        elif os.path.isdir(path):
            shutil.rmtree(path, onerror=handle_remove_readonly)

        else:
            return "unsupported file type", 400

        return "deleted", 200

    except Exception as e:
        print(f"ERRO DELETE: {type(e).__name__}: {e}", flush=True)
        return f"Delete failed: {type(e).__name__}: {e}", 500


@files_bp.route("/api/files")
@login_required
def api_files():
    req_path = request.args.get("path", "/htdocs")

    relative_path = req_path.replace("/htdocs", "", 1)
    full_path = os.path.abspath(
        os.path.join(HTDOCS_FOLDER, relative_path.strip("/"))
    )
    base_path = os.path.abspath(HTDOCS_FOLDER)

    if os.path.commonpath([base_path, full_path]) != base_path:
        return jsonify([])

    if not os.path.exists(full_path):
        return jsonify([])

    files = []

    for f in os.listdir(full_path):
        path = os.path.join(full_path, f)

        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0

        files.append({
            "name": f,
            "date": mtime,
            "is_dir": os.path.isdir(path)
        })

    return jsonify(files)



@files_bp.route("/create_folder/<path:name>", methods=["GET", "POST"])
@login_required
def create_folder(name):
    base_path = os.path.realpath(HTDOCS_FOLDER)

    name = name.replace("\\", "/").strip("/")

    if name == "htdocs":
        return "invalid folder name", 400

    if name.startswith("htdocs/"):
        name = name[len("htdocs/"):]

    path = os.path.realpath(
        os.path.join(base_path, name)
    )

    try:
        if os.path.commonpath([base_path, path]) != base_path:
            return "invalid path", 400
    except ValueError:
        return "invalid path", 400

    if path == base_path:
        return "invalid folder name", 400

    try:
        os.makedirs(path, exist_ok=True)
        return "ok", 200
    except OSError as error:
        print(
            f"ERRO CREATE FOLDER: {type(error).__name__}: {error}",
            flush=True
        )
        return "Não foi possível criar a pasta.", 500
