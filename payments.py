"""
Ενσωμάτωση πληρωμών (Stripe Checkout) για την υιοθεσία δέντρων.

Πραγματική λειτουργία: αν υπάρχει το πακέτο "stripe" εγκατεστημένο ΚΑΙ έχει
οριστεί το περιβαλλοντικό μεταβλητό STRIPE_SECRET_KEY, η εφαρμογή δημιουργεί
πραγματικό Stripe Checkout Session και ο πελάτης πληρώνει κανονικά.

Λειτουργία δοκιμής (όταν δεν υπάρχει κλειδί — π.χ. τώρα, σε αυτό το sandbox
χωρίς πρόσβαση σε εξωτερικό internet): η πληρωμή προσομοιώνεται με μια
τοπική σελίδα επιβεβαίωσης, ώστε όλη η ροή (αγρότης -> δέντρο -> πελάτης ->
"πληρωμή" -> επιβεβαίωση) να δουλεύει κανονικά από άκρη σε άκρη.

Για να ενεργοποιηθούν οι πραγματικές πληρωμές:
  1. pip install stripe
  2. export STRIPE_SECRET_KEY="sk_live_..." (ή sk_test_... για δοκιμές Stripe)
  3. export STRIPE_PUBLISHABLE_KEY="pk_..."
  4. Ρύθμισε ένα webhook στο Stripe dashboard να δείχνει σε /checkout/webhook
"""
import os

try:
    import stripe
    _STRIPE_AVAILABLE = True
except ImportError:
    _STRIPE_AVAILABLE = False

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

IS_LIVE = _STRIPE_AVAILABLE and bool(STRIPE_SECRET_KEY)

if IS_LIVE:
    stripe.api_key = STRIPE_SECRET_KEY


def create_checkout_session(adoption, tree, success_url, cancel_url):
    """
    Δημιουργεί checkout session (πραγματικό Stripe ή test-mode) και επιστρέφει
    το URL όπου πρέπει να ανακατευθυνθεί ο πελάτης.
    """
    if IS_LIVE:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Υιοθεσία δέντρου {tree['code']} — σεζόν {adoption['season_year']}",
                        },
                        "unit_amount": int(round(adoption["amount"] * 100)),
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            client_reference_id=str(adoption["id"]),
        )
        return session.url, session.id
    else:
        # Test mode: πάμε κατευθείαν σε τοπική σελίδα "πληρωμής".
        return f"/trees/checkout/test/{adoption['id']}", None
