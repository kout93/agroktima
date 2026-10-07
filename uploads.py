"""
Ασφαλής αποθήκευση φωτογραφιών που ανεβάζουν οι χρήστες.
"""
import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "heic"}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024  # 8MB ανά φωτογραφία


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_photo(file_storage):
    """
    Αποθηκεύει ένα ανεβασμένο αρχείο εικόνας με ασφαλές, μοναδικό όνομα.
    Επιστρέφει το filename (για αποθήκευση στη βάση) ή None αν δεν υπάρχει/δεν επιτρέπεται.
    Δεν σταματάει τη ροή σε περίπτωση κακού αρχείου — απλά το αγνοεί.
    """
    if file_storage is None or file_storage.filename == "":
        return None
    if not _allowed(file_storage.filename):
        return None

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    ext = secure_filename(file_storage.filename).rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    dest_path = os.path.join(UPLOAD_FOLDER, unique_name)

    file_storage.save(dest_path)

    # Έλεγχος μεγέθους ΜΕΤΑ την αποθήκευση (το Flask MAX_CONTENT_LENGTH
    # στο app.py είναι η κύρια γραμμή άμυνας πριν φτάσει καν εδώ).
    if os.path.getsize(dest_path) > MAX_FILE_SIZE_BYTES:
        os.remove(dest_path)
        return None

    return unique_name
