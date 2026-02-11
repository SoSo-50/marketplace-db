from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Order, OrderItem, Product, Payment
from decimal import Decimal

bp = Blueprint('orders', __name__)

@bp.route('/orders', methods=['GET', 'POST'])
@jwt_required()
def handle_orders():
    uid = int(get_jwt_identity())
    
    if request.method == 'GET':
        orders = Order.query.filter_by(user_id=uid).order_by(Order.order_id.desc()).all()
        return jsonify([o.to_dict() for o in orders])
    
    if request.method == 'POST':
        d = request.get_json()
        try:
            order = Order(user_id=uid, shipping_address=d.get('shipping_address', '-'), status='Pending')
            db.session.add(order)
            db.session.flush()
            
            total_calc = 0
            for item in d['items']:
                p = Product.query.with_for_update().get(item['product_id'])
                if not p or p.stock < item['quantity']: 
                    raise Exception(f'موجودی ناکافی: {p.name}')
                
                p.stock -= item['quantity']
                db.session.add(OrderItem(order_id=order.order_id, product_id=p.product_id, quantity=item['quantity'], item_price=p.price))
                total_calc += p.price * item['quantity']
            
            order.total_amount = total_calc 
            db.session.commit()
            return jsonify({'msg': 'OK', 'order_id': order.order_id, 'total_amount': float(order.total_amount)}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

@bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    d = request.get_json()
    order = Order.query.get(order_id)
    if order:
        order.status = d.get('status')
        db.session.commit()
        return jsonify({'msg': 'Updated'})
    return jsonify({'error': 'Not found'}), 404

@bp.route('/orders/<int:order_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_my_order(order_id):
    uid = int(get_jwt_identity())
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify({'error': 'سفارش یافت نشد'}), 404

    if order.user_id != uid:
        return jsonify({'error': 'شما اجازه تغییر این سفارش را ندارید'}), 403
        
    if order.status not in ['Pending', 'Processing']:
        return jsonify({'error': 'سفارش وارد مراحل ارسال شده و قابل لغو نیست'}), 400
        
    try:
        order.status = 'Cancelled'
        db.session.commit()
        return jsonify({'msg': 'سفارش با موفقیت لغو شد'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/payments', methods=['POST'])
@jwt_required()
def create_payment():
    d = request.get_json()
    try:
        payment = Payment(
            order_id=d['order_id'], transaction_no=d['transaction_no'],
            amount=Decimal(str(d['amount'])), method=d['method'], status=d['status']
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify(payment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400