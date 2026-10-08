"""
Γεωμετρικοί υπολογισμοί για περιγράμματα κτημάτων (πολύγωνα σημείων).
"""
import math


def polygon_area_stremma(points):
    """points: λίστα από (lat, lng). Υπολογίζει το εμβαδόν σε στρέμματα
    (1 στρέμμα = 1000 m²) με τοπική προβολή γύρω από τον μέσο όρο των
    σημείων — αρκετά ακριβές για το μέγεθος ενός αγροτεμαχίου."""
    if len(points) < 3:
        return 0.0

    avg_lat = sum(p[0] for p in points) / len(points)
    lat_rad = math.radians(avg_lat)
    m_per_deg_lat = 111320.0
    m_per_deg_lng = 111320.0 * math.cos(lat_rad)

    xy = [(p[1] * m_per_deg_lng, p[0] * m_per_deg_lat) for p in points]

    area_m2 = 0.0
    n = len(xy)
    for i in range(n):
        x1, y1 = xy[i]
        x2, y2 = xy[(i + 1) % n]
        area_m2 += x1 * y2 - x2 * y1
    area_m2 = abs(area_m2) / 2.0

    return area_m2 / 1000.0


def polygon_centroid(points):
    lat = sum(p[0] for p in points) / len(points)
    lng = sum(p[1] for p in points) / len(points)
    return lat, lng
