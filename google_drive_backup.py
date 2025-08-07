import os
import io
import shutil
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import schedule
import time
import threading
# إزالة الاستيراد الدائري
# from app import app, db
# from models import Settings

# نطاقات Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveBackup:
    def __init__(self):
        self.service = None
        self.folder_id = None
        self.setup_drive_service()
    
    def setup_drive_service(self):
        """إعداد خدمة Google Drive"""
        creds = None
        
        # تحميل الرموز المحفوظة
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # إذا لم تكن هناك رموز صالحة، اطلب من المستخدم تسجيل الدخول
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # حفظ الرموز للاستخدام التالي
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        self.create_backup_folder()
    
    def create_backup_folder(self):
        """إنشاء مجلد النسخ الاحتياطية في Google Drive"""
        try:
            # البحث عن مجلد موجود
            results = self.service.files().list(
                q="name='RAIZO HR Backups' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                self.folder_id = folders[0]['id']
                print(f"تم العثور على مجلد النسخ الاحتياطية: {self.folder_id}")
            else:
                # إنشاء مجلد جديد
                folder_metadata = {
                    'name': 'RAIZO HR Backups',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                self.folder_id = folder.get('id')
                print(f"تم إنشاء مجلد النسخ الاحتياطية: {self.folder_id}")
                
        except Exception as e:
            print(f"خطأ في إنشاء مجلد Google Drive: {e}")
    
    def upload_backup(self, file_path, file_name):
        """رفع ملف النسخة الاحتياطية إلى Google Drive"""
        try:
            file_metadata = {
                'name': file_name,
                'parents': [self.folder_id]
            }
            
            with open(file_path, 'rb') as file_data:
                media = MediaIoBaseUpload(
                    io.BytesIO(file_data.read()),
                    mimetype='application/octet-stream'
                )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            print(f"تم رفع النسخة الاحتياطية بنجاح: {file.get('id')}")
            return file.get('id')
            
        except Exception as e:
            print(f"خطأ في رفع النسخة الاحتياطية: {e}")
            return None
    
    def create_database_backup(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            # إنشاء مجلد النسخ الاحتياطية المحلي
            backup_dir = 'backups'
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # تاريخ ووقت النسخة
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'raizo_backup_{timestamp}.db'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # نسخ قاعدة البيانات
            db_path = os.path.join('instance', 'raizo_hr.db')
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                
                # رفع إلى Google Drive
                file_id = self.upload_backup(backup_path, backup_filename)
                
                if file_id:
                    # حذف النسخة المحلية بعد الرفع
                    os.remove(backup_path)
                    return True
            
            return False
            
        except Exception as e:
            print(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count=10):
        """حذف النسخ الاحتياطية القديمة (الاحتفاظ بآخر 10 نسخ)"""
        try:
            # البحث عن جميع النسخ الاحتياطية
            results = self.service.files().list(
                q=f"parents in '{self.folder_id}' and name contains 'raizo_backup_'",
                orderBy='createdTime desc',
                fields="files(id, name, createdTime)"
            ).execute()
            
            files = results.get('files', [])
            
            # حذف النسخ الزائدة
            if len(files) > keep_count:
                for file in files[keep_count:]:
                    self.service.files().delete(fileId=file['id']).execute()
                    print(f"تم حذف النسخة القديمة: {file['name']}")
                    
        except Exception as e:
            print(f"خطأ في تنظيف النسخ القديمة: {e}")

# إنشاء كائن النسخ الاحتياطي
backup_manager = None

def get_backup_manager():
    """الحصول على مدير النسخ الاحتياطي بشكل آمن"""
    global backup_manager
    if backup_manager is None:
        backup_manager = GoogleDriveBackup()
    return backup_manager

def scheduled_backup():
    """تنفيذ النسخ الاحتياطي المجدول"""
    try:
        manager = get_backup_manager()
        manager.create_database_backup()
        print(f"تم إنشاء نسخة احتياطية في {datetime.now()}")
    except Exception as e:
        print(f"خطأ في النسخ الاحتياطي المجدول: {e}")

def setup_backup_schedule():
    """إعداد جدولة النسخ الاحتياطي"""
    try:
        manager = get_backup_manager()
        settings = manager.get_settings()
        
        if settings and settings.auto_backup:
            # مسح الجدولة السابقة
            schedule.clear()
            
            # إعداد الجدولة الجديدة
            if settings.backup_frequency == 'daily':
                schedule.every().day.at("02:00").do(scheduled_backup)
            elif settings.backup_frequency == 'weekly':
                schedule.every().sunday.at("02:00").do(scheduled_backup)
            elif settings.backup_frequency == 'monthly':
                schedule.every().month.do(scheduled_backup)
            
            print(f"تم إعداد النسخ الاحتياطي: {settings.backup_frequency}")
    except Exception as e:
        print(f"خطأ في إعداد جدولة النسخ الاحتياطي: {e}")

def run_scheduler():
    """تشغيل المجدول في خيط منفصل"""
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # فحص كل دقيقة
        except Exception as e:
            print(f"خطأ في المجدول: {e}")
            time.sleep(300)  # انتظار 5 دقائق في حالة الخطأ

# بدء المجدول في خيط منفصل
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# إعداد الجدولة عند بدء التشغيل
setup_backup_schedule()