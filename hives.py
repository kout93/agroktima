"""
Μελίσσια (κυψέλες) προς υιοθεσία: διαχείριση από τον αγρότη, περιήγηση &
υιοθεσία από πελάτη. Ίδιο μοντέλο με τα δέντρα ελιάς (trees.py), αλλά για
μέλι αντί για λάδι — ξεχωριστοί πίνακες/routes ώστε να μη μπλέξουμε με τη
λειτουργία της υιοθεσίας δέντρων.

Η ίδια η παραγωγή μελιού (πόσα κιλά μαζεύτηκαν) καταγράφεται ήδη μέσω της
γενικής συγκομιδής ανά κτήμα (fields.py / harvests, με είδος "Μέλι") —
δεν χρειάζεται ξεχωριστό μηχανισμό. Οι επιθεωρήσεις/ενημερώσεις ανά
κυψέλη καταγράφονται εδώ (hive_updates), ακριβώς όπως και στα δέντρα.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db
from auth import role_required, current_user
from payments import create_checkout_session, IS_LIVE
from uploads import save_photo
from translations import t as _

bp = Blueprint("hives", __name__, url_prefix="/hives")


# ---------- Αγρότης: διαχείριση μελισσιών ----------

@bp.route("/manage")
@role_required("farmer")
def manage_hives():
    db = get_db()
    user = current_user()
    rows = db.execute(
        """SELECT h.*, f.name AS field_name, f.latitude AS field_latitude, f.longitude AS field_longitude
           FROM hives h LEFT JOIN fields f ON f.id = h.field_id
           WHERE h.farmer_id = ? ORDER BY h.created_at DESC""",
        (user["id"],),
    ).fetchall()
    fields = db.execute(
        "SELECT id, name, latitude, longitude FROM fields WHERE farmer_id = ?", (user["id"],)
    ).fetchall()
    return render_template("hives/manage.html", hives=rows, fields=fields)


@bp.route("/manage/new", methods=["POST"])
@role_required("farmer")
def new_hive():
    db = get_db()
    user = current_user()
    code = request.form.get("code", "").strip()
    field_id = request.form.get("field_id") or None
    est_min = request.form.get("est_honey_kg_min", "").strip()
    est_max = request.form.get("est_honey_kg_max", "").strip()
    price = request.form.get("price_per_year", "").strip()
    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()
    photo_filename = save_photo(request.files.get("photo"))

    if not code or not price:
        flash(_("Χρειάζεται τουλάχιστον κωδικός κυψέλης και τιμή."), "error")
        return redirect(url_for("hives.manage_hives"))

    db.execute(
        """INSERT INTO hives (farmer_id, field_id, code, est_honey_kg_min, est_honey_kg_max, price_per_year, latitude, longitude, photo_filename)
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
    flash(_("Η κυψέλη προστέθηκε προς υιοθεσία."), "success")
    return redirect(url_for("hives.manage_hives"))


@bp.route("/manage/<int:hive_id>/location", methods=["POST"])
@role_required("farmer")
def update_hive_location(hive_id):
    db = get_db()
    user = current_user()
    hive = db.execute(
        "SELECT * FROM hives WHERE id = ? AND farmer_id = ?", (hive_id, user["id"])
    ).fetchone()
    if hive is None:
        flash(_("Η κυψέλη δεν βρέθηκε."), "error")
        return redirect(url_for("hives.manage_hives"))

    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()
    if not latitude or not longitude:
        flash(_("Σημείωσε ένα σημείο στον χάρτη πρώτα."), "error")
        return redirect(url_for("hives.manage_hives"))

    db.execute(
        "UPDATE hives SET latitude = ?, longitude = ? WHERE id = ?",
        (float(latitude), float(longitude), hive_id),
    )
    db.commit()
    flash(_("Η θέση της κυψέλης ενημερώθηκε."), "success")
    return redirect(url_for("hives.manage_hives"))


@bp.route("/manage/<int:hive_id>/photo", methods=["POST"])
@role_required("farmer")
def update_hive_photo(hive_id):
    db = get_db()
    user = current_user()
    hive = db.execute(
        "SELECT * FROM hives WHERE id = ? AND farmer_id = ?", (hive_id, user["id"])
    ).fetchone()
    if hive is None:
        flash(_("Η κυψέλη δεν βρέθηκε."), "error")
        return redirect(url_for("hives.manage_hives"))

    photo_filename = save_photo(request.files.get("photo"))
    if photo_filename:
        db.execute("UPDATE hives SET photo_filename = ? WHERE id = ?", (photo_filename, hive_id))
        db.commit()
        flash(_("Η φωτογραφία της κυψέλης ενημερώθηκε."), "success")
    else:
        flash(_("Δεν ανέβηκε έγκυρη φωτογραφία."), "error")
    return redirect(url_for("hives.manage_hives"))


@bp.route("/manage/<int:hive_id>/update", methods=["POST"])
@role_required("farmer")
def add_update(hive_id):
    db = get_db()
    user = current_user()
    hive = db.execute(
        "SELECT * FROM hives WHERE id = ? AND farmer_id = ?", (hive_id, user["id"])
    ).fetchone()
    if hive is None:
        flash(_("Η κυψέλη δεν βρέθηκε."), "error")
        return redirect(url_for("hives.manage_hives"))

    message = request.form.get("message", "").strip()
    photo_filename = save_photo(request.files.get("photo"))
    if message:
        db.execute(
            """INSERT INTO hive_updates (hive_id, update_date, message, photo_filename)
               VALUES (?, ?, ?, ?)""",
            (hive_id, datetime.now().strftime("%Y-%m-%d"), message, photo_filename),
        )
        db.commit()
        flash(_("Η ενημέρωση προστέθηκε."), "success")
    else:
        flash(_("Χρειάζεται τουλάχιστον κείμενο για την ενημέρωση."), "error")
    return redirect(url_for("hives.manage_hives"))


# ---------- Πελάτης: περιήγηση & υιοθεσία ----------

@bp.route("/")
def browse():
    db = get_db()
    rows = db.execute(
        """SELECT h.*, f.name AS field_name, f.location AS field_location,
                  COALESCE(h.latitude, f.latitude) AS display_latitude,
                  COALESCE(h.longitude, f.longitude) AS display_longitude,
                  u.name AS farmer_name
           FROM hives h
           LEFT JOIN fields f ON f.id = h.field_id
           JOIN users u ON u.id = h.farmer_id
           WHERE h.status = 'available'
           ORDER BY h.created_at DESC"""
    ).fetchall()
    return render_template("hives/browse.html", hives=rows)


@bp.route("/<int:hive_id>")
def view_hive(hive_id):
    db = get_db()
    hive = db.execute(
        """SELECT h.*, f.name AS field_name, f.location AS field_location,
                  COALESCE(h.latitude, f.latitude) AS display_latitude,
                  COALESCE(h.longitude, f.longitude) AS display_longitude,
                  u.name AS farmer_name
           FROM hives h
           LEFT JOIN fields f ON f.id = h.field_id
           JOIN users u ON u.id = h.farmer_id
           WHERE h.id = ?""",
        (hive_id,),
    ).fetchone()
    if hive is None:
        flash(_("Η κυψέλη δεν βρέθηκε."), "error")
        return redirect(url_for("hives.browse"))

    updates = db.execute(
        "SELECT * FROM hive_updates WHERE hive_id = ? ORDER BY update_date DESC",
        (hive_id,),
    ).fetchall()
    return render_template("hives/view.html", hive=hive, updates=updates)


@bp.route("/<int:hive_id>/adopt", methods=["POST"])
@role_required("customer")
def adopt(hive_id):
    db = get_db()
    user = current_user()
    hive = db.execute("SELECT * FROM hives WHERE id = ?", (hive_id,)).fetchone()
    if hive is None or hive["status"] != "available":
        flash(_("Αυτή η κυψέλη δεν είναι πλέον διαθέσιμη."), "error")
        return redirect(url_for("hives.browse"))

    year = datetime.now().year
    cur = db.execute(
        """INSERT INTO hive_adoptions (hive_id, customer_id, season_year, amount, status)
           VALUES (?, ?, ?, ?, 'pending')""",
        (hive_id, user["id"], year, hive["price_per_year"]),
    )
    db.commit()
    adoption_id = cur.lastrowid
    adoption = db.execute("SELECT * FROM hive_adoptions WHERE id = ?", (adoption_id,)).fetchone()

    success_url = url_for("hives.checkout_success", adoption_id=adoption_id, _external=True)
    cancel_url = url_for("hives.view_hive", hive_id=hive_id, _external=True)
    checkout_url, session_id = create_checkout_session(
        adoption, hive, success_url, cancel_url,
        item_label="κυψέλης", test_checkout_prefix="/hives/checkout/test",
    )

    if session_id:
        db.execute("UPDATE hive_adoptions SET stripe_session_id = ? WHERE id = ?", (session_id, adoption_id))
        db.commit()

    return redirect(checkout_url)


@bp.route("/checkout/test/<int:adoption_id>")
@role_required("customer")
def checkout_test(adoption_id):
    """Σελίδα προσομοίωσης πληρωμής — ενεργή μόνο όταν δεν υπάρχει πραγματικό κλειδί Stripe."""
    if IS_LIVE:
        flash(_("Η δοκιμαστική πληρωμή δεν είναι διαθέσιμη (έχει ρυθμιστεί πραγματικό Stripe)."), "error")
        return redirect(url_for("hives.browse"))

    db = get_db()
    user = current_user()
    adoption = db.execute(
        "SELECT * FROM hive_adoptions WHERE id = ? AND customer_id = ?", (adoption_id, user["id"])
    ).fetchone()
    if adoption is None:
        flash(_("Η υιοθεσία δεν βρέθηκε."), "error")
        return redirect(url_for("hives.browse"))
    hive = db.execute("SELECT * FROM hives WHERE id = ?", (adoption["hive_id"],)).fetchone()
    return render_template("hives/checkout_test.html", adoption=adoption, hive=hive)


@bp.route("/checkout/test/<int:adoption_id>/confirm", methods=["POST"])
@role_required("customer")
def checkout_test_confirm(adoption_id):
    db = get_db()
    user = current_user()
    adoption = db.execute(
        "SELECT * FROM hive_adoptions WHERE id = ? AND customer_id = ?", (adoption_id, user["id"])
    ).fetchone()
    if adoption is None:
        flash(_("Η υιοθεσία δεν βρέθηκε."), "error")
        return redirect(url_for("hives.browse"))

    _mark_adoption_paid(db, adoption)
    flash(_("Η (δοκιμαστική) πληρωμή ολοκληρώθηκε — η κυψέλη είναι δική σου!"), "success")
    return redirect(url_for("trees.my_adoptions"))


@bp.route("/checkout/success")
@role_required("customer")
def checkout_success():
    """Επιστροφή από πραγματικό Stripe Checkout."""
    adoption_id = request.args.get("adoption_id")
    db = get_db()
    adoption = db.execute("SELECT * FROM hive_adoptions WHERE id = ?", (adoption_id,)).fetchone()
    if adoption and adoption["status"] != "paid":
        _mark_adoption_paid(db, adoption)
    flash(_("Η πληρωμή ολοκληρώθηκε — η κυψέλη είναι δική σου!"), "success")
    return redirect(url_for("trees.my_adoptions"))


def _mark_adoption_paid(db, adoption):
    db.execute(
        "UPDATE hive_adoptions SET status = 'paid', paid_at = datetime('now') WHERE id = ?",
        (adoption["id"],),
    )
    db.execute("UPDATE hives SET status = 'adopted' WHERE id = ?", (adoption["hive_id"],))
    db.commit()
