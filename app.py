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

from config import HTDOCS_FOLDER

app = Flask(__name__)

app.secret_key = "super_secret_key"

os.makedirs(
    HTDOCS_FOLDER,
    exist_ok=True
)

# BLUEPRINTS
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(files_bp)
app.register_blueprint(mysql_bp)
app.register_blueprint(google_bp)

# HOME PAGE
@app.route("/")
def index():

    return render_template(
        "index.html"
    )

# API STATUS
@app.route("/status")
def status():

    return jsonify({
        "status": "online",
        "server": "PyPanel Flask",
        "mysql": "connected"
    })

# LOGIN
@app.route("/login")
def login():

    return render_template(
        "login.html"
    )

# START SERVER
if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )