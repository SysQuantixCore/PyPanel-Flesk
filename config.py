import os
from functools import wraps
from flask import session, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTDOCS_FOLDER = os.path.join(BASE_DIR, "htdocs")

USERNAME = "admin"
PASSWORD = "1234"

# 🔐 middleware de login
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged"):
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper