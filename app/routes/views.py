from flask import Blueprint, render_template

bp = Blueprint('views', __name__)

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/admin/login')
def admin_login_page():
    return render_template('admin_login.html')