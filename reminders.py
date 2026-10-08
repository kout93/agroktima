"""
Υπενθυμίσεις εργασιών: μπάνερ μέσα στην εφαρμογή + email μία φορά τη μέρα.

Λειτουργία email: αν δεν έχουν οριστεί οι μεταβλητές περιβάλλοντος SMTP_HOST,
SMTP_USER, SMTP_PASSWORD, η αποστολή email απλά παραλείπεται (καμία
ψεύτικη αποστολή) — η υπενθύμιση μέσα στην εφαρμογή (μπάνερ) δουλεύει πάντα,
χωρίς να χρειάζεται τίποτα.

Για να ενεργοποιηθούν πραγματικά email:
  export SMTP_HOST="smtp.gmail.com"
  export SMTP_PORT="587"
  export SMTP_USER="you@gmail.com"
  export SMTP_PASSWORD="..."          (app password, όχι ο κανονικός κωδικός)
  export SMTP_FROM="you@gmail.com"    (προαιρετικό, αλλιώς = SMTP_USER)
  export REMINDER_CRON_TOKEN="..."    (μυστικό token για το /reminders/run-daily)

Το /reminders/run-daily καλείται μία φορά τη μέρα από εξωτερικό
προγραμματισμένο task (π.χ. Render Cron Job) — βλέπε README.
"""
import os
import smtplib
from datetime import date
from email.mime.text import MIMEText

from flask import Blueprint, redirect, request, session, url_for, abort

from db import get_db

bp = Blueprint("reminders", __name__, url_prefix="/reminders")

WATERING_DAYS_THRESHOLD = 7
FERTILIZING_DAYS_THRESHOLD = 60

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587") or 587)
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "") or SMTP_USER
IS_EMAIL_LIVE = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)

REMINDER_CRON_TOKEN = os.environ.get("REMINDER_CRON_TOKEN", "")


def _days_since(date_str):
    try:
        d = date.fromisoformat(date_str)
        return (date.today() - d).days
    except (ValueError, TypeError):
        return None


def get_reminders(db, farmer_id):
    """Λίστα υπενθυμίσεων {field_id, field_name, message} βασισμένων στο
    πραγματικό ιστορικό εργασιών του αγρότη."""
    fields = db.execute(
        "SELECT id, name FROM fields WHERE farmer_id = ?", (farmer_id,)
    ).fetchall()

    reminders = []
    for f in fields:
        last_tasks = {
            row["task_type"]: row["last_date"]
            for row in db.execute(
                """SELECT task_type, MAX(task_date) AS last_date
                   FROM tasks WHERE field_id = ? GROUP BY task_type""",
                (f["id"],),
            ).fetchall()
        }

        if not last_tasks:
            reminders.append({
                "field_id": f["id"], "field_name": f["name"],
                "message": f"Το «{f['name']}» δεν έχει καμία καταχωρημένη εργασία ακόμα.",
            })
            continue

        watering_days = _days_since(last_tasks.get("Πότισμα"))
        if watering_days is not None and watering_days >= WATERING_DAYS_THRESHOLD:
            reminders.append({
                "field_id": f["id"], "field_name": f["name"],
                "message": f"Στο «{f['name']}» το τελευταίο πότισμα ήταν πριν {watering_days} μέρες.",
            })

        fert_days = _days_since(last_tasks.get("Λίπανση"))
        if fert_days is not None and fert_days >= FERTILIZING_DAYS_THRESHOLD:
            reminders.append({
                "field_id": f["id"], "field_name": f["name"],
                "message": f"Στο «{f['name']}» η τελευταία λίπανση ήταν πριν {fert_days} μέρες.",
            })

    return reminders


def send_email(to_email, subject, body):
    """Στέλνει πραγματικό email αν υπάρχει ρυθμισμένο SMTP, αλλιώς δεν κάνει
    τίποτα (επιστρέφει False) — καμία ψεύτικη/demo αποστολή."""
    if not IS_EMAIL_LIVE:
        return False
    try:
        msg = MIMEText(body, charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())
        return True
    except Exception:
        return False


def run_daily_reminders(db):
    """Για κάθε αγρότη με εκκρεμείς υπενθυμίσεις, στέλνει ένα email την ημέρα
    (αν υπάρχει ρυθμισμένο SMTP) και καταγράφει την αποστολή για να μην
    ξαναστείλει την ίδια μέρα. Επιστρέφει πόσα email στάλθηκαν πραγματικά."""
    today_str = date.today().isoformat()
    farmers = db.execute("SELECT id, name, email FROM users WHERE role = 'farmer'").fetchall()

    sent_count = 0
    for farmer in farmers:
        reminders = get_reminders(db, farmer["id"])
        if not reminders:
            continue

        already_sent = db.execute(
            "SELECT 1 FROM reminder_log WHERE farmer_id = ? AND sent_date = ?",
            (farmer["id"], today_str),
        ).fetchone()
        if already_sent:
            continue

        body = "Γεια σου " + farmer["name"] + ",\n\nΣήμερα έχεις τις εξής υπενθυμίσεις:\n\n"
        body += "\n".join(f"• {r['message']}" for r in reminders)
        body += "\n\n— Αγρόκτημα"

        if send_email(farmer["email"], "Υπενθυμίσεις εργασιών — Αγρόκτημα", body):
            db.execute(
                "INSERT INTO reminder_log (farmer_id, sent_date) VALUES (?, ?)",
                (farmer["id"], today_str),
            )
            db.commit()
            sent_count += 1

    return sent_count


@bp.route("/dismiss")
def dismiss():
    session["reminders_dismissed_date"] = date.today().isoformat()
    return redirect(request.referrer or url_for("main.home"))


@bp.route("/run-daily")
def run_daily():
    """Προστατευμένο endpoint — καλείται από ένα εξωτερικό προγραμματισμένο
    task (Render Cron Job) μία φορά τη μέρα. Χωρίς σωστό token, 404."""
    if not REMINDER_CRON_TOKEN or request.args.get("token") != REMINDER_CRON_TOKEN:
        abort(404)
    db = get_db()
    sent = run_daily_reminders(db)
    return {"ok": True, "emails_sent": sent, "email_configured": IS_EMAIL_LIVE}
