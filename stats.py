"""
Σύνοψη εξόδων ανά κτήμα, και εσόδων από υιοθεσίες δέντρων, για τον αγρότη.
"""
from flask import Blueprint, render_template
from db import get_db
from auth import role_required, current_user

bp = Blueprint("stats", __name__, url_prefix="/stats")


@bp.route("/")
@role_required("farmer")
def overview():
    db = get_db()
    user = current_user()

    field_costs = db.execute(
        """SELECT f.id, f.name, COALESCE(SUM(t.cost), 0) AS total_cost, COUNT(t.id) AS task_count
           FROM fields f
           LEFT JOIN tasks t ON t.field_id = f.id
           WHERE f.farmer_id = ?
           GROUP BY f.id
           ORDER BY total_cost DESC""",
        (user["id"],),
    ).fetchall()

    total_cost = sum(f["total_cost"] for f in field_costs)
    max_cost = max((f["total_cost"] for f in field_costs), default=0) or 1

    adoption_income = db.execute(
        """SELECT COALESCE(SUM(a.amount), 0) AS total, COUNT(a.id) AS count
           FROM adoptions a
           JOIN trees tr ON tr.id = a.tree_id
           WHERE tr.farmer_id = ? AND a.status = 'paid'""",
        (user["id"],),
    ).fetchone()

    tree_counts = db.execute(
        """SELECT
             COUNT(*) AS total,
             SUM(CASE WHEN status = 'adopted' THEN 1 ELSE 0 END) AS adopted
           FROM trees WHERE farmer_id = ?""",
        (user["id"],),
    ).fetchone()

    production_totals = db.execute(
        """SELECT h.product, SUM(h.quantity_kg) AS total_kg
           FROM harvests h
           JOIN fields f ON f.id = h.field_id
           WHERE f.farmer_id = ?
           GROUP BY h.product
           ORDER BY total_kg DESC""",
        (user["id"],),
    ).fetchall()

    return render_template(
        "stats/overview.html",
        field_costs=field_costs,
        total_cost=total_cost,
        max_cost=max_cost,
        adoption_income=adoption_income,
        tree_counts=tree_counts,
        production_totals=production_totals,
    )
