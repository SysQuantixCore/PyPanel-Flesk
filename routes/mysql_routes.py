
import os
import re
import subprocess

from flask import Blueprint, jsonify, request
from services.db import get_db
from config import login_required

mysql_bp = Blueprint("mysql", __name__)

# CONFIGURAÇÃO DO MYSQL NO WINDOWS
MYSQL_SERVICE = "MySQL80"


# INICIAR MYSQL
@mysql_bp.route("/start_mysql")
@login_required
def start_mysql():

    try:
        result = subprocess.run(
            ["sc", "start", MYSQL_SERVICE],
            capture_output=True,
            text=True,
            shell=False
        )

        if result.returncode == 0:
            return "MySQL iniciado"

        return (
            result.stderr.strip()
            or result.stdout.strip()
            or "Não foi possível iniciar o MySQL"
        ), 500

    except Exception as e:
        return f"Erro ao iniciar MySQL: {e}", 500


# PARAR MYSQL
@mysql_bp.route("/stop_mysql")
@login_required
def stop_mysql():

    try:
        result = subprocess.run(
            ["sc", "stop", MYSQL_SERVICE],
            capture_output=True,
            text=True,
            shell=False
        )

        if result.returncode == 0:
            return "MySQL parado"

        return (
            result.stderr.strip()
            or result.stdout.strip()
            or "Não foi possível parar o MySQL"
        ), 500

    except Exception as e:
        return f"Erro ao parar MySQL: {e}", 500


# STATUS MYSQL
@mysql_bp.route("/mysql_status")
@login_required
def mysql_status():

    try:
        db = get_db()
        db.close()

        return "Online"

    except Exception as e:
        print(f"Erro MySQL: {e}")
        return "Offline"


# LISTAR TABELAS
@mysql_bp.route("/tables")
@login_required
def tables():

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SHOW TABLES")

        result = [t[0] for t in cursor.fetchall()]

        cursor.close()
        db.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# CRIAR TABELA
@mysql_bp.route("/create_table", methods=["POST"])
@login_required
def create_table():

    try:
        name = request.json["name"]

        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            return "invalid name", 400

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            f"CREATE TABLE `{name}` (id INT AUTO_INCREMENT PRIMARY KEY)"
        )

        db.commit()

        cursor.close()
        db.close()

        return "ok"

    except Exception as e:
        return str(e), 500

@mysql_bp.route("/create_database", methods=["POST"])
def create_database():
    from flask import request, jsonify
    from mysql.connector import Error
    from services.db import get_db

    data = request.get_json(silent=True) or {}
    database_name = data.get("name", "").strip()

    if not database_name:
        return jsonify({
            "success": False,
            "error": "Informe o nome do banco de dados."
        }), 400

    # Permite apenas nomes simples de banco de dados.
    import re
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        return jsonify({
            "success": False,
            "error": "Nome inválido. Use letras, números e underline."
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db()
        cursor = connection.cursor()

        cursor.execute(f"CREATE DATABASE `{database_name}`")

        return jsonify({
            "success": True,
            "message": f"Banco '{database_name}' criado com sucesso."
        })

    except Error as err:
        return jsonify({
            "success": False,
            "error": str(err)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# EXCLUIR TABELA
@mysql_bp.route("/delete_table/<name>")
@login_required
def delete_table(name):

    try:
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            return "invalid name", 400

        db = get_db()
        cursor = db.cursor()

        cursor.execute(f"DROP TABLE `{name}`")

        db.commit()

        cursor.close()
        db.close()

        return "ok"

    except Exception as e:
        return str(e), 500