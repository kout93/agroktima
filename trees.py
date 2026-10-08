"""
Δέντρα προς υιοθεσία: διαχείριση από τον αγρότη, περιήγηση & υιοθεσία από πελάτη.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db
from auth import role_required, current_user
from payments import create_checkout_session, IS_LIVE
from uploads import save_photo
from translations import t as _

bp = Blueprint("trees", __name__, url_prefix="/trees")


# ---------- Αγρότης: διαχείριση δέντρων ----------

@bp.route("/manage")
@role_required("farmer")
def manage_trees():
    db = get_db()
    user = current_user()
    rows = db.execute(
        """SELECT tr.*, f.name AS field_name, f.latitude AS field_latitude, f.longitude AS field_longitude
           FROM trees tr LEFT JOIN fields f ON f.id = tr.field_id
           WHERE tr.farmer_id = ? ORDER BY tr.created_at DESC""",
        (user["id"],),
    ).fetchall()
    fields = db.execute(
        "SELECT id, name, latitude, longitude FROM fields WHERE farmer_id = ?", (user["id"],)
    ).fetchall()
    return render_template("trees/manage.html", trees=rows, fields=fields)


@bp.route("/manage/new", methods=["POST"])
@role_required("farmer")
def new_tree():
    db = get_db()
    user = current_user()
    code = request.form.get("code", "").strip()
    field_id = request.form.get("field_id") or None
    est_min = request.form.get("est_oil_kg_min", "").strip()
    est_max = request.form.get("est_oil_kg_max", "").strip()
    price = request.form.get("price_per_year", "").strip()
    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()
    photo_filename = save_photo(request.files.get("photo"))

    if not code or not price:
        flash(_("Χρειάζεται τουλάχιστον κωδικός δέντρου και τιμή."), "error")
        return redirect(url_for("trees.manage_trees"))

    db.execute(
        """INSERT INTO trees (farmer_id, field_id, code, est_oil_kg_min, est_oil_kg_max, price_per_year, latitude, longitude, photo_filename)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user["id"],
            int(field_id) if field_id else None,
            code,
            float(est_min) if est_min else None,
            float(est_max) if est_max else None,
            float(price),
            float(latitude) if latitude else None,
            float(longitude) if longitude else None,
            photo_filename,
        ),
    )
    db.commit()
    flash(_("Το δέντρο προστέθηκε προς υιοθεσία."), "success")
    return redirect(url_for("trees.manage_trees"))


@bp.route("/manage/<int:tree_id>/location", methods=["POST"])
@role_required("farmer")
def update_tree_location(tree_id):
    db = get_db()
    user = current_user()
    tree = db.execute(
        "SELECT * FROM trees WHERE id = ? AND farmer_id = ?", (tree_id, user["id"])
    ).fetchone()
    if tree is None:
        flash(_("Το δέντρο δεν βρέθηκε."), "error")
        return redirect(url_for("trees.manage_trees"))

    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()
    if not latitude or not longitude:
        flash(_("Σημείωσε ένα σημείο στον χάρτη πρώτα."), "error")
        return redirect(url_for("trees.manage_trees"))

    db.execute(
        "UPDATE trees SET latitude = ?, longitude = ? WHERE id = ?",
        (float(latitude), float(longitude), tree_id),
    )
    db.commit()
    flash(_("Η θέση του δέντρου ενημερώθηκε."), "success")
    return redirect(url_for("trees.manage_trees"))


@bp.route("/manage/<int:tree_id>/photo", methods=["POST"])
@role_required("farmer")
def update_tree_photo(tree_id):
    db = get_db()
    user = current_user()
    tree = db.execute(
        "SELECT * FROM trees WHERE id = ? AND farmer_id = ?", (tree_id, user["id"])
    ).fetchone()
    if tree is None:
        flash(_("Το δέντρο δεν βρέθηκε."), "error")
        return redirect(url_for("trees.manage_trees"))

    photo_filename = save_photo(request.files.get("photo"))
    if photo_filename:
        db.execute("UPDATE trees SET photo_filename = ? WHERE id = ?", (photo_filename, tree_id))
        db.commit()
        flash(_("Η φωτογραφία του δέντρου ενημερώθηκε."), "success")
    else:
        flash(_("Δεν ανέβηκε έγκυρη φωτογραφία."), "error")
    return redirect(url_for("trees.manage_trees"))


@bp.route("/manage/<int:tree_id>/update", methods=["POST"])
@role_required("farmer")
def add_update(tree_id):
    db = get_db()
    user = current_user()
    tree = db.execute(
        "SELECT * FROM trees WHERE id = ? AND farmer_id = ?", (tree_id, user["id"])
    ).fetchone()
    if tree is None:
        flash(_("Το δέντρο δεν βρέθηκε."), "error")
        return redirect(url_for("trees.manage_trees"))

    message = request.form.get("message", "").strip()
    photo_filename = save_photo(request.files.get("photo"))
    if message:
        db.execute(
            """INSERT INTO production_updates (tree_id, update_date, message, photo_filename)
               VALUES (?, ?, ?, ?)""",
            (tree_id, datetime.now().strftime("%Y-%m-%d"), message, photo_filename),
        )
        db.commit()
        flash(_("Η ενημέρωση προστέθηκε."), "success")
    else:
        flash(_("Χρειάζεται τουλάχιστον κείμενο για την ενημέρωση."), "error")
    return redirect(url_for("trees.manage_trees"))


# ---------- Πελάτης: περιήγηση & υιοθεσία ----------

@bp.route("/")
def browse():
    db = get_db()
    rows = db.execute(
        """SELECT tr.*, f.name AS field_name, f.location AS field_location,
                  COALESCE(tr.latitude, f.latitude) AS display_latitude,
                  COALESCE(tr.longitude, f.longitude) AS display_longitude,
                  u.name AS farmer_name
           FROM trees tr
           LEFT JOIN fields f ON f.id = tr.field_id
           JOIN users u ON u.id = tr.farmer_id
           WHERE tr.status = 'available'
           ORDER BY tr.created_at DESC"""
    ).fetchall()
    return render_template("trees/browse.html", trees=rows)


@bp.route("/<int:tree_id>")
def view_tree(tree_id):
    db = get_db()
    tree = db.execute(
        """SELECT tr.*, f.name AS field_name, f.location AS field_location,
                  COALESCE(tr.latitude, f.latitude) AS display_latitude,
                  COALESCE(tr.longitude, f.longitude) AS display_longitude,
                  u.name AS farmer_name
           FROM trees tr
           LEFT JOIN fields f ON f.id = tr.field_id
           JOIN users u ON u.id = tr.farmer_id
           WHERE tr.id = ?""",
        (tree_id,),
    ).fetchone()
    if tree is None:
        flash(_("Το δέντρο δεν βρέθηκε."), "error")
        return redirect(url_for("trees.browse"))

    updates = db.execute(
        "SELECT * FROM production_updates WHERE tree_id = ? ORDER BY update_date DESC",
        (tree_id,),
    ).fetchall()
    return render_template("trees/view.html", tree=tree, updates=updates)


@bp.route("/<int:tree_id>/adopt", methods=["POST"])
@role_required("customer")
def adopt(tree_id):
    db = get_db()
    user = current_user()
    tree = db.execute("SELECT * FROM trees WHERE id = ?", (tree_id,)).fetchone()
    if tree is None or tree["status"] != "available":
        flash(_("Αυτό το δέντρο δεν είναι πλέον διαθέσιμο."), "error")
        return redirect(url_for("trees.browse"))

    year = datetime.now().year
    cur = db.execute(
        """INSERT INTO adoptions (tree_id, customer_id, season_year, amount, status)
           VALUES (?, ?, ?, ?, 'pending')""",
        (tree_id, user["id"], year, tree["price_per_year"]),
    )
    db.commit()
    adoption_id = cur.lastrowid
    adoption = db.execute("SELECT * FROM adoptions WHERE id = ?", (adoption_id,)).fetchone()

    success_url = url_for("trees.checkout_success", adoption_id=adoption_id, _external=True)
    cancel_url = url_for("trees.view_tree", tree_id=tree_id, _external=True)
    checkout_url, session_id = create_checkout_session(adoption, tree, success_url, cancel_url)

    if session_id:
        db.execute("UPDATE adoptions SET stripe_session_id = ? WHERE id = ?", (session_id, adoption_id))
        db.commit()

    return redirect(checkout_url)


@bp.route("/checkout/test/<int:adoption_id>")
@role_required("customer")
def checkout_test(adoption_id):
    """Σελίδα προσομοίωσης πληρωμής — ενεργή μόνο όταν δεν υπάρχει πραγματικό κλειδί Stripe."""
    if IS_LIVE:
        flash(_("Η δοκιμαστική πληρωμή δεν είναι διαθέσιμη (έχει ρυθμιστεί πραγματικό Stripe)."), "error")
        return redirect(url_for("trees.browse"))

    db = get_db()
    user = current_user()
    adoption = db.execute(
        "SELECT * FROM adoptions WHERE id = ? AND customer_id = ?", (adoption_id, user["id"])
    ).fetchone()
    if adoption is None:
        flash(_("Η υιοθεσία δεν βρέθηκε."), "error")
        return redirect(url_for("trees.browse"))
    tree = db.execute("SELECT * FROM trees WHERE id = ?", (adoption["tree_id"],)).fetchone()
    return render_template("trees/checkout_test.html", adoption=adoption, tree=tree)


@bp.route("/checkout/test/<int:adoption_id>/confirm", methods=["POST"])
@role_required("customer")
def checkout_test_confirm(adoption_id):
    db = get_db()
    user = current_user()
    adoption = db.execute(
        "SELECT * FROM adoptions WHERE id = ? AND customer_id = ?", (adoption_id, user["id"])
    ).fetchone()
    if adoption is None:
        flash(_("Η υιοθεσία δεν βρέθηκε."), "error")
        return redirect(url_for("trees.browse"))

    _mark_adoption_paid(db, adoption)
    flash(_("Η (δοκιμαστική) πληρωμή ολοκληρώθηκε — το δέντρο είναι δικό σου!"), "success")
    return redirect(url_for("trees.my_adoptions"))


@bp.route("/checkout/success")
@role_required("customer")
def checkout_success():
    """Επιστροφή από πραγματικό Stripe Checkout."""
    adoption_id = request.args.get("adoption_id")
    db = get_db()
    adoption = db.execute("SELECT * FROM adoptions WHERE id = ?", (adoption_id,)).fetchone()
    if adoption and adoption["status"] != "paid":
        _mark_adoption_paid(db, adoption)
    flash(_("Η πληρωμή ολοκληρώθηκε — το δέντρο είναι δικό σου!"), "success")
    return redirect(url_for("trees.my_adoptions"))


def _mark_adoption_paid(db, adoption):
    db.execute(
        "UPDATE adoptions SET status = 'paid', paid_at = datetime('now') WHERE id = ?",
        (adoption["id"],),
    )
    db.execute("UPDATE trees SET status = 'adopted' WHERE id = ?", (adoption["tree_id"],))
    db.commit()


@bp.route("/my-adoptions")
@role_required("customer")
def my_adoptions():
    db = get_db()
    user = current_user()
    tree_rows = db.execute(
        """SELECT a.*, 'tree' AS kind, tr.code, tr.est_oil_kg_min, tr.est_oil_kg_max, tr.photo_filename,
                  COALESCE(tr.latitude, f.latitude) AS display_latitude,
                  COALESCE(tr.longitude, f.longitude) AS display_longitude,
                  f.name AS field_name, u.name AS farmer_name
           FROM adoptions a
           JOIN trees tr ON tr.id = a.tree_id
           LEFT JOIN fields f ON f.id = tr.field_id
           JOIN users u ON u.id = tr.farmer_id
           WHERE a.customer_id = ?""",
        (user["id"],),
    ).fetchall()
    hive_rows = db.execute(
        """SELECT a.*, 'hive' AS kind, h.code,
                  h.est_honey_kg_min AS est_oil_kg_min, h.est_honey_kg_max AS est_oil_kg_max,
                  h.photo_filename,
                  COALESCE(h.latitude, f.latitude) AS display_latitude,
                  COALESCE(h.longitude, f.longitude) AS display_longitude,
                  f.name AS field_name, u.name AS farmer_name
           FROM hive_adoptions a
           JOIN hives h ON h.id = a.hive_id
           LEFT JOIN fields f ON f.id = h.field_id
           JOIN users u ON u.id = h.farmer_id
           WHERE a.customer_id = ?""",
        (user["id"],),
    ).fetchall()
    rows = sorted(list(tree_rows) + list(hive_rows), key=lambda r: r["created_at"], reverse=True)
    return render_template("trees/my_adoptions.html", adoptions=rows)
