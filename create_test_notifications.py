from app import app
from models import db, Notification, User
from datetime import datetime

with app.app_context():
    # البحث عن المستخدم admin
    admin_user = User.query.filter_by(username='admin').first()
    
    if admin_user:
        # حذف الإشعارات القديمة
        Notification.query.filter_by(user_id=admin_user.id).delete()
        
        # إنشاء إشعارات تجريبية
        notifications = [
            {
                'title': 'مرحباً بك في النظام',
                'message': 'تم تسجيل دخولك بنجاح إلى نظام إدارة الموارد البشرية',
                'notification_type': 'success',
                'priority': 'medium'
            },
            {
                'title': 'تنبيه مهم',
                'message': 'يرجى مراجعة بيانات الموظفين الجدد',
                'notification_type': 'warning',
                'priority': 'high'
            },
            {
                'title': 'معلومة',
                'message': 'تم إضافة موظف جديد إلى النظام',
                'notification_type': 'info',
                'priority': 'low'
            }
        ]
        
        for notif_data in notifications:
            notification = Notification(
                title=notif_data['title'],
                message=notif_data['message'],
                notification_type=notif_data['notification_type'],
                priority=notif_data['priority'],
                user_id=admin_user.id,
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
        
        db.session.commit()
        
        # التحقق من الإشعارات
        count = Notification.query.filter_by(user_id=admin_user.id, is_read=False).count()
        print(f"تم إنشاء {count} إشعارات غير مقروءة للمستخدم {admin_user.username}")
        
        # عرض الإشعارات
        notifications = Notification.query.filter_by(user_id=admin_user.id).all()
        for notif in notifications:
            print(f"- {notif.title}: {notif.message}")
    else:
        print("لم يتم العثور على المستخدم admin")