import os
from app import app, db
from models import *

def fix_database():
    with app.app_context():
        # حذف قاعدة البيانات الحالية
        db_path = os.path.join('instance', 'raizo_hr.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print("تم حذف قاعدة البيانات القديمة")
        
        # إنشاء قاعدة البيانات الجديدة
        db.create_all()
        print("تم إنشاء قاعدة البيانات الجديدة بنجاح")
        
        # إنشاء مستخدم افتراضي
        from models import User
        admin_user = User(
            username='admin',
            email='admin@raizo.com',
            role='admin'
        )
        admin_user.set_password('admin123')
        
        db.session.add(admin_user)
        db.session.commit()
        print("تم إنشاء المستخدم الافتراضي: admin / admin123")

if __name__ == '__main__':
    fix_database()