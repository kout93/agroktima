"""
Συμβουλές AI για τον αγρότη, βασισμένες στα δικά του καταγεγραμμένα δεδομένα.

Πραγματική λειτουργία: αν υπάρχει το πακέτο "anthropic" εγκατεστημένο ΚΑΙ
έχει οριστεί το περιβαλλοντικό μεταβλητό ANTHROPIC_API_KEY, οι ερωτήσεις
στέλνονται σε πραγματικό μοντέλο Claude μαζί με περίληψη των κτημάτων,
εργασιών και δέντρων του αγρότη, για πραγματικά εξατομικευμένη συμβουλή.

Λειτουργία χωρίς κλειδί (π.χ. τώρα, σε αυτό το sandbox χωρίς πρόσβαση σε
εξωτερικό AI API): δίνονται βασικές, κανόνα-βασισμένες συμβουλές φτιαγμένες
από τα ίδια τα δεδομένα του αγρότη (πότε έγινε η τελευταία εργασία κάθε
τύπου, πόσο καιρό πέρασε) — πραγματικά χρήσιμες, απλά όχι ελεύθερου
κειμένου από μοντέλο. Η απάντηση λέει καθαρά ποιο από τα δύο έγινε.

Για να ενεργοποιηθούν οι πραγματικές συμβουλές AI:
  1. pip install anthropic
  2. export ANTHROPIC_API_KEY="sk-ant-..."
"""
import os
from datetime import datetime, date

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
IS_LIVE = _ANTHROPIC_AVAILABLE and bool(ANTHROPIC_API_KEY)

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "Είσαι ένας έμπειρος γεωπόνος-σύμβουλος μέσα σε μια εφαρμογή διαχείρισης "
    "αγροκτήματος στην Ελλάδα. Σου δίνεται περίληψη των κτημάτων, εργασιών και "
    "δέντρων ενός συγκεκριμένου αγρότη, και μια ερώτησή του. Απάντησε στα "
    "ελληνικά, πρακτικά και σύντομα (3-6 προτάσεις ή μια μικρή λίστα), "
    "βασισμένος στα δεδομένα που σου δίνονται όταν είναι σχετικά. Αν η "
    "ερώτηση χρειάζεται στοιχεία που δεν έχεις (π.χ. συγκεκριμένη ασθένεια "
    "φυτού χωρίς φωτογραφία), πες το καθαρά και πρότεινε το επόμενο βήμα "
    "(π.χ. επικοινωνία με τοπικό γεωπόνο). Μην επινοείς δεδομένα που δεν "
    "βλέπεις στην περίληψη."
)


def build_context_summary(db, farmer_id):
    """Μαζεύει περίληψη των δεδομένων του αγρότη, για να τροφοδοτήσει το AI
    (ή τη λειτουργία χωρίς AI) με πραγματικό context, όχι γενικότητες."""
    fields = db.execute(
        "SELECT id, name, crop, area_stremma, tree_count FROM fields WHERE farmer_id = ?",
        (farmer_id,),
    ).fetchall()

    lines = []
    if not fields:
        lines.append("Ο αγρότης δεν έχει καταχωρήσει ακόμα κανένα κτήμα.")
        return "\n".join(lines), []

    field_task_info = []
    for f in fields:
        last_tasks = db.execute(
            """SELECT task_type, MAX(task_date) AS last_date
               FROM tasks WHERE field_id = ? GROUP BY task_type""",
            (f["id"],),
        ).fetchall()
        task_summary = ", ".join(
            f"{t['task_type']}: τελευταία φορά {t['last_date']}" for t in last_tasks
        ) or "καμία καταχωρημένη εργασία ακόμα"

        lines.append(
            f"- Κτήμα «{f['name']}»"
            + (f" ({f['crop']})" if f["crop"] else "")
            + (f", {f['area_stremma']} στρέμματα" if f["area_stremma"] else "")
            + f". Εργασίες: {task_summary}."
        )
        field_task_info.append({"field": f, "last_tasks": {t["task_type"]: t["last_date"] for t in last_tasks}})

    tree_counts = db.execute(
        "SELECT COUNT(*) AS total, SUM(CASE WHEN status='adopted' THEN 1 ELSE 0 END) AS adopted FROM trees WHERE farmer_id = ?",
        (farmer_id,),
    ).fetchone()
    if tree_counts and tree_counts["total"]:
        lines.append(f"- Δέντρα προς υιοθεσία: {tree_counts['total']} σύνολο, {tree_counts['adopted'] or 0} υιοθετημένα.")

    return "\n".join(lines), field_task_info


def _days_since(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (date.today() - d).days
    except (ValueError, TypeError):
        return None


def _fallback_advice(question, field_task_info):
    """Απλές, κανόνα-βασισμένες συμβουλές από τα πραγματικά δεδομένα του
    αγρότη, όταν δεν υπάρχει συνδεδεμένο μοντέλο AI."""
    if not field_task_info:
        return (
            "Δεν έχεις ακόμα κανένα κτήμα καταχωρημένο, οπότε δεν μπορώ να δώσω "
            "εξατομικευμένη συμβουλή. Πρόσθεσε πρώτα ένα κτήμα και κατέγραψε "
            "μερικές εργασίες — τότε οι συμβουλές εδώ θα βασίζονται στο δικό σου "
            "ιστορικό."
        )

    notes = []
    for info in field_task_info:
        field = info["field"]
        last = info["last_tasks"]

        watering_days = _days_since(last.get("Πότισμα"))
        if watering_days is not None and watering_days >= 7:
            notes.append(f"Στο «{field['name']}» το τελευταίο πότισμα ήταν πριν {watering_days} μέρες — ίσως χρειάζεται έλεγχος.")

        fert_days = _days_since(last.get("Λίπανση"))
        if fert_days is not None and fert_days >= 60:
            notes.append(f"Στο «{field['name']}» η τελευταία λίπανση ήταν πριν {fert_days} μέρες.")

        if not last:
            notes.append(f"Στο «{field['name']}» δεν έχει καταχωρηθεί καμία εργασία ακόμα — ξεκίνα καταγράφοντας την επόμενη.")

    header = (
        "🧪 Βασικές συμβουλές από το ιστορικό σου (χωρίς συνδεδεμένο AI μοντέλο "
        "αυτή τη στιγμή):\n\n"
    )
    if notes:
        body = "\n".join(f"• {n}" for n in notes)
    else:
        body = "Τα κτήματά σου φαίνονται ενημερωμένα με βάση το ιστορικό εργασιών — καμία άμεση ανησυχία."

    footer = (
        "\n\nΗ ερώτησή σου: «"
        + question
        + "» χρειάζεται πιο εξειδικευμένη ανάλυση — ενεργοποίησε πραγματικό AI "
        "(βλέπε README) για πλήρεις, προσαρμοσμένες απαντήσεις."
    )
    return header + body + footer


def get_advice(question, context_summary, field_task_info):
    """
    Επιστρέφει (answer_text, used_ai: bool).
    """
    if IS_LIVE:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        user_message = (
            f"Δεδομένα αγροκτήματος:\n{context_summary}\n\n"
            f"Ερώτηση αγρότη: {question}"
        )
        response = client.messages.create(
            model=MODEL,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        answer = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
        return answer or "Δεν ελήφθη απάντηση από το μοντέλο.", True
    else:
        return _fallback_advice(question, field_task_info), False
