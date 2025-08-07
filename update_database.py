from app import app, db
from models import Payroll, Document
from sqlalchemy import text

def update_payroll_table():
    with app.app_context():
        try:
            # إضافة الحقول الجديدة إلى جدول payroll باستخدام الطريقة الحديثة
            db.session.execute(text('''
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS period_from DATE;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS period_to DATE;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS period_days INTEGER DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS present_days INTEGER DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS absent_days INTEGER DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS withdrawal_days INTEGER DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS daily_salary FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS due_salary FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS overtime_days FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS overtime_due FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS total_salary FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS advance_deduction FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS violation_deduction FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS absence_deduction FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS withdrawal_deduction FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS total_deductions FLOAT DEFAULT 0;
                ALTER TABLE payroll ADD COLUMN IF NOT EXISTS notes TEXT;
            '''))
            
            db.session.commit()
            print("تم تحديث جدول الرواتب بنجاح!")
            
        except Exception as e:
            db.session.rollback()
            print(f"خطأ في تحديث قاعدة البيانات: {e}")
            # في حالة فشل التحديث، يمكن إعادة إنشاء قاعدة البيانات
            print("جاري إعادة إنشاء قاعدة البيانات...")
            try:
                db.drop_all()
                db.create_all()
                print("تم إنشاء جدول المستندات بنجاح")
                print("تم إعادة إنشاء قاعدة البيانات بنجاح!")
            except Exception as create_error:
                print(f"خطأ في إعادة إنشاء قاعدة البيانات: {create_error}")

if __name__ == '__main__':
    update_payroll_table()