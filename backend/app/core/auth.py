import jwt
import datetime
import os
import uuid
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()

# Secret key for signing the JWT (Should be set in .env for production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "unisplit-super-secret-key-2024")
ALGORITHM = "HS256"
ADMIN_DOMAIN = "@unisplit.com"


def create_access_token(user_id: int, email: str):
    """
    Generate a JWT Token.
    Role logic: If email ends with @unisplit.com, set is_admin to True.
    """
    is_admin = email.lower().endswith(ADMIN_DOMAIN)

    payload = {
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1),
        "iat": datetime.datetime.now(datetime.UTC),
        "sub": str(user_id),
        "is_admin": is_admin,
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def token_required(f):
    """
    Decorator to protect routes.
    Extracts user_id and is_admin status from the token.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Expected Header: Authorization: Bearer <token>
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Inject identity into the request context
            request.current_user_id = int(data["sub"])
            request.is_admin = data.get("is_admin", False)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception:
            return jsonify({"error": "Authentication failed"}), 401

        return f(*args, **kwargs)

    return decorated
