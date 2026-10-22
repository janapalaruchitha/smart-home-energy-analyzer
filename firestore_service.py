from google.cloud import firestore
from werkzeug.security import generate_password_hash, check_password_hash

PROJECT_ID = "smart-home-energy-2026"

db = firestore.Client(project=PROJECT_ID)


def register_user(email, password):
    """Register a user with a securely hashed password."""
    email = email.strip().lower()
    user_ref = db.collection("users").document(email)

    if user_ref.get().exists:
        return False

    user_ref.set({
        "email": email,
        "password_hash": generate_password_hash(password),
    })

    return True


def verify_user(email, password):
    """Verify a user's email and password."""
    email = email.strip().lower()
    user_ref = db.collection("users").document(email)
    user_data = user_ref.get().to_dict()

    if not user_data:
        return None

    if check_password_hash(user_data["password_hash"], password):
        return email

    return None


def get_appliances(user_id):
    """Retrieve appliance records for one user."""
    collection = (
        db.collection("users")
        .document(user_id)
        .collection("appliances")
    )

    return [
        {"id": doc.id, **doc.to_dict()}
        for doc in collection.stream()
    ]


def add_appliance(appliance, user_id):
    """Save an appliance record for one user."""
    collection = (
        db.collection("users")
        .document(user_id)
        .collection("appliances")
    )

    doc_ref = collection.document()
    doc_ref.set(appliance)
    return doc_ref.id


def delete_appliance(appliance_id, user_id):
    """Delete an appliance belonging to one user."""
    (
        db.collection("users")
        .document(user_id)
        .collection("appliances")
        .document(appliance_id)
        .delete()
    )