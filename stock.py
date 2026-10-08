"""
Απόθεμα παραγωγής: πόσο από ό,τι μάζεψε ο αγρότης (σύνολο από τις
καταχωρημένες συγκομιδές, σε όλα τα κτήματά του) έχει ακόμα αδιάθετο, και
πόσο έχει ήδη βγει (πουλήθηκε, δόθηκε σε πελάτη, καταναλώθηκε, χάθηκε).

Τρέχον απόθεμα ανά είδος = σύνολο συγκομιδών (harvests) − σύνολο διαθέσεων
(stock_outflows). Δεν επιτρέπεται να καταχωρηθεί διάθεση μεγαλύτερη από το
διαθέσιμο απόθεμα — πραγματικός έλεγχος, όχι demo.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db
from auth import role_required, current_user
from fields import PRODUCT_TYPES

bp = Blueprint("stock", __name__, url_prefix="/stock")

OUTFLOW_REASONS = ["Πώληση", "Διάθεση σε πελάτη", "Προσωπική χρήση", "Απώλεια/Φύρα", "Άλλο"]


def _stock_levels(db, farmer_id):
    harvested = db.execute(
        """SELECT h.product, SUM(h.quantity_kg) AS total_kg
           FROM harvests h JOIN fields f ON f.id = h.field_id
           WHERE f.farmer_id = ? GROUP BY h.product""",
        (farmer_id,),
    ).fetchall()
    harvested_map = {r["product"]: r["total_kg"] or 0 for r in harvested}

    outflows = db.execute(
        "SELECT product, SUM(quantity_kg) AS total_kg FROM stock_outflows WHERE farmer_id = ? GROUP BY product",
        (farmer_id,),
    ).fetchall()
    outflow_map = {r["product"]: r["total_kg"] or 0 for r in outflows}

    products = sorted(set(harvested_map) | set(outflow_map))
    rows = []
    for p in products:
        in_kg = harvested_map.get(p, 0)
        out_kg = outflow_map.get(p, 0)
        rows.append({"product": p, "harvested": in_kg, "out": out_kg, "available": in_kg - out_kg})
    return rows


@bp.route("/")
@role_required("farmer")
def overview():
    db = get_db()
    user = current_user()

    stock_rows = _stock_levels(db, user["id"])
    outflow_history = db.execute(
        "SELECT * FROM stock_outflows WHERE farmer_id = ? ORDER BY outflow_date DESC, id DESC",
        (user["id"],),
    ).fetchall()

    return render_template(
        "stock/overview.html",
        stock_rows=stock_rows,
        outflow_history=outflow_history,
        product_types=PRODUCT_TYPES,
        reasons=OUTFLOW_REASONS,
    )


@bp.route("/new", methods=["POST"])
@role_required("farmer")
def new_outflow():
    db = get_db()
    user = current_user()

    product = request.form.get("product", "").strip()
    quantity_kg = request.form.get("quantity_kg", "").strip()
    outflow_date = request.form.get("outflow_date", "").strip()
    reason = request.form.get("reason", "").strip()
    notes = request.form.get("notes", "").strip()

    if product not in PRODUCT_TYPES or not quantity_kg or not outflow_date or reason not in OUTFLOW_REASONS:
        flash("Συμπλήρωσε είδος, ποσότητα, ημερομηνία και αιτία.", "error")
        return redirect(url_for("stock.overview"))

    try:
        qty = float(quantity_kg)
    except ValueError:
        flash("Η ποσότητα πρέπει να είναι αριθμός.", "error")
        return redirect(url_for("stock.overview"))

    if qty <= 0:
        flash("Η ποσότητα πρέπει να είναι θετικός αριθμός.", "error")
        return redirect(url_for("stock.overview"))

    current = {r["product"]: r["available"] for r in _stock_levels(db, user["id"])}
    available = current.get(product, 0)
    if qty > available:
        flash(f"Δεν έχεις τόσο απόθεμα «{product}» — διαθέσιμο αυτή τη στιγμή: {available:.1f} κιλά.", "error")
        return redirect(url_for("stock.overview"))

    db.execute(
        """INSERT INTO stock_outflows (farmer_id, product, quantity_kg, outflow_date, reason, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user["id"], product, qty, outflow_date, reason, notes or None),
    )
    db.commit()
    flash("Η διάθεση καταχωρήθηκε.", "success")
    return redirect(url_for("stock.overview"))


@bp.route("/<int:outflow_id>/delete", methods=["POST"])
@role_required("farmer")
def delete_outflow(outflow_id):
    db = get_db()
    user = current_user()
    row = db.execute(
        "SELECT * FROM stock_outflows WHERE id = ? AND farmer_id = ?", (outflow_id, user["id"])
    ).fetchone()
    if row is None:
        flash("Η καταχώρηση δεν βρέθηκε.", "error")
        return redirect(url_for("stock.overview"))

    db.execute("DELETE FROM stock_outflows WHERE id = ?", (outflow_id,))
    db.commit()
    flash("Η καταχώρηση διαγράφηκε.", "success")
    return redirect(url_for("stock.overview"))
