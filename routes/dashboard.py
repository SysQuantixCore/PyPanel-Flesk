import os
from flask import Blueprint, render_template
from config import HTDOCS_FOLDER, login_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    files = os.listdir(HTDOCS_FOLDER)
    return render_template("dashboard.html", files=files)

@dashboard_bp.route("/backup")
@login_required
def backup():
    return render_template("backup.html")

@dashboard_bp.route("/database")
@login_required
def database():
    return render_template("mysql.html")

@dashboard_bp.route("/filemanager")
@login_required
def filemanager():
    return render_template("filemanager.html")

@dashboard_bp.route("/traffic-monitor")
@login_required
def monitor():
    return render_template("monitor.html")