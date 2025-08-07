from app import app, db
from models import User, Settings

def init_production_database():
    with app.app_context():
        # إنشاء الجداول
        db.create_all()
        
        # إنشاء مستخدم المدير
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            admin_user = User(
                username='admin',
                email='admin@yourcompany.com',  # غير هذا الإيميل
                role='admin'
            )
            admin_user.set_password('SecurePassword123!')  # غير كلمة المرور
            
            try:
                db.session.add(admin_user)
                db.session.commit()
                print('تم إنشاء مستخدم المدير بنجاح')
            except Exception as e:
                db.session.rollback()
                print(f'خطأ في إنشاء المستخدم: {e}')
        
        # إنشاء الإعدادات الافتراضية
        settings = Settings.query.first()
        if not settings:
            default_settings = Settings(
                company_name='شركتك',
                auto_backup=True,
                backup_frequency='weekly'
            )
            try:
                db.session.add(default_settings)
                db.session.commit()
                print('تم إنشاء الإعدادات الافتراضية')
            except Exception as e:
                db.session.rollback()
                print(f'خطأ في إنشاء الإعدادات: {e}')

if __name__ == '__main__':
    init_production_database()