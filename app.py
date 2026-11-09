import os

from flask import (
    Flask,
    jsonify,
    render_template
)

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.files import files_bp
from routes.mysql_routes import mysql_bp
from routes.google_routes import google_bp
from routes.monitor import traffic_bp

from config import HTDOCS_FOLDER


# =========================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "super_secret_key"
)

os.makedirs(
    HTDOCS_FOLDER,
    exist_ok=True
)


# =========================================================
# REGISTRO DOS BLUEPRINTS
# =========================================================

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(files_bp)
app.register_blueprint(mysql_bp)
app.register_blueprint(google_bp)
app.register_blueprint(traffic_bp)


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# STATUS GERAL DA APLICAÇÃO
# =========================================================

@app.route("/status", methods=["GET"])
def status():

    mysql_status = "disconnected"
    connection = None

    try:
        from services.db import get_db

        connection = get_db()

        if connection and connection.is_connected():
            mysql_status = "connected"

    except Exception as err:
        print(f"[APP STATUS] Erro MySQL: {err}")

    finally:
        if connection:
            try:
                connection.close()
            except Exception as err:
                print(f"[APP STATUS] Erro ao fechar conexão: {err}")

    return jsonify({
        "status": "online",
        "server": "PyPanel Flask",
        "mysql": mysql_status
    })


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


# =========================================================
# DIAGNÓSTICO DAS ROTAS
# =========================================================

def show_registered_routes():

    print("\n========== ROTAS REGISTRADAS ==========")

    for rule in app.url_map.iter_rules():
        methods = ", ".join(
            sorted(rule.methods - {"HEAD", "OPTIONS"})
        )

        print(f"{methods:20} {rule}")

    print("=======================================\n")


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    show_registered_routes()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )