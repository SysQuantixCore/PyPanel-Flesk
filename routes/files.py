import os
import shutil
from flask import Blueprint, request, redirect, jsonify, send_from_directory
from config import HTDOCS_FOLDER, login_required

files_bp = Blueprint("files", __name__)

@files_bp.route("/htdocs/<path:filename>")
def serve_file(filename):
    return send_from_directory(HTDOCS_FOLDER, filename)

@files_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    if file:
        file.save(os.path.join(HTDOCS_FOLDER, file.filename))
    return redirect("/dashboard")

@files_bp.route("/delete/<path:filename>")
@login_required
def delete(filename):
    try:
        path = os.path.join(HTDOCS_FOLDER, filename)

        if not os.path.abspath(path).startswith(os.path.abspath(HTDOCS_FOLDER)):
            return "invalid path", 400

        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
                return "deleted", 200
            elif os.path.isdir(path):
                shutil.rmtree(path)
                return "folder deleted", 200

        return "not found", 404

    except Exception as e:
        print("ERRO DELETE:", e)
        return "error", 500

@files_bp.route("/api/files")
@login_required
def api_files():
    req_path = request.args.get("path", "/htdocs")

    relative_path = req_path.replace("/htdocs", "", 1)
    full_path = os.path.abspath(os.path.join(HTDOCS_FOLDER, relative_path.strip("/")))
    base_path = os.path.abspath(HTDOCS_FOLDER)

    if not full_path.startswith(base_path):
        return jsonify([])

    if not os.path.exists(full_path):
        return jsonify([])

    files = []

    for f in os.listdir(full_path):
        path = os.path.join(full_path, f)

        try:
            mtime = os.path.getmtime(path)
        except:
            mtime = 0

        files.append({
            "name": f,
            "date": mtime,
            "is_dir": os.path.isdir(path)
        })

    return jsonify(files)

@files_bp.route("/create_folder/<name>")
@login_required
def create_folder(name):
    path = os.path.join(HTDOCS_FOLDER, name)
    os.makedirs(path, exist_ok=True)
    return "ok"