from app.models import User
from app.core import db
import bcrypt

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def create_user(name, email, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(name=name, email=email, password=hashed)
    db.session.add(user)
    db.session.commit()
    return user

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode(), hashed.encode())