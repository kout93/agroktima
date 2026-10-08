"""
Αγρόκτημα — κεντρική εφαρμογή Flask.
Τρέξιμο: python app.py
"""
import os
from datetime import date
from flask import Flask, render_template, session

from db import register_app, get_db
import auth
import fields
import stats
import trees
import advisor
import reminders
import planner

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["STRIPE_CONFIGURED"] = bool(STRIPE_SECRET_KEY)
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB ανά request (ασφάλεια ανεβάσματος)

    register_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(fields.bp)
    app.register_blueprint(stats.bp)
    app.register_blueprint(trees.bp)
    app.register_blueprint(advisor.bp)
    app.register_blueprint(reminders.bp)
    app.register_blueprint(planner.bp)

    @app.context_processor
    def inject_globals():
        return {"stripe_configured": app.config["STRIPE_CONFIGURED"]}

    @app.context_processor
    def inject_reminders_banner():
        user = auth.current_user()
        items = []
        if user and user["role"] == "farmer":
            today_str = date.today().isoformat()
            if session.get("reminders_dismissed_date") != today_str:
                items = reminders.get_reminders(get_db(), user["id"])
        return {"daily_reminders": items}

    from flask import Blueprint
    main = Blueprint("main", __name__)

    @main.route("/")
    def home():
        return render_template("home.html")

    app.register_blueprint(main)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
