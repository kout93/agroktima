"""
Πρόγνωση καιρού για τη θέση κάθε κτήματος.

Χρησιμοποιεί το Open-Meteo API (https://open-meteo.com) — δωρεάν, χωρίς
κλειδί, χωρίς διαφημίσεις. Δεν ενσωματώνουμε το site κάποιου παρόχου μέσα
στην εφαρμογή· παίρνουμε μόνο τα καθαρά δεδομένα πρόγνωσης και τα δείχνουμε
με τα δικά μας εικονίδια.
"""
import requests

WEATHER_ICONS = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌧️",
    56: "🌧️", 57: "🌧️",
    61: "🌧️", 63: "🌧️", 65: "⛈️",
    66: "🌧️", 67: "🌧️",
    71: "🌨️", 73: "🌨️", 75: "❄️", 77: "🌨️",
    80: "🌦️", 81: "🌧️", 82: "⛈️",
    85: "🌨️", 86: "❄️",
    95: "⛈️", 96: "⛈️", 99: "⛈️",
}

WEATHER_LABELS = {
    0: "Αίθριος", 1: "Κυρίως αίθριος", 2: "Μερική νέφωση", 3: "Νεφώσεις",
    45: "Ομίχλη", 48: "Ομίχλη με πάχνη",
    51: "Ελαφρά ψιχάλα", 53: "Ψιχάλα", 55: "Πυκνή ψιχάλα",
    56: "Παγωμένη ψιχάλα", 57: "Πυκνή παγωμένη ψιχάλα",
    61: "Ελαφρά βροχή", 63: "Βροχή", 65: "Έντονη βροχή",
    66: "Παγωμένη βροχή", 67: "Έντονη παγωμένη βροχή",
    71: "Ελαφρό χιόνι", 73: "Χιόνι", 75: "Έντονο χιόνι", 77: "Χιονόκοκκοι",
    80: "Σποραδικές βροχές", 81: "Βροχές", 82: "Έντονες βροχές",
    85: "Χιονόπτωση", 86: "Έντονη χιονόπτωση",
    95: "Καταιγίδα", 96: "Καταιγίδα με χαλάζι", 99: "Έντονη καταιγίδα με χαλάζι",
}


def fetch_forecast(lat, lon, days=5):
    """Επιστρέφει λίστα με ημερήσια πρόγνωση ή None αν αποτύχει η κλήση."""
    if lat is None or lon is None:
        return None
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
            },
            timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        codes = daily.get("weathercode", [])
        tmax = daily.get("temperature_2m_max", [])
        tmin = daily.get("temperature_2m_min", [])
        rain = daily.get("precipitation_probability_max", [])

        result = []
        for i in range(min(days, len(dates))):
            code = codes[i] if i < len(codes) else None
            result.append({
                "date": dates[i],
                "icon": WEATHER_ICONS.get(code, "🌡️"),
                "label": WEATHER_LABELS.get(code, "—"),
                "temp_max": tmax[i] if i < len(tmax) else None,
                "temp_min": tmin[i] if i < len(tmin) else None,
                "rain_chance": rain[i] if i < len(rain) else None,
            })
        return result
    except Exception:
        return None
