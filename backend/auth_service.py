
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     Authentication       *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------

import re
from .models import User
from .database import SessionLocal

def is_valid_email(email):
    # Simple regex pattern for email validation
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def register_user(username, email, password):
    db = SessionLocal()
    try:
        # Perform email validation first
        if not is_valid_email(email):
            return False, "Invalid email address"

        # Check if user exists by username or email
        if db.query(User).filter((User.username == username) | (User.email == email)).first():
            return False, "User already exists"

        new_user = User(username=username, email=email, password=password)
        db.add(new_user)
        db.commit()
        return True, "User registered successfully"
    except Exception as e:
        db.rollback()
        return False, f"Registration error: {e}"
    finally:
        db.close()


def login_user(identifier: str, password: str):
    db = SessionLocal()
    try:
        # Identifier matches username or email
        user = db.query(User).filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        # Standard password check
        if user and user.password == password:
            return True, user
        return False, None
    except Exception as e:
        db.rollback()
        return False, None
    finally:
        db.close()


