from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Role-based access control functions
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user']['role'] != 'admin':
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user']['role'] != 'doctor':
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def lab_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user']['role'] != 'lab':
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user']['role'] != 'patient':
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Database connection function
def get_db_connection(db_name):
    try:
        # Print current directory and full path for debugging
        import os
        current_dir = os.getcwd()
        db_path = os.path.join(current_dir, 'data', f'{db_name}.db')
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

# Fetch user info from the database
def fetch_user(email, password):
    try:
        conn = get_db_connection('users')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND status = "active"', (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            return dict(user)
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Add user to the database
def add_user(role, name, email, password, mrn=None, license=None, year=None):
    try:
        conn = get_db_connection('users')
        cursor = conn.cursor()
        hashed_password = password
        
        # Generate MRN if not provided
        if not mrn:
            if role == 'patient':
                prefix = 'MRN'
            elif role == 'doctor':
                prefix = 'DR'
            elif role == 'lab':
                prefix = 'LB'
            elif role == 'admin':
                prefix = 'ADM'
            else:
                prefix = 'USR'
            
            mrn = prefix + secrets.token_hex(4).upper()
        
        cursor.execute('''
            INSERT INTO users (role, name, email, password, license, year, mrn)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (role, name, email, hashed_password, license, year, mrn))
        
        conn.commit()
        print(f"User added: {name} - {email}")
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

@app.route('/')
def index():
    if 'user' in session:
        role = session['user']['role']
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'doctor':
            return redirect(url_for('dashboard'))
        elif role == 'lab':
            return redirect(url_for('lab_dashboard'))
        elif role == 'patient':
            return redirect(url_for('patient_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.content_type == 'application/json':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
    
    user = fetch_user(email, password)
    print(f"User found: {user is not None}")
    if user:
        session['user'] = user
        role = user['role']
        
        if role == 'admin':
            redirect_url = url_for('admin_dashboard')
        elif role == 'doctor':
            redirect_url = url_for('dashboard')
        elif role == 'lab':
            redirect_url = url_for('lab_dashboard')
        elif role == 'patient':
            redirect_url = url_for('patient_dashboard')
        else:
            redirect_url = url_for('index')
        
        if request.content_type == 'application/json':
            return jsonify({
                'success': True,
                'role': role,
                'redirect': redirect_url
            })
        return redirect(redirect_url)
    
    if request.content_type == 'application/json':
        return jsonify({'success': False, 'message': 'Invalid email or password'})
    
    flash('Invalid email or password', 'error')
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    try:
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form
        
        role = data.get('role')
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        license = data.get('license')
        registration_year = data.get('registrationYear')
        
        # Skip MRN generation - the function will generate one
        if add_user(role=role, name=name, email=email, password=password, license=license, year=registration_year):
            print('User added successfully')
            if request.content_type == 'application/json':
                return jsonify({'success': True})
            
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': 'Signup failed'})
        
        flash('Signup failed. Please try again.', 'error')
        return redirect(url_for('signup'))
    
    except Exception as e:
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': str(e)})
        
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('signup'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    doctor_name = session['user']['name']
    patients = fetch_patients_by_doctor(doctor_name)
    return render_template('doctor_dashboard.html', 
                          doctor={'name': doctor_name, 
                                  'specialty': 'Internal Medicine', 
                                  'location': 'New York, NY'},
                          patients=patients)

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', admin=session['user'])

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    conn = get_db_connection('users')
    users = conn.execute('SELECT * FROM users ORDER BY role, name').fetchall()
    conn.close()
    return render_template('admin_users.html', users=users)

@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    if request.method == 'GET':
        return render_template('admin_add_user.html')
    
    role = request.form.get('role')
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    license = request.form.get('license')
    year = request.form.get('year')
    
    if add_user(role=role, name=name, email=email, password=password, license=license, year=year):
        flash('User added successfully', 'success')
    else:
        flash('Failed to add user', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    if request.method == 'GET':
        conn = get_db_connection('users')
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('admin_users'))
        
        return render_template('admin_edit_user.html', user=user)
    
    name = request.form.get('name')
    email = request.form.get('email')
    role = request.form.get('role')
    status = request.form.get('status')
    license = request.form.get('license')
    year = request.form.get('year')
    
    conn = get_db_connection('users')
    
    # Check if password needs to be updated
    password = request.form.get('password')
    if password:
        hashed_password = generate_password_hash(password)
        conn.execute('''
            UPDATE users 
            SET name = ?, email = ?, role = ?, status = ?, license = ?, year = ?, password = ?
            WHERE id = ?
        ''', (name, email, role, status, license, year, hashed_password, user_id))
    else:
        conn.execute('''
            UPDATE users 
            SET name = ?, email = ?, role = ?, status = ?, license = ?, year = ?
            WHERE id = ?
        ''', (name, email, role, status, license, year, user_id))
    
    conn.commit()
    conn.close()
    
    flash('User updated successfully', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def admin_delete_user(user_id):
    conn = get_db_connection('users')
    conn.execute('UPDATE users SET status = "inactive" WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    flash('User has been deactivated', 'success')
    return redirect(url_for('admin_users'))

@app.route('/lab/dashboard')
@login_required
@lab_required
def lab_dashboard():
    # Get all patients for lab tests
    conn = get_db_connection('patients')
    patients = conn.execute('SELECT * FROM patients ORDER BY name').fetchall()
    conn.close()
    
    return render_template('lab_dashboard.html', 
                         lab_tech=session['user'],
                         patients=patients)

@app.route('/lab/patient/<mrn>')
@login_required
@lab_required
def lab_patient(mrn):
    patient_info = fetch_patient_info(mrn)
    lab_results_data = fetch_lab_results_data(mrn)
    
    return render_template('lab_patient.html',
                         patient_info=patient_info,
                         lab_results=lab_results_data,
                         lab_tech=session['user'])

@app.route('/lab/add_result', methods=['POST'])
@login_required
@lab_required
def add_lab_result():
    mrn = request.form.get('mrn')
    test = request.form.get('test')
    result = request.form.get('result')
    reference = request.form.get('reference')
    status = request.form.get('status')
    ordering_provider = request.form.get('ordering_provider')
    lab = request.form.get('lab')
    date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    created_by = session['user']['name']
    
    try:
        conn = get_db_connection('labs')
        conn.execute('''
            INSERT INTO labs (mrn, date, test, result, reference, status, ordering_provider, lab, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (mrn, date, test, result, reference, status, ordering_provider, lab, created_by))
        conn.commit()
        
        # Add to timeline
        timeline_conn = get_db_connection('timeline')
        timeline_conn.execute('''
            INSERT INTO timeline (mrn, date, event, details, provider, system)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (mrn, date, f"Lab Test: {test}", f"Result: {result} - {status}", created_by, "Laboratory"))
        timeline_conn.commit()
        timeline_conn.close()
        
        flash('Lab result added successfully', 'success')
        return redirect(url_for('lab_patient', mrn=mrn))
    except sqlite3.Error as e:
        flash(f'Error adding lab result: {str(e)}', 'error')
        return redirect(url_for('lab_patient', mrn=mrn))

@app.route('/patient/dashboard')
@login_required
@patient_required
def patient_dashboard():
    patient_mrn = session['user']['mrn']
    patient_info = fetch_patient_info(patient_mrn)
    timeline_data = fetch_timeline_data(patient_mrn)
    vitals_data = fetch_vitals_data(patient_mrn)
    medications_data = fetch_medications_data(patient_mrn)
    lab_results_data = fetch_lab_results_data(patient_mrn)
    
    return render_template('patient_view.html',
                          patient_info=patient_info,
                          timeline_data=timeline_data,
                          vitals_data=vitals_data, 
                          medications_data=medications_data,
                          lab_results_data=lab_results_data)

# Doctor routes for prescribing medications
@app.route('/prescribe/<mrn>', methods=['GET', 'POST'])
@login_required
@doctor_required
def prescribe_medication(mrn):
    if request.method == 'GET':
        patient_info = fetch_patient_info(mrn)
        return render_template('prescribe.html', patient=patient_info)
    
    name = request.form.get('medication')
    dosage = request.form.get('dosage')
    frequency = request.form.get('frequency')
    refills = request.form.get('refills', 0)
    pharmacy = request.form.get('pharmacy')
    notes = request.form.get('notes', '')
    prescriber = session['user']['name']
    prescribed_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        conn = get_db_connection('medications')
        conn.execute('''
            INSERT INTO medications (mrn, name, dosage, frequency, status, prescribed, prescriber, refills, pharmacy, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (mrn, name, dosage, frequency, 'Active', prescribed_date, prescriber, refills, pharmacy, notes))
        conn.commit()
        conn.close()
        
        # Add to timeline
        timeline_conn = get_db_connection('timeline')
        timeline_conn.execute('''
            INSERT INTO timeline (mrn, date, event, details, provider, system)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (mrn, prescribed_date, "Medication Prescribed", f"{name} {dosage} - {frequency}", prescriber, "EHR"))
        timeline_conn.commit()
        timeline_conn.close()
        
        flash('Medication prescribed successfully', 'success')
        return redirect(url_for('patient', mrn=mrn))
    except sqlite3.Error as e:
        flash(f'Error prescribing medication: {str(e)}', 'error')
        return redirect(url_for('prescribe_medication', mrn=mrn))

# Doctor routes for adding vitals
@app.route('/add_vitals/<mrn>', methods=['GET', 'POST'])
@login_required
@doctor_required
def add_vitals(mrn):
    if request.method == 'GET':
        patient_info = fetch_patient_info(mrn)
        return render_template('add_vitals.html', patient=patient_info)
    
    bp = request.form.get('bp')
    pulse = request.form.get('pulse')
    temp = request.form.get('temp')
    weight = request.form.get('weight')
    glucose = request.form.get('glucose')
    date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    created_by = session['user']['name']
    
    try:
        conn = get_db_connection('vitals')
        conn.execute('''
            INSERT INTO vitals (mrn, date, bp, pulse, temp, weight, glucose, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (mrn, date, bp, pulse, temp, weight, glucose, created_by))
        conn.commit()
        conn.close()
        
        # Add to timeline
        timeline_conn = get_db_connection('timeline')
        timeline_conn.execute('''
            INSERT INTO timeline (mrn, date, event, details, provider, system)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (mrn, date, "Vitals Recorded", f"BP: {bp}, Pulse: {pulse}, Temp: {temp}°F", created_by, "EHR"))
        timeline_conn.commit()
        timeline_conn.close()
        
        flash('Vitals added successfully', 'success')
        return redirect(url_for('patient', mrn=mrn))
    except sqlite3.Error as e:
        flash(f'Error adding vitals: {str(e)}', 'error')
        return redirect(url_for('add_vitals', mrn=mrn))

# Fetch patient info from the database
def fetch_patient_info(mrn):
    conn = get_db_connection('patients')
    patient = conn.execute('SELECT * FROM patients WHERE mrn = ?', (mrn,)).fetchone()
    conn.close()
    if patient:
        patient_dict = {key: patient[key] for key in patient.keys()}
        return patient_dict
    return None

# Fetch timeline data from the database
def fetch_timeline_data(mrn):
    conn = get_db_connection('timeline')
    timeline = conn.execute('SELECT * FROM timeline WHERE mrn = ? ORDER BY date DESC', (mrn,)).fetchall()
    conn.close()
    return [dict(row) for row in timeline]

# Fetch vitals data from the database
def fetch_vitals_data(mrn):
    conn = get_db_connection('vitals')
    vitals = conn.execute('SELECT * FROM vitals WHERE mrn = ? ORDER BY date DESC', (mrn,)).fetchall()
    conn.close()
    return [dict(row) for row in vitals]

# Fetch medications data from the database
def fetch_medications_data(mrn):
    conn = get_db_connection('medications')
    medications = conn.execute('SELECT * FROM medications WHERE mrn = ? ORDER BY prescribed DESC', (mrn,)).fetchall()
    conn.close()
    return [dict(row) for row in medications]

# Fetch lab results data from the database
def fetch_lab_results_data(mrn):
    conn = get_db_connection('labs')
    labs = conn.execute('SELECT * FROM labs WHERE mrn = ? ORDER BY date DESC', (mrn,)).fetchall()
    conn.close()
    return [dict(row) for row in labs]

# Fetch imaging data from the database
def fetch_imaging_data(mrn):
    conn = get_db_connection('imaging')
    imaging = conn.execute('SELECT * FROM imaging WHERE mrn = ? ORDER BY date DESC', (mrn,)).fetchall()
    conn.close()
    return [dict(row) for row in imaging]

# Fetch patients by doctor from the database
def fetch_patients_by_doctor(doctor_name):
    conn = get_db_connection('patients')
    patients = conn.execute('SELECT * FROM patients WHERE primaryCare = ?', (doctor_name,)).fetchall()
    patients = [dict(row) for row in patients]
    conn.close()
    return patients

@app.route('/patient/<mrn>')
@login_required
def patient(mrn):
    # Check permissions
    if 'user' in session:
        user_role = session['user']['role']
        if user_role == 'patient' and session['user']['mrn'] != mrn:
            flash('You do not have permission to view this patient record', 'error')
            return redirect(url_for('index'))
    
    patient_info = fetch_patient_info(mrn)
    timeline_data = fetch_timeline_data(mrn)
    vitals_data = fetch_vitals_data(mrn)
    medications_data = fetch_medications_data(mrn)
    lab_results_data = fetch_lab_results_data(mrn)
    imaging_data = fetch_imaging_data(mrn)
    systems = ['all', 'EHR', 'Pharmacy', 'Laboratory', 'Hospital', 'Specialist', 'Radiology']
    
    return render_template('doctor_patient.html', 
                          patient_info=patient_info, 
                          timeline_data=timeline_data,
                          vitals_data=vitals_data,
                          medications_data=medications_data,
                          lab_results_data=lab_results_data,
                          imaging_data=imaging_data,
                          systems=systems)

@app.route('/api/timeline')
@login_required
def get_timeline():
    mrn = request.args.get('mrn')
    
    # Check permissions
    if 'user' in session:
        user_role = session['user']['role']
        if user_role == 'patient' and session['user']['mrn'] != mrn:
            return jsonify({"error": "Permission denied"}), 403
    
    system = request.args.get('system', 'all')
    timeline_data = fetch_timeline_data(mrn)
    
    if system == 'all':
        return jsonify(timeline_data)
    else:
        filtered_data = [item for item in timeline_data if item['system'] == system]
        return jsonify(filtered_data)

@app.route('/api/patient/<mrn>')
@login_required
def get_patient(mrn):
    # Check permissions
    if 'user' in session:
        user_role = session['user']['role']
        if user_role == 'patient' and session['user']['mrn'] != mrn:
            return jsonify({"error": "Permission denied"}), 403
    
    patient_info = fetch_patient_info(mrn)
    if patient_info:
        return jsonify(patient_info)
    else:
        return jsonify({"error": "Patient not found"}), 404

@app.route('/api/medications')
@login_required
def get_medications():
    mrn = request.args.get('mrn')
    
    # Check permissions
    if 'user' in session:
        user_role = session['user']['role']
        if user_role == 'patient' and session['user']['mrn'] != mrn:
            return jsonify({"error": "Permission denied"}), 403
    
    medications_data = fetch_medications_data(mrn)
    return jsonify(medications_data)

@app.route('/api/labs')
@login_required
def get_labs():
    mrn = request.args.get('mrn')
    
    # Check permissions
    if 'user' in session:
        user_role = session['user']['role']
        if user_role == 'patient' and session['user']['mrn'] != mrn:
            return jsonify({"error": "Permission denied"}), 403
    
    lab_results_data = fetch_lab_results_data(mrn)
    return jsonify(lab_results_data)

@app.route('/api/imaging')
@login_required
def get_imaging():
    mrn = request.args.get('mrn')
    
    # Check permissions
    if 'user' in session:
        user_role = session['user']['role']
        if user_role == 'patient' and session['user']['mrn'] != mrn:
            return jsonify({"error": "Permission denied"}), 403
    
    imaging_data = fetch_imaging_data(mrn)
    return jsonify(imaging_data)

@app.route('/api/vitals')
@login_required
def get_vitals():
    mrn = request.args.get('mrn')
    
    # Check permissions
    if 'user' in session:
        user_role = session['user']['role']
        if user_role == 'patient' and session['user']['mrn'] != mrn:
            return jsonify({"error": "Permission denied"}), 403
    
    vitals_data = fetch_vitals_data(mrn)
    return jsonify(vitals_data)

@app.route('/api/patients/<doctor_name>')
@login_required
@doctor_required
def get_patients_by_doctor(doctor_name):
    patients_data = fetch_patients_by_doctor(doctor_name)
    return jsonify(patients_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
