from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, FloatField, IntegerField, TimeField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
from datetime import date

class EmployeeForm(FlaskForm):
    # صورة الموظف (مطلوبة في الإضافة، اختيارية في التعديل)
    employee_photo = FileField('صورة الموظف', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'الصور فقط!')])
    
    # بيانات الموظف الأساسية
    name_arabic = StringField('اسم الموظف بالعربي', validators=[DataRequired(), Length(min=2, max=100)])
    name_english = StringField('اسم الموظف بالإنجليزي', validators=[Length(max=100)])
    national_id = StringField('رقم الهوية', validators=[DataRequired(), Length(min=10, max=20)])
    id_validity = SelectField('سارية الهوية', choices=[('سارية', 'سارية'), ('غير سارية', 'غير سارية')], validators=[DataRequired()])
    id_expiry_date = DateField('تاريخ انتهاء الهوية', validators=[DataRequired()])
    birth_date = DateField('تاريخ الميلاد', validators=[DataRequired()])
    nationality = StringField('الجنسية', validators=[DataRequired(), Length(max=50)])
    birth_place = StringField('مكان الميلاد', validators=[Length(max=100)])
    marital_status = SelectField('الحالة الاجتماعية', 
                                choices=[('', 'اختر الحالة'), ('أعزب', 'أعزب'), ('متزوج', 'متزوج'), ('مطلق', 'مطلق'), ('أرمل', 'أرمل')],
                                validators=[Optional()])
    gender = SelectField('الجنس', choices=[('ذكر', 'ذكر'), ('أنثى', 'أنثى')], validators=[DataRequired()])
    id_issuer = StringField('جهة إصدار الهوية', validators=[Length(max=100)])
    has_driving_license = BooleanField('يحمل رخصة قيادة')
    license_expiry_date = DateField('تاريخ انتهاء رخصة القيادة', validators=[Optional()])
    
    # بيانات التواصل
    phone = StringField('رقم الجوال', validators=[DataRequired(), Length(max=20)])
    additional_phone = StringField('رقم جوال إضافي', validators=[Length(max=20)])
    email = StringField('الإيميل', validators=[Email(), Optional()])
    address = TextAreaField('عنوان السكن')
    emergency_phone = StringField('رقم جوال للطوارئ', validators=[Length(max=20)])
    
    # بيانات العقد
    salary = FloatField('الراتب', validators=[DataRequired(), NumberRange(min=0)])
    contract_signing_date = DateField('تاريخ توقيع العقد', validators=[DataRequired()])
    contract_end_date = DateField('تاريخ انتهاء العقد', validators=[DataRequired()])
    start_work_date = DateField('تاريخ المباشرة', validators=[Optional()])
    contract_duration = StringField('مدة العقد', validators=[DataRequired(), Length(max=50)])
    
    # بنود العقد
    job_title = StringField('المسمى الوظيفي', validators=[DataRequired(), Length(max=100)])
    contract_type = StringField('نوع العقد', validators=[DataRequired(), Length(max=50)])
    probation_period = StringField('فترة التجربة', validators=[Length(max=50)])
    working_hours = IntegerField('عدد ساعات العمل', validators=[Optional()])
    uniform_provision = StringField('بند استلام البدلة', validators=[DataRequired(), Length(max=50)])
    operating_company = StringField('اسم الشركة المشغلة', validators=[DataRequired(), Length(max=100)])
    notes = TextAreaField('ملاحظات')
    penalty_clause = TextAreaField('الشرط الجزائي')
    internet_provision = StringField('بند توفير انترنت', validators=[DataRequired(), Length(max=50)])
    
    # بيانات العمل
    department = StringField('القسم', validators=[DataRequired(), Length(max=50)])
    center = StringField('المركز', validators=[Length(max=100)])
    square = StringField('المربع', validators=[Length(max=100)])
    camp_number = StringField('رقم المخيم', validators=[Length(max=50)])
    work_shift = StringField('فترة العمل', validators=[Length(max=50)])
    
    # بيانات البنك
    bank_type = StringField('نوع البنك', validators=[Length(max=100)])
    iban_number = StringField('رقم الآيبان', validators=[Length(max=50)])
    iban_certificate = FileField('شهادة الآيبان', validators=[FileAllowed(['pdf', 'jpg', 'png', 'jpeg'], 'ملفات PDF أو صور فقط!')])
    additional_bank = StringField('بنك إضافي', validators=[Length(max=100)])
    additional_iban = StringField('رقم الآيبان الإضافي', validators=[Length(max=50)])
    beneficiary_name = StringField('اسم المستفيد', validators=[Length(max=100)])
    beneficiary_phone = StringField('رقم جوال المستفيد', validators=[Length(max=20)])
    
    # حقول النظام القديمة للتوافق
    employee_type = SelectField('نوع الموظف', 
                               choices=[
                                   ('الإدارة', 'الإدارة'),
                                   ('الإداريات', 'الإداريات'),
                                   ('الحراسات الأمنية', 'الحراسات الأمنية'),
                                   ('الحارسات', 'الحارسات'),
                                   ('العمالة رجال', 'العمالة رجال'),
                                   ('العاملات', 'العاملات'),
                                   ('مرشدي الحافلات', 'مرشدي الحافلات')
                               ],
                               validators=[DataRequired()])
    hire_date = DateField('تاريخ التوظيف', validators=[DataRequired()], default=date.today)
    emergency_contact = StringField('جهة الاتصال في الطوارئ', validators=[Length(max=100)])
    # emergency_phone = StringField('هاتف الطوارئ', validators=[Length(max=20)])  # مكرر - احذفه

class AttendanceForm(FlaskForm):
    employee_id = SelectField('الموظف', coerce=int, validators=[DataRequired()])
    date = DateField('التاريخ', validators=[DataRequired()], default=date.today)
    check_in = TimeField('وقت الدخول', validators=[Optional()])
    check_out = TimeField('وقت الخروج', validators=[Optional()])
    break_start = TimeField('بداية الاستراحة', validators=[Optional()])
    break_end = TimeField('نهاية الاستراحة', validators=[Optional()])
    status = SelectField('الحالة',
                        choices=[
                            ('present', 'حاضر'),
                            ('absent', 'غائب'),
                            ('late', 'متأخر'),
                            ('half_day', 'نصف يوم')
                        ],
                        validators=[DataRequired()])
    notes = TextAreaField('ملاحظات')

class PayrollForm(FlaskForm):
    employee_id = SelectField('الموظف', coerce=int, validators=[DataRequired()])
    month = SelectField('الشهر',
                       choices=[(i, f'الشهر {i}') for i in range(1, 13)],
                       coerce=int,
                       validators=[DataRequired()])
    year = IntegerField('السنة', validators=[DataRequired()], default=date.today().year)
    
    # الفترة
    period_from = DateField('من الفترة', validators=[DataRequired()])
    period_to = DateField('إلى الفترة', validators=[DataRequired()])
    period_days = IntegerField('مدة أيام الفترة', validators=[DataRequired(), NumberRange(min=1)])
    
    # الحضور والغياب والانسحاب
    present_days = IntegerField('عدد أيام الحضور', validators=[NumberRange(min=0)], default=0)
    absent_days = IntegerField('عدد أيام الغياب', validators=[NumberRange(min=0)], default=0)
    withdrawal_days = IntegerField('عدد أيام الانسحاب', validators=[NumberRange(min=0)], default=0)
    
    # الراتب والعمل الإضافي
    basic_salary = FloatField('الراتب الأساسي', validators=[DataRequired(), NumberRange(min=0)])
    overtime_days = FloatField('عدد أيام العمل الإضافي', validators=[NumberRange(min=0)], default=0)
    overtime_rate = FloatField('معدل العمل الإضافي', validators=[NumberRange(min=1)], default=1.5)
    
    # البدلات
    housing_allowance = FloatField('بدل السكن', validators=[NumberRange(min=0)], default=0)
    transport_allowance = FloatField('بدل المواصلات', validators=[NumberRange(min=0)], default=0)
    other_allowances = FloatField('بدلات أخرى', validators=[NumberRange(min=0)], default=0)
    
    # المخالفات والحسميات
    advance_deduction = FloatField('حسم السلف', validators=[NumberRange(min=0)], default=0)
    violation_deduction = FloatField('حسم المخالفات', validators=[NumberRange(min=0)], default=0)
    
    # خصومات أخرى
    insurance_deduction = FloatField('خصم التأمين', validators=[NumberRange(min=0)], default=0)
    tax_deduction = FloatField('خصم الضريبة', validators=[NumberRange(min=0)], default=0)
    other_deductions = FloatField('خصومات أخرى', validators=[NumberRange(min=0)], default=0)
    
    # ملاحظات
    notes = TextAreaField('ملاحظات')
    
    # الحقول المحسوبة (للعرض فقط)
    regular_hours = FloatField('ساعات العمل العادية', validators=[NumberRange(min=0)], default=160)
    overtime_hours = FloatField('ساعات العمل الإضافية', validators=[NumberRange(min=0)], default=0)
    overtime_rate = FloatField('معدل العمل الإضافي', validators=[NumberRange(min=1)], default=1.5)

class AssetForm(FlaskForm):
    asset_id = StringField('رقم العهدة', validators=[
        DataRequired(message='رقم العهدة مطلوب'), 
        Length(min=3, max=20, message='رقم العهدة يجب أن يكون بين 3 و 20 حرف')
    ])
    name = StringField('اسم العهدة', validators=[
        DataRequired(message='اسم العهدة مطلوب'), 
        Length(min=2, max=100, message='اسم العهدة يجب أن يكون بين 2 و 100 حرف')
    ])
    description = TextAreaField('الوصف')
    category = StringField('الفئة', validators=[
        DataRequired(message='الفئة مطلوبة'), 
        Length(max=50, message='الفئة لا يجب أن تتجاوز 50 حرف')
    ])
    value = FloatField('القيمة', validators=[
        Optional(),
        NumberRange(min=0, message='القيمة لا يمكن أن تكون سالبة')
    ])
    
    employee_id = SelectField('الموظف المخصص له', validators=[Optional()])
    assigned_date = DateField('تاريخ التخصيص', validators=[Optional()])
    condition = SelectField('الحالة',
                           choices=[
                               ('good', 'جيدة'),
                               ('fair', 'مقبولة'),
                               ('poor', 'سيئة'),
                               ('damaged', 'تالفة')
                           ],
                           validators=[DataRequired(message='حالة العهدة مطلوبة')])
    notes = TextAreaField('ملاحظات')
    
    def validate_asset_id(self, field):
        """التحقق من عدم تكرار رقم العهدة"""
        from models import Asset
        if field.data:
            asset = Asset.query.filter_by(asset_id=field.data.strip()).first()
            if asset:
                raise ValidationError('رقم العهدة موجود مسبقاً! يرجى استخدام رقم آخر.')
    
    def validate_assigned_date(self, field):
        """التحقق من صحة تاريخ التخصيص"""
        if field.data and field.data > date.today():
            raise ValidationError('تاريخ التخصيص لا يمكن أن يكون في المستقبل!')

class JobApplicationForm(FlaskForm):
    first_name = StringField('الاسم الأول', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('اسم العائلة', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    phone = StringField('رقم الهاتف', validators=[DataRequired(), Length(max=20)])
    position_applied = StringField('المنصب المطلوب', validators=[DataRequired(), Length(max=50)])
    
    education = StringField('المؤهل التعليمي', validators=[Length(max=100)])
    experience_years = IntegerField('سنوات الخبرة', validators=[NumberRange(min=0)])
    skills = TextAreaField('المهارات')
    cover_letter = TextAreaField('خطاب التقديم')
    
    def validate_national_id(self, field):
        """التحقق من عدم تكرار رقم الهوية"""
        # تأجيل الاستيراد لتجنب المشكلة الدائرية
        try:
            from models import Employee
            # في حالة التعديل، نتجاهل الموظف الحالي
            query = Employee.query.filter_by(national_id=field.data)
            if hasattr(self, '_obj') and self._obj:
                query = query.filter(Employee.id != self._obj.id)
            existing = query.first()
            if existing:
                raise ValidationError('رقم الهوية موجود مسبقاً في النظام')
        except ImportError:
            # في حالة فشل الاستيراد، تجاهل التحقق
            pass
    
    def validate_contract_end_date(self, field):
        """التحقق من صحة تاريخ انتهاء العقد"""
        if field.data and self.contract_signing_date.data:
            if field.data <= self.contract_signing_date.data:
                raise ValidationError('تاريخ انتهاء العقد يجب أن يكون بعد تاريخ توقيع العقد')
    
    def validate_id_expiry_date(self, field):
        """التحقق من صحة تاريخ انتهاء الهوية"""
        if field.data and field.data <= date.today():
            raise ValidationError('تاريخ انتهاء الهوية يجب أن يكون في المستقبل')
    
    def validate_license_expiry_date(self, field):
        """التحقق من تاريخ انتهاء رخصة القيادة"""
        if self.has_driving_license.data and not field.data:
            raise ValidationError('يجب إدخال تاريخ انتهاء رخصة القيادة')
        if field.data and field.data <= date.today():
            raise ValidationError('تاريخ انتهاء رخصة القيادة يجب أن يكون في المستقبل')

class UserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = StringField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    role = SelectField('الدور', 
                      choices=[
                          ('admin', 'مدير النظام'),
                          ('manager', 'مدير'),
                          ('hr', 'موارد بشرية'),
                          ('employee', 'موظف'),
                          ('user', 'مستخدم عادي')
                      ],
                      validators=[DataRequired()])
    
    def validate_username(self, field):
        from models import User
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('اسم المستخدم موجود بالفعل')
    
    def validate_email(self, field):
        from models import User
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('البريد الإلكتروني موجود بالفعل')

class EditUserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = StringField('كلمة المرور الجديدة (اتركها فارغة للاحتفاظ بالحالية)', validators=[Optional(), Length(min=6)])
    role = SelectField('الدور', 
                      choices=[
                          ('admin', 'مدير النظام'),
                          ('manager', 'مدير'),
                          ('hr', 'موارد بشرية'),
                          ('employee', 'موظف'),
                          ('user', 'مستخدم عادي')
                      ],
                      validators=[DataRequired()])
    
    def __init__(self, original_user, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_user = original_user
    
    def validate_username(self, field):
        from models import User
        if field.data != self.original_user.username:
            if User.query.filter_by(username=field.data).first():
                raise ValidationError('اسم المستخدم موجود بالفعل')
    
    def validate_email(self, field):
        from models import User
        if field.data != self.original_user.email:
            if User.query.filter_by(email=field.data).first():
                raise ValidationError('البريد الإلكتروني موجود بالفعل')

class DocumentForm(FlaskForm):
    document_name = StringField('اسم المستند', validators=[DataRequired(), Length(min=2, max=200)])
    document_file = FileField('ملف PDF', validators=[
        DataRequired('يرجى اختيار ملف'),
        FileAllowed(['pdf'], 'ملفات PDF فقط!')
    ])
    
    department = SelectField('القسم', validators=[DataRequired()], choices=[
        ('', 'اختر القسم'),
        ('الإدارة', 'الإدارة'),
        ('الموارد البشرية', 'الموارد البشرية'),
        ('المالية', 'المالية'),
        ('تقنية المعلومات', 'تقنية المعلومات'),
        ('العمليات', 'العمليات'),
        ('الأمن', 'الأمن'),
        ('الصيانة', 'الصيانة'),
        ('أخرى', 'أخرى')
    ])
    
    category = SelectField('فئة المستند', validators=[DataRequired()], choices=[
        ('', 'اختر الفئة'),
        ('عقود العمل', 'عقود العمل'),
        ('الهويات والوثائق', 'الهويات والوثائق'),
        ('الشهادات والمؤهلات', 'الشهادات والمؤهلات'),
        ('التقارير الطبية', 'التقارير الطبية'),
        ('المراسلات الرسمية', 'المراسلات الرسمية'),
        ('السياسات والإجراءات', 'السياسات والإجراءات'),
        ('التقارير المالية', 'التقارير المالية'),
        ('تقارير الأداء', 'تقارير الأداء'),
        ('أخرى', 'أخرى')
    ])
    
    employee_id = SelectField('الموظف المرتبط (اختياري)', validators=[Optional()])
    description = TextAreaField('وصف المستند', validators=[Length(max=500)])
    is_confidential = BooleanField('مستند سري')

class DocumentSearchForm(FlaskForm):
    search_name = StringField('اسم المستند')
    search_employee_name = StringField('اسم الموظف')
    search_employee_number = StringField('الرقم الوظيفي')
    search_department = SelectField('القسم', choices=[
        ('', 'جميع الأقسام'),
        ('الإدارة', 'الإدارة'),
        ('الموارد البشرية', 'الموارد البشرية'),
        ('المالية', 'المالية'),
        ('تقنية المعلومات', 'تقنية المعلومات'),
        ('العمليات', 'العمليات'),
        ('الأمن', 'الأمن'),
        ('الصيانة', 'الصيانة'),
        ('أخرى', 'أخرى')
    ])
    search_category = SelectField('فئة المستند', choices=[
        ('', 'جميع الفئات'),
        ('عقود العمل', 'عقود العمل'),
        ('الهويات والوثائق', 'الهويات والوثائق'),
        ('الشهادات والمؤهلات', 'الشهادات والمؤهلات'),
        ('التقارير الطبية', 'التقارير الطبية'),
        ('المراسلات الرسمية', 'المراسلات الرسمية'),
        ('السياسات والإجراءات', 'السياسات والإجراءات'),
        ('التقارير المالية', 'التقارير المالية'),
        ('تقارير الأداء', 'تقارير الأداء'),
        ('أخرى', 'أخرى')
    ])
    date_from = DateField('من تاريخ')
    date_to = DateField('إلى تاريخ')

class SettingsForm(FlaskForm):
    # معلومات الشركة
    company_name = StringField('اسم الشركة', validators=[DataRequired()])
    app_name = StringField('اسم النظام', validators=[DataRequired()])
    commercial_register = StringField('رقم السجل التجاري')
    tax_number = StringField('الرقم الضريبي')
    company_address = TextAreaField('عنوان الشركة')
    
    # إعدادات الرواتب
    currency = StringField('العملة', validators=[DataRequired()])
    currency_symbol = StringField('رمز العملة', validators=[DataRequired()])
    monthly_hours = IntegerField('ساعات العمل الشهرية', validators=[DataRequired(), NumberRange(min=1)])
    default_overtime_rate = FloatField('معدل العمل الإضافي الافتراضي', validators=[DataRequired(), NumberRange(min=0)])
    
    # إعدادات النظام
    session_lifetime = IntegerField('مدة الجلسة (بالساعات)', validators=[DataRequired(), NumberRange(min=1)])
    max_file_size = IntegerField('الحد الأقصى لحجم الملف (MB)', validators=[DataRequired(), NumberRange(min=1)])
    default_language = SelectField('اللغة الافتراضية', choices=[('ar', 'العربية'), ('en', 'English')])
    timezone = SelectField('المنطقة الزمنية', choices=[('Asia/Riyadh', 'الرياض (GMT+3)'), ('Asia/Dubai', 'دبي (GMT+4)')])
    
    # إعدادات الأمان
    require_strong_password = BooleanField('طلب كلمة مرور قوية')
    enable_login_attempts = BooleanField('تحديد محاولات تسجيل الدخول')
    max_login_attempts = IntegerField('عدد محاولات تسجيل الدخول المسموحة', validators=[NumberRange(min=1)])
    lockout_duration = IntegerField('مدة الحظر (بالدقائق)', validators=[NumberRange(min=1)])
    
    # إعدادات النسخ الاحتياطي
    auto_backup = BooleanField('النسخ الاحتياطي التلقائي')
    backup_frequency = SelectField('تكرار النسخ الاحتياطي', choices=[('daily', 'يومي'), ('weekly', 'أسبوعي'), ('monthly', 'شهري')])
    
    submit = SubmitField('حفظ الإعدادات')

class SendNotificationForm(FlaskForm):
    """نموذج إرسال الإشعارات"""
    recipient_type = SelectField('نوع المستلم', 
                                choices=[
                                    ('single', 'مستخدم واحد'),
                                    ('role', 'حسب الدور'),
                                    ('all', 'جميع المستخدمين')
                                ], 
                                validators=[DataRequired()])
    
    recipient_user = SelectField('المستخدم', coerce=int, validators=[Optional()])
    recipient_role = SelectField('الدور', 
                                choices=[
                                    ('user', 'مستخدم عادي'),
                                    ('hr', 'موارد بشرية'),
                                    ('manager', 'مدير'),
                                    ('admin', 'مدير النظام')
                                ], 
                                validators=[Optional()])
    
    title = StringField('عنوان الإشعار', 
                       validators=[DataRequired(), Length(min=3, max=200)])
    
    message = TextAreaField('نص الإشعار', 
                           validators=[DataRequired(), Length(min=10, max=1000)])
    
    notification_type = SelectField('نوع الإشعار',
                                   choices=[
                                       ('info', 'معلومات'),
                                       ('warning', 'تحذير'),
                                       ('success', 'نجاح'),
                                       ('error', 'خطأ')
                                   ],
                                   validators=[DataRequired()])
    
    priority = SelectField('الأولوية',
                          choices=[
                              ('low', 'منخفضة'),
                              ('normal', 'عادية'),
                              ('high', 'عالية'),
                              ('urgent', 'عاجلة')
                          ],
                          validators=[DataRequired()])
    
    action_url = StringField('رابط الإجراء (اختياري)', validators=[Optional()])
    action_text = StringField('نص الإجراء (اختياري)', validators=[Optional()])
    
    expires_at = DateField('تاريخ انتهاء الصلاحية (اختياري)', validators=[Optional()])
    
    submit = SubmitField('إرسال الإشعار')