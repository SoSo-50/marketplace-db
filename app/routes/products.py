from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import Product, Category, Seller
from decimal import Decimal

bp = Blueprint('products', __name__)

@bp.route('/categories', methods=['GET'])
def get_categories():
    cats = Category.query.all()
    return jsonify([c.to_dict() for c in cats])

@bp.route('/products', methods=['GET', 'POST'])
def handle_products():
    if request.method == 'POST':
        d = request.get_json()
        
        if not d.get('name') or not d.get('price') or not d.get('stock'):
            return jsonify({'error': 'نام، قیمت و موجودی الزامی هستند'}), 400

        try:
            p = Product(
                name=d['name'], 
                price=Decimal(str(d['price'])), 
                stock=int(d['stock']), 
                seller_id=int(d['seller_id']), 
                category_id=int(d['category_id']),
                is_active=True 
            )
            db.session.add(p)
            db.session.commit()
            return jsonify(p.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    search = request.args.get('search')
    cat_id = request.args.get('category_id')
    query = Product.query.filter_by(is_active=True)
    
    if search: query = query.filter(Product.name.ilike(f'%{search}%'))
    if cat_id: query = query.filter_by(category_id=int(cat_id))
    
    p = query.order_by(Product.product_id.desc()).paginate(page=1, per_page=50, error_out=False)
    return jsonify({'products': [x.to_dict() for x in p.items]})

@bp.route('/products/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    try:
        p = Product.query.get(id)
        if not p:
            return jsonify({'error': 'محصول یافت نشد'}), 404
        
        p.is_active = False 
        
        db.session.commit()
        return jsonify({'message': 'محصول حذف شد'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'خطا در حذف محصول'}), 400

@bp.route('/sellers', methods=['GET'])
def get_sellers():
    return jsonify([s.to_dict() for s in Seller.query.all()])