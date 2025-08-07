from app import app, db
from models import User

with app.app_context():
    # إنشاء مستخدم admin جديد
    admin = User(
        username='superadmin',
        email='superadmin@raizo.com',
        role='admin'
    )
    admin.set_password('123456')
    
    db.session.add(admin)
    db.session.commit()
    print('تم إنشاء مستخدم المدير الجديد')