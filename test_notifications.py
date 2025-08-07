from app import app, db
from models import User, Notification
from datetime import datetime

def test_notifications():
    with app.app_context():
        try:
            # التحقق من وجود المستخدم admin
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("لم يتم العثور على مستخدم admin")
                return
            
            print(f"تم العثور على المستخدم: {admin_user.username} (ID: {admin_user.id})")
            
            # إنشاء إشعار تجريبي
            test_notification = Notification.create_notification(
                user_id=admin_user.id,
                title="إشعار تجريبي",
                message="هذا إشعار تجريبي للتأكد من عمل النظام",
                notification_type="info",
                priority="normal"
            )
            
            print(f"تم إنشاء إشعار تجريبي بنجاح (ID: {test_notification.id})")
            
            # عرض جميع الإشعارات للمستخدم
            notifications = Notification.get_user_notifications(admin_user.id)
            print(f"عدد الإشعارات الإجمالي: {len(notifications)}")
            
            # عرض الإشعارات غير المقروءة
            unread_notifications = Notification.query.filter_by(
                user_id=admin_user.id, 
                is_read=False, 
                is_dismissed=False
            ).count()
            print(f"عدد الإشعارات غير المقروءة: {unread_notifications}")
            
            # عرض تفاصيل الإشعارات
            for notification in notifications:
                print(f"- {notification.title}: {notification.message} (مقروء: {notification.is_read})")
                
        except Exception as e:
            print(f"خطأ في اختبار الإشعارات: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_notifications()