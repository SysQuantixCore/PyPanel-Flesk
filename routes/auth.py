from flask import Blueprint, render_template, request, redirect, session, url_for
from config import USERNAME, PASSWORD

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        if user == USERNAME and pw == PASSWORD:
            session["logged"] = True
            return redirect("/dashboard")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))