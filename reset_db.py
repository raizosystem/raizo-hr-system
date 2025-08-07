from app import app, db
from models import User

def reset_database():
    with app.app_context():
        try:
            # حذف جميع الجداول
            db.drop_all()
            print("تم حذف جميع الجداول")
            
            # إنشاء الجداول من جديد
            db.create_all()
            print("تم إنشاء الجداول من جديد")
            
            # إنشاء مستخدم admin
            admin_user = User(
                username='admin',
                email='admin@raizo.com',
                role='admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("تم إنشاء مستخدم admin")
            
        except Exception as e:
            print(f"خطأ في إعادة إنشاء قاعدة البيانات: {e}")
            db.session.rollback()

if __name__ == '__main__':
    reset_database()