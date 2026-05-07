import os
import re
from flask import Blueprint, jsonify, request
from services.db import get_db
from config import login_required

mysql_bp = Blueprint("mysql", __name__)

@mysql_bp.route("/start_mysql")
@login_required
def start_mysql():
    os.system("sudo service mysql start")
    return "MySQL iniciado"

@mysql_bp.route("/stop_mysql")
@login_required
def stop_mysql():
    os.system("sudo service mysql stop")
    return "MySQL parado"

@mysql_bp.route("/mysql_status")
@login_required
def mysql_status():
    result = os.popen("pgrep mysqld").read()
    return "Online" if result.strip() else "Offline"

@mysql_bp.route("/tables")
@login_required
def tables():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    return jsonify([t[0] for t in cursor.fetchall()])

@mysql_bp.route("/create_table", methods=["POST"])
@login_required
def create_table():
    name = request.json["name"]

    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        return "invalid name", 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"CREATE TABLE {name} (id INT AUTO_INCREMENT PRIMARY KEY)")
    db.commit()
    return "ok"

@mysql_bp.route("/delete_table/<name>")
@login_required
def delete_table(name):
    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        return "invalid name", 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"DROP TABLE {name}")
    db.commit()
    return "ok"