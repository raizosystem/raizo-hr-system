from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # بيانات الموظف الأساسية
    employee_photo = db.Column(db.String(200))  # صورة الموظف
    employee_id = db.Column(db.String(20), unique=True, nullable=False)  # الرقم الوظيفي
    name_arabic = db.Column(db.String(100), nullable=False)  # اسم الموظف بالعربي
    name_english = db.Column(db.String(100))  # اسم الموظف بالإنجليزي
    national_id = db.Column(db.String(20), unique=True, nullable=False)  # رقم الهوية
    id_validity = db.Column(db.String(20), nullable=False)  # سارية / غير سارية
    id_expiry_date = db.Column(db.Date, nullable=False)  # تاريخ انتهاء رقم الهوية
    birth_date = db.Column(db.Date, nullable=False)  # تاريخ الميلاد
    nationality = db.Column(db.String(50), nullable=False)  # الجنسية
    birth_place = db.Column(db.String(100))  # مكان الميلاد
    marital_status = db.Column(db.String(20))  # الحالة الاجتماعية
    gender = db.Column(db.String(10), nullable=False)  # الجنس
    id_issuer = db.Column(db.String(100))  # جهة اصدار الهوية
    has_driving_license = db.Column(db.Boolean, default=False)  # هل يحمل رخصة قيادة
    license_expiry_date = db.Column(db.Date)  # تاريخ انتهاء رخصة القيادة
    
    # بيانات التواصل
    phone = db.Column(db.String(20), nullable=False)  # رقم الجوال
    additional_phone = db.Column(db.String(20))  # رقم جوال إضافي
    email = db.Column(db.String(120))  # الإيميل
    address = db.Column(db.Text)  # عنوان السكن
    emergency_phone = db.Column(db.String(20))  # رقم جوال للطوارئ
    
    # بيانات العقد
    salary = db.Column(db.Float, nullable=False)  # الراتب
    contract_signing_date = db.Column(db.Date, nullable=False)  # تاريخ توقيع العقد
    contract_end_date = db.Column(db.Date, nullable=False)  # تاريخ انتهاء العقد
    start_work_date = db.Column(db.Date)  # تاريخ المباشرة
    contract_duration = db.Column(db.String(50), nullable=False)  # مدة العقد
    
    # بيانات الوظيفة
    job_title = db.Column(db.String(100), nullable=False)  # المسمى الوظيفي
    contract_type = db.Column(db.String(50), nullable=False)  # نوع العقد
    probation_period = db.Column(db.String(50))  # فترة التجربة
    working_hours = db.Column(db.Integer)  # عدد ساعات العمل
    uniform_provision = db.Column(db.String(50), nullable=False)  # بند استلام البدلة
    operating_company = db.Column(db.String(100), nullable=False)  # اسم الشركة المشغلة
    notes = db.Column(db.Text)  # ملاحظات
    penalty_clause = db.Column(db.Text)  # الشرط الجزائي
    internet_provision = db.Column(db.String(50), nullable=False)  # بند توفير انترنت
    
    # بيانات العمل
    department = db.Column(db.String(50), nullable=False)  # القسم
    center = db.Column(db.String(100))  # المركز
    square = db.Column(db.String(100))  # المربع
    camp_number = db.Column(db.String(50))  # رقم المخيم
    work_shift = db.Column(db.String(50))  # فترة العمل
    
    # بيانات البنك
    bank_type = db.Column(db.String(100))  # نوع البنك
    iban_number = db.Column(db.String(50))  # رقم الآيبان
    iban_certificate = db.Column(db.String(200))  # شهادة الآيبان
    additional_bank = db.Column(db.String(100))  # بنك إضافي
    additional_iban = db.Column(db.String(50))  # رقم الآيبان الإضافي
    beneficiary_name = db.Column(db.String(100))  # اسم المستفيد
    beneficiary_phone = db.Column(db.String(20))  # رقم جوال المستفيد
    
    # حقول النظام القديمة للتوافق
    first_name = db.Column(db.String(50))  # للتوافق مع النظام القديم
    last_name = db.Column(db.String(50))  # للتوافق مع النظام القديم
    employee_type = db.Column(db.String(30), nullable=False)  # نوع الموظف
    hire_date = db.Column(db.Date, nullable=False)  # تاريخ التوظيف
    status = db.Column(db.String(20), default='active')  # حالة الموظف
    emergency_contact = db.Column(db.String(100))  # جهة الاتصال في الطوارئ
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات - تحديث العلاقات
    payroll_records = db.relationship('Payroll', backref='employee', lazy=True)
    assets = db.relationship('Asset', backref='employee', lazy=True)
    # لا حاجة لإضافة علاقة attendance_records هنا لأنها موجودة في backref أعلاه
    
    @property
    def full_name(self):
        return self.name_arabic or f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None
    
    @staticmethod
    def generate_employee_id():
        """توليد رقم وظيفي تلقائي"""
        import random
        import string
        
        while True:
            # توليد رقم وظيفي من 6 أرقام
            employee_id = ''.join(random.choices(string.digits, k=6))
            
            # التحقق من عدم وجود هذا الرقم مسبقاً
            existing = Employee.query.filter_by(employee_id=employee_id).first()
            if not existing:
                return employee_id
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    break_start = db.Column(db.Time)
    break_end = db.Column(db.Time)
    status = db.Column(db.String(20), default='present')
    notes = db.Column(db.Text)
    
    # الحقول الجديدة
    employee_type = db.Column(db.String(20), default='primary')
    substitute_for_employee_id = db.Column(db.String(20), nullable=True)  # رقم الموظف البديل كنص
    report_file = db.Column(db.String(200), nullable=True)
    data_completeness = db.Column(db.String(20), default='incomplete')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # إضافة العلاقة الصحيحة
    employee = db.relationship('Employee', backref='attendance_records', lazy=True)
    
    @property
    def total_hours(self):
        if self.check_in and self.check_out:
            start = datetime.combine(date.today(), self.check_in)
            end = datetime.combine(date.today(), self.check_out)
            total = end - start
            
            # خصم وقت الاستراحة
            if self.break_start and self.break_end:
                break_start = datetime.combine(date.today(), self.break_start)
                break_end = datetime.combine(date.today(), self.break_end)
                break_duration = break_end - break_start
                total -= break_duration
            
            return total.total_seconds() / 3600
        return 0
    
    def check_data_completeness(self):
        """فحص اكتمال البيانات"""
        if self.status in ['absent', 'withdrawn']:
            # للغياب والانسحاب: يجب وجود المحضر
            if self.report_file:
                self.data_completeness = 'complete'
            else:
                self.data_completeness = 'incomplete'
        elif self.status == 'present':
            # للحضور: يجب وجود أوقات الدخول والخروج
            if self.check_in and self.check_out:
                self.data_completeness = 'complete'
            else:
                self.data_completeness = 'incomplete'
        else:
            self.data_completeness = 'incomplete'
        
        return self.data_completeness

# إضافة نموذج جديد لأوقات الورديات
class ShiftTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shift_name = db.Column(db.String(50), nullable=False)  # اسم الوردية
    start_time = db.Column(db.Time, nullable=False)  # وقت البداية
    end_time = db.Column(db.Time, nullable=False)  # وقت النهاية
    break_start = db.Column(db.Time)  # بداية الاستراحة
    break_end = db.Column(db.Time)  # نهاية الاستراحة
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    
    # الفترة
    period_from = db.Column(db.Date, nullable=False)  # من الفترة
    period_to = db.Column(db.Date, nullable=False)    # إلى الفترة
    period_days = db.Column(db.Integer, nullable=False)  # مدة أيام الفترة
    
    # الحضور والغياب والانسحاب
    present_days = db.Column(db.Integer, default=0)     # عدد أيام الحضور
    absent_days = db.Column(db.Integer, default=0)      # عدد أيام الغياب
    withdrawal_days = db.Column(db.Integer, default=0)  # عدد أيام الانسحاب
    
    # الراتب والعمل الإضافي
    basic_salary = db.Column(db.Float, nullable=False)   # الراتب الأساسي
    daily_salary = db.Column(db.Float, nullable=False)   # الراتب اليومي
    due_salary = db.Column(db.Float, nullable=False)     # الراتب المستحق
    overtime_days = db.Column(db.Float, default=0)       # عدد أيام العمل الإضافي
    overtime_due = db.Column(db.Float, default=0)        # مستحق العمل الإضافي
    total_salary = db.Column(db.Float, nullable=False)   # إجمالي الراتب
    
    # المخالفات والحسميات
    advance_deduction = db.Column(db.Float, default=0)      # حسم السلف
    violation_deduction = db.Column(db.Float, default=0)    # حسم المخالفات
    absence_deduction = db.Column(db.Float, default=0)      # حسم الغياب
    withdrawal_deduction = db.Column(db.Float, default=0)   # حسم الانسحاب
    total_deductions = db.Column(db.Float, default=0)       # إجمالي الحسميات
    
    # صافي الراتب
    net_salary = db.Column(db.Float, nullable=False)     # صافي الراتب
    notes = db.Column(db.Text)                           # ملاحظات
    
    # الحقول الموجودة سابقاً
    housing_allowance = db.Column(db.Float, default=0)
    transport_allowance = db.Column(db.Float, default=0)
    other_allowances = db.Column(db.Float, default=0)
    insurance_deduction = db.Column(db.Float, default=0)
    tax_deduction = db.Column(db.Float, default=0)
    other_deductions = db.Column(db.Float, default=0)
    regular_hours = db.Column(db.Float, default=0)
    overtime_hours = db.Column(db.Float, default=0)
    overtime_rate = db.Column(db.Float, default=1.5)
    gross_salary = db.Column(db.Float)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_detailed_salary(self):
        # حساب الراتب اليومي
        self.daily_salary = self.basic_salary / 30
        
        # حساب الراتب المستحق بناءً على أيام الحضور
        self.due_salary = self.daily_salary * self.present_days
        
        # حساب مستحق العمل الإضافي
        self.overtime_due = self.overtime_days * self.daily_salary * self.overtime_rate
        
        # حساب إجمالي الراتب
        self.total_salary = (
            self.due_salary + 
            self.overtime_due + 
            self.housing_allowance + 
            self.transport_allowance + 
            self.other_allowances
        )
        
        # حساب حسم الغياب
        self.absence_deduction = self.absent_days * self.daily_salary
        
        # حساب حسم الانسحاب
        self.withdrawal_deduction = self.withdrawal_days * self.daily_salary
        
        # حساب إجمالي الحسميات
        self.total_deductions = (
            self.advance_deduction +
            self.violation_deduction +
            self.absence_deduction +
            self.withdrawal_deduction +
            self.insurance_deduction +
            self.tax_deduction +
            self.other_deductions
        )
        
        # حساب صافي الراتب
        self.net_salary = self.total_salary - self.total_deductions
        
        # حساب الراتب الإجمالي للتوافق مع النظام القديم
        self.gross_salary = self.total_salary

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float)
    
    # معلومات التخصيص
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    assigned_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='available')  # available, assigned, returned, damaged
    
    condition = db.Column(db.String(20), default='good')  # good, fair, poor, damaged
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_name = db.Column(db.String(200), nullable=False)  # اسم المستند
    original_filename = db.Column(db.String(200), nullable=False)  # اسم الملف الأصلي
    filename = db.Column(db.String(200), nullable=False)  # اسم الملف المحفوظ
    file_path = db.Column(db.String(500), nullable=False)  # مسار الملف
    file_size = db.Column(db.Integer)  # حجم الملف بالبايت
    
    # بيانات التصنيف
    department = db.Column(db.String(100), nullable=False)  # القسم
    category = db.Column(db.String(100), nullable=False)  # فئة المستند
    description = db.Column(db.Text)  # وصف المستند
    
    # ربط بالموظف (اختياري)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    employee_name = db.Column(db.String(100))  # اسم الموظف للبحث السريع
    employee_number = db.Column(db.String(20))  # الرقم الوظيفي للبحث
    
    # بيانات النظام
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime)
    access_count = db.Column(db.Integer, default=0)
    
    # حالة المستند
    status = db.Column(db.String(20), default='active')  # active, archived, deleted
    is_confidential = db.Column(db.Boolean, default=False)  # سري أم لا
    
    # العلاقات
    uploader = db.relationship('User', backref='uploaded_documents')
    employee = db.relationship('Employee', backref='documents')
    
    def __repr__(self):
        return f'<Document {self.document_name}>'
    
    @property
    def file_size_mb(self):
        """حجم الملف بالميجابايت"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    position_applied = db.Column(db.String(50), nullable=False)
    
    # المؤهلات
    education = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    skills = db.Column(db.Text)
    
    # الملفات
    cv_filename = db.Column(db.String(100))
    cover_letter = db.Column(db.Text)
    
    # حالة الطلب
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, interviewed, hired, rejected
    notes = db.Column(db.Text)
    
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_date = db.Column(db.DateTime)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # معلومات الشركة
    company_name = db.Column(db.String(200), default='شركة رايزو')
    app_name = db.Column(db.String(200), default='RAIZO HR System')
    commercial_register = db.Column(db.String(100))
    tax_number = db.Column(db.String(100))
    company_address = db.Column(db.Text)
    
    # إعدادات الرواتب
    currency = db.Column(db.String(50), default='ريال سعودي')
    currency_symbol = db.Column(db.String(10), default='ر.س')
    monthly_hours = db.Column(db.Integer, default=160)
    default_overtime_rate = db.Column(db.Float, default=1.5)
    
    # إعدادات النظام
    session_lifetime = db.Column(db.Integer, default=2)  # بالساعات
    max_file_size = db.Column(db.Integer, default=16)  # بالميجابايت
    default_language = db.Column(db.String(10), default='ar')
    timezone = db.Column(db.String(50), default='Asia/Riyadh')
    
    # إعدادات الأمان
    require_strong_password = db.Column(db.Boolean, default=True)
    enable_login_attempts = db.Column(db.Boolean, default=True)
    max_login_attempts = db.Column(db.Integer, default=5)
    lockout_duration = db.Column(db.Integer, default=30)  # بالدقائق
    
    # إعدادات النسخ الاحتياطي
    auto_backup = db.Column(db.Boolean, default=False)
    backup_frequency = db.Column(db.String(20), default='weekly')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_settings():
        """الحصول على الإعدادات الحالية أو إنشاء إعدادات افتراضية"""
        try:
            settings = Settings.query.first()
            if not settings:
                settings = Settings()
                db.session.add(settings)
                db.session.commit()
            return settings
        except Exception as e:
            print(f"خطأ في get_settings: {e}")
            db.session.rollback()
            # إرجاع إعدادات افتراضية في حالة الخطأ
            return Settings()

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # عنوان الإشعار
    message = db.Column(db.Text, nullable=False)  # نص الإشعار
    notification_type = db.Column(db.String(50), nullable=False)  # نوع الإشعار (info, warning, error, success)
    priority = db.Column(db.String(20), default='normal')  # أولوية الإشعار (low, normal, high, urgent)
    
    # المستخدم المرسل إليه الإشعار
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # معلومات الحالة
    is_read = db.Column(db.Boolean, default=False)  # هل تم قراءة الإشعار
    is_dismissed = db.Column(db.Boolean, default=False)  # هل تم إخفاء الإشعار
    
    # معلومات إضافية
    action_url = db.Column(db.String(500))  # رابط الإجراء المطلوب
    action_text = db.Column(db.String(100))  # نص زر الإجراء
    expires_at = db.Column(db.DateTime)  # تاريخ انتهاء صلاحية الإشعار
    
    # معلومات المصدر
    source_type = db.Column(db.String(50))  # نوع المصدر (employee, attendance, payroll, etc.)
    source_id = db.Column(db.Integer)  # معرف المصدر
    
    # التواريخ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)  # تاريخ القراءة
    
    # العلاقات
    user = db.relationship('User', backref='notifications')
    
    def mark_as_read(self):
        """تحديد الإشعار كمقروء"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def dismiss(self):
        """إخفاء الإشعار"""
        self.is_dismissed = True
        db.session.commit()
    
    @property
    def is_expired(self):
        """التحقق من انتهاء صلاحية الإشعار"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    @staticmethod
    def create_notification(user_id, title, message, notification_type='info', 
                          priority='normal', action_url=None, action_text=None,
                          expires_at=None, source_type=None, source_id=None):
        """إنشاء إشعار جديد"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            action_text=action_text,
            expires_at=expires_at,
            source_type=source_type,
            source_id=source_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def get_user_notifications(user_id, unread_only=False, limit=None):
        """جلب إشعارات المستخدم"""
        query = Notification.query.filter_by(user_id=user_id, is_dismissed=False)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        # استبعاد الإشعارات المنتهية الصلاحية
        query = query.filter(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
        
        query = query.order_by(Notification.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def to_dict(self):
        """تحويل الإشعار إلى قاموس"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'priority': self.priority,
            'is_read': self.is_read,
            'action_url': self.action_url,
            'action_text': self.action_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'source_type': self.source_type,
            'source_id': self.source_id
        }

class NotificationSettings(db.Model):
    __tablename__ = 'notification_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # إعدادات أنواع الإشعارات
    employee_notifications = db.Column(db.Boolean, default=True)  # إشعارات الموظفين
    attendance_notifications = db.Column(db.Boolean, default=True)  # إشعارات الحضور
    payroll_notifications = db.Column(db.Boolean, default=True)  # إشعارات الرواتب
    document_notifications = db.Column(db.Boolean, default=True)  # إشعارات المستندات
    system_notifications = db.Column(db.Boolean, default=True)  # إشعارات النظام
    
    # إعدادات الأولوية
    show_low_priority = db.Column(db.Boolean, default=True)
    show_normal_priority = db.Column(db.Boolean, default=True)
    show_high_priority = db.Column(db.Boolean, default=True)
    show_urgent_priority = db.Column(db.Boolean, default=True)
    
    # إعدادات العرض
    auto_dismiss_after_days = db.Column(db.Integer, default=7)  # إخفاء تلقائي بعد أيام
    max_notifications_display = db.Column(db.Integer, default=10)  # عدد الإشعارات المعروضة
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    user = db.relationship('User', backref='notification_settings')
    
    @staticmethod
    def get_or_create_settings(user_id):
        """جلب أو إنشاء إعدادات الإشعارات للمستخدم"""
        settings = NotificationSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = NotificationSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
        return settings