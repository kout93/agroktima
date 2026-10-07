"""
Διαχείριση κτημάτων και καταγραφή εργασιών.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db
from auth import role_required, current_user
from uploads import save_photo

bp = Blueprint("fields", __name__, url_prefix="/fields")

TASK_TYPES = ["Όργωμα", "Πότισμα", "Λίπανση", "Ψεκασμός", "Κλάδεμα", "Συγκομιδή", "Άλλο"]


@bp.route("/")
@role_required("farmer")
def list_fields():
    db = get_db()
    user = current_user()
    rows = db.execute(
        "SELECT * FROM fields WHERE farmer_id = ? ORDER BY created_at DESC", (user["id"],)
    ).fetchall()
    return render_template("fields/list.html", fields=rows)


@bp.route("/map")
@role_required("farmer")
def fields_map():
    """Συνολικός χάρτης με όλα τα κτήματα που έχουν σημειωμένη τοποθεσία."""
    db = get_db()
    user = current_user()
    rows = db.execute(
        """SELECT id, name, location, latitude, longitude FROM fields
           WHERE farmer_id = ? AND latitude IS NOT NULL AND longitude IS NOT NULL
           ORDER BY created_at DESC""",
        (user["id"],),
    ).fetchall()
    return render_template("fields/map.html", fields=rows)


@bp.route("/new", methods=["GET", "POST"])
@role_required("farmer")
def new_field():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        area = request.form.get("area_stremma", "").strip()
        crop = request.form.get("crop", "").strip()
        tree_count = request.form.get("tree_count", "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()

        if not name:
            flash("Το όνομα του κτήματος είναι υποχρεωτικό.", "error")
            return render_template("fields/new.html")

        db = get_db()
        db.execute(
            """INSERT INTO fields (farmer_id, name, location, area_stremma, crop, tree_count, latitude, longitude)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                current_user()["id"],
                name,
                location or None,
                float(area) if area else None,
                crop or None,
                int(tree_count) if tree_count else 0,
                float(latitude) if latitude else None,
                float(longitude) if longitude else None,
            ),
        )
        db.commit()
        flash("Το κτήμα προστέθηκε!", "success")
        return redirect(url_for("fields.list_fields"))

    return render_template("fields/new.html")


@bp.route("/<int:field_id>")
@role_required("farmer")
def view_field(field_id):
    db = get_db()
    user = current_user()
    field = db.execute(
        "SELECT * FROM fields WHERE id = ? AND farmer_id = ?", (field_id, user["id"])
    ).fetchone()
    if field is None:
        flash("Το κτήμα δεν βρέθηκε.", "error")
        return redirect(url_for("fields.list_fields"))

    tasks = db.execute(
        "SELECT * FROM tasks WHERE field_id = ? ORDER BY task_date DESC, id DESC", (field_id,)
    ).fetchall()
    total_cost = sum(t["cost"] or 0 for t in tasks)

    return render_template(
        "fields/view.html", field=field, tasks=tasks, total_cost=total_cost, task_types=TASK_TYPES
    )


@bp.route("/<int:field_id>/location", methods=["POST"])
@role_required("farmer")
def update_location(field_id):
    db = get_db()
    user = current_user()
    field = db.execute(
        "SELECT * FROM fields WHERE id = ? AND farmer_id = ?", (field_id, user["id"])
    ).fetchone()
    if field is None:
        flash("Το κτήμα δεν βρέθηκε.", "error")
        return redirect(url_for("fields.list_fields"))

    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()
    if not latitude or not longitude:
        flash("Σημείωσε ένα σημείο στον χάρτη πρώτα.", "error")
        return redirect(url_for("fields.view_field", field_id=field_id))

    db.execute(
        "UPDATE fields SET latitude = ?, longitude = ? WHERE id = ?",
        (float(latitude), float(longitude), field_id),
    )
    db.commit()
    flash("Η τοποθεσία του κτήματος ενημερώθηκε.", "success")
    return redirect(url_for("fields.view_field", field_id=field_id))


@bp.route("/<int:field_id>/tasks/new", methods=["POST"])
@role_required("farmer")
def new_task(field_id):
    db = get_db()
    user = current_user()
    field = db.execute(
        "SELECT * FROM fields WHERE id = ? AND farmer_id = ?", (field_id, user["id"])
    ).fetchone()
    if field is None:
        flash("Το κτήμα δεν βρέθηκε.", "error")
        return redirect(url_for("fields.list_fields"))

    task_type = request.form.get("task_type", "")
    task_date = request.form.get("task_date", "")
    cost = request.form.get("cost", "0").strip() or "0"
    notes = request.form.get("notes", "").strip()
    photo_filename = save_photo(request.files.get("photo"))

    if task_type not in TASK_TYPES or not task_date:
        flash("Συμπλήρωσε τύπο εργασίας και ημερομηνία.", "error")
        return redirect(url_for("fields.view_field", field_id=field_id))

    db.execute(
        """INSERT INTO tasks (field_id, task_type, task_date, cost, notes, photo_filename)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (field_id, task_type, task_date, float(cost), notes or None, photo_filename),
    )
    db.commit()
    flash("Η εργασία καταχωρήθηκε.", "success")
    return redirect(url_for("fields.view_field", field_id=field_id))
