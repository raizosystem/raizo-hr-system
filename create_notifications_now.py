from app import app
from models import db, Notification, User
from datetime import datetime

with app.app_context():
    try:
        # البحث عن المستخدم admin
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("❌ لم يتم العثور على المستخدم admin")
            exit()
        
        print(f"✅ تم العثور على المستخدم: {admin_user.username}")
        
        # حذف الإشعارات القديمة
        old_count = Notification.query.filter_by(user_id=admin_user.id).count()
        Notification.query.filter_by(user_id=admin_user.id).delete()
        db.session.commit()
        print(f"🗑️ تم حذف {old_count} إشعارات قديمة")
        
        # إنشاء إشعارات تجريبية جديدة
        notifications_data = [
            {
                'title': '🎉 مرحباً بك في نظام رايزو',
                'message': 'تم تسجيل دخولك بنجاح إلى نظام إدارة الموارد البشرية رايزو. نتمنى لك تجربة ممتعة!',
                'notification_type': 'success',
                'priority': 'high'
            },
            {
                'title': '⚠️ تنبيه مهم',
                'message': 'يرجى مراجعة بيانات الموظفين الجدد والتأكد من اكتمال جميع المعلومات المطلوبة.',
                'notification_type': 'warning',
                'priority': 'high'
            },
            {
                'title': '📋 إشعار جديد',
                'message': 'تم إضافة موظف جديد إلى النظام بنجاح. يمكنك مراجعة بياناته من قسم الموظفين.',
                'notification_type': 'info',
                'priority': 'medium'
            },
            {
                'title': '💰 تحديث الرواتب',
                'message': 'تم تحديث كشوف الرواتب لهذا الشهر. يرجى مراجعة التفاصيل.',
                'notification_type': 'info',
                'priority': 'medium'
            },
            {
                'title': '🔔 تذكير',
                'message': 'لا تنس مراجعة تقارير الحضور والغياب اليومية.',
                'notification_type': 'info',
                'priority': 'low'
            }
        ]
        
        created_count = 0
        for notif_data in notifications_data:
            notification = Notification(
                title=notif_data['title'],
                message=notif_data['message'],
                notification_type=notif_data['notification_type'],
                priority=notif_data['priority'],
                user_id=admin_user.id,
                is_read=False,
                is_dismissed=False,
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
            created_count += 1
        
        db.session.commit()
        
        # التحقق من النتائج
        total_count = Notification.query.filter_by(user_id=admin_user.id).count()
        unread_count = Notification.query.filter_by(user_id=admin_user.id, is_read=False).count()
        
        print(f"✅ تم إنشاء {created_count} إشعارات جديدة بنجاح!")
        print(f"📊 إجمالي الإشعارات: {total_count}")
        print(f"📬 الإشعارات غير المقروءة: {unread_count}")
        
        # عرض قائمة الإشعارات
        print("\n📋 قائمة الإشعارات المُنشأة:")
        notifications = Notification.query.filter_by(user_id=admin_user.id).all()
        for i, notif in enumerate(notifications, 1):
            status = "🔴 غير مقروء" if not notif.is_read else "✅ مقروء"
            print(f"{i}. {notif.title} - {status}")
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        db.session.rollback()
        import traceback
        traceback.print_exc()