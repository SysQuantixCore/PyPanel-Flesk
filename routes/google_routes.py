from flask import Blueprint, jsonify

google_bp = Blueprint("google", __name__)


@google_bp.route("/google_status", methods=["GET"])
def google_status():
    return jsonify({
        "connected": False,
        "message": "Google Drive não conectado. Configure a autenticação OAuth."
    })


@google_bp.route("/google_connect", methods=["GET"])
def google_connect():
    return jsonify({
        "success": False,
        "message": "A autenticação OAuth do Google Drive ainda não foi configurada."
    }), 501


@google_bp.route("/google_backup", methods=["POST"])
def google_backup():
    return jsonify({
        "success": False,
        "message": "Backup indisponível: conecte uma conta Google primeiro."
    }), 501