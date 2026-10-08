"""
Πλάνο εργασιών: ο αγρότης προγραμματίζει εργασίες μπροστά στο χρόνο (όχι
μόνο ιστορικό), τις βλέπει σε μορφή ημερολογίου μήνα, τις σημειώνει ως
ολοκληρωμένες (οπότε περνάνε κανονικά στο ιστορικό εργασιών του κτήματος),
και — κατόπιν αιτήματος του ίδιου — τις προσθέτει στο δικό του ημερολόγιο
(Google Calendar, κινητό, Outlook) μέσω αρχείων .ics, είτε μία-μία είτε με
μόνιμη σύνδεση συνδρομής (ο αγρότης την ενεργοποιεί ο ίδιος, δεν γίνεται
τίποτα αυτόματα χωρίς να το ζητήσει).
"""
import calendar as pycalendar
import secrets
from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort

from db import get_db
from auth import role_required, current_user
from fields import TASK_TYPES
from ics_calendar import build_event, build_calendar

bp = Blueprint("planner", __name__, url_prefix="/planner")

GREEK_MONTHS = ["", "Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος",
                "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"]
GREEK_WEEKDAYS = ["Δε", "Τρ", "Τε", "Πε", "Πα", "Σα", "Κυ"]


def _get_calendar_token(db, user):
    if user["calendar_token"]:
        return user["calendar_token"]
    token = secrets.token_urlsafe(24)
    db.execute("UPDATE users SET calendar_token = ? WHERE id = ?", (token, user["id"]))
    db.commit()
    return token


def _owned_planned_task(db, task_id, farmer_id):
    return db.execute(
        """SELECT pt.* FROM planned_tasks pt
           JOIN fields f ON f.id = pt.field_id
           WHERE pt.id = ? AND f.farmer_id = ?""",
        (task_id, farmer_id),
    ).fetchone()


@bp.route("/")
@role_required("farmer")
def calendar_view():
    db = get_db()
    user = current_user()

    month_param = request.args.get("month", "")
    try:
        year, month = (int(x) for x in month_param.split("-"))
    except ValueError:
        today = date.today()
        year, month = today.year, today.month

    rows = db.execute(
        """SELECT pt.*, f.name AS field_name FROM planned_tasks pt
           JOIN fields f ON f.id = pt.field_id
           WHERE f.farmer_id = ? AND pt.planned_date LIKE ?
           ORDER BY pt.planned_date""",
        (user["id"], f"{year:04d}-{month:02d}-%"),
    ).fetchall()

    by_day = {}
    for r in rows:
        day = int(r["planned_date"][8:10])
        by_day.setdefault(day, []).append(r)

    weeks = pycalendar.Calendar(firstweekday=0).monthdayscalendar(year, month)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    fields = db.execute(
        "SELECT id, name FROM fields WHERE farmer_id = ? ORDER BY name", (user["id"],)
    ).fetchall()

    token = _get_calendar_token(db, user)
    feed_url = url_for("planner.calendar_feed", token=token, _external=True)

    return render_template(
        "planner/calendar.html",
        year=year, month=month,
        month_name=GREEK_MONTHS[month],
        weekdays=GREEK_WEEKDAYS,
        weeks=weeks, by_day=by_day,
        today=date.today(),
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year,
        fields=fields, task_types=TASK_TYPES,
        feed_url=feed_url,
    )


@bp.route("/new", methods=["POST"])
@role_required("farmer")
def new_planned_task():
    db = get_db()
    user = current_user()

    field_id = request.form.get("field_id", "")
    task_type = request.form.get("task_type", "")
    planned_date = request.form.get("planned_date", "").strip()
    notes = request.form.get("notes", "").strip()

    field = db.execute(
        "SELECT * FROM fields WHERE id = ? AND farmer_id = ?", (field_id, user["id"])
    ).fetchone()

    if field is None or task_type not in TASK_TYPES or not planned_date:
        flash("Συμπλήρωσε κτήμα, τύπο εργασίας και ημερομηνία.", "error")
        return redirect(url_for("planner.calendar_view", month=planned_date[:7] if planned_date else None))

    db.execute(
        "INSERT INTO planned_tasks (field_id, task_type, planned_date, notes) VALUES (?, ?, ?, ?)",
        (field_id, task_type, planned_date, notes or None),
    )
    db.commit()
    flash("Η εργασία προγραμματίστηκε.", "success")
    return redirect(url_for("planner.calendar_view", month=planned_date[:7]))


@bp.route("/<int:task_id>/done", methods=["POST"])
@role_required("farmer")
def mark_done(task_id):
    db = get_db()
    user = current_user()
    task = _owned_planned_task(db, task_id, user["id"])
    if task is None:
        flash("Η προγραμματισμένη εργασία δεν βρέθηκε.", "error")
        return redirect(url_for("planner.calendar_view"))

    cost = request.form.get("cost", "0").strip() or "0"
    db.execute(
        """INSERT INTO tasks (field_id, task_type, task_date, cost, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (task["field_id"], task["task_type"], task["planned_date"], float(cost), task["notes"]),
    )
    db.execute("UPDATE planned_tasks SET status = 'done' WHERE id = ?", (task_id,))
    db.commit()
    flash("Η εργασία ολοκληρώθηκε και καταχωρήθηκε στο ιστορικό του κτήματος.", "success")
    return redirect(url_for("planner.calendar_view", month=task["planned_date"][:7]))


@bp.route("/<int:task_id>/delete", methods=["POST"])
@role_required("farmer")
def delete_planned(task_id):
    db = get_db()
    user = current_user()
    task = _owned_planned_task(db, task_id, user["id"])
    if task is None:
        flash("Η προγραμματισμένη εργασία δεν βρέθηκε.", "error")
        return redirect(url_for("planner.calendar_view"))

    month = task["planned_date"][:7]
    db.execute("DELETE FROM planned_tasks WHERE id = ?", (task_id,))
    db.commit()
    flash("Η προγραμματισμένη εργασία διαγράφηκε.", "success")
    return redirect(url_for("planner.calendar_view", month=month))


@bp.route("/<int:task_id>/ics")
@role_required("farmer")
def download_ics(task_id):
    db = get_db()
    user = current_user()
    task = db.execute(
        """SELECT pt.*, f.name AS field_name FROM planned_tasks pt
           JOIN fields f ON f.id = pt.field_id
           WHERE pt.id = ? AND f.farmer_id = ?""",
        (task_id, user["id"]),
    ).fetchone()
    if task is None:
        abort(404)

    event = build_event(
        uid=f"task-{task['id']}",
        summary=f"{task['task_type']} — {task['field_name']}",
        date_str=task["planned_date"],
        description=task["notes"] or "",
    )
    ics_text = build_calendar([event])
    return Response(
        ics_text,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=agroktima-{task['id']}.ics"},
    )


@bp.route("/feed/<token>.ics")
def calendar_feed(token):
    """Μόνιμη συνδρομή ημερολογίου (webcal) — ο αγρότης τη προσθέτει ο ίδιος
    μία φορά στο Google Calendar/κινητό, και μετά ενημερώνεται αυτόματα.
    Δημόσιο URL αλλά προστατευμένο από το μυστικό token, όχι login (έτσι
    δουλεύουν όλες οι εφαρμογές ημερολογίου — δεν μπορούν να κάνουν login)."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE calendar_token = ?", (token,)).fetchone()
    if user is None:
        abort(404)

    rows = db.execute(
        """SELECT pt.*, f.name AS field_name FROM planned_tasks pt
           JOIN fields f ON f.id = pt.field_id
           WHERE f.farmer_id = ? AND pt.status = 'pending'
           ORDER BY pt.planned_date""",
        (user["id"],),
    ).fetchall()

    events = [
        build_event(
            uid=f"task-{r['id']}",
            summary=f"{r['task_type']} — {r['field_name']}",
            date_str=r["planned_date"],
            description=r["notes"] or "",
        )
        for r in rows
    ]
    ics_text = build_calendar(events, calendar_name="Αγρόκτημα — Πλάνο εργασιών")
    return Response(ics_text, mimetype="text/calendar")
