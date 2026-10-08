"""
Διαχείριση κτημάτων και καταγραφή εργασιών.
"""
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db
from auth import role_required, current_user
from uploads import save_photo
from weather import fetch_forecast
from geo import polygon_area_stremma, polygon_centroid

bp = Blueprint("fields", __name__, url_prefix="/fields")

TASK_TYPES = ["Όργωμα", "Πότισμα", "Λίπανση", "Ψεκασμός", "Κλάδεμα", "Συγκομιδή", "Άλλο"]
PRODUCT_TYPES = ["Ελιές", "Ελαιόλαδο", "Άλλο"]


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

    harvests = db.execute(
        "SELECT * FROM harvests WHERE field_id = ? ORDER BY harvest_date DESC, id DESC", (field_id,)
    ).fetchall()
    production_totals = db.execute(
        """SELECT product, SUM(quantity_kg) AS total_kg
           FROM harvests WHERE field_id = ? GROUP BY product ORDER BY total_kg DESC""",
        (field_id,),
    ).fetchall()

    total_kg_all = sum(h["quantity_kg"] or 0 for h in harvests)
    cost_per_kg = (total_cost / total_kg_all) if total_kg_all else None

    forecast = None
    if field["latitude"] and field["longitude"]:
        forecast = fetch_forecast(field["latitude"], field["longitude"])

    if field["boundary_points"]:
        boundary_points = json.loads(field["boundary_points"])
    elif field["latitude"] and field["longitude"]:
        boundary_points = [[field["latitude"], field["longitude"]]]
    else:
        boundary_points = []

    return render_template(
        "fields/view.html",
        field=field,
        tasks=tasks,
        total_cost=total_cost,
        task_types=TASK_TYPES,
        harvests=harvests,
        production_totals=production_totals,
        product_types=PRODUCT_TYPES,
        cost_per_kg=cost_per_kg,
        forecast=forecast,
        boundary_points=boundary_points,
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


@bp.route("/<int:field_id>/boundary", methods=["POST"])
@role_required("farmer")
def update_boundary(field_id):
    db = get_db()
    user = current_user()
    field = db.execute(
        "SELECT * FROM fields WHERE id = ? AND farmer_id = ?", (field_id, user["id"])
    ).fetchone()
    if field is None:
        flash("Το κτήμα δεν βρέθηκε.", "error")
        return redirect(url_for("fields.list_fields"))

    try:
        points = json.loads(request.form.get("points_json", "[]"))
        points = [[float(p[0]), float(p[1])] for p in points]
    except (ValueError, TypeError, IndexError):
        points = []

    if len(points) < 3:
        flash("Σημείωσε τουλάχιστον 3 σημεία στον χάρτη (ή φόρτωσέ τα από το τοπογραφικό) για να υπολογιστεί το εμβαδόν.", "error")
        return redirect(url_for("fields.view_field", field_id=field_id))

    area = polygon_area_stremma(points)
    centroid_lat, centroid_lng = polygon_centroid(points)

    db.execute(
        """UPDATE fields SET boundary_points = ?, area_stremma = ?, latitude = ?, longitude = ?
           WHERE id = ?""",
        (json.dumps(points), round(area, 3), centroid_lat, centroid_lng, field_id),
    )
    db.commit()
    flash(f"Το περίγραμμα αποθηκεύτηκε — υπολογισμένο εμβαδόν: {area:.2f} στρέμματα.", "success")
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


@bp.route("/<int:field_id>/harvests/new", methods=["POST"])
@role_required("farmer")
def new_harvest(field_id):
    db = get_db()
    user = current_user()
    field = db.execute(
        "SELECT * FROM fields WHERE id = ? AND farmer_id = ?", (field_id, user["id"])
    ).fetchone()
    if field is None:
        flash("Το κτήμα δεν βρέθηκε.", "error")
        return redirect(url_for("fields.list_fields"))

    harvest_date = request.form.get("harvest_date", "").strip()
    product = request.form.get("product", "").strip()
    quantity_kg = request.form.get("quantity_kg", "").strip()
    notes = request.form.get("notes", "").strip()

    if not harvest_date or product not in PRODUCT_TYPES or not quantity_kg:
        flash("Συμπλήρωσε ημερομηνία, είδος παραγωγής και ποσότητα.", "error")
        return redirect(url_for("fields.view_field", field_id=field_id))

    try:
        quantity_val = float(quantity_kg)
    except ValueError:
        flash("Η ποσότητα πρέπει να είναι αριθμός.", "error")
        return redirect(url_for("fields.view_field", field_id=field_id))

    db.execute(
        """INSERT INTO harvests (field_id, harvest_date, product, quantity_kg, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (field_id, harvest_date, product, quantity_val, notes or None),
    )
    db.commit()
    flash("Η παραγωγή καταχωρήθηκε.", "success")
    return redirect(url_for("fields.view_field", field_id=field_id))
