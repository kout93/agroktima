"""
Δημιουργία αρχείων .ics (iCalendar) — το ανοιχτό, καθολικό πρότυπο που
διαβάζουν το Google Calendar, το Apple Calendar και το Outlook. Δεν
χρειάζεται κανένα κλειδί API ή σύνδεση λογαριασμού Google — απλό αρχείο
κειμένου με συγκεκριμένη μορφή.
"""
from datetime import datetime


def _escape(text):
    return (text or "").replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def _fold(line):
    """Τα iCalendar γραμμές δεν πρέπει να ξεπερνούν τους 75 χαρακτήρες."""
    if len(line) <= 75:
        return line
    parts = [line[:75]]
    rest = line[75:]
    while rest:
        parts.append(" " + rest[:74])
        rest = rest[74:]
    return "\r\n".join(parts)


def build_event(uid, summary, date_str, description=""):
    """Ένα all-day event για μία ημερομηνία (YYYY-MM-DD)."""
    date_compact = date_str.replace("-", "")
    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}@agroktima",
        f"DTSTAMP:{now_stamp}",
        f"DTSTART;VALUE=DATE:{date_compact}",
        f"SUMMARY:{_escape(summary)}",
        f"DESCRIPTION:{_escape(description)}",
        "END:VEVENT",
    ]
    return "\r\n".join(_fold(l) for l in lines)


def build_calendar(events, calendar_name="Αγρόκτημα"):
    """Τυλίγει μία ή περισσότερες VEVENT σε ένα πλήρες VCALENDAR."""
    header = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Agroktima//Calendar//EL",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
    ]
    footer = ["END:VCALENDAR"]
    body = "\r\n".join(header) + "\r\n" + "\r\n".join(events) + "\r\n" + "\r\n".join(footer) + "\r\n"
    return body
