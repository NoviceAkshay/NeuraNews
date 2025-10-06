
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     Authentication       *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------


from .database import SessionLocal
from .models import User

db = SessionLocal()


def register_user(username, password):
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            return False, "User already exists"

        new_user = User(username=username, password=password)
        db.add(new_user)
        db.commit()
        return True, "User registered successfully"
    finally:
        db.close()

def login_user(username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if user and user.password == password:
        return True, user
    return False, None
