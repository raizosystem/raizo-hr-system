from app import app
from models import db, Notification, User
from datetime import datetime

with app.app_context():
    try:
        # البحث عن المستخدم admin
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("لم يتم العثور على المستخدم admin")
            exit()
        
        # حذف الإشعارات القديمة
        Notification.query.filter_by(user_id=admin_user.id).delete()
        db.session.commit()
        
        # إنشاء إشعارات تجريبية
        test_notifications = [
            Notification(
                title='مرحباً بك في النظام',
                message='تم تسجيل دخولك بنجاح إلى نظام إدارة الموارد البشرية رايزو',
                notification_type='success',
                priority='medium',
                user_id=admin_user.id,
                is_read=False,
                created_at=datetime.utcnow()
            ),
            Notification(
                title='تنبيه مهم',
                message='يرجى مراجعة بيانات الموظفين الجدد والتأكد من اكتمال المعلومات',
                notification_type='warning',
                priority='high',
                user_id=admin_user.id,
                is_read=False,
                created_at=datetime.utcnow()
            ),
            Notification(
                title='إشعار جديد',
                message='تم إضافة موظف جديد إلى النظام بنجاح',
                notification_type='info',
                priority='low',
                user_id=admin_user.id,
                is_read=False,
                created_at=datetime.utcnow()
            )
        ]
        
        for notification in test_notifications:
            db.session.add(notification)
        
        db.session.commit()
        
        # التحقق من النتائج
        total_count = Notification.query.filter_by(user_id=admin_user.id).count()
        unread_count = Notification.query.filter_by(user_id=admin_user.id, is_read=False).count()
        
        print(f"✅ تم إنشاء {total_count} إشعارات بنجاح")
        print(f"📬 عدد الإشعارات غير المقروءة: {unread_count}")
        
        # عرض الإشعارات
        notifications = Notification.query.filter_by(user_id=admin_user.id).all()
        print("\n📋 قائمة الإشعارات:")
        for i, notif in enumerate(notifications, 1):
            status = "غير مقروء" if not notif.is_read else "مقروء"
            print(f"{i}. {notif.title} - {status}")
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        db.session.rollback()