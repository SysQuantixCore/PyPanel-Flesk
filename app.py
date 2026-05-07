import os
from flask import Flask

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.files import files_bp
from routes.mysql_routes import mysql_bp

from config import HTDOCS_FOLDER

app = Flask(__name__)
app.secret_key = "super_secret_key"

os.makedirs(HTDOCS_FOLDER, exist_ok=True)

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(files_bp)
app.register_blueprint(mysql_bp)

if __name__ == "__main__":
    app.run(debug=True)