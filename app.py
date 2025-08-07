from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
# تغيير طريقة الاستيراد لتجنب الاستيراد الدائري
# from google_drive_backup import backup_manager, setup_backup_schedule
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, User, Employee, Attendance, Payroll, Asset, JobApplication, Document, Settings, Notification, NotificationSettings
from forms import EmployeeForm, AttendanceForm, PayrollForm, AssetForm, JobApplicationForm, UserForm, EditUserForm, DocumentForm, DocumentSearchForm, SettingsForm, SendNotificationForm
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from functools import wraps
from flask import abort
import pandas as pd
import io
import re
from flask_talisman import Talisman
from flask_cors import CORS

def _safe_salary_conversion(value):
    """تحويل آمن للراتب مع معالجة جميع الحالات الممكنة"""
    if pd.isna(value) or str(value).strip().lower() in ['', 'nan', 'none', 'null']:
        return 3000.0  # راتب افتراضي
    
    try:
        # إزالة الفواصل والرموز
        clean_value = str(value).replace(',', '').replace('ر.س', '').replace('ريال', '').strip()
        
        # محاولة التحويل إلى رقم
        salary = float(clean_value)
        
        # التحقق من أن الراتب في نطاق معقول
        if salary < 0:
            return 3000.0
        elif salary > 1000000:  # حد أقصى مليون
            return 50000.0
        
        return salary
        
    except (ValueError, TypeError):
        return 3000.0  # راتب افتراضي في حالة الخطأ

app = Flask(__name__)
app.config.from_object(Config)

# إضافة CSRF Protection
csrf = CSRFProtect(app)

# إعدادات الأمان
Talisman(app, force_https=True)

# إعدادات CORS إذا لزم الأمر
CORS(app, origins=['https://yourdomain.com'])

# إعدادات إضافية للأمان
@app.before_request
def force_https():
    if not request.is_secure and app.env != 'development':
        return redirect(request.url.replace('http://', 'https://'))

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# إعدادات رفع الملفات
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# تهيئة قاعدة البيانات
db.init_app(app)

# تهيئة نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'

# إضافة معالج خطأ حجم الملف
@app.errorhandler(413)
def too_large(e):
    flash('حجم الملف كبير جداً. الحد الأقصى المسموح هو 10 ميجابايت.', 'error')
    return redirect(request.url)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None

# نظام الصلاحيات - يجب تعريفه قبل استخدامه
def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in allowed_roles:
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# تعريف جميع الوحدات والحقول في النظام
SYSTEM_MODULES = {
    'employees': {
        'name': 'إدارة الموظفين',
        'icon': 'fas fa-users',
        'fields': {
            'basic_info': {
                'name': 'البيانات الأساسية',
                'fields': ['employee_photo', 'name_arabic', 'name_english', 'national_id', 'birth_date', 'nationality', 'gender']
            },
            'contact_info': {
                'name': 'بيانات التواصل',
                'fields': ['phone', 'additional_phone', 'email', 'address', 'emergency_phone']
            },
            'contract_info': {
                'name': 'بيانات العقد',
                'fields': ['salary', 'contract_signing_date', 'contract_end_date', 'job_title', 'contract_type']
            },
            'work_info': {
                'name': 'بيانات العمل',
                'fields': ['department', 'center', 'square', 'camp_number', 'work_shift', 'employee_type']
            },
            'bank_info': {
                'name': 'البيانات البنكية',
                'fields': ['bank_type', 'iban_number', 'additional_bank', 'beneficiary_name']
            }
        }
    },
    'documents': {
        'name': 'إدارة المستندات',
        'icon': 'fas fa-file-pdf',
        'fields': {
            'document_info': {
                'name': 'معلومات المستند',
                'fields': ['document_name', 'document_file', 'department', 'category', 'description']
            },
            'employee_link': {
                'name': 'ربط الموظف',
                'fields': ['employee_id', 'employee_name', 'employee_number']
            },
            'security': {
                'name': 'الأمان',
                'fields': ['is_confidential', 'status']
            }
        }
    },
    'attendance': {
        'name': 'الحضور والغياب',
        'icon': 'fas fa-clock',
        'fields': {
            'time_tracking': {
                'name': 'تتبع الوقت',
                'fields': ['check_in', 'check_out', 'break_start', 'break_end']
            },
            'status_info': {
                'name': 'معلومات الحالة',
                'fields': ['status', 'notes', 'date']
            }
        }
    },
    'payroll': {
        'name': 'كشوف الرواتب',
        'icon': 'fas fa-money-bill-wave',
        'fields': {
            'salary_components': {
                'name': 'مكونات الراتب',
                'fields': ['basic_salary', 'housing_allowance', 'transport_allowance', 'other_allowances']
            },
            'deductions': {
                'name': 'الخصومات',
                'fields': ['insurance_deduction', 'tax_deduction', 'other_deductions']
            },
            'working_hours': {
                'name': 'ساعات العمل',
                'fields': ['regular_hours', 'overtime_hours', 'overtime_rate']
            }
        }
    },
    'assets': {
        'name': 'إدارة الأصول',
        'icon': 'fas fa-laptop',
        'fields': {
            'asset_info': {
                'name': 'معلومات الأصل',
                'fields': ['asset_id', 'name', 'description', 'category', 'value']
            },
            'assignment_info': {
                'name': 'معلومات التخصيص',
                'fields': ['employee_id', 'assigned_date', 'return_date', 'condition', 'status']
            }
        }
    },
    'recruitment': {
        'name': 'التوظيف',
        'icon': 'fas fa-user-plus',
        'fields': {
            'applicant_info': {
                'name': 'معلومات المتقدم',
                'fields': ['first_name', 'last_name', 'email', 'phone', 'position_applied']
            },
            'qualifications': {
                'name': 'المؤهلات',
                'fields': ['education', 'experience_years', 'skills', 'cover_letter']
            }
        }
    },
    'users': {
        'name': 'إدارة المستخدمين',
        'icon': 'fas fa-user-cog',
        'fields': {
            'user_info': {
                'name': 'معلومات المستخدم',
                'fields': ['username', 'email', 'role', 'created_at']
            }
        }
    }
}

# تعريف الصلاحيات التفصيلية لكل دور
ROLE_PERMISSIONS = {
    'admin': {
        'name': 'مدير النظام',
        'modules': {
            'employees': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'attendance': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'payroll': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'assets': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'recruitment': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'documents': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'users': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'}
        }
    },
    'manager': {
        'name': 'مدير',
        'modules': {
            'employees': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': ['basic_info', 'contact_info', 'work_info']},
            'attendance': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'payroll': {'view': True, 'add': True, 'edit': True, 'delete': False, 'fields': ['salary_components', 'working_hours']},
            'assets': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'recruitment': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'documents': {'view': True, 'add': True, 'edit': True, 'delete': True, 'fields': 'all'},
            'users': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []}
        }
    },
    'hr': {
        'name': 'موارد بشرية',
        'modules': {
            'employees': {'view': True, 'add': True, 'edit': True, 'delete': False, 'fields': ['basic_info', 'contact_info', 'contract_info', 'work_info']},
            'attendance': {'view': True, 'add': True, 'edit': True, 'delete': False, 'fields': 'all'},
            'payroll': {'view': True, 'add': False, 'edit': False, 'delete': False, 'fields': ['salary_components']},
            'assets': {'view': True, 'add': True, 'edit': True, 'delete': False, 'fields': 'all'},
            'recruitment': {'view': True, 'add': True, 'edit': True, 'delete': False, 'fields': 'all'},
            'documents': {'view': True, 'add': True, 'edit': False, 'delete': False, 'fields': 'all'},
            'users': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []}
        }
    },
    'employee': {
        'name': 'موظف',
        'modules': {
            'employees': {'view': True, 'add': False, 'edit': False, 'delete': False, 'fields': ['basic_info', 'contact_info']},
            'attendance': {'view': True, 'add': False, 'edit': False, 'delete': False, 'fields': ['time_tracking', 'status_info']},
            'payroll': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'assets': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'recruitment': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'documents': {'view': True, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'users': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []}
        }
    },
    'user': {
        'name': 'مستخدم عادي',
        'modules': {
            'employees': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'attendance': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'payroll': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'assets': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'recruitment': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'documents': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []},
            'users': {'view': False, 'add': False, 'edit': False, 'delete': False, 'fields': []}
        }
    }
}

# دوال الصلاحيات المحدثة
def can_view(resource_type):
    if not current_user.is_authenticated:
        return False
    return ROLE_PERMISSIONS.get(current_user.role, {}).get('modules', {}).get(resource_type, {}).get('view', False)

def can_edit(resource_type):
    if not current_user.is_authenticated:
        return False
    return ROLE_PERMISSIONS.get(current_user.role, {}).get('modules', {}).get(resource_type, {}).get('edit', False)

def can_delete(resource_type):
    if not current_user.is_authenticated:
        return False
    return ROLE_PERMISSIONS.get(current_user.role, {}).get('modules', {}).get(resource_type, {}).get('delete', False)

def can_add(resource_type):
    if not current_user.is_authenticated:
        return False
    return ROLE_PERMISSIONS.get(current_user.role, {}).get('modules', {}).get(resource_type, {}).get('add', False)

def get_accessible_fields(resource_type):
    if not current_user.is_authenticated:
        return []
    
    user_permissions = ROLE_PERMISSIONS.get(current_user.role, {}).get('modules', {}).get(resource_type, {})
    allowed_fields = user_permissions.get('fields', [])
    
    if allowed_fields == 'all':
        return list(SYSTEM_MODULES.get(resource_type, {}).get('fields', {}).keys())
    
    return allowed_fields

# إتاحة الدوال والبيانات في القوالب
@app.context_processor
def inject_permissions():
    return dict(
        can_view=can_view,
        can_edit=can_edit,
        can_delete=can_delete,
        can_add=can_add,
        get_accessible_fields=get_accessible_fields,
        SYSTEM_MODULES=SYSTEM_MODULES,
        ROLE_PERMISSIONS=ROLE_PERMISSIONS
    )

# وظائف مساعدة للإشعارات
def create_system_notification(user_id, title, message, notification_type='info', priority='normal'):
    """إنشاء إشعار نظام"""
    return Notification.create_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        source_type='system'
    )

def create_employee_notification(user_id, employee_id, title, message, action_url=None):
    """إنشاء إشعار متعلق بالموظفين"""
    return Notification.create_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type='info',
        action_url=action_url,
        source_type='employee',
        source_id=employee_id
    )

def create_attendance_notification(user_id, attendance_id, title, message, priority='normal'):
    """إنشاء إشعار متعلق بالحضور"""
    return Notification.create_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type='warning',
        priority=priority,
        source_type='attendance',
        source_id=attendance_id
    )

def notify_all_admins(title, message, notification_type='info', priority='normal'):
    """إرسال إشعار لجميع المديرين"""
    admins = User.query.filter(User.role.in_(['admin', 'manager'])).all()
    for admin in admins:
        create_system_notification(admin.id, title, message, notification_type, priority)

def notify_hr_staff(title, message, notification_type='info', priority='normal'):
    """إرسال إشعار لموظفي الموارد البشرية"""
    hr_users = User.query.filter(User.role.in_(['admin', 'manager', 'hr'])).all()
    for user in hr_users:
        create_system_notification(user.id, title, message, notification_type, priority)

# إضافة context processor للإشعارات
@app.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        try:
            unread_count = Notification.query.filter_by(
                user_id=current_user.id, 
                is_read=False, 
                is_dismissed=False
            ).filter(
                db.or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.utcnow()
                )
            ).count()
            
            recent_notifications = Notification.get_user_notifications(
                current_user.id, 
                unread_only=False, 
                limit=5
            )
            
            return {
                'unread_notifications_count': unread_count,
                'recent_notifications': recent_notifications
            }
        except Exception as e:
            # في حالة عدم وجود جدول الإشعارات أو أي خطأ آخر
            print(f"خطأ في جلب الإشعارات: {e}")
            return {
                'unread_notifications_count': 0,
                'recent_notifications': []
            }
    return {}

# إنشاء الجداول
with app.app_context():
    db.create_all()
    
    # التحقق من وجود مستخدم مدير
    admin_exists = User.query.filter_by(role='admin').first()
    if not admin_exists:
        admin_user = User(
            username='admin',
            email='admin@raizo.com',
            role='admin'
        )
        admin_user.set_password('admin123')
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print('تم إنشاء مستخدم المدير الافتراضي')
        except Exception as e:
            db.session.rollback()
            print(f'خطأ في إنشاء المستخدم الافتراضي: {e}')

# الصفحة الرئيسية
@app.route('/')
@login_required
def index():
    # إحصائيات الموظفين
    stats = {
        'الإدارة': Employee.query.filter_by(employee_type='الإدارة', status='active').count(),
        'الإداريات': Employee.query.filter_by(employee_type='الإداريات', status='active').count(),
        'الحراسات الأمنية': Employee.query.filter_by(employee_type='الحراسات الأمنية', status='active').count(),
        'الحارسات': Employee.query.filter_by(employee_type='الحارسات', status='active').count(),
        'العمالة رجال': Employee.query.filter_by(employee_type='العمالة رجال', status='active').count(),
        'العاملات': Employee.query.filter_by(employee_type='العاملات', status='active').count(),
        'مرشدي الحافلات': Employee.query.filter_by(employee_type='مرشدي الحافلات', status='active').count()
    }
    
    total_employees = sum(stats.values())
    
    # إحصائيات إضافية
    today = date.today()
    present_today = Attendance.query.filter_by(date=today, status='present').count()
    absent_today = Attendance.query.filter_by(date=today, status='absent').count()
    
    pending_applications = JobApplication.query.filter_by(status='pending').count()
    
    return render_template('index.html', 
                         stats=stats, 
                         total_employees=total_employees,
                         present_today=present_today,
                         absent_today=absent_today,
                         pending_applications=pending_applications)

# لوحة التحكم
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# قسم الموظفين
# استبدال route الموظفين الحالي (حوالي السطر 87)
@app.route('/employees')
@login_required
@role_required('admin', 'manager', 'hr', 'employee')
def employees():
    page = request.args.get('page', 1, type=int)
    
    # الحصول على معاملات البحث
    search_name = request.args.get('search_name', '').strip()
    search_national_id = request.args.get('search_national_id', '').strip()
    search_employee_id = request.args.get('search_employee_id', '').strip()
    search_department = request.args.get('search_department', '').strip()
    search_job_title = request.args.get('search_job_title', '').strip()
    search_phone = request.args.get('search_phone', '').strip()
    search_email = request.args.get('search_email', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    search_gender = request.args.get('search_gender', '').strip()
    search_nationality = request.args.get('search_nationality', '').strip()
    search_contract_type = request.args.get('search_contract_type', '').strip()
    search_employee_type = request.args.get('search_employee_type', '').strip()
    
    # بناء الاستعلام الأساسي
    query = Employee.query.filter_by(status='active')
    
    # تطبيق الفلاتر
    if search_name:
        query = query.filter(
            db.or_(
                Employee.name_arabic.contains(search_name),
                Employee.name_english.contains(search_name)
            )
        )
    
    if search_national_id:
        query = query.filter(Employee.national_id.contains(search_national_id))
    
    if search_employee_id:
        query = query.filter(Employee.id == search_employee_id)
    
    if search_department:
        query = query.filter(Employee.department.contains(search_department))
    
    if search_job_title:
        query = query.filter(Employee.job_title.contains(search_job_title))
    
    if search_phone:
        query = query.filter(
            db.or_(
                Employee.phone.contains(search_phone),
                Employee.additional_phone.contains(search_phone)
            )
        )
    
    if search_email:
        query = query.filter(Employee.email.contains(search_email))
    
    if search_gender:
        query = query.filter(Employee.gender == search_gender)
    
    if search_nationality:
        query = query.filter(Employee.nationality.contains(search_nationality))
    
    if search_contract_type:
        query = query.filter(Employee.contract_type == search_contract_type)
    
    if search_employee_type:
        query = query.filter(Employee.employee_type == search_employee_type)
    
    # فلترة التاريخ
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Employee.contract_signing_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Employee.contract_signing_date <= date_to_obj)
        except ValueError:
            pass
    
    # ترتيب النتائج وتقسيمها إلى صفحات
    employees = query.order_by(Employee.id.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # الحصول على القيم الفريدة للفلاتر
    departments = db.session.query(Employee.department).filter(
        Employee.department.isnot(None), 
        Employee.department != '',
        Employee.status == 'active'
    ).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    job_titles = db.session.query(Employee.job_title).filter(
        Employee.job_title.isnot(None), 
        Employee.job_title != '',
        Employee.status == 'active'
    ).distinct().all()
    job_titles = [title[0] for title in job_titles if title[0]]
    
    nationalities = db.session.query(Employee.nationality).filter(
        Employee.nationality.isnot(None), 
        Employee.nationality != '',
        Employee.status == 'active'
    ).distinct().all()
    nationalities = [nat[0] for nat in nationalities if nat[0]]
    
    return render_template('employees/list.html', 
                         employees=employees,
                         departments=departments,
                         job_titles=job_titles,
                         nationalities=nationalities,
                         # تمرير قيم البحث الحالية
                         search_name=search_name,
                         search_national_id=search_national_id,
                         search_employee_id=search_employee_id,
                         search_department=search_department,
                         search_job_title=search_job_title,
                         search_phone=search_phone,
                         search_email=search_email,
                         date_from=date_from,
                         date_to=date_to,
                         search_gender=search_gender,
                         search_nationality=search_nationality,
                         search_contract_type=search_contract_type,
                         search_employee_type=search_employee_type)

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def add_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        try:
            # التحقق من المجلدات المطلوبة
            photos_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'photos')
            docs_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'documents')
            os.makedirs(photos_dir, exist_ok=True)
            os.makedirs(docs_dir, exist_ok=True)
            
            # التحقق من صورة الموظف (مطلوبة)
            if not form.employee_photo.data:
                flash('صورة الموظف مطلوبة', 'error')
                return render_template('employees/add.html', form=form)
            
            # معالجة رفع الملفات
            employee_photo_filename = None
            iban_certificate_filename = None
            
            # رفع صورة الموظف
            try:
                employee_photo_filename = secure_filename(form.employee_photo.data.filename)
                # إضافة timestamp لتجنب تكرار الأسماء
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                employee_photo_filename = timestamp + employee_photo_filename
                photo_path = os.path.join(photos_dir, employee_photo_filename)
                form.employee_photo.data.save(photo_path)
            except Exception as e:
                flash(f'خطأ في رفع صورة الموظف: {str(e)}', 'error')
                return render_template('employees/add.html', form=form)
            
            # رفع شهادة الآيبان (اختيارية)
            if form.iban_certificate.data:
                try:
                    iban_certificate_filename = secure_filename(form.iban_certificate.data.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    iban_certificate_filename = timestamp + iban_certificate_filename
                    doc_path = os.path.join(docs_dir, iban_certificate_filename)
                    form.iban_certificate.data.save(doc_path)
                except Exception as e:
                    flash(f'خطأ في رفع شهادة الآيبان: {str(e)}', 'error')
                    return render_template('employees/add.html', form=form)
            
            # التحقق من عدم تكرار رقم الهوية
            existing_employee = Employee.query.filter_by(national_id=form.national_id.data).first()
            if existing_employee:
                flash('رقم الهوية موجود مسبقاً في النظام', 'error')
                return render_template('employees/add.html', form=form)
            
            # توليد الرقم الوظيفي التلقائي
            auto_employee_id = Employee.generate_employee_id()
            if not auto_employee_id:
                flash('خطأ في توليد الرقم الوظيفي', 'error')
                return render_template('employees/add.html', form=form)
            
            # التحقق من صحة التواريخ
            if form.contract_end_date.data <= form.contract_signing_date.data:
                flash('تاريخ انتهاء العقد يجب أن يكون بعد تاريخ توقيع العقد', 'error')
                return render_template('employees/add.html', form=form)
            
            if form.id_expiry_date.data <= date.today():
                flash('تاريخ انتهاء الهوية يجب أن يكون في المستقبل', 'error')
                return render_template('employees/add.html', form=form)
            
            # التحقق من رخصة القيادة
            if form.has_driving_license.data and not form.license_expiry_date.data:
                flash('يجب إدخال تاريخ انتهاء رخصة القيادة', 'error')
                return render_template('employees/add.html', form=form)
            
            # إنشاء الموظف الجديد
            employee = Employee(
                # بيانات الموظف
                employee_photo=employee_photo_filename,
                employee_id=auto_employee_id,
                name_arabic=form.name_arabic.data,
                name_english=form.name_english.data,
                national_id=form.national_id.data,
                id_validity=form.id_validity.data,
                id_expiry_date=form.id_expiry_date.data,
                birth_date=form.birth_date.data,
                nationality=form.nationality.data,
                birth_place=form.birth_place.data,
                marital_status=form.marital_status.data,
                gender=form.gender.data,
                id_issuer=form.id_issuer.data,
                has_driving_license=form.has_driving_license.data,
                license_expiry_date=form.license_expiry_date.data,
                
                # بيانات التواصل
                phone=form.phone.data,
                additional_phone=form.additional_phone.data,
                email=form.email.data,
                address=form.address.data,
                emergency_phone=form.emergency_phone.data,
                
                # بيانات العقد
                salary=form.salary.data,
                contract_signing_date=form.contract_signing_date.data,
                contract_end_date=form.contract_end_date.data,
                start_work_date=form.start_work_date.data,
                contract_duration=form.contract_duration.data,
                
                # بنود العقد
                job_title=form.job_title.data,
                contract_type=form.contract_type.data,
                probation_period=form.probation_period.data,
                working_hours=form.working_hours.data,
                uniform_provision=form.uniform_provision.data,
                operating_company=form.operating_company.data,
                notes=form.notes.data,
                penalty_clause=form.penalty_clause.data,
                internet_provision=form.internet_provision.data,
                
                # بيانات العمل
                department=form.department.data,
                center=form.center.data,
                square=form.square.data,
                camp_number=form.camp_number.data,
                work_shift=form.work_shift.data,
                
                # بيانات البنك
                bank_type=form.bank_type.data,
                iban_number=form.iban_number.data,
                iban_certificate=iban_certificate_filename,
                additional_bank=form.additional_bank.data,
                additional_iban=form.additional_iban.data,
                beneficiary_name=form.beneficiary_name.data,
                beneficiary_phone=form.beneficiary_phone.data,
                
                # حقول النظام القديمة للتوافق
                first_name=form.name_arabic.data.split()[0] if form.name_arabic.data else '',
                last_name=' '.join(form.name_arabic.data.split()[1:]) if form.name_arabic.data and len(form.name_arabic.data.split()) > 1 else '',
                employee_type=form.employee_type.data,
                hire_date=form.contract_signing_date.data,
                status='active'
            )
            
            # حفظ البيانات
            db.session.add(employee)
            db.session.commit()
            flash(f'تم إضافة الموظف بنجاح! الرقم الوظيفي: {auto_employee_id}', 'success')
            return redirect(url_for('employees'))
            
        except Exception as e:
            db.session.rollback()
            # طباعة تفاصيل الخطأ للتشخيص
            import traceback
            print(f"خطأ في إضافة الموظف: {str(e)}")
            print(traceback.format_exc())
            flash(f'حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')
            return render_template('employees/add.html', form=form)
    
    else:
        # عرض أخطاء التحقق من صحة البيانات
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'خطأ في حقل {field}: {error}', 'error')
    
    return render_template('employees/add.html', form=form)

# قسم الحضور والغياب
@app.route('/attendance')
@login_required
@role_required('admin', 'manager', 'hr', 'employee')
def attendance():
    # إحصائيات الجنس
    male_count = Employee.query.filter_by(gender='ذكر', status='active').count()
    female_count = Employee.query.filter_by(gender='أنثى', status='active').count()
    
    return render_template('attendance/gender_selection.html', 
                         male_count=male_count, 
                         female_count=female_count)

@app.route('/attendance/gender/<gender>')
@login_required
@role_required('admin', 'manager', 'hr', 'employee')
def attendance_by_gender(gender):
    today = date.today()
    
    # الحصول على معاملات البحث
    search = request.args.get('search', '')
    selected_date = request.args.get('date', today.strftime('%Y-%m-%d'))
    department = request.args.get('department', '')
    shift = request.args.get('shift', '')
    status = request.args.get('status', '')
    
    # تحويل التاريخ
    try:
        filter_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except:
        filter_date = today
    
    # بناء الاستعلام
    query = Attendance.query.join(Employee).filter(
        Employee.gender == gender,
        Attendance.date == filter_date
    )
    
    # تطبيق الفلاتر
    if search:
        query = query.filter(
            db.or_(
                Employee.employee_id.contains(search),
                Employee.name_arabic.contains(search),
                Employee.national_id.contains(search),
                Employee.phone.contains(search)
            )
        )
    
    if department:
        query = query.filter(Employee.department == department)
    
    if shift:
        query = query.filter(Employee.work_shift == shift)
    
    if status:
        query = query.filter(Attendance.status == status)
    
    records = query.all()
    
    # الحصول على قوائم الأقسام والورديات
    departments = db.session.query(Employee.department).filter(
        Employee.gender == gender,
        Employee.status == 'active'
    ).distinct().all()
    departments = [d[0] for d in departments if d[0]]
    
    shifts = db.session.query(Employee.work_shift).filter(
        Employee.gender == gender,
        Employee.status == 'active'
    ).distinct().all()
    shifts = [s[0] for s in shifts if s[0]]
    
    return render_template('attendance/list_by_gender.html',
                         records=records,
                         gender=gender,
                         today=filter_date,
                         departments=departments,
                         shifts=shifts)

@app.route('/attendance/add-status')
@login_required
@role_required('admin', 'manager', 'hr')
def add_attendance_status():
    today = date.today()
    
    # الحصول على الموظفين النشطين
    employees = Employee.query.filter_by(status='active').all()
    
    # الحصول على قوائم الأقسام والورديات
    departments = db.session.query(Employee.department).filter(
        Employee.status == 'active'
    ).distinct().all()
    departments = [d[0] for d in departments if d[0]]
    
    shifts = db.session.query(Employee.work_shift).filter(
        Employee.status == 'active'
    ).distinct().all()
    shifts = [s[0] for s in shifts if s[0]]
    
    return render_template('attendance/add_status.html',
                         employees=employees,
                         today=today,
                         departments=departments,
                         shifts=shifts)

@app.route('/attendance/save-status', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def save_attendance_status():
    try:
        # الحصول على البيانات من JSON بدلاً من form
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'لا توجد بيانات للحفظ'})
        
        attendance_data = data.get('attendance_data', {})
        selected_date = data.get('selected_date')
        
        if not attendance_data or not selected_date:
            return jsonify({'success': False, 'message': 'بيانات غير مكتملة'})
        
        attendance_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        saved_count = 0
        
        for employee_id, emp_data in attendance_data.items():
            # التحقق من وجود سجل حضور
            existing_record = Attendance.query.filter_by(
                employee_id=employee_id,
                date=attendance_date
            ).first()
            
            if existing_record:
                # تحديث السجل الموجود
                existing_record.status = emp_data.get('status')
                if emp_data.get('check_in'):
                    existing_record.check_in = datetime.strptime(emp_data.get('check_in'), '%H:%M').time()
                if emp_data.get('check_out'):
                    existing_record.check_out = datetime.strptime(emp_data.get('check_out'), '%H:%M').time()
                existing_record.notes = emp_data.get('notes')
                existing_record.substitute_for_employee_id = emp_data.get('substitute_id')
                existing_record.employee_type = 'substitute' if emp_data.get('substitute_id') else 'primary'
            else:
                # إنشاء سجل جديد
                new_record = Attendance(
                    employee_id=employee_id,
                    date=attendance_date,
                    status=emp_data.get('status'),
                    check_in=datetime.strptime(emp_data.get('check_in'), '%H:%M').time() if emp_data.get('check_in') else None,
                    check_out=datetime.strptime(emp_data.get('check_out'), '%H:%M').time() if emp_data.get('check_out') else None,
                    notes=emp_data.get('notes'),
                    substitute_for_employee_id=emp_data.get('substitute_id'),
                    employee_type='substitute' if emp_data.get('substitute_id') else 'primary'
                )
                db.session.add(new_record)
            
            saved_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'تم حفظ {saved_count} سجل حضور بنجاح!',
            'redirect_url': url_for('attendance')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@app.route('/attendance/export/<gender>')
@login_required
@role_required('admin', 'manager', 'hr')
def export_attendance(gender):
    # يمكن إضافة وظيفة التصدير هنا
    flash('سيتم إضافة وظيفة التصدير قريباً', 'info')
    return redirect(url_for('attendance_by_gender', gender=gender))

@app.route('/attendance/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def add_attendance():
    form = AttendanceForm()
    form.employee_id.choices = [(e.id, f'{e.employee_id} - {e.full_name}') 
                               for e in Employee.query.filter_by(status='active').all()]
    
    if form.validate_on_submit():
        attendance = Attendance(
            employee_id=form.employee_id.data,
            date=form.date.data,
            check_in=form.check_in.data,
            check_out=form.check_out.data,
            break_start=form.break_start.data,
            break_end=form.break_end.data,
            status=form.status.data,
            notes=form.notes.data
        )
        
        try:
            db.session.add(attendance)
            db.session.commit()
            flash('تم إضافة سجل الحضور بنجاح!', 'success')
            return redirect(url_for('attendance'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إضافة سجل الحضور!', 'error')
    
    return render_template('attendance/add.html', form=form)

@app.route('/attendance/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def edit_attendance(id):
    attendance = Attendance.query.get_or_404(id)
    form = AttendanceForm(obj=attendance)
    form.employee_id.choices = [(e.id, f'{e.employee_id} - {e.full_name}') 
                               for e in Employee.query.filter_by(status='active').all()]
    
    if form.validate_on_submit():
        attendance.employee_id = form.employee_id.data
        attendance.date = form.date.data
        attendance.check_in = form.check_in.data
        attendance.check_out = form.check_out.data
        attendance.break_start = form.break_start.data
        attendance.break_end = form.break_end.data
        attendance.status = form.status.data
        attendance.notes = form.notes.data
        
        try:
            db.session.commit()
            flash('تم تحديث سجل الحضور بنجاح!', 'success')
            return redirect(url_for('attendance'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تحديث سجل الحضور!', 'error')
    
    return render_template('attendance/edit.html', form=form, attendance=attendance)

@app.route('/attendance/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_attendance(id):
    if not can_delete('attendance'):
        flash('ليس لديك صلاحية لحذف سجلات الحضور', 'error')
        return redirect(url_for('attendance'))
    
    attendance = Attendance.query.get_or_404(id)
    
    try:
        db.session.delete(attendance)
        db.session.commit()
        flash('تم حذف سجل الحضور بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف سجل الحضور!', 'error')
    
    # العودة إلى الصفحة المناسبة
    if request.referrer and 'gender' in request.referrer:
        # إذا كان المستخدم في صفحة الجنس، العودة إليها
        gender = request.args.get('gender', 'ذكر')
        return redirect(url_for('attendance_by_gender', gender=gender))
    else:
        return redirect(url_for('attendance'))

# قسم الرواتب
@app.route('/payroll')
@login_required
@role_required('admin', 'manager', 'hr')
def payroll():
    current_month = date.today().month
    current_year = date.today().year
    
    payroll_records = Payroll.query.filter_by(
        month=current_month, 
        year=current_year
    ).all()
    
    return render_template('payroll/list.html', 
                         records=payroll_records,
                         current_month=current_month,
                         current_year=current_year)

@app.route('/payroll/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add_payroll():
    form = PayrollForm()
    form.employee_id.choices = [(e.id, e.full_name) for e in Employee.query.filter_by(status='active').all()]
    
    if form.validate_on_submit():
        payroll = Payroll(
            employee_id=form.employee_id.data,
            month=form.month.data,
            year=form.year.data,
            period_from=form.period_from.data,
            period_to=form.period_to.data,
            period_days=form.period_days.data,
            present_days=form.present_days.data,
            absent_days=form.absent_days.data,
            withdrawal_days=form.withdrawal_days.data,
            basic_salary=form.basic_salary.data,
            overtime_days=form.overtime_days.data,
            overtime_rate=form.overtime_rate.data,
            housing_allowance=form.housing_allowance.data,
            transport_allowance=form.transport_allowance.data,
            other_allowances=form.other_allowances.data,
            advance_deduction=form.advance_deduction.data,
            violation_deduction=form.violation_deduction.data,
            insurance_deduction=form.insurance_deduction.data,
            tax_deduction=form.tax_deduction.data,
            other_deductions=form.other_deductions.data,
            notes=form.notes.data
        )
        
        # حساب الراتب التفصيلي
        payroll.calculate_detailed_salary()
        
        db.session.add(payroll)
        db.session.commit()
        
        flash('تم إضافة كشف الراتب بنجاح!', 'success')
        return redirect(url_for('payroll'))
    
    return render_template('payroll/add.html', form=form)

@app.route('/payroll/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit_payroll(id):
    payroll = Payroll.query.get_or_404(id)
    form = PayrollForm(obj=payroll)
    form.employee_id.choices = [(e.id, f'{e.employee_id} - {e.full_name}') 
                               for e in Employee.query.filter_by(status='active').all()]
    
    if form.validate_on_submit():
        payroll.employee_id = form.employee_id.data
        payroll.month = form.month.data
        payroll.year = form.year.data
        payroll.basic_salary = form.basic_salary.data
        payroll.housing_allowance = form.housing_allowance.data
        payroll.transport_allowance = form.transport_allowance.data
        payroll.other_allowances = form.other_allowances.data
        payroll.insurance_deduction = form.insurance_deduction.data
        payroll.tax_deduction = form.tax_deduction.data
        payroll.other_deductions = form.other_deductions.data
        payroll.regular_hours = form.regular_hours.data
        payroll.overtime_hours = form.overtime_hours.data
        payroll.overtime_rate = form.overtime_rate.data
        payroll.status = form.status.data
        
        # حساب الراتب الإجمالي والصافي
        total_allowances = (payroll.housing_allowance or 0) + (payroll.transport_allowance or 0) + (payroll.other_allowances or 0)
        total_deductions = (payroll.insurance_deduction or 0) + (payroll.tax_deduction or 0) + (payroll.other_deductions or 0)
        overtime_pay = (payroll.overtime_hours or 0) * (payroll.overtime_rate or 0)
        
        payroll.gross_salary = payroll.basic_salary + total_allowances + overtime_pay
        payroll.net_salary = payroll.gross_salary - total_deductions
        
        db.session.commit()
        flash('تم تحديث كشف الراتب بنجاح!', 'success')
        return redirect(url_for('payroll'))
    
    return render_template('payroll/edit.html', form=form, payroll=payroll)

@app.route('/payroll/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_payroll(id):
    payroll = Payroll.query.get_or_404(id)
    
    try:
        db.session.delete(payroll)
        db.session.commit()
        flash('تم حذف كشف الراتب بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف كشف الراتب!', 'error')
    
    return redirect(url_for('payroll'))

# قسم العهد
@app.route('/assets')
@login_required
@role_required('admin', 'manager', 'hr')
def assets():
    assets = Asset.query.all()
    return render_template('assets/list.html', assets=assets)

@app.route('/assets/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def add_asset():
    form = AssetForm()
    
    # إعداد خيارات الموظفين مع معالجة صحيحة للقيم
    try:
        employees = Employee.query.filter_by(status='active').all()
        form.employee_id.choices = [('', 'غير مخصص')] + \
                                  [(str(e.id), f'{e.employee_id} - {e.full_name}') for e in employees]
    except Exception as e:
        form.employee_id.choices = [('', 'غير مخصص')]
        flash(f'خطأ في تحميل قائمة الموظفين: {str(e)}', 'warning')
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # التحقق من عدم وجود رقم العهدة مسبقاً
                existing_asset = Asset.query.filter_by(asset_id=form.asset_id.data).first()
                if existing_asset:
                    flash('رقم العهدة موجود مسبقاً! يرجى استخدام رقم آخر.', 'error')
                    return render_template('assets/add.html', form=form)
                
                # معالجة employee_id بشكل آمن
                employee_id = None
                if form.employee_id.data and form.employee_id.data.strip() != '':
                    try:
                        employee_id = int(form.employee_id.data)
                        # التحقق من وجود الموظف
                        employee = Employee.query.get(employee_id)
                        if not employee:
                            flash('الموظف المحدد غير موجود!', 'error')
                            return render_template('assets/add.html', form=form)
                    except (ValueError, TypeError):
                        flash('خطأ في بيانات الموظف المحدد!', 'error')
                        return render_template('assets/add.html', form=form)
                
                # معالجة تاريخ التخصيص
                assigned_date = None
                if employee_id and form.assigned_date.data:
                    assigned_date = form.assigned_date.data
                elif employee_id and not form.assigned_date.data:
                    # تعيين التاريخ الحالي تلقائياً إذا تم تخصيص الموظف
                    assigned_date = date.today()
                
                # معالجة القيمة
                value = None
                if form.value.data is not None:
                    try:
                        value = float(form.value.data)
                        if value < 0:
                            flash('قيمة العهدة لا يمكن أن تكون سالبة!', 'error')
                            return render_template('assets/add.html', form=form)
                    except (ValueError, TypeError):
                        flash('قيمة العهدة غير صحيحة!', 'error')
                        return render_template('assets/add.html', form=form)
                
                # إنشاء العهدة الجديدة
                asset = Asset(
                    asset_id=form.asset_id.data.strip(),
                    name=form.name.data.strip(),
                    description=form.description.data.strip() if form.description.data else None,
                    category=form.category.data.strip(),
                    value=value,
                    employee_id=employee_id,
                    assigned_date=assigned_date,
                    condition=form.condition.data,
                    notes=form.notes.data.strip() if form.notes.data else None,
                    status='assigned' if employee_id else 'available'
                )
                
                # حفظ في قاعدة البيانات
                db.session.add(asset)
                db.session.commit()
                
                success_msg = f'تم إضافة العهدة "{asset.name}" بنجاح!'
                if employee_id:
                    employee = Employee.query.get(employee_id)
                    success_msg += f' وتم تخصيصها للموظف {employee.full_name}'
                
                flash(success_msg, 'success')
                return redirect(url_for('assets'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'حدث خطأ أثناء إضافة العهدة: {str(e)}', 'error')
                return render_template('assets/add.html', form=form)
        else:
            # عرض أخطاء التحقق من صحة النموذج
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'خطأ في حقل {getattr(form, field).label.text}: {error}', 'error')
    
    return render_template('assets/add.html', form=form)

@app.route('/assets/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def edit_asset(id):
    asset = Asset.query.get_or_404(id)
    form = AssetForm(obj=asset)
    form.employee_id.choices = [('', 'غير مخصص')] + \
                              [(e.id, f'{e.employee_id} - {e.full_name}') 
                               for e in Employee.query.filter_by(status='active').all()]
    
    if form.validate_on_submit():
        asset.asset_id = form.asset_id.data
        asset.name = form.name.data
        asset.description = form.description.data
        asset.category = form.category.data
        asset.value = form.value.data
        
        # تحديث تخصيص الموظف
        old_employee_id = asset.employee_id
        new_employee_id = form.employee_id.data if form.employee_id.data else None
        
        asset.employee_id = new_employee_id
        asset.assigned_date = form.assigned_date.data if new_employee_id else None
        asset.condition = form.condition.data
        asset.notes = form.notes.data
        
        # تحديث الحالة بناءً على التخصيص
        if new_employee_id:
            asset.status = 'assigned'
        else:
            asset.status = 'available'
            asset.return_date = datetime.now().date() if old_employee_id else None
        
        try:
            db.session.commit()
            flash('تم تحديث العهدة بنجاح!', 'success')
            return redirect(url_for('assets'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث العهدة: {str(e)}', 'danger')
    
    return render_template('assets/edit.html', form=form, asset=asset)

@app.route('/assets/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_asset(id):
    asset = Asset.query.get_or_404(id)
    
    try:
        db.session.delete(asset)
        db.session.commit()
        flash('تم حذف العهدة بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف العهدة: {str(e)}', 'danger')
    
    return redirect(url_for('assets'))

# قسم التوظيف
@app.route('/recruitment')
@login_required
def recruitment():
    applications = JobApplication.query.order_by(JobApplication.applied_date.desc()).all()
    return render_template('recruitment/list.html', applications=applications)

@app.route('/recruitment/apply', methods=['GET', 'POST'])
def apply_job():
    form = JobApplicationForm()
    if form.validate_on_submit():
        application = JobApplication(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            position_applied=form.position_applied.data,
            education=form.education.data,
            experience_years=form.experience_years.data,
            skills=form.skills.data,
            cover_letter=form.cover_letter.data
        )
        db.session.add(application)
        db.session.commit()
        flash('تم تقديم طلب التوظيف بنجاح!', 'success')
        return redirect(url_for('apply_job'))
    
    return render_template('recruitment/apply.html', form=form)

# API للإحصائيات
@app.route('/api/stats')
@login_required
def api_stats():
    stats = {
        'employees_by_type': {
            'الإدارة': Employee.query.filter_by(employee_type='الإدارة', status='active').count(),
            'الحراسات الأمنية': Employee.query.filter_by(employee_type='الحراسات الأمنية', status='active').count(),
            'الحارسات': Employee.query.filter_by(employee_type='الحارسات', status='active').count(),
            'العمالة رجال': Employee.query.filter_by(employee_type='العمالة رجال', status='active').count(),
            'العاملات': Employee.query.filter_by(employee_type='العاملات', status='active').count(),
            'مرشدي الحافلات': Employee.query.filter_by(employee_type='مرشدي الحافلات', status='active').count()
        },
        'attendance_today': {
            'present': Attendance.query.filter_by(date=date.today(), status='present').count(),
            'absent': Attendance.query.filter_by(date=date.today(), status='absent').count(),
            'late': Attendance.query.filter_by(date=date.today(), status='late').count()
        }
    }
    return jsonify(stats)

# تسجيل الدخول والخروج
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/settings')
@login_required
@role_required('admin')  # إضافة تقييد الصلاحيات
def settings():
    current_settings = Settings.get_settings()
    return render_template('settings.html', settings=current_settings)

@app.route('/settings/update', methods=['POST'])
@login_required
@role_required('admin')
def update_settings():
    try:
        # البحث عن الإعدادات الموجودة أو إنشاء جديدة
        current_settings = Settings.query.first()
        
        if not current_settings:
            # إنشاء إعدادات جديدة إذا لم تكن موجودة
            current_settings = Settings()
            db.session.add(current_settings)
            # حفظ أولي لإنشاء السجل
            db.session.flush()
        
        # تحديث معلومات الشركة
        current_settings.company_name = request.form.get('company_name', 'شركة رايزو')
        current_settings.app_name = request.form.get('app_name', 'RAIZO HR System')
        current_settings.commercial_register = request.form.get('commercial_register', '')
        current_settings.tax_number = request.form.get('tax_number', '')
        current_settings.company_address = request.form.get('company_address', '')
        
        # تحديث إعدادات الرواتب
        current_settings.currency = request.form.get('currency', 'ريال سعودي')
        current_settings.currency_symbol = request.form.get('currency_symbol', 'ر.س')
        
        # التعامل مع الأرقام بحذر
        try:
            current_settings.monthly_hours = int(request.form.get('monthly_hours', 160))
        except (ValueError, TypeError):
            current_settings.monthly_hours = 160
            
        try:
            current_settings.default_overtime_rate = float(request.form.get('default_overtime_rate', 1.5))
        except (ValueError, TypeError):
            current_settings.default_overtime_rate = 1.5
        
        # تحديث إعدادات النظام
        try:
            current_settings.session_lifetime = int(request.form.get('session_lifetime', 2))
        except (ValueError, TypeError):
            current_settings.session_lifetime = 2
            
        try:
            current_settings.max_file_size = int(request.form.get('max_file_size', 16))
        except (ValueError, TypeError):
            current_settings.max_file_size = 16
            
        current_settings.default_language = request.form.get('default_language', 'ar')
        current_settings.timezone = request.form.get('timezone', 'Asia/Riyadh')
        
        # تحديث إعدادات الأمان
        current_settings.require_strong_password = 'require_strong_password' in request.form
        current_settings.enable_login_attempts = 'enable_login_attempts' in request.form
        
        try:
            current_settings.max_login_attempts = int(request.form.get('max_login_attempts', 5))
        except (ValueError, TypeError):
            current_settings.max_login_attempts = 5
            
        try:
            current_settings.lockout_duration = int(request.form.get('lockout_duration', 30))
        except (ValueError, TypeError):
            current_settings.lockout_duration = 30
        
        # تحديث إعدادات النسخ الاحتياطي
        current_settings.auto_backup = 'auto_backup' in request.form
        current_settings.backup_frequency = request.form.get('backup_frequency', 'weekly')
        
        # تحديث تاريخ التعديل
        current_settings.updated_at = datetime.utcnow()
        
        # حفظ التغييرات في قاعدة البيانات
        db.session.commit()
        
        # تحديث إعدادات التطبيق الحالية
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=current_settings.session_lifetime)
        app.config['MAX_CONTENT_LENGTH'] = current_settings.max_file_size * 1024 * 1024
        
        # إعادة إعداد جدولة النسخ الاحتياطي
        try:
            from google_drive_backup import setup_backup_schedule
            setup_backup_schedule()
        except Exception as e:
            print(f"خطأ في إعادة إعداد النسخ الاحتياطي: {e}")
        
        flash('تم تحديث الإعدادات بنجاح!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حفظ الإعدادات: {str(e)}', 'error')
        print(f"خطأ في حفظ الإعدادات: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(url_for('settings'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/employees/export')
@login_required
@role_required('admin', 'manager', 'hr')
def export_employees():
    try:
        # جلب جميع الموظفين النشطين
        employees = Employee.query.filter_by(status='active').all()
        
        # إنشاء قائمة البيانات
        data = []
        for emp in employees:
            data.append({
                'رقم الموظف': emp.id,
                'الاسم بالعربية': emp.name_arabic,
                'الاسم بالإنجليزية': emp.name_english,
                'رقم الهوية': emp.national_id,
                'تاريخ الميلاد': emp.birth_date.strftime('%Y-%m-%d') if emp.birth_date else '',
                'الجنسية': emp.nationality,
                'الجنس': emp.gender,
                'رقم الهاتف': emp.phone,
                'البريد الإلكتروني': emp.email,
                'العنوان': emp.address,
                'المسمى الوظيفي': emp.job_title,
                'القسم': emp.department,
                'المركز': emp.center,
                'الراتب الأساسي': emp.salary,
                'تاريخ بداية العقد': emp.contract_signing_date.strftime('%Y-%m-%d') if emp.contract_signing_date else '',
                'تاريخ انتهاء العقد': emp.contract_end_date.strftime('%Y-%m-%d') if emp.contract_end_date else '',
                'نوع العقد': emp.contract_type,
                'نوع الموظف': emp.employee_type,
                'نوع البنك': emp.bank_type,
                'رقم الآيبان': emp.iban_number
            })
        
        # إنشاء DataFrame
        df = pd.DataFrame(data)
        
        # إنشاء ملف Excel في الذاكرة
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='الموظفين', index=False)
        
        output.seek(0)
        
        # إرسال الملف للتحميل
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'employees_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        flash(f'حدث خطأ أثناء تصدير البيانات: {str(e)}', 'error')
        return redirect(url_for('employees'))

@app.route('/employees/import', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def import_employees():
    if request.method == 'POST':
        try:
            # التحقق من وجود الملف
            if 'file' not in request.files:
                flash('لم يتم اختيار أي ملف', 'error')
                return redirect(url_for('employees'))
            
            file = request.files['file']
            if not file or file.filename == '':
                flash('يرجى اختيار ملف للاستيراد', 'error')
                return redirect(url_for('employees'))
            
            # التحقق من نوع الملف
            allowed_extensions = ['.xlsx', '.xls']
            if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                flash('يجب أن يكون الملف من نوع Excel (.xlsx أو .xls)', 'error')
                return redirect(url_for('employees'))
            
            # قراءة ملف Excel مع معالجة الأخطاء
            try:
                df = pd.read_excel(file, engine='openpyxl' if file.filename.endswith('.xlsx') else 'xlrd')
            except Exception as e:
                flash(f'خطأ في قراءة ملف Excel: {str(e)}', 'error')
                return redirect(url_for('employees'))
            
            # التحقق من وجود بيانات في الملف
            if df.empty:
                flash('الملف فارغ أو لا يحتوي على بيانات صالحة', 'error')
                return redirect(url_for('employees'))
            
            # تنظيف أسماء الأعمدة
            df.columns = df.columns.str.strip()
            
            # التحقق من الأعمدة المطلوبة
            required_columns = ['الاسم بالعربية', 'رقم الهوية']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                flash(f'الأعمدة التالية مفقودة في الملف: {", ".join(missing_columns)}', 'error')
                return redirect(url_for('employees'))
            
            # معالجة البيانات وإدراجها
            success_count = 0
            error_count = 0
            error_details = []
            
            for index, row in df.iterrows():
                try:
                    # التحقق من عدم وجود موظف بنفس رقم الهوية
                    national_id_value = str(row['رقم الهوية']).strip()
                    if not national_id_value or national_id_value == 'nan':
                        error_count += 1
                        error_details.append(f'الصف {index + 2}: رقم الهوية مفقود')
                        continue
                        
                    existing_employee = Employee.query.filter_by(national_id=national_id_value).first()
                    if existing_employee:
                        error_count += 1
                        error_details.append(f'الصف {index + 2}: رقم الهوية {national_id_value} موجود مسبقاً')
                        continue
                    
                    # التحقق من الاسم العربي
                    name_arabic = str(row['الاسم بالعربية']).strip()
                    if not name_arabic or name_arabic == 'nan':
                        error_count += 1
                        error_details.append(f'الصف {index + 2}: الاسم بالعربية مفقود')
                        continue
                    
                    # إنشاء employee_id تلقائياً
                    employee_id = Employee.generate_employee_id()
                    
                    # تحويل التواريخ بأمان
                    def safe_date_conversion(date_value):
                        if pd.isna(date_value) or str(date_value).strip() == '':
                            return None
                        try:
                            return pd.to_datetime(date_value, errors='coerce').date()
                        except:
                            return None
                    
                    # تعيين قيم افتراضية للحقول الإجبارية
                    birth_date = safe_date_conversion(row.get('تاريخ الميلاد'))
                    if not birth_date:
                        birth_date = date(1990, 1, 1)  # تاريخ افتراضي
                    
                    contract_signing_date = safe_date_conversion(row.get('تاريخ بداية العقد'))
                    if not contract_signing_date:
                        contract_signing_date = date.today()
                    
                    contract_end_date = safe_date_conversion(row.get('تاريخ انتهاء العقد'))
                    if not contract_end_date:
                        contract_end_date = date.today() + timedelta(days=365)  # سنة من اليوم
                    
                    id_expiry_date = safe_date_conversion(row.get('تاريخ انتهاء الهوية'))
                    if not id_expiry_date:
                        id_expiry_date = date.today() + timedelta(days=3650)  # 10 سنوات
                    
                    # إنشاء موظف جديد مع جميع الحقول المطلوبة
                    employee = Employee(
                        employee_id=employee_id,
                        name_arabic=name_arabic,
                        name_english=str(row.get('الاسم بالإنجليزية', '')).strip(),
                        national_id=national_id_value,
                        id_validity=str(row.get('صلاحية الهوية', 'سارية')).strip(),
                        id_expiry_date=id_expiry_date,
                        birth_date=birth_date,
                        nationality=str(row.get('الجنسية', 'سعودي')).strip(),
                        birth_place=str(row.get('مكان الميلاد', '')).strip(),
                        marital_status=str(row.get('الحالة الاجتماعية', 'أعزب')).strip(),
                        gender=str(row.get('الجنس', 'ذكر')).strip(),
                        id_issuer=str(row.get('جهة إصدار الهوية', '')).strip(),
                        phone=str(row.get('رقم الهاتف', '')).strip(),
                        additional_phone=str(row.get('رقم هاتف إضافي', '')).strip(),
                        email=str(row.get('البريد الإلكتروني', '')).strip(),
                        address=str(row.get('العنوان', '')).strip(),
                        emergency_phone=str(row.get('رقم الطوارئ', '')).strip(),
                        salary=_safe_salary_conversion(row.get('الراتب الأساسي', 0)),
                        contract_signing_date=contract_signing_date,
                        contract_end_date=contract_end_date,
                        start_work_date=safe_date_conversion(row.get('تاريخ المباشرة')),
                        contract_duration=str(row.get('مدة العقد', 'سنة واحدة')).strip(),
                        job_title=str(row.get('المسمى الوظيفي', 'موظف')).strip(),
                        contract_type=str(row.get('نوع العقد', 'دائم')).strip(),
                        probation_period=str(row.get('فترة التجربة', '3 أشهر')).strip(),
                        working_hours=int(row.get('ساعات العمل', 8)) if pd.notna(row.get('ساعات العمل')) else 8,
                        uniform_provision=str(row.get('بند البدلة', 'نعم')).strip(),
                        operating_company=str(row.get('الشركة المشغلة', 'شركة رايزو')).strip(),
                        notes=str(row.get('ملاحظات', '')).strip(),
                        penalty_clause=str(row.get('الشرط الجزائي', '')).strip(),
                        internet_provision=str(row.get('بند الإنترنت', 'لا')).strip(),
                        department=str(row.get('القسم', 'عام')).strip(),
                        center=str(row.get('المركز', '')).strip(),
                        square=str(row.get('المربع', '')).strip(),
                        camp_number=str(row.get('رقم المخيم', '')).strip(),
                        work_shift=str(row.get('فترة العمل', 'صباحية')).strip(),
                        bank_type=str(row.get('نوع البنك', '')).strip(),
                        iban_number=str(row.get('رقم الآيبان', '')).strip(),
                        iban_certificate=str(row.get('شهادة الآيبان', '')).strip(),
                        additional_bank=str(row.get('بنك إضافي', '')).strip(),
                        additional_iban=str(row.get('آيبان إضافي', '')).strip(),
                        beneficiary_name=str(row.get('اسم المستفيد', '')).strip(),
                        beneficiary_phone=str(row.get('رقم المستفيد', '')).strip(),
                        # حقول التوافق مع النظام القديم
                        first_name=name_arabic.split()[0] if name_arabic else '',
                        last_name=' '.join(name_arabic.split()[1:]) if len(name_arabic.split()) > 1 else '',
                        employee_type=str(row.get('نوع الموظف', 'دائم')).strip(),
                        hire_date=contract_signing_date,
                        status='active',
                        emergency_contact=str(row.get('جهة الطوارئ', '')).strip()
                    )
                    
                    db.session.add(employee)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_details.append(f'الصف {index + 2}: {str(e)}')
                    continue
            
            # حفظ التغييرات
            if success_count > 0:
                db.session.commit()
                flash(f'تم استيراد {success_count} موظف بنجاح.', 'success')
            
            if error_count > 0:
                flash(f'فشل في استيراد {error_count} موظف. التفاصيل: {"; ".join(error_details[:5])}', 'warning')
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء استيراد البيانات: {str(e)}', 'error')
    
    return redirect(url_for('employees'))

@app.route('/employees/view/<int:id>')
@login_required
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    return render_template('employees/view.html', employee=employee)

@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        # تحديث بيانات الموظف
        form.populate_obj(employee)
        
        # معالجة رفع الصور والمستندات
        if form.employee_photo.data and hasattr(form.employee_photo.data, 'filename') and form.employee_photo.data.filename:
            photo_filename = secure_filename(form.employee_photo.data.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', photo_filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            form.employee_photo.data.save(photo_path)
            employee.employee_photo = photo_filename
            
        if form.iban_certificate.data and hasattr(form.iban_certificate.data, 'filename') and form.iban_certificate.data.filename:
            doc_filename = secure_filename(form.iban_certificate.data.filename)
            doc_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', doc_filename)
            os.makedirs(os.path.dirname(doc_path), exist_ok=True)
            form.iban_certificate.data.save(doc_path)
            employee.iban_certificate = doc_filename
        
        try:
            db.session.commit()
            flash('تم تحديث بيانات الموظف بنجاح!', 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تحديث البيانات.', 'error')
    
    return render_template('employees/edit.html', form=form, employee=employee)

@app.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    try:
        employee = Employee.query.get_or_404(id)
        db.session.delete(employee)
        db.session.commit()
        flash('تم حذف الموظف بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف الموظف.', 'error')
    return redirect(url_for('employees'))

@app.route('/employees/print/<int:id>')
@login_required
def print_employee(id):
    employee = Employee.query.get_or_404(id)
    return render_template('employees/print.html', employee=employee)

import logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/debug/photos')
@login_required
def debug_photos():
    photos_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'photos')
    if os.path.exists(photos_dir):
        files = os.listdir(photos_dir)
        return f"Photos directory exists. Files: {files}"
    else:
        return "Photos directory does not exist"

# إدارة المستخدمين (للمدير فقط)
@app.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('users/list.html', users=users)

# إضافة route الصلاحيات بشكل منفصل
@app.route('/permissions')
@login_required
def permissions():
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('permissions.html')

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        # التحقق من عدم وجود مستخدم بنفس اسم المستخدم أو البريد الإلكتروني
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            if existing_user.username == form.username.data:
                flash('اسم المستخدم موجود بالفعل', 'error')
            else:
                flash('البريد الإلكتروني موجود بالفعل', 'error')
        else:
            try:
                user = User(
                    username=form.username.data,
                    email=form.email.data,
                    role=form.role.data
                )
                user.set_password(form.password.data)
                
                db.session.add(user)
                db.session.commit()
                flash('تم إضافة المستخدم بنجاح!', 'success')
                return redirect(url_for('users'))
            except Exception as e:
                db.session.rollback()
                flash('حدث خطأ أثناء إضافة المستخدم.', 'error')
    
    return render_template('users/add.html', form=form)

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(id):
    user = User.query.get_or_404(id)
    form = EditUserForm(original_user=user, obj=user)
    
    if form.validate_on_submit():
        try:
            # التحقق من عدم تكرار اسم المستخدم
            existing_user = User.query.filter(User.username == form.username.data, User.id != id).first()
            if existing_user:
                flash('اسم المستخدم موجود بالفعل', 'error')
                return render_template('users/edit.html', form=form, user=user)
            
            # التحقق من عدم تكرار البريد الإلكتروني
            existing_email = User.query.filter(User.email == form.email.data, User.id != id).first()
            if existing_email:
                flash('البريد الإلكتروني موجود بالفعل', 'error')
                return render_template('users/edit.html', form=form, user=user)
            
            # تحديث بيانات المستخدم
            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data
            
            # تحديث كلمة المرور إذا تم إدخالها
            if form.password.data:
                user.set_password(form.password.data)
            
            db.session.commit()
            flash('تم تحديث بيانات المستخدم بنجاح!', 'success')
            return redirect(url_for('users'))
            
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تحديث بيانات المستخدم.', 'error')
    
    return render_template('users/edit.html', form=form, user=user)

@app.route('/users/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # منع حذف المستخدم الحالي
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'error')
        return redirect(url_for('users'))
    
    try:
        # حذف الإشعارات المرتبطة بالمستخدم
        Notification.query.filter_by(user_id=user.id).delete()
        
        # حذف إعدادات الإشعارات المرتبطة بالمستخدم
        NotificationSettings.query.filter_by(user_id=user.id).delete()
        
        # تحديث المستندات المرفوعة من قبل المستخدم (إزالة الربط بدلاً من الحذف)
        Document.query.filter_by(uploaded_by=user.id).update({'uploaded_by': None})
        
        # الآن يمكن حذف المستخدم بأمان
        db.session.delete(user)
        db.session.commit()
        
        flash('تم حذف المستخدم بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المستخدم: {str(e)}', 'error')
    
    return redirect(url_for('users'))

# ===== إدارة المستندات =====
@app.route('/documents')
@login_required
def documents():
    if not can_view('documents'):
        flash('ليس لديك صلاحية لعرض المستندات', 'error')
        return redirect(url_for('index'))
    
    # معاملات البحث
    search_name = request.args.get('search_name', '')
    search_employee_name = request.args.get('search_employee_name', '')
    search_employee_number = request.args.get('search_employee_number', '')
    search_department = request.args.get('search_department', '')
    search_category = request.args.get('search_category', '')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # بناء الاستعلام
    query = Document.query.filter_by(status='active')
    
    if search_name:
        query = query.filter(Document.document_name.contains(search_name))
    
    if search_employee_name:
        query = query.filter(Document.employee_name.contains(search_employee_name))
    
    if search_employee_number:
        query = query.filter(Document.employee_number.contains(search_employee_number))
    
    if search_department:
        query = query.filter(Document.department == search_department)
    
    if search_category:
        query = query.filter(Document.category == search_category)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Document.upload_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Document.upload_date <= date_to_obj)
        except ValueError:
            pass
    
    # ترتيب النتائج
    documents = query.order_by(Document.upload_date.desc()).all()
    
    # إحصائيات
    total_documents = Document.query.filter_by(status='active').count()
    total_size = db.session.query(db.func.sum(Document.file_size)).filter_by(status='active').scalar() or 0
    total_size_mb = round(total_size / (1024 * 1024), 2)
    
    # الأقسام والفئات للفلترة
    departments = db.session.query(Document.department).filter_by(status='active').distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    categories = db.session.query(Document.category).filter_by(status='active').distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('documents/list.html',
                         documents=documents,
                         total_documents=total_documents,
                         total_size_mb=total_size_mb,
                         departments=departments,
                         categories=categories,
                         search_name=search_name,
                         search_employee_name=search_employee_name,
                         search_employee_number=search_employee_number,
                         search_department=search_department,
                         search_category=search_category,
                         date_from=date_from,
                         date_to=date_to)

@app.route('/documents/add', methods=['GET', 'POST'])
@login_required
def add_document():
    # التحقق من صلاحيات المستخدم
    if not can_add('documents'):
        flash('ليس لديك صلاحية لإضافة المستندات', 'error')
        return redirect(url_for('documents'))
    
    form = DocumentForm()
    
    # إضافة خيارات الموظفين مع معالجة الحالة التي لا يوجد فيها موظفين
    try:
        active_employees = Employee.query.filter_by(status='active').all()
        form.employee_id.choices = [('', 'بدون ربط بموظف')] + \
                                  [(e.id, f'{e.employee_id} - {e.name_arabic}') 
                                   for e in active_employees]
    except Exception as e:
        # في حالة وجود خطأ في الاستعلام، استخدم قائمة فارغة
        form.employee_id.choices = [('', 'بدون ربط بموظف')]
        flash('تحذير: لا يمكن تحميل قائمة الموظفين', 'warning')
    
    if form.validate_on_submit():
        try:
            file = form.document_file.data
            
            # التحقق من حجم الملف قبل المعالجة
            if hasattr(file, 'content_length') and file.content_length:
                if file.content_length > 10 * 1024 * 1024:  # 10MB
                    flash('حجم الملف كبير جداً. الحد الأقصى المسموح هو 10 ميجابايت.', 'error')
                    return render_template('documents/add.html', form=form)
            
            # التحقق من نوع الملف
            if not file.filename.lower().endswith('.pdf'):
                flash('يُسمح برفع ملفات PDF فقط.', 'error')
                return render_template('documents/add.html', form=form)
            
            filename = secure_filename(file.filename)
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            unique_filename = timestamp + filename
            
            # إنشاء مجلد الرفع إذا لم يكن موجوداً
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file_path = os.path.join(upload_folder, unique_filename)
            
            # حفظ الملف مع التحقق من النجاح
            try:
                file.save(file_path)
                if not os.path.exists(file_path):
                    flash('فشل في حفظ الملف. يرجى المحاولة مرة أخرى.', 'error')
                    return render_template('documents/add.html', form=form)
            except Exception as save_error:
                flash(f'خطأ في حفظ الملف: {str(save_error)}', 'error')
                return render_template('documents/add.html', form=form)
            
            # الحصول على حجم الملف
            file_size = os.path.getsize(file_path)
            
            # التحقق مرة أخرى من حجم الملف بعد الحفظ
            if file_size > 10 * 1024 * 1024:  # 10MB
                os.remove(file_path)  # حذف الملف
                flash('حجم الملف كبير جداً. الحد الأقصى المسموح هو 10 ميجابايت.', 'error')
                return render_template('documents/add.html', form=form)
            
            # معالجة employee_id بشكل صحيح
            employee_id_value = None
            if form.employee_id.data and form.employee_id.data != '':
                try:
                    employee_id_value = int(form.employee_id.data)
                except (ValueError, TypeError):
                    employee_id_value = None
            
            # معالجة employee_id بشكل صحيح
            employee_id_value = None
            if form.employee_id.data and form.employee_id.data != '':
                try:
                    employee_id_value = int(form.employee_id.data)
                except (ValueError, TypeError):
                    employee_id_value = None

            # إنشاء سجل المستند
            document = Document(
                document_name=form.document_name.data,
                original_filename=filename,
                filename=unique_filename,
                file_path=file_path,
                file_size=file_size,
                department=form.department.data,
                category=form.category.data,
                description=form.description.data,
                employee_id=employee_id_value,
                uploaded_by=current_user.id,
                is_confidential=form.is_confidential.data
            )
            
            # إضافة معلومات الموظف إذا تم اختياره
            if employee_id_value:
                try:
                    employee = Employee.query.get(employee_id_value)
                    if employee:
                        document.employee_name = employee.name_arabic
                        document.employee_number = employee.employee_id
                except Exception:
                    pass  # تجاهل الخطأ إذا لم يتم العثور على الموظف
            
            db.session.add(document)
            db.session.commit()
            
            flash('تم رفع المستند بنجاح', 'success')
            return redirect(url_for('documents'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء رفع المستند: {str(e)}', 'error')
    
    return render_template('documents/add.html', form=form)

@app.route('/documents/download/<int:id>')
@login_required
def download_document(id):
    if not can_view('documents'):
        flash('ليس لديك صلاحية لتحميل المستندات', 'error')
        return redirect(url_for('documents'))
    
    document = Document.query.get_or_404(id)
    
    # التحقق من وجود الملف
    if not os.path.exists(document.file_path):
        flash('الملف غير موجود على الخادم', 'error')
        return redirect(url_for('documents'))
    
    try:
        # تحديث إحصائيات الوصول
        document.last_accessed = datetime.utcnow()
        document.access_count += 1
        db.session.commit()
        
        # تحديد نوع المحتوى بناءً على امتداد الملف
        mimetype = 'application/pdf' if document.original_filename.lower().endswith('.pdf') else 'application/octet-stream'
        
        return send_file(
            document.file_path, 
            as_attachment=True, 
            download_name=document.original_filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        flash(f'حدث خطأ أثناء تحميل الملف: {str(e)}', 'error')
        return redirect(url_for('documents'))

@app.route('/documents/delete/<int:id>', methods=['POST'])
@login_required
def delete_document(id):
    if not can_delete('documents'):
        flash('ليس لديك صلاحية لحذف المستندات', 'error')
        return redirect(url_for('documents'))
    
    document = Document.query.get_or_404(id)
    
    try:
        # حذف الملف من النظام
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # تحديث حالة المستند بدلاً من الحذف النهائي
        document.status = 'deleted'
        db.session.commit()
        
        flash('تم حذف المستند بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المستند: {str(e)}', 'error')
    
    return redirect(url_for('documents'))

# قسم التوظيف

# إضافة route لإضافة دور جديد
@app.route('/roles/add', methods=['POST'])
@login_required
def add_role():
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية لإضافة أدوار جديدة', 'error')
        return redirect(url_for('permissions'))
    
    role_key = request.form.get('role_key')
    role_name = request.form.get('role_name')
    
    # التحقق من صحة البيانات
    if not role_key or not role_name:
        flash('يرجى ملء جميع الحقول المطلوبة', 'error')
        return redirect(url_for('permissions'))
    
    # التحقق من عدم وجود الدور مسبقاً
    if role_key in ROLE_PERMISSIONS:
        flash('هذا الدور موجود بالفعل', 'error')
        return redirect(url_for('permissions'))
    
    # إنشاء الدور الجديد
    new_role = {
        'name': role_name,
        'modules': {}
    }
    
    # إضافة صلاحيات الوحدات
    for module_key in SYSTEM_MODULES.keys():
        module_permissions = {
            'view': bool(request.form.get(f'{module_key}_view')),
            'add': bool(request.form.get(f'{module_key}_add')),
            'edit': bool(request.form.get(f'{module_key}_edit')),
            'delete': bool(request.form.get(f'{module_key}_delete')),
            'fields': request.form.getlist(f'{module_key}_fields') or []
        }
        
        # إذا تم اختيار "جميع الحقول"
        if 'all' in module_permissions['fields']:
            module_permissions['fields'] = 'all'
        
        new_role['modules'][module_key] = module_permissions
    
    # إضافة الدور الجديد إلى ROLE_PERMISSIONS
    ROLE_PERMISSIONS[role_key] = new_role
    
    # حفظ الأدوار في ملف منفصل (اختياري)
    try:
        import json
        with open('roles_config.json', 'w', encoding='utf-8') as f:
            json.dump(ROLE_PERMISSIONS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'تحذير: لم يتم حفظ الأدوار في الملف: {e}')
    
    flash(f'تم إضافة الدور "{role_name}" بنجاح', 'success')
    return redirect(url_for('permissions'))

# إضافة route لحذف دور
@app.route('/roles/delete/<role_key>', methods=['POST'])
@login_required
def delete_role(role_key):
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية لحذف الأدوار', 'error')
        return redirect(url_for('permissions'))
    
    # منع حذف الأدوار الأساسية
    protected_roles = ['admin', 'manager', 'hr', 'employee', 'user']
    if role_key in protected_roles:
        flash('لا يمكن حذف الأدوار الأساسية للنظام', 'error')
        return redirect(url_for('permissions'))
    
    # التحقق من وجود مستخدمين بهذا الدور
    users_with_role = User.query.filter_by(role=role_key).count()
    if users_with_role > 0:
        flash(f'لا يمكن حذف هذا الدور لأن هناك {users_with_role} مستخدم يستخدمه', 'error')
        return redirect(url_for('permissions'))
    
    if role_key in ROLE_PERMISSIONS:
        role_name = ROLE_PERMISSIONS[role_key]['name']
        del ROLE_PERMISSIONS[role_key]
        
        # حفظ التغييرات في الملف
        try:
            import json
            with open('roles_config.json', 'w', encoding='utf-8') as f:
                json.dump(ROLE_PERMISSIONS, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'تحذير: لم يتم حفظ التغييرات في الملف: {e}')
        
        flash(f'تم حذف الدور "{role_name}" بنجاح', 'success')
    else:
        flash('الدور غير موجود', 'error')
    
    return redirect(url_for('permissions'))

# قسم التقارير
@app.route('/reports')
@login_required
@role_required('admin', 'manager', 'hr')
def reports():
    # إحصائيات الموظفين
    total_employees = Employee.query.filter_by(status='active').count()
    employees_by_type = {
        'الإدارة': Employee.query.filter_by(employee_type='الإدارة', status='active').count(),
        'الإداريات': Employee.query.filter_by(employee_type='الإداريات', status='active').count(),
        'الحراسات الأمنية': Employee.query.filter_by(employee_type='الحراسات الأمنية', status='active').count(),
        'العمال': Employee.query.filter_by(employee_type='العمال', status='active').count(),
        'المقاولين': Employee.query.filter_by(employee_type='المقاولين', status='active').count()
    }
    
    # إحصائيات الحضور
    today = date.today()
    attendance_today = Attendance.query.filter(
        func.date(Attendance.date) == today
    ).count()
    
    # إحصائيات الرواتب
    current_month = today.month
    current_year = today.year
    payroll_count = Payroll.query.filter(
        Payroll.month == current_month,
        Payroll.year == current_year
    ).count()
    
    # إحصائيات الوثائق
    total_documents = Document.query.count()
    confidential_documents = Document.query.filter_by(is_confidential=True).count()
    
    # إحصائيات الأصول
    total_assets = Asset.query.count()
    assigned_assets = Asset.query.filter_by(status='assigned').count()
    
    return render_template('reports.html', 
                         total_employees=total_employees,
                         employees_by_type=employees_by_type,
                         attendance_today=attendance_today,
                         payroll_count=payroll_count,
                         total_documents=total_documents,
                         confidential_documents=confidential_documents,
                         total_assets=total_assets,
                         assigned_assets=assigned_assets)

@app.route('/api/search-substitute', methods=['POST'])
@login_required
def search_substitute():
    try:
        data = request.get_json()
        search_term = data.get('search', '').strip()
        
        if not search_term:
            return jsonify({'employees': []})
        
        # البحث في الموظفين النشطين
        employees = Employee.query.filter(
            Employee.status == 'active',
            db.or_(
                Employee.employee_id.contains(search_term),
                Employee.name_arabic.contains(search_term),
                Employee.name_english.contains(search_term),
                Employee.national_id.contains(search_term),
                Employee.phone.contains(search_term)
            )
        ).limit(10).all()
        
        result = []
        for emp in employees:
            result.append({
                'id': emp.id,
                'employee_id': emp.employee_id,
                'name': emp.full_name,
                'department': emp.department
            })
        
        return jsonify({'employees': result})
        
    except Exception as e:
        return jsonify({'employees': [], 'error': str(e)})

# مسارات الإشعارات
@app.route('/notifications')
@login_required
def notifications():
    """صفحة عرض جميع الإشعارات"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_dismissed=False
    ).filter(
        db.or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > datetime.utcnow()
        )
    ).order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('notifications/list.html', notifications=notifications)

@app.route('/api/notifications')
@login_required
def api_notifications():
    """API لجلب الإشعارات"""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 10, type=int)
    
    # الحصول على الإشعارات
    notifications = Notification.get_user_notifications(
        current_user.id,
        unread_only=unread_only,
        limit=limit
    )
    
    # حساب العدد الصحيح للإشعارات غير المقروءة
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False,
        is_dismissed=False
    ).filter(
        db.or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > datetime.utcnow()
        )
    ).count()
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count
    })

@app.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """تحديد إشعار كمقروء"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.mark_as_read()
    
    return jsonify({'success': True})

@app.route('/notifications/<int:notification_id>/dismiss', methods=['POST'])
@login_required
def dismiss_notification(notification_id):
    """إخفاء إشعار"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.dismiss()
    
    return jsonify({'success': True})

@app.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """تحديد جميع الإشعارات كمقروءة"""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True, 'read_at': datetime.utcnow()})
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/notifications/settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    """إعدادات الإشعارات"""
    settings = NotificationSettings.get_or_create_settings(current_user.id)
    
    if request.method == 'POST':
        settings.employee_notifications = 'employee_notifications' in request.form
        settings.attendance_notifications = 'attendance_notifications' in request.form
        settings.payroll_notifications = 'payroll_notifications' in request.form
        settings.document_notifications = 'document_notifications' in request.form
        settings.system_notifications = 'system_notifications' in request.form
        
        settings.show_low_priority = 'show_low_priority' in request.form
        settings.show_normal_priority = 'show_normal_priority' in request.form
        settings.show_high_priority = 'show_high_priority' in request.form
        settings.show_urgent_priority = 'show_urgent_priority' in request.form
        
        settings.auto_dismiss_after_days = int(request.form.get('auto_dismiss_after_days', 7))
        settings.max_notifications_display = int(request.form.get('max_notifications_display', 10))
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('تم حفظ إعدادات الإشعارات بنجاح', 'success')
        return redirect(url_for('notification_settings'))
    
    return render_template('notifications/settings.html', settings=settings)

@app.route('/notifications/send', methods=['GET', 'POST'])
@login_required
def send_notification():
    """صفحة إرسال الإشعارات - للمديرين وموظفي الموارد البشرية فقط"""
    # التحقق من صلاحيات المستخدم
    if current_user.role not in ['admin', 'manager', 'hr']:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    form = SendNotificationForm()
    
    # تحديث خيارات المستخدمين
    users = User.query.all()
    form.recipient_user.choices = [(0, 'اختر المستخدم')] + [(user.id, f'{user.username} ({user.email})') for user in users]
    
    if form.validate_on_submit():
        try:
            recipients = []
            
            # تحديد المستلمين حسب النوع
            if form.recipient_type.data == 'single':
                if form.recipient_user.data and form.recipient_user.data != 0:
                    user = User.query.get(form.recipient_user.data)
                    if user:
                        recipients = [user]
                    else:
                        flash('المستخدم المحدد غير موجود', 'error')
                        return render_template('notifications/send.html', form=form)
                else:
                    flash('يرجى اختيار مستخدم', 'error')
                    return render_template('notifications/send.html', form=form)
                    
            elif form.recipient_type.data == 'role':
                if form.recipient_role.data:
                    recipients = User.query.filter_by(role=form.recipient_role.data).all()
                else:
                    flash('يرجى اختيار الدور', 'error')
                    return render_template('notifications/send.html', form=form)
                    
            elif form.recipient_type.data == 'all':
                recipients = User.query.all()
            
            if not recipients:
                flash('لم يتم العثور على مستلمين', 'error')
                return render_template('notifications/send.html', form=form)
            
            # إرسال الإشعار لكل مستلم
            sent_count = 0
            for recipient in recipients:
                try:
                    expires_at = None
                    if form.expires_at.data:
                        expires_at = datetime.combine(form.expires_at.data, datetime.min.time())
                    
                    notification = Notification.create_notification(
                        user_id=recipient.id,
                        title=form.title.data,
                        message=form.message.data,
                        notification_type=form.notification_type.data,
                        priority=form.priority.data,
                        action_url=form.action_url.data if form.action_url.data else None,
                        action_text=form.action_text.data if form.action_text.data else None,
                        expires_at=expires_at,
                        source_type='admin_message',
                        source_id=current_user.id
                    )
                    
                    if notification:
                        db.session.add(notification)
                        sent_count += 1
                        
                except Exception as e:
                    print(f'خطأ في إرسال الإشعار للمستخدم {recipient.username}: {str(e)}')
                    continue
            
            if sent_count > 0:
                db.session.commit()
                flash(f'تم إرسال الإشعار بنجاح إلى {sent_count} مستخدم', 'success')
                return redirect(url_for('notifications'))
            else:
                flash('فشل في إرسال الإشعار', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إرسال الإشعار: {str(e)}', 'error')
    
    return render_template('notifications/send.html', form=form)

# إضافة route جديد للنسخ الاحتياطي
@app.route('/backup/create')
@login_required
@role_required('admin')
def create_backup():
    try:
        from google_drive_backup import get_backup_manager
        backup_manager = get_backup_manager()
        result = backup_manager.create_database_backup()
        return jsonify({'success': True, 'message': 'تم إنشاء النسخة الاحتياطية بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في إنشاء النسخة الاحتياطية: {str(e)}'})

@app.route('/backup/setup-drive')
@login_required
@role_required('admin')
def setup_drive():
    try:
        from google_drive_backup import get_backup_manager
        backup_manager = get_backup_manager()
        backup_manager.setup_drive_service()
        return jsonify({'success': True, 'message': 'تم إعداد Google Drive بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في إعداد Google Drive: {str(e)}'})


@app.route('/backup/export-all')
@login_required
@role_required('admin')
def export_all_data():
    try:
        # إنشاء ملف Excel متعدد الأوراق
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # تصدير الموظفين
            employees = Employee.query.all()
            emp_data = [{
                'ID': emp.id,
                'الاسم': emp.name_arabic,
                'الهاتف': emp.phone,
                'القسم': emp.department,
                'الراتب': emp.salary
            } for emp in employees]
            pd.DataFrame(emp_data).to_excel(writer, sheet_name='الموظفين', index=False)
            
            # تصدير الحضور
            attendance = Attendance.query.all()
            att_data = [{
                'الموظف': att.employee.name_arabic if att.employee else '',
                'التاريخ': att.date,
                'الحالة': att.status,
                'دخول': att.check_in,
                'خروج': att.check_out
            } for att in attendance]
            pd.DataFrame(att_data).to_excel(writer, sheet_name='الحضور', index=False)
            
            # تصدير الرواتب
            payrolls = Payroll.query.all()
            pay_data = [{
                'الموظف': pay.employee.name_arabic if pay.employee else '',
                'الشهر': pay.month,
                'السنة': pay.year,
                'الراتب الإجمالي': pay.total_salary
            } for pay in payrolls]
            pd.DataFrame(pay_data).to_excel(writer, sheet_name='الرواتب', index=False)
        
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'raizo_complete_backup_{timestamp}.xlsx'
        )
        
    except Exception as e:
        flash(f'حدث خطأ أثناء تصدير البيانات: {str(e)}', 'error')
        return redirect(url_for('settings'))

if __name__ == '__main__':
    # للتطوير المحلي فقط
    app.run(debug=False, host='0.0.0.0', port=5000)