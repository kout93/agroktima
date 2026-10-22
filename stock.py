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
        product_options=[r["product"] for r in stock_rows],
        reasons=OUTFLOW_REASONS,
    )


def _parse_outflow_form(form):
    """Διαβάζει και ελέγχει τη φόρμα διάθεσης. Επιστρέφει (data, error)."""
    product = form.get("product", "").strip()
    quantity_kg = form.get("quantity_kg", "").strip().replace(",", ".")
    outflow_date = form.get("outflow_date", "").strip()
    reason = form.get("reason", "").strip()
    notes = form.get("notes", "").strip()
    buyer = form.get("buyer", "").strip()
    amount_raw = form.get("amount_eur", "").strip().replace(",", ".")

    if not product or not quantity_kg or not outflow_date or reason not in OUTFLOW_REASONS:
        return None, "Συμπλήρωσε είδος, ποσότητα, ημερομηνία και αιτία."
    try:
        qty = float(quantity_kg)
    except ValueError:
        return None, "Η ποσότητα πρέπει να είναι αριθμός."
    if qty <= 0:
        return None, "Η ποσότητα πρέπει να είναι θετικός αριθμός."

    amount_eur = None
    if amount_raw:
        try:
            amount_eur = float(amount_raw)
        except ValueError:
            return None, "Το ποσό πρέπει να είναι αριθμός."
        if amount_eur < 0:
            return None, "Το ποσό δεν μπορεί να είναι αρνητικό."
    if reason != "Πώληση":
        amount_eur = None
        buyer = ""
    return {
        "product": product, "qty": qty, "date": outflow_date, "reason": reason,
        "notes": notes or None, "buyer": buyer or None, "amount_eur": amount_eur,
    }, None


@bp.route("/new", methods=["POST"])
@role_required("farmer")
def new_outflow():
    db = get_db()
    user = current_user()
    data, err = _parse_outflow_form(request.form)
    if err:
        flash(err, "error")
        return redirect(url_for("stock.overview"))

    current = {r["product"]: r["available"] for r in _stock_levels(db, user["id"])}
    if data["product"] not in current:
        flash(f"Δεν έχεις καταχωρημένη συγκομιδή «{data['product']}» — πρόσθεσέ την πρώτα από τη σελίδα του κτήματος.", "error")
        return redirect(url_for("stock.overview"))
    available = current.get(data["product"], 0)
    if data["qty"] > available:
        flash(f"Δεν έχεις τόσο απόθεμα «{data['product']}» — διαθέσιμο αυτή τη στιγμή: {available:.1f} κιλά.", "error")
        return redirect(url_for("stock.overview"))

    db.execute(
        """INSERT INTO stock_outflows (farmer_id, product, quantity_kg, outflow_date, reason, notes, amount_eur, buyer)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user["id"], data["product"], data["qty"], data["date"], data["reason"], data["notes"], data["amount_eur"], data["buyer"]),
    )
    db.commit()
    flash("Η διάθεση καταχωρήθηκε.", "success")
    return redirect(url_for("stock.overview"))


@bp.route("/<int:outflow_id>/edit", methods=["GET", "POST"])
@role_required("farmer")
def edit_outflow(outflow_id):
    db = get_db()
    user = current_user()
    row = db.execute(
        "SELECT * FROM stock_outflows WHERE id = ? AND farmer_id = ?", (outflow_id, user["id"])
    ).fetchone()
    if row is None:
        flash("Η καταχώρηση δεν βρέθηκε.", "error")
        return redirect(url_for("stock.overview"))

    if request.method == "POST":
        data, err = _parse_outflow_form(request.form)
        if err:
            flash(err, "error")
            return redirect(url_for("stock.edit_outflow", outflow_id=outflow_id))
        # διαθέσιμο απόθεμα χωρίς αυτή την καταχώρηση
        levels = {r["product"]: r["available"] for r in _stock_levels(db, user["id"])}
        available = levels.get(data["product"], 0)
        if data["product"] == row["product"]:
            available += row["quantity_kg"]
        if data["qty"] > available + 1e-9:
            flash(f"Δεν έχεις τόσο απόθεμα «{data['product']}» — διαθέσιμο: {available:.1f} κιλά.", "error")
            return redirect(url_for("stock.edit_outflow", outflow_id=outflow_id))
        db.execute(
            """UPDATE stock_outflows SET product=?, quantity_kg=?, outflow_date=?, reason=?, notes=?, amount_eur=?, buyer=?
               WHERE id=?""",
            (data["product"], data["qty"], data["date"], data["reason"], data["notes"], data["amount_eur"], data["buyer"], outflow_id),
        )
        db.commit()
        flash("Η καταχώρηση ενημερώθηκε.", "success")
        return redirect(url_for("stock.overview"))

    products = sorted({r["product"] for r in _stock_levels(db, user["id"])} | {row["product"]})
    return render_template("stock/edit.html", o=row, product_options=products, reasons=OUTFLOW_REASONS)


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
