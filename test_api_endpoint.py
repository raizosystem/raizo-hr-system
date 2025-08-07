from app import app
from models import db, Notification, User
import json

with app.app_context():
    with app.test_client() as client:
        # محاكاة تسجيل الدخول
        with client.session_transaction() as sess:
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                sess['user_id'] = admin_user.id
                sess['_fresh'] = True
        
        # اختبار API
        response = client.get('/api/notifications?unread_only=true&limit=5')
        
        print(f"📡 حالة الاستجابة: {response.status_code}")
        print(f"📊 البيانات المرجعة:")
        
        if response.status_code == 200:
            data = response.get_json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ خطأ: {response.data.decode()}")