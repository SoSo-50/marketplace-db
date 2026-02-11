from .extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {'id': self.category_id, 'name': self.category_name, 'description': self.description}

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='customer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.user_id, 'first_name': self.first_name, 'last_name': self.last_name,
            'email': self.email, 'phone': self.phone, 'username': self.username, 'role': self.role
        }

class Seller(db.Model):
    __tablename__ = 'seller'
    seller_id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    join_date = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    products = db.relationship('Product', backref='seller', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {'id': self.seller_id, 'store_name': self.store_name, 'owner_name': self.owner_name}

class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.seller_id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    images = db.Column(JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.product_id, 'name': self.name, 'description': self.description,
            'price': float(self.price), 'stock': self.stock, 'category_id': self.category_id, 'seller_id': self.seller_id
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    shipping_address = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.order_id, 'user_id': self.user_id, 'total_amount': float(self.total_amount),
            'shipping_address': self.shipping_address, 'status': self.status, 'order_date': self.order_date.isoformat()
        }

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Numeric(12, 2), nullable=False)

class Payment(db.Model):
    __tablename__ = 'payment'
    payment_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    transaction_no = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.payment_id, 'order_id': self.order_id, 'transaction_no': self.transaction_no,
            'amount': float(self.amount), 'status': self.status
        }