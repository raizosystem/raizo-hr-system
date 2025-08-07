from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # حذف جميع الجداول
        db.drop_all()
        
        # إنشاء جميع الجداول
        db.create_all()
        
        # إنشاء مستخدم مدير افتراضي
        admin_user = User(
            username='admin',
            email='admin@raizo.com',
            role='admin'
        )
        admin_user.set_password('admin123')
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print('تم إنشاء قاعدة البيانات بنجاح!')
            print('بيانات المدير الافتراضي:')
            print('اسم المستخدم: admin')
            print('كلمة المرور: admin123')
            print('البريد الإلكتروني: admin@raizo.com')
        except Exception as e:
            db.session.rollback()
            print(f'خطأ في إنشاء المستخدم الافتراضي: {e}')

if __name__ == '__main__':
    init_database()