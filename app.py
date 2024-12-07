from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# تعيين المفتاح السري
app.secret_key = os.environ.get('SECRET_KEY', 'secret_key')

# كلمة المرور لتسجيل الدخول
APP_PASSWORD = os.environ.get('APP_PASSWORD', 'Fares1999')

# وضع الصيانة
MAINTENANCE_MODE = False  # قم بتعيينها إلى False عندما تنتهي من الصيانة

# تفعيل أو تعطيل تسجيل الدخول
REQUIRE_LOGIN = os.environ.get('REQUIRE_LOGIN', 'False') == 'True'

# إعداد قاعدة البيانات
DATABASE = 'visitors.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.before_request
def check_access():
    if MAINTENANCE_MODE and request.endpoint != 'maintenance':
        return redirect(url_for('maintenance'))
    
    if REQUIRE_LOGIN:
        # السماح بالوصول إلى صفحة تسجيل الدخول وصفحة الصيانة والمجلدات الثابتة بدون تسجيل الدخول
        if request.endpoint in ['login', 'maintenance', 'static']:
            return
        # التحقق من تسجيل الدخول
        if not session.get('logged_in'):
            return redirect(url_for('login'))
    
    # عد الزوار فقط للطلبات GET إلى الصفحات الرئيسية
    if request.method == 'GET' and request.endpoint not in ['maintenance', 'static']:
        log_visitor()

def log_visitor():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO visitors (timestamp) VALUES (?)', (datetime.now(),))
    conn.commit()
    conn.close()

def get_visitor_count():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM visitors')
    count = cursor.fetchone()[0]
    conn.close()
    return count

@app.route('/maintenance')
def maintenance():
    return render_template('maintenance.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if not REQUIRE_LOGIN:
        return redirect(url_for('index'))
    
    name = "Fares Ayoub"
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == APP_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('كلمة المرور غير صحيحة. حاول مرة أخرى.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', name=name)

@app.route('/index', methods=['GET', 'POST'])
def index():
    # تسجيل الدخول يتم التحقق منه في before_request
    name = "Fares Ayoub"
    visitor_count = get_visitor_count()

    duplicates = []
    unique = []
    duplicate_count = 0
    unique_count = 0

    if request.method == 'POST':
        text = request.form.get('text', '')
        # تقسيم النص إلى سطور وتجاهل السطور الفارغة
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        seen = set()
        duplicate_set = set()

        for line in lines:
            if line in seen:
                if line not in duplicate_set:
                    duplicates.append(line)
                    duplicate_set.add(line)
            else:
                unique.append(line)
                seen.add(line)

        duplicate_count = len(duplicates)
        unique_count = len(unique)

        # مسح النص المدخل بجعل المتغير text فارغًا
        text = ''

        return render_template('index.html', duplicates=duplicates, unique=unique, text=text,
                               duplicate_count=duplicate_count, unique_count=unique_count, name=name,
                               visitor_count=visitor_count)
    else:
        # عند إعادة تحميل الصفحة، نجعل النتائج فارغة
        return render_template('index.html', duplicates=[], unique=[], text='', duplicate_count=0,
                               unique_count=0, name=name, visitor_count=visitor_count)

@app.route('/email_password_tool', methods=['GET', 'POST'])
def email_password_tool():
    # تسجيل الدخول يتم التحقق منه في before_request
    name = "Fares Ayoub"
    emails_text = ''
    password = ''
    result = ''
    email_count = 0
    visitor_count = get_visitor_count()

    if request.method == 'POST':
        emails_text = request.form.get('emails', '')
        password = request.form.get('password', '')
        action = request.form.get('action', '')

        # تقسيم النص إلى سطور وتجاهل السطور الفارغة
        emails = [email.strip() for email in emails_text.split('\n') if email.strip()]
        email_count = len(emails)

        if action == 'add_password':
            if not password:
                flash('يرجى إدخال كلمة المرور.', 'danger')
                return redirect(url_for('email_password_tool'))
            # إضافة الباسورد إلى البريدات
            result = '\n'.join([f"{email}:{password}" for email in emails])
        elif action == 'remove_password':
            # إزالة الباسورد من البريدات
            result = '\n'.join([email.split(':')[0] for email in emails])
        else:
            flash('يرجى اختيار إجراء صحيح.', 'danger')
            return redirect(url_for('email_password_tool'))

        return render_template('email_password_tool.html', name=name, result=result,
                               emails_text=emails_text, password=password, email_count=email_count,
                               visitor_count=visitor_count)
    else:
        return render_template('email_password_tool.html', name=name, result='',
                               emails_text='', password='', email_count=0, visitor_count=visitor_count)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run()
