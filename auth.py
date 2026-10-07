"""
Σύστημα σύνδεσης χρηστών: εγγραφή, login, logout, προστασία σελίδων.
Δύο ρόλοι: 'farmer' (αγρότης) και 'customer' (πελάτης).
"""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

bp = Blueprint("auth", __name__)


def current_user():
    uid = session.get("user_id")
    if uid is None:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            flash("Πρέπει πρώτα να συνδεθείς.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                flash("Πρέπει πρώτα να συνδεθείς.", "error")
                return redirect(url_for("auth.login", next=request.path))
            if user["role"] != role:
                flash("Δεν έχεις πρόσβαση σε αυτή τη σελίδα.", "error")
                return redirect(url_for("main.home"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        error = None
        if not name:
            error = "Συμπλήρωσε το όνομά σου."
        elif not email or "@" not in email:
            error = "Δώσε ένα έγκυρο email."
        elif len(password) < 6:
            error = "Ο κωδικός χρειάζεται τουλάχιστον 6 χαρακτήρες."
        elif role not in ("farmer", "customer"):
            error = "Επίλεξε αν είσαι αγρότης ή πελάτης."

        db = get_db()
        if error is None:
            existing = db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing is not None:
                error = "Υπάρχει ήδη λογαριασμός με αυτό το email."

        if error is None:
            db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name, email, generate_password_hash(password), role),
            )
            db.commit()
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            session.clear()
            session["user_id"] = user["id"]
            flash("Ο λογαριασμός δημιουργήθηκε!", "success")
            return redirect(url_for("main.home"))

        flash(error, "error")

    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        error = None
        if user is None or not check_password_hash(user["password_hash"], password):
            error = "Λάθος email ή κωδικός."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            next_url = request.args.get("next") or url_for("main.home")
            return redirect(next_url)

        flash(error, "error")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))


@bp.app_context_processor
def inject_user():
    return {"current_user": current_user()}
