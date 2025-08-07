class Config:
    SECRET_KEY = 'your-very-secure-secret-key-here'  # غير هذا المفتاح
    SQLALCHEMY_DATABASE_URI = 'sqlite:///raizo_hr.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات الإنتاج
    DEBUG = False
    TESTING = False
    
    # إعدادات الأمان
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # إعدادات رفع الملفات
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = 'static/uploads'

class ProductionConfig(Config):
    DEBUG = False
    # يمكن إضافة قاعدة بيانات خارجية هنا
    # SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@host:port/database'

class DevelopmentConfig(Config):
    DEBUG = True