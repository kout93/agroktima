"""
Συμβουλές AI για τον αγρότη — ρωτάει κάτι, βλέπει απάντηση βασισμένη στα
δικά του δεδομένα, και κρατάει ιστορικό προηγούμενων ερωτήσεων.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db
from auth import role_required, current_user
from advisor_ai import build_context_summary, get_advice, IS_LIVE

bp = Blueprint("advisor", __name__, url_prefix="/advisor")


@bp.route("/", methods=["GET", "POST"])
@role_required("farmer")
def ask():
    db = get_db()
    user = current_user()

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if not question:
            flash("Γράψε μια ερώτηση πρώτα.", "error")
            return redirect(url_for("advisor.ask"))

        context_summary, field_task_info = build_context_summary(db, user["id"])
        answer, used_ai = get_advice(question, context_summary, field_task_info)

        db.execute(
            "INSERT INTO advisor_messages (farmer_id, question, answer, is_ai) VALUES (?, ?, ?, ?)",
            (user["id"], question, answer, 1 if used_ai else 0),
        )
        db.commit()
        return redirect(url_for("advisor.ask"))

    history = db.execute(
        "SELECT * FROM advisor_messages WHERE farmer_id = ? ORDER BY created_at DESC",
        (user["id"],),
    ).fetchall()
    return render_template("advisor/ask.html", history=history, ai_configured=IS_LIVE)
