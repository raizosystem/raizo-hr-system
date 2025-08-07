from app import app, db
from models import Notification, User
from sqlalchemy import text

def check_database():
    with app.app_context():
        try:
            # فحص الجداول الموجودة
            result = db.engine.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            print(f"الجداول الموجودة: {tables}")
            
            # فحص جدول الإشعارات
            if 'notifications' in tables:
                notifications_count = Notification.query.count()
                print(f"عدد الإشعارات في قاعدة البيانات: {notifications_count}")
            else:
                print("جدول الإشعارات غير موجود")
                
            # فحص المستخدمين
            users_count = User.query.count()
            print(f"عدد المستخدمين: {users_count}")
            
        except Exception as e:
            print(f"خطأ في فحص قاعدة البيانات: {e}")

if __name__ == '__main__':
    check_database()