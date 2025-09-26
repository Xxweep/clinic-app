# app.py (النسخة النهائية الكاملة والمصححة)

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openpyxl
from io import BytesIO
import json # سنستخدم json بدلاً من eval لزيادة الأمان

# --- 1. إعدادات التطبيق وقاعدة البيانات ---
clinc = Flask(__name__)
clinc.secret_key = 'a_very_strong_and_permanent_secret_key' # الرجاء استخدام مفتاح سري قوي

# إعدادات الاتصال بقاعدة بيانات PostgreSQL
import os # أضف هذا السطر في أعلى الملف مع باقي الـ imports

# ... (باقي الكود)

# إعدادات الاتصال بقاعدة بيانات PostgreSQL (للإنتاج والمحلي)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

clinc.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'postgresql://clinic_user:clinic_pass@localhost:5432/clinic_db'

clinc.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(clinc)

# --- 2. تعريف موديل قاعدة البيانات ---
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    allergies = db.Column(db.String(255), nullable=True, default='لا يوجد')
    history = db.Column(db.Text, nullable=True, default='[]') # سيتم تخزين الملاحظات كنص JSON
    status = db.Column(db.String(50), default='في الانتظار', nullable=False)
    is_returning = db.Column(db.Boolean, default=False)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)

# --- بيانات الأدمن ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# --- المسارات العامة ---
@clinc.route('/')
def index():
    return render_template('index.html')

@clinc.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    phone = request.form.get('phone')
    age = request.form.get('age')
    gender = request.form.get('gender')
    allergies = request.form.get('allergies', 'لا يوجد')

    if not name or not phone or not age or not gender:
        flash('الرجاء إدخال جميع الحقول الإلزامية')
        return redirect(url_for('index'))

    in_queue = Patient.query.filter_by(phone=phone, status='في الانتظار').first()
    if in_queue:
        flash('أنت بالفعل في طابور الانتظار!')
        waiting_list = Patient.query.filter_by(status='في الانتظار').order_by(Patient.visit_date).all()
        position = waiting_list.index(in_queue)
        return redirect(url_for('queue_page', position=position))

    patient = Patient.query.filter_by(phone=phone).first()
    if patient:
        patient.status = 'في الانتظار'
        patient.is_returning = True
        patient.visit_date = datetime.utcnow()
    else:
        patient = Patient(name=name, phone=phone, age=age, gender=gender, allergies=allergies, history='[]', status='في الانتظار')
        db.session.add(patient)
    
    db.session.commit() # حفظ التغييرات في قاعدة البيانات

    waiting_list = Patient.query.filter_by(status='في الانتظار').order_by(Patient.visit_date).all()
    position = waiting_list.index(patient)
    return redirect(url_for('queue_page', position=position))

@clinc.route('/queue/<int:position>')
def queue_page(position):
    waiting_list = Patient.query.filter_by(status='في الانتظار').order_by(Patient.visit_date).all()
    if position >= len(waiting_list):
        return render_template('queue.html', client_served=True)
    total_before = position
    return render_template('queue.html', position=position, total_before=total_before, client_served=False)

@clinc.route('/cancel/<int:position>', methods=['POST'])
def cancel(position):
    waiting_list = Patient.query.filter_by(status='في الانتظار').order_by(Patient.visit_date).all()
    if position < len(waiting_list):
        patient = waiting_list[position]
        patient.status = 'ملغي من قبل العميل'
        db.session.commit() # حفظ التغييرات
    return redirect(url_for('index'))

# --- مسارات الأدمن ---
@clinc.route('/admin', methods=['GET', 'POST'])
def admin_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_page'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة')
            return render_template('signs.html')

    if session.get('logged_in'):
        current_waiting_list = Patient.query.filter_by(status='في الانتظار').order_by(Patient.visit_date).all()
        history_list = Patient.query.filter(Patient.status != 'في الانتظار').order_by(Patient.visit_date.desc()).all()
        
        # تحويل نص JSON إلى قائمة بايثون بشكل آمن
        for p in current_waiting_list:
            p.history_list = json.loads(p.history)
        for p in history_list:
            p.history_list = json.loads(p.history)
            
        return render_template('admin.html', queue=current_waiting_list, done_queue=history_list)
    else:
        return render_template('signs.html')

@clinc.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('تم تسجيل خروجك بنجاح.')
    return redirect(url_for('index'))

# --- مسارات الإجراءات ---
@clinc.route('/done/<int:position>', methods=['POST'])
def done(position):
    if not session.get('logged_in'): return redirect(url_for('admin_page'))
    
    waiting_list = Patient.query.filter_by(status='في الانتظار').order_by(Patient.visit_date).all()
    if position < len(waiting_list):
        patient = waiting_list[position]
        patient.status = 'تمت الخدمة'
        patient.is_returning = False
        db.session.commit() # حفظ التغييرات
    return redirect(url_for('admin_page'))

@clinc.route('/cancel_admin/<int:position>', methods=['POST'])
def cancel_admin(position):
    if not session.get('logged_in'): return redirect(url_for('admin_page'))
    
    waiting_list = Patient.query.filter_by(status='في الانتظار').order_by(Patient.visit_date).all()
    if position < len(waiting_list):
        patient = waiting_list[position]
        patient.status = 'ملغي من قبل الأدمن'
        patient.is_returning = False
        db.session.commit() # حفظ التغييرات
    return redirect(url_for('admin_page'))

@clinc.route('/add_note/<phone>', methods=['POST'])
def add_note(phone):
    if not session.get('logged_in'): return redirect(url_for('admin_page'))
    
    note_text = request.form.get('note')
    patient = Patient.query.filter_by(phone=phone).first()
    if patient and note_text:
        history_list = json.loads(patient.history)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        history_list.append(f"[{timestamp}] {note_text}")
        patient.history = json.dumps(history_list) # تحويل القائمة إلى نص JSON
        db.session.commit() # حفظ التغييرات
    return redirect(url_for('admin_page'))

# --- مسار تحميل Excel ---
@clinc.route('/download_excel')
def download_excel():
    if not session.get('logged_in'): return redirect(url_for('admin_page'))
    
    all_patients = Patient.query.order_by(Patient.name).all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "سجل المرضى"
    ws.sheet_view.rightToLeft = True # جعل الشيت من اليمين لليسار
    headers = ["الاسم", "رقم الهاتف", "العمر", "الجنس", "الحساسية", "آخر حالة", "كامل التاريخ المرضي"]
    ws.append(headers)
    
    for p in all_patients:
        history_notes = "\n".join(json.loads(p.history))
        ws.append([p.name, p.phone, p.age, p.gender, p.allergies, p.status, history_notes])
        
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    return send_file(file_stream, as_attachment=True, download_name='clinic_patients_report.xlsx')

# --- تشغيل التطبيق ---
if __name__ == '__main__':
    with clinc.app_context():
        db.create_all() # إنشاء الجداول إذا لم تكن موجودة
    clinc.run(debug=True)
