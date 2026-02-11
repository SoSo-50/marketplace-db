from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from ..models import Order, Payment

bp = Blueprint('admin', __name__)

@bp.route('/admin/orders', methods=['GET'])
@jwt_required()
def get_all_orders_admin():
    orders = Order.query.order_by(Order.order_id.desc()).all()
    
    result = []
    for o in orders:
        data = o.to_dict()
        if o.user:
            data['user_full_name'] = f"{o.user.first_name} {o.user.last_name}"
        else:
            data['user_full_name'] = "کاربر ناشناس"
        result.append(data)

    return jsonify(result)

@bp.route('/payments', methods=['GET'])
@jwt_required()
def get_all_payments():
    payments = Payment.query.order_by(Payment.payment_id.desc()).all()
    return jsonify([p.to_dict() for p in payments])