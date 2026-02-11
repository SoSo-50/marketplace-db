import sys
import traceback
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import User

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'اطلاعاتی دریافت نشد'}), 400

        username = data.get('username')
        password = data.get('password')
        phone = data.get('phone')
        
        if not username or not password or not phone:
            return jsonify({'error': 'نام کاربری، رمز عبور و شماره موبایل الزامی هستند'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'این نام کاربری قبلاً ثبت شده است'}), 400
        
        if User.query.filter_by(phone=phone).first():
            return jsonify({'error': 'این شماره موبایل قبلاً ثبت شده است'}), 400

        email = data.get('email') or f"{username}@market.com"

        new_user = User(
            first_name=data.get('first_name', 'کاربر'), 
            last_name=data.get('last_name', 'جدید'),
            username=username, 
            phone=phone,
            email=email, 
            role='customer',
            password=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'ثبت نام با موفقیت انجام شد'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'خطای دیتابیس: {str(e)}'}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            token = create_access_token(identity=str(user.user_id), additional_claims={'role': user.role})
            return jsonify({'access_token': token, 'user': user.to_dict()})
            
        return jsonify({'error': 'نام کاربری یا رمز عبور اشتباه است'}), 401
    except Exception as e:
        return jsonify({'error': 'مشکل در ورود'}), 500

@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        data = request.get_json()
        
        if 'first_name' in data: user.first_name = data['first_name']
        if 'last_name' in data: user.last_name = data['last_name']
        if 'phone' in data: user.phone = data['phone']
        if 'email' in data: user.email = data['email']
        
        db.session.commit()
        return jsonify({'message': 'پروفایل بروزرسانی شد', 'user': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500