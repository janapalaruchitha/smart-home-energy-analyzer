import os
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from services.firestore_service import (
    get_appliances,
    add_appliance,
    delete_appliance,
    register_user,
    verify_user,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "Set the SECRET_KEY environment variable before starting the app."
    )

TARIFF = 8.0


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def calculate_totals(appliances):
    total_kwh = round(sum(a["energy"] for a in appliances), 2)
    total_cost = round(sum(a["cost"] for a in appliances), 2)
    return total_kwh, total_cost


@app.route("/")
@login_required
def dashboard():
    user_id = session["user_id"]
    appliance_list = get_appliances(user_id)
    total_kwh, total_cost = calculate_totals(appliance_list)

    return render_template(
        "index.html",
        appliances=appliance_list,
        total_kwh=total_kwh,
        total_cost=total_cost,
        tariff=TARIFF,
    )


@app.route("/appliances", methods=["GET", "POST"])
@login_required
def appliances():
    user_id = session["user_id"]
    error = None

    if request.method == "POST":
        action = request.form.get("action", "add")

        if action == "remove":
            appliance_id = request.form.get("id", "")
            appliance_list = get_appliances(user_id)

            if any(a["id"] == appliance_id for a in appliance_list):
                delete_appliance(appliance_id, user_id)

            return redirect(url_for("appliances"))

        try:
            name = request.form.get("name", "").strip()
            watts = float(request.form.get("watts", 0))
            hours = float(request.form.get("hours", 0))
            days = int(request.form.get("days", 30))

            if (
                not name
                or len(name) > 80
                or watts <= 0
                or watts > 100000
                or not 0 <= hours <= 24
                or not 1 <= days <= 31
            ):
                raise ValueError

            energy = round(watts * hours * days / 1000, 2)
            appliance = {
                "name": name,
                "watts": watts,
                "hours": hours,
                "days": days,
                "energy": energy,
                "cost": round(energy * TARIFF, 2),
            }

            add_appliance(appliance, user_id)
            return redirect(url_for("appliances"))

        except (ValueError, TypeError):
            error = "Please enter valid appliance details."

    appliance_list = get_appliances(user_id)
    total_kwh, total_cost = calculate_totals(appliance_list)

    return render_template(
        "appliances.html",
        appliances=appliance_list,
        total_kwh=total_kwh,
        total_cost=total_cost,
        tariff=TARIFF,
        error=error,
    )


@app.route("/reports")
@login_required
def reports():
    appliance_list = get_appliances(session["user_id"])
    total_kwh, total_cost = calculate_totals(appliance_list)

    highest = max(
        appliance_list,
        key=lambda item: item["energy"],
        default=None,
    )

    recommendations = []

    for item in appliance_list:
        if item["hours"] >= 8:
            recommendations.append(
                f"Review the daily usage of {item['name']}, "
                "which runs for 8 or more hours per day."
            )

    if not recommendations:
        recommendations.append(
            "Continue monitoring usage and switch off appliances "
            "when they are not needed."
        )

    return render_template(
        "reports.html",
        appliances=appliance_list,
        total_kwh=total_kwh,
        total_cost=total_cost,
        highest=highest,
        recommendations=recommendations,
        tariff=TARIFF,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if verify_user(email, password):
            session.clear()
            session["user_id"] = email
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if (
            not email
            or len(email) > 254
            or "@" not in email
            or len(password) < 8
            or len(password) > 128
        ):
            flash("Enter a valid email and a password of 8–128 characters.")
            return render_template("register.html")

        try:
            if register_user(email, password):
                flash("Account created! You can now sign in.")
                return redirect(url_for("login"))

            flash("An account with that email already exists.")

        except Exception:
            app.logger.exception("Registration failed")
            flash("Unable to create your account. Please try again.")

    return render_template("register.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been signed out.")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
    