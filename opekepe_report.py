"""
Αναφορά-εξαγωγή κτημάτων για ΟΠΕΚΕΠΕ (Ενιαία Αίτηση Ενίσχυσης/ΟΣΔΕ) και
ΕΛΓΑ (Ενιαία Δήλωση Καλλιέργειας/Εκτροφής — ΔΚΕ).

ΣΗΜΑΝΤΙΚΟ: Οι δηλώσεις αυτές υποβάλλονται ΜΟΝΟ από τον ίδιο τον αγρότη,
ψηφιακά, με προσωπική σύνδεση TAXISnet, στο opekepe.gr και στο gov.gr.
Δεν υπάρχει δημόσιο API για αυτόματη υποβολή από εφαρμογή τρίτου, και η
Αγρόκτημα δεν ζητάει ποτέ κωδικούς TAXISnet. Αυτό που κάνει η σελίδα αυτή
είναι να μαζέψει τα στοιχεία που έχει ήδη καταγεγραμμένα ο αγρότης
(καλλιέργεια, έκταση, αριθμός δέντρων, τοποθεσία) σε μορφή έτοιμη για
αντιγραφή/επισύναψη όταν ο ίδιος συμπληρώνει τις επίσημες δηλώσεις.
"""
import io
from datetime import date

from flask import Blueprint, render_template, Response
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from db import get_db
from auth import role_required, current_user

bp = Blueprint("opekepe", __name__, url_prefix="/opekepe")

COLUMNS = ["Κτήμα", "Τοποθεσία", "Καλλιέργεια", "Έκταση (στρέμματα)", "Αριθμός δέντρων", "Συντεταγμένες"]


def _field_rows(db, farmer_id):
    fields = db.execute(
        "SELECT * FROM fields WHERE farmer_id = ? ORDER BY name", (farmer_id,)
    ).fetchall()
    rows = []
    for f in fields:
        coords = f"{f['latitude']:.5f}, {f['longitude']:.5f}" if f["latitude"] and f["longitude"] else "—"
        rows.append([
            f["name"],
            f["location"] or "—",
            f["crop"] or "—",
            f["area_stremma"] if f["area_stremma"] else "—",
            f["tree_count"] or 0,
            coords,
        ])
    return rows


@bp.route("/")
@role_required("farmer")
def overview():
    db = get_db()
    user = current_user()
    rows = _field_rows(db, user["id"])
    total_area = sum(r[3] for r in rows if isinstance(r[3], (int, float)))
    total_trees = sum(r[4] for r in rows if isinstance(r[4], (int, float)))
    return render_template(
        "opekepe/overview.html",
        rows=rows, columns=COLUMNS,
        total_area=total_area, total_trees=total_trees,
    )


@bp.route("/export.xlsx")
@role_required("farmer")
def export_xlsx():
    db = get_db()
    user = current_user()
    rows = _field_rows(db, user["id"])

    wb = Workbook()
    ws = wb.active
    ws.title = "Κτήματα"

    ws.append([f"Αναφορά κτημάτων — {user['name']} — {date.today().isoformat()}"])
    ws["A1"].font = Font(bold=True, size=13)
    ws.append([])
    ws.append(COLUMNS)
    for cell in ws[3]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for r in rows:
        ws.append(r)

    total_area = sum(r[3] for r in rows if isinstance(r[3], (int, float)))
    total_trees = sum(r[4] for r in rows if isinstance(r[4], (int, float)))
    ws.append([])
    ws.append(["Σύνολο", "", "", total_area, total_trees, ""])
    ws[ws.max_row][0].font = Font(bold=True)

    for col in ws.columns:
        max_len = max((len(str(c.value)) for c in col if c.value is not None), default=10)
        ws.column_dimensions[col[0].column_letter].width = max_len + 4

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        buf.read(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=agroktima-opekepe.xlsx"},
    )


@bp.route("/export.pdf")
@role_required("farmer")
def export_pdf():
    db = get_db()
    user = current_user()
    rows = _field_rows(db, user["id"])
    total_area = sum(r[3] for r in rows if isinstance(r[3], (int, float)))
    total_trees = sum(r[4] for r in rows if isinstance(r[4], (int, float)))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Αναφορά κτημάτων — Αγρόκτημα", styles["Title"]),
        Paragraph(f"{user['name']} · {date.today().isoformat()}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    table_data = [COLUMNS] + [[str(c) for c in r] for r in rows] + [
        ["Σύνολο", "", "", str(total_area), str(total_trees), ""]
    ]
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5B6B3E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F4F1E8")]),
        ("ALIGN", (3, 0), (4, -1), "CENTER"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(
        "Στοιχεία όπως τα έχει καταχωρήσει ο ίδιος ο χρήστης στην εφαρμογή Αγρόκτημα. "
        "Η υποβολή στον ΟΠΕΚΕΠΕ (opekepe.gr) και στον ΕΛΓΑ (gov.gr) γίνεται από τον ίδιο "
        "τον αγρότη με προσωπική σύνδεση TAXISnet — η εφαρμογή δεν υποβάλλει τίποτα αυτόματα.",
        styles["Italic"],
    ))
    doc.build(elements)
    buf.seek(0)

    return Response(
        buf.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=agroktima-opekepe.pdf"},
    )
