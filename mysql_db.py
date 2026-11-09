
import re
import subprocess

from flask import Blueprint, jsonify, request
from mysql.connector import Error

from services.db import get_db
from config import login_required


mysql_bp = Blueprint("mysql", __name__)

# CONFIGURAÇÃO DO SERVIÇO MYSQL NO WINDOWS
MYSQL_SERVICE = "MySQL80"


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def valid_name(name):
    """Valida nomes de bancos e tabelas."""
    return (
        isinstance(name, str)
        and re.fullmatch(r"[A-Za-z0-9_]+", name) is not None
    )


def close_mysql(cursor=None, db=None):
    """Fecha cursor e conexão sem interromper o tratamento de erros."""
    try:
        if cursor:
            cursor.close()
    except Exception:
        pass

    try:
        if db:
            db.close()
    except Exception:
        pass


def select_database(db, database_name):
    """Seleciona o banco informado após validar seu nome."""
    if not valid_name(database_name):
        raise ValueError("Nome de banco de dados inválido.")

    cursor = db.cursor()

    try:
        cursor.execute(f"USE `{database_name}`")
    finally:
        cursor.close()


# =========================================================
# INICIAR MYSQL
# =========================================================

@mysql_bp.route("/start_mysql", methods=["GET"])
@login_required
def start_mysql():
    try:
        result = subprocess.run(
            ["sc.exe", "start", MYSQL_SERVICE],
            capture_output=True,
            text=True,
            shell=False,
            timeout=20
        )

        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "Solicitação de inicialização do MySQL enviada."
            })

        message = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Não foi possível iniciar o MySQL."
        )

        return jsonify({
            "success": False,
            "error": message
        }), 500

    except Exception as e:
        print(f"[MYSQL START] {type(e).__name__}: {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# PARAR MYSQL
# =========================================================

@mysql_bp.route("/stop_mysql", methods=["GET"])
@login_required
def stop_mysql():
    try:
        result = subprocess.run(
            ["sc.exe", "stop", MYSQL_SERVICE],
            capture_output=True,
            text=True,
            shell=False,
            timeout=20
        )

        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "Solicitação para parar o MySQL enviada."
            })

        message = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Não foi possível parar o MySQL."
        )

        return jsonify({
            "success": False,
            "error": message
        }), 500

    except Exception as e:
        print(f"[MYSQL STOP] {type(e).__name__}: {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# STATUS MYSQL
# =========================================================

@mysql_bp.route("/mysql_status", methods=["GET"])
@login_required
def mysql_status():
    db = None

    try:
        db = get_db()

        if not db.is_connected():
            raise Exception("A conexão foi aberta, mas não está ativa.")

        return jsonify({
            "success": True,
            "status": "Online",
            "message": "Conexão com MySQL estabelecida."
        })

    except Exception as e:
        print(f"[MYSQL STATUS] {type(e).__name__}: {e}")

        return jsonify({
            "success": False,
            "status": "Offline",
            "error": str(e)
        }), 503

    finally:
        if db:
            try:
                db.close()
            except Exception as close_error:
                print(f"[MYSQL STATUS CLOSE] {close_error}")


# =========================================================
# LISTAR BANCOS DE DADOS
# =========================================================

@mysql_bp.route("/databases", methods=["GET"])
@login_required
def databases():
    db = None
    cursor = None

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SHOW DATABASES")

        result = [
            row[0]
            for row in cursor.fetchall()
        ]

        return jsonify(result)

    except Exception as e:
        print(f"[MYSQL DATABASES] {type(e).__name__}: {e}")

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        close_mysql(cursor, db)


# =========================================================
# CRIAR BANCO DE DADOS
# =========================================================

@mysql_bp.route("/create_database", methods=["POST"])
@login_required
def create_database():
    db = None
    cursor = None

    try:
        data = request.get_json(silent=True) or {}
        database_name = data.get("name", "")

        if not isinstance(database_name, str):
            return jsonify({
                "success": False,
                "error": "Nome do banco inválido."
            }), 400

        database_name = database_name.strip()

        if not database_name:
            return jsonify({
                "success": False,
                "error": "Informe o nome do banco de dados."
            }), 400

        if not valid_name(database_name):
            return jsonify({
                "success": False,
                "error": "Use somente letras, números e underline."
            }), 400

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            f"CREATE DATABASE `{database_name}`"
        )

        return jsonify({
            "success": True,
            "message": f"Banco '{database_name}' criado com sucesso.",
            "database": database_name
        })

    except Error as e:
        print(f"[MYSQL CREATE DATABASE] {type(e).__name__}: {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    except Exception as e:
        print(f"[CREATE DATABASE] {type(e).__name__}: {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        close_mysql(cursor, db)


# =========================================================
# EXCLUIR BANCO DE DADOS
# =========================================================

@mysql_bp.route("/delete_database/<name>", methods=["DELETE"])
@login_required
def delete_database(name):
    db = None
    cursor = None

    try:
        if not valid_name(name):
            return jsonify({
                "success": False,
                "error": "Nome de banco inválido."
            }), 400

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            f"DROP DATABASE `{name}`"
        )

        return jsonify({
            "success": True,
            "message": f"Banco '{name}' excluído com sucesso."
        })

    except Exception as e:
        print(f"[MYSQL DELETE DATABASE] {type(e).__name__}: {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        close_mysql(cursor, db)


# =========================================================
# LISTAR TABELAS DO BANCO SELECIONADO
# =========================================================

@mysql_bp.route("/tables", methods=["GET"])
@login_required
def tables():
    db = None
    cursor = None

    try:
        database_name = request.args.get("database", "").strip()

        if not valid_name(database_name):
            return jsonify({
                "error": "Banco de dados inválido ou não informado."
            }), 400

        db = get_db()
        select_database(db, database_name)

        cursor = db.cursor()
        cursor.execute("SHOW TABLES")

        result = [
            row[0]
            for row in cursor.fetchall()
        ]

        return jsonify(result)

    except Exception as e:
        print(f"[MYSQL TABLES] {type(e).__name__}: {e}")

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        close_mysql(cursor, db)


# =========================================================
# CRIAR TABELA
# =========================================================

@mysql_bp.route("/create_table", methods=["POST"])
@login_required
def create_table():
    db = None
    cursor = None

    try:
        data = request.get_json(silent=True) or {}

        table_name = data.get("name", "")
        database_name = data.get("database", "")

        if not valid_name(table_name):
            return jsonify({
                "success": False,
                "error": "Nome de tabela inválido."
            }), 400

        if not valid_name(database_name):
            return jsonify({
                "success": False,
                "error": "Banco de dados inválido."
            }), 400

        db = get_db()
        select_database(db, database_name)

        cursor = db.cursor()

        cursor.execute(
            f"""
            CREATE TABLE `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY
            )
            """
        )

        return jsonify({
            "success": True,
            "message": f"Tabela '{table_name}' criada com sucesso."
        })

    except Exception as e:
        print(f"[MYSQL CREATE TABLE] {type(e).__name__}: {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        close_mysql(cursor, db)


# =========================================================
# EXCLUIR TABELA
# =========================================================

@mysql_bp.route("/delete_table/<name>", methods=["DELETE"])
@login_required
def delete_table(name):
    db = None
    cursor = None

    try:
        database_name = request.args.get("database", "").strip()

        if not valid_name(name):
            return jsonify({
                "success": False,
                "error": "Nome de tabela inválido."
            }), 400

        if not valid_name(database_name):
            return jsonify({
                "success": False,
                "error": "Banco de dados inválido."
            }), 400

        db = get_db()
        select_database(db, database_name)

        cursor = db.cursor()

        cursor.execute(
            f"DROP TABLE `{name}`"
        )

        return jsonify({
            "success": True,
            "message": f"Tabela '{name}' excluída com sucesso."
        })

    except Exception as e:
        print(f"[MYSQL DELETE TABLE] {type(e).__name__}: {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        close_mysql(cursor, db)