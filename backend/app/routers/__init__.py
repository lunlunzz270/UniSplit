from flask import Blueprint, request, jsonify
from ..services import get_user_by_email, create_user, verify_password
from .expenses import expenses_bp
from .groups import groups_bp
from .settlements import settlements_bp
from .activity_logs import activity_logs_bp

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400

    if get_user_by_email(email):
        return jsonify({'error': 'Email already registered'}), 400

    user = create_user(name, email, password)
    return jsonify({'id': user.id, 'name': user.full_name, 'email': user.email}), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = get_user_by_email(email)
    if not user or not verify_password(password, user.password):
        return jsonify({'error': 'Invalid email or password'}), 401

    return jsonify({'id': user.id, 'name': user.full_name, 'email': user.email}), 200
