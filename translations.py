"""
Απλό, χωρίς εξωτερικές εξαρτήσεις, σύστημα πολλών γλωσσών.
Δεν χρησιμοποιούμε Flask-Babel (δεν ήταν διαθέσιμο να εγκατασταθεί
κατά την ανάπτυξη), αλλά ένα απλό λεξικό μετάφρασης ανά γλώσσα.

Η ελληνική (el) είναι η "πηγή" — τα κείμενα στα templates/flash
γράφονται στα ελληνικά και το t() τα αναζητά στο TRANSLATIONS[lang].
Αν δεν βρεθεί μετάφραση, επιστρέφεται το ελληνικό κείμενο (ποτέ κενό).
"""
from flask import session

SUPPORTED_LANGS = {"el": "ΕΛ", "en": "EN", "it": "IT"}
DEFAULT_LANG = "el"


def get_lang():
    lang = session.get("lang", DEFAULT_LANG)
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    return lang


def t(text, **kwargs):
    """Μεταφράζει το text στην τρέχουσα γλώσσα. Υποστηρίζει placeholders
    τύπου %(name)s μέσα στο ίδιο το ελληνικό κείμενο."""
    lang = get_lang()
    if lang != DEFAULT_LANG:
        text = TRANSLATIONS.get(lang, {}).get(text, text)
    if kwargs:
        try:
            text = text % kwargs
        except (KeyError, ValueError, TypeError):
            pass
    return text


TRANSLATIONS = {
    "en": {
        # ---- nav / base ----
        "🫒 Αγρόκτημα": "🫒 Agroktima",
        "Αγρόκτημα": "Agroktima",
        "Κτήματα": "Fields",
        "Χάρτης": "Map",
        "Δέντρα μου": "My Trees",
        "Πλάνο εργασιών": "Task planner",
        "Απόθεμα": "Stock",
        "ΟΠΕΚΕΠΕ/ΕΛΓΑ": "Subsidy reports",
        "Στατιστικά": "Statistics",
        "Συμβουλές AI": "AI advice",
        "Υιοθέτησε Δέντρο": "Adopt a Tree",
        "Οι Υιοθεσίες μου": "My Adoptions",
        "Οι υιοθεσίες μου": "My adoptions",
        "Αποσύνδεση (%(name)s)": "Log out (%(name)s)",
        "Σύνδεση": "Log in",
        "Εγγραφή": "Sign up",
        "🧪 Λειτουργία δοκιμής — οι πληρωμές δεν είναι πραγματικές μέχρι να προστεθεί κλειδί Stripe":
            "🧪 Test mode — payments are not real until a Stripe key is added",
        "🔔 Υπενθυμίσεις σήμερα:": "🔔 Reminders for today:",
        "Υπενθυμίσεις σήμερα:": "Reminders for today:",
        "Κλείσιμο για σήμερα": "Dismiss for today",
        "Ξεκούραση ματιών (σκοτεινό φόντο)": "Rest your eyes (dark background)",
        "Ξεκούραση ματιών — σκοτεινό φόντο": "Rest your eyes — dark background",

        # ---- home ----
        "Το χωράφι σου, στο κινητό σου": "Your field, on your phone",
        "Καταγραφή κτημάτων, εργασιών και εξόδων για αγρότες — και ένα σύστημα όπου κάποιος μπορεί να «υιοθετήσει» ένα δέντρο ελιάς με αντάλλαγμα το λάδι του.":
            "Track fields, tasks and costs as a farmer — and a system where anyone can “adopt” an olive tree in exchange for its oil.",
        "Δημιουργία λογαριασμού": "Create account",
        "Δες δέντρα προς υιοθεσία": "See trees available for adoption",
        "Τα κτήματά μου": "My fields",
        "Δέντρα προς υιοθεσία": "Trees for adoption",
        "Ξεκίνα τώρα": "Get started",
        "Αν είσαι αγρότης, φτιάξε λογαριασμό για να καταγράφεις τα κτήματα και τις εργασίες σου.<br>\n  Αν θέλεις να υιοθετήσεις ένα δέντρο ελιάς, φτιάξε λογαριασμό πελάτη.":
            "If you're a farmer, create an account to track your fields and tasks.<br>\n  If you'd like to adopt an olive tree, create a customer account.",
        "Καλώς ήρθες, %(name)s": "Welcome, %(name)s",
        "Συνέχισε από εκεί που σταμάτησες — κτήματα, εργασίες, παραγωγή, καιρός και αναφορές, όλα σε ένα μέρος.":
            "Pick up right where you left off — fields, tasks, harvest, weather and reports, all in one place.",
        "Βρες ένα δέντρο ελιάς να υιοθετήσεις και παρακολούθησε την πρόοδό του μέχρι τη συγκομιδή.":
            "Find an olive tree to adopt and follow its progress through to the harvest.",

        # ---- auth ----
        "Σύνδεση λογαριασμού": "Log in to your account",
        "Email": "Email",
        "Κωδικός": "Password",
        "Δεν έχεις λογαριασμό;": "Don't have an account?",
        "Δημιουργία νέου λογαριασμού": "Create a new account",
        "Όνομα": "Name",
        "Είμαι...": "I am a...",
        "Είσαι...": "You are a...",
        "Επίλεξε": "Choose",
        "Αγρότης": "Farmer",
        "Αγρότης / Παραγωγός": "Farmer / Grower",
        "Πελάτης (θέλω να υιοθετήσω δέντρο)": "Customer (I want to adopt a tree)",
        "Έχεις ήδη λογαριασμό;": "Already have an account?",
        "Σύνδεση εδώ": "Log in here",
        "Πρέπει πρώτα να συνδεθείς.": "You need to log in first.",
        "Δεν έχεις πρόσβαση σε αυτή τη σελίδα.": "You don't have access to this page.",
        "Συμπλήρωσε το όνομά σου.": "Please enter your name.",
        "Δώσε ένα έγκυρο email.": "Please enter a valid email.",
        "Ο κωδικός χρειάζεται τουλάχιστον 6 χαρακτήρες.": "The password needs at least 6 characters.",
        "Επίλεξε αν είσαι αγρότης ή πελάτης.": "Please choose whether you're a farmer or a customer.",
        "Υπάρχει ήδη λογαριασμός με αυτό το email.": "An account with this email already exists.",
        "Ο λογαριασμός δημιουργήθηκε!": "Your account has been created!",
        "Λάθος email ή κωδικός.": "Wrong email or password.",

        # ---- trees: browse / view / adoptions ----
        "Υιοθέτησε ένα δέντρο ελιάς": "Adopt an olive tree",
        "Πλήρωσε την ετήσια συνδρομή ενός δέντρου και πάρε στο τέλος της σεζόν το λάδι που παρήγαγε.":
            "Pay a tree's yearly fee and receive the oil it produced at the end of the season.",
        "Δεν υπάρχουν αυτή τη στιγμή διαθέσιμα δέντρα.": "There are no trees available right now.",
        "Διαθέσιμο": "Available",
        "με σημείο στον χάρτη": "located on the map",
        "kg λάδι/έτος": "kg oil/year",
        "€ / έτος": " / year",
        "Δες περισσότερα": "See more",
        "Δες το δέντρο": "See the tree",
        "Παραγωγός:": "Grower:",
        "Εκτιμώμενη παραγωγή λαδιού/έτος": "Estimated oil output/year",
        "Τιμή υιοθεσίας/έτος": "Adoption price/year",
        "Υιοθέτησε αυτό το δέντρο — %(price).2f€": "Adopt this tree — €%(price).2f",
        "Η υιοθεσία είναι διαθέσιμη μόνο για λογαριασμούς πελάτη.": "Adoption is only available for customer accounts.",
        "Σύνδεση για υιοθεσία": "Log in to adopt",
        "Υιοθετημένο": "Adopted",
        "Αυτό το δέντρο έχει ήδη υιοθετηθεί.": "This tree has already been adopted.",
        "Πού βρίσκεται": "Where it is",
        "Ενημερώσεις προόδου": "Progress updates",
        "Δεν υπάρχουν ακόμα ενημερώσεις.": "No updates yet.",
        "Φωτογραφία ενημέρωσης": "Update photo",
        "Οι υιοθεσίες μου": "My adoptions",
        "Πληρωμένο": "Paid",
        "Εκκρεμεί": "Pending",
        "Ακυρώθηκε": "Cancelled",
        "Σεζόν": "Season",
        "kg λάδι αναμενόμενα": "kg oil expected",
        "Δεν έχεις υιοθετήσει ακόμα κάποιο δέντρο.": "You haven't adopted a tree yet.",
        "Δες διαθέσιμα δέντρα": "See available trees",
        "Αυτό το δέντρο δεν είναι πλέον διαθέσιμο.": "This tree is no longer available.",
        "Η (δοκιμαστική) πληρωμή ολοκληρώθηκε — το δέντρο είναι δικό σου!": "The (test) payment is complete — the tree is yours!",
        "Η πληρωμή ολοκληρώθηκε — το δέντρο είναι δικό σου!": "Payment complete — the tree is yours!",
        "Η υιοθεσία δεν βρέθηκε.": "Adoption not found.",
        "Το δέντρο δεν βρέθηκε.": "Tree not found.",
        "Δοκιμαστική πληρωμή": "Test payment",
        "Η δοκιμαστική πληρωμή δεν είναι διαθέσιμη (έχει ρυθμιστεί πραγματικό Stripe).": "Test payment isn't available (a real Stripe key is configured).",
        "Ολοκλήρωση υιοθεσίας": "Complete the adoption",
        "Επιβεβαίωση πληρωμής (δοκιμή)": "Confirm payment (test)",
        "🧪 Αυτή είναι δοκιμαστική πληρωμή — δεν θα χρεωθεί καμία πραγματική κάρτα. Όταν προστεθεί κλειδί Stripe, αυτή η σελίδα αντικαθίσταται αυτόματα από το πραγματικό Stripe Checkout.":
            "🧪 This is a test payment — no real card will be charged. Once a Stripe key is added, this page is automatically replaced by real Stripe Checkout.",
    },
    "it": {
        # ---- nav / base ----
        "🫒 Αγρόκτημα": "🫒 Agroktima",
        "Αγρόκτημα": "Agroktima",
        "Κτήματα": "Terreni",
        "Χάρτης": "Mappa",
        "Δέντρα μου": "I miei alberi",
        "Πλάνο εργασιών": "Piano dei lavori",
        "Απόθεμα": "Giacenze",
        "ΟΠΕΚΕΠΕ/ΕΛΓΑ": "Report sussidi",
        "Στατιστικά": "Statistiche",
        "Συμβουλές AI": "Consigli AI",
        "Υιοθέτησε Δέντρο": "Adotta un Albero",
        "Οι Υιοθεσίες μου": "Le mie Adozioni",
        "Οι υιοθεσίες μου": "Le mie adozioni",
        "Αποσύνδεση (%(name)s)": "Esci (%(name)s)",
        "Σύνδεση": "Accedi",
        "Εγγραφή": "Registrati",
        "🧪 Λειτουργία δοκιμής — οι πληρωμές δεν είναι πραγματικές μέχρι να προστεθεί κλειδί Stripe":
            "🧪 Modalità di prova — i pagamenti non sono reali finché non viene aggiunta una chiave Stripe",
        "🔔 Υπενθυμίσεις σήμερα:": "🔔 Promemoria di oggi:",
        "Υπενθυμίσεις σήμερα:": "Promemoria di oggi:",
        "Κλείσιμο για σήμερα": "Chiudi per oggi",
        "Ξεκούραση ματιών (σκοτεινό φόντο)": "Riposo per gli occhi (sfondo scuro)",
        "Ξεκούραση ματιών — σκοτεινό φόντο": "Riposo per gli occhi — sfondo scuro",

        # ---- home ----
        "Το χωράφι σου, στο κινητό σου": "Il tuo campo, sul tuo telefono",
        "Καταγραφή κτημάτων, εργασιών και εξόδων για αγρότες — και ένα σύστημα όπου κάποιος μπορεί να «υιοθετήσει» ένα δέντρο ελιάς με αντάλλαγμα το λάδι του.":
            "Registra terreni, lavori e spese per gli agricoltori — e un sistema in cui chiunque può “adottare” un ulivo in cambio del suo olio.",
        "Δημιουργία λογαριασμού": "Crea un account",
        "Δες δέντρα προς υιοθεσία": "Guarda gli alberi disponibili per l'adozione",
        "Τα κτήματά μου": "I miei terreni",
        "Δέντρα προς υιοθεσία": "Alberi da adottare",
        "Ξεκίνα τώρα": "Inizia ora",
        "Αν είσαι αγρότης, φτιάξε λογαριασμό για να καταγράφεις τα κτήματα και τις εργασίες σου.<br>\n  Αν θέλεις να υιοθετήσεις ένα δέντρο ελιάς, φτιάξε λογαριασμό πελάτη.":
            "Se sei un agricoltore, crea un account per registrare i tuoi terreni e lavori.<br>\n  Se vuoi adottare un ulivo, crea un account cliente.",
        "Καλώς ήρθες, %(name)s": "Benvenuto/a, %(name)s",
        "Συνέχισε από εκεί που σταμάτησες — κτήματα, εργασίες, παραγωγή, καιρός και αναφορές, όλα σε ένα μέρος.":
            "Riprendi da dove avevi lasciato — terreni, lavori, raccolto, meteo e report, tutto in un unico posto.",
        "Βρες ένα δέντρο ελιάς να υιοθετήσεις και παρακολούθησε την πρόοδό του μέχρι τη συγκομιδή.":
            "Trova un ulivo da adottare e segui i suoi progressi fino al raccolto.",

        # ---- auth ----
        "Σύνδεση λογαριασμού": "Accedi al tuo account",
        "Email": "Email",
        "Κωδικός": "Password",
        "Δεν έχεις λογαριασμό;": "Non hai un account?",
        "Δημιουργία νέου λογαριασμού": "Crea un nuovo account",
        "Όνομα": "Nome",
        "Είμαι...": "Sono un...",
        "Είσαι...": "Sei un...",
        "Επίλεξε": "Scegli",
        "Αγρότης": "Agricoltore",
        "Αγρότης / Παραγωγός": "Agricoltore / Produttore",
        "Πελάτης (θέλω να υιοθετήσω δέντρο)": "Cliente (voglio adottare un albero)",
        "Έχεις ήδη λογαριασμό;": "Hai già un account?",
        "Σύνδεση εδώ": "Accedi qui",
        "Πρέπει πρώτα να συνδεθείς.": "Devi prima accedere.",
        "Δεν έχεις πρόσβαση σε αυτή τη σελίδα.": "Non hai accesso a questa pagina.",
        "Συμπλήρωσε το όνομά σου.": "Inserisci il tuo nome.",
        "Δώσε ένα έγκυρο email.": "Inserisci un'email valida.",
        "Ο κωδικός χρειάζεται τουλάχιστον 6 χαρακτήρες.": "La password deve contenere almeno 6 caratteri.",
        "Επίλεξε αν είσαι αγρότης ή πελάτης.": "Scegli se sei un agricoltore o un cliente.",
        "Υπάρχει ήδη λογαριασμός με αυτό το email.": "Esiste già un account con questa email.",
        "Ο λογαριασμός δημιουργήθηκε!": "Il tuo account è stato creato!",
        "Λάθος email ή κωδικός.": "Email o password errati.",

        # ---- trees: browse / view / adoptions ----
        "Υιοθέτησε ένα δέντρο ελιάς": "Adotta un ulivo",
        "Πλήρωσε την ετήσια συνδρομή ενός δέντρου και πάρε στο τέλος της σεζόν το λάδι που παρήγαγε.":
            "Paga la quota annuale di un albero e ricevi, a fine stagione, l'olio che ha prodotto.",
        "Δεν υπάρχουν αυτή τη στιγμή διαθέσιμα δέντρα.": "Al momento non ci sono alberi disponibili.",
        "Διαθέσιμο": "Disponibile",
        "με σημείο στον χάρτη": "con posizione sulla mappa",
        "kg λάδι/έτος": "kg olio/anno",
        "€ / έτος": " / anno",
        "Δες περισσότερα": "Scopri di più",
        "Δες το δέντρο": "Guarda l'albero",
        "Παραγωγός:": "Produttore:",
        "Εκτιμώμενη παραγωγή λαδιού/έτος": "Produzione stimata di olio/anno",
        "Τιμή υιοθεσίας/έτος": "Prezzo di adozione/anno",
        "Υιοθέτησε αυτό το δέντρο — %(price).2f€": "Adotta questo albero — €%(price).2f",
        "Η υιοθεσία είναι διαθέσιμη μόνο για λογαριασμούς πελάτη.": "L'adozione è disponibile solo per gli account cliente.",
        "Σύνδεση για υιοθεσία": "Accedi per adottare",
        "Υιοθετημένο": "Adottato",
        "Αυτό το δέντρο έχει ήδη υιοθετηθεί.": "Questo albero è già stato adottato.",
        "Πού βρίσκεται": "Dove si trova",
        "Ενημερώσεις προόδου": "Aggiornamenti sui progressi",
        "Δεν υπάρχουν ακόμα ενημερώσεις.": "Ancora nessun aggiornamento.",
        "Φωτογραφία ενημέρωσης": "Foto dell'aggiornamento",
        "Οι υιοθεσίες μου": "Le mie adozioni",
        "Πληρωμένο": "Pagato",
        "Εκκρεμεί": "In attesa",
        "Ακυρώθηκε": "Annullato",
        "Σεζόν": "Stagione",
        "kg λάδι αναμενόμενα": "kg olio previsti",
        "Δεν έχεις υιοθετήσει ακόμα κάποιο δέντρο.": "Non hai ancora adottato nessun albero.",
        "Δες διαθέσιμα δέντρα": "Guarda gli alberi disponibili",
        "Αυτό το δέντρο δεν είναι πλέον διαθέσιμο.": "Questo albero non è più disponibile.",
        "Η (δοκιμαστική) πληρωμή ολοκληρώθηκε — το δέντρο είναι δικό σου!": "Il pagamento (di prova) è completato — l'albero è tuo!",
        "Η πληρωμή ολοκληρώθηκε — το δέντρο είναι δικό σου!": "Pagamento completato — l'albero è tuo!",
        "Η υιοθεσία δεν βρέθηκε.": "Adozione non trovata.",
        "Το δέντρο δεν βρέθηκε.": "Albero non trovato.",
        "Δοκιμαστική πληρωμή": "Pagamento di prova",
        "Η δοκιμαστική πληρωμή δεν είναι διαθέσιμη (έχει ρυθμιστεί πραγματικό Stripe).": "Il pagamento di prova non è disponibile (è configurata una chiave Stripe reale).",
        "Ολοκλήρωση υιοθεσίας": "Completa l'adozione",
        "Επιβεβαίωση πληρωμής (δοκιμή)": "Confirma il pagamento (prova)",
        "🧪 Αυτή είναι δοκιμαστική πληρωμή — δεν θα χρεωθεί καμία πραγματική κάρτα. Όταν προστεθεί κλειδί Stripe, αυτή η σελίδα αντικαθίσταται αυτόματα από το πραγματικό Stripe Checkout.":
            "🧪 Questo è un pagamento di prova — nessuna carta reale verrà addebitata. Quando verrà aggiunta una chiave Stripe, questa pagina sarà sostituita automaticamente dal vero Stripe Checkout.",
    },
}
