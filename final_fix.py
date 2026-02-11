import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from app import create_app
from app.extensions import db
from app.models import User, Category, Product, Seller
from sqlalchemy import text
from werkzeug.security import generate_password_hash

def run_super_fix():
    app = create_app()
    with app.app_context():
        print("🔍 مرحله ۰: تست اتصال...")
        try:
            db.session.execute(text('SELECT 1'))
            print("✅ اتصال دیتابیس برقرار است.")
        except Exception as e:
            print(f"❌ خطا در اتصال: {e}")
            return

        print("\n⏳ مرحله ۱: بازسازی جداول...")
        db.create_all()
        print("✅ جداول آماده‌اند.")

        print("\n⏳ مرحله ۲: ساخت کاربران...")
        
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(
                first_name='مدیر', last_name='سیستم', username='admin',
                password=generate_password_hash('admin'), 
                email='admin@market.com', phone='09001111111', role='admin'
            ))
            print("✅ ادمین ساخته شد.")

        if not User.query.filter_by(username='ali_ahmadi').first():
            db.session.add(User(
                first_name='علی', last_name='احمدی', username='ali_ahmadi',
                password=generate_password_hash('123456'), 
                email='ali@test.com', phone='09121234567', role='customer'
            ))
            print("✅ مشتری تست ساخته شد.")
        
        try:
            db.session.commit()
        except:
            db.session.rollback()

        print("\n⏳ مرحله ۳: داده‌های فروشگاه...")
        
        seller = Seller.query.first()
        if not seller:
            seller = Seller(
                store_name='فروشگاه مرکزی (ادمین)', 
                owner_name='مدیر سیستم', 
                phone='02100000000',
                address='دفتر مرکزی', 
                join_date=datetime.now(), 
                status='Approved'
            )
            db.session.add(seller)
            db.session.commit() 
            print("✅ پروفایل فروشنده برای ادمین ایجاد شد.")
            
            seller = Seller.query.first()

        categories_data = [
            {'name': 'کالای دیجیتال', 'desc': 'موبایل، لپ‌تاپ و لوازم جانبی'},
            {'name': 'مد و پوشاک', 'desc': 'لباس مردانه، زنانه و اکسسوری'},
            {'name': 'خانه و آشپزخانه', 'desc': 'لوازم برقی و دکوراسیون'},
            {'name': 'کتاب و لوازم تحریر', 'desc': 'کتاب‌های چاپی و صوتی'}
        ]

        cats_db = {}
        for c_data in categories_data:
            cat = Category.query.filter_by(category_name=c_data['name']).first()
            if not cat:
                cat = Category(category_name=c_data['name'], description=c_data['desc'])
                db.session.add(cat)
                db.session.commit()
                print(f"✅ دسته '{c_data['name']}' اضافه شد.")
            cats_db[c_data['name']] = cat.category_id

        if Product.query.count() == 0:
            products_list = [
                {'name': 'گوشی موبایل X', 'price': 25000000, 'stock': 10, 'cat': 'کالای دیجیتال', 'desc': 'گوشی هوشمند پرچمدار'},
                {'name': 'لپ‌تاپ گیمینگ', 'price': 65000000, 'stock': 3, 'cat': 'کالای دیجیتال', 'desc': 'مناسب بازی و رندرینگ'},
                {'name': 'تی‌شرت نخی', 'price': 350000, 'stock': 100, 'cat': 'مد و پوشاک', 'desc': 'خنک و راحت'},
                {'name': 'کفش ورزشی', 'price': 1200000, 'stock': 20, 'cat': 'مد و پوشاک', 'desc': 'مناسب پیاده‌روی'},
                {'name': 'قهوه‌ساز برقی', 'price': 4500000, 'stock': 15, 'cat': 'خانه و آشپزخانه', 'desc': 'قهوه دمی تازه'},
                {'name': '', 'price': 0, 'stock': 0, 'cat': 'کالای دیجیتال', 'desc': 'محصول ناقص'} 
            ]

            added_count = 0
            for p_data in products_list:
                if not p_data['name'] or p_data['name'].strip() == "":
                    print("⚠️ هشدار: یک محصول بدون نام نادیده گرفته شد.")
                    continue

                cat_id = cats_db.get(p_data['cat'])
                if cat_id and seller:
                    new_p = Product(
                        name=p_data['name'],
                        price=p_data['price'],
                        stock=p_data['stock'],
                        category_id=cat_id,
                        seller_id=seller.seller_id, 
                        description=p_data['desc']
                    )
                    db.session.add(new_p)
                    added_count += 1
            
            db.session.commit()
            print(f"✅ {added_count} محصول معتبر به فروشگاه اضافه شد.")
        else:
            print("ℹ️ محصولات از قبل وجود دارند.")

        print("\n🎉 تمام عملیات با موفقیت انجام شد!")

if __name__ == "__main__":
    run_super_fix()