import sqlite3
import os
from werkzeug.security import generate_password_hash
import secrets

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Function to initialize databases
def initialize_database(db_name, schema):
    conn = sqlite3.connect(os.path.join('data', f'{db_name}.db'))
    cursor = conn.cursor()
    
    # Execute all schema statements
    for statement in schema:
        cursor.execute(statement)
    
    conn.commit()
    conn.close()
    print(f"Database {db_name}.db initialized successfully")

# Define schemas for each database
users_schema = [
    '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        license TEXT,
        year INTEGER,
        mrn TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    '''
]

patients_schema = [
    '''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mrn TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        dob TEXT NOT NULL,
        gender TEXT NOT NULL,
        primaryCare TEXT NOT NULL,
        insurance TEXT,
        allergies TEXT,
        chronicConditions TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    '''
]

timeline_schema = [
    '''
    CREATE TABLE IF NOT EXISTS timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mrn TEXT NOT NULL,
        date TEXT NOT NULL,
        event TEXT NOT NULL,
        details TEXT,
        provider TEXT,
        system TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mrn) REFERENCES patients(mrn)
    )
    '''
]

vitals_schema = [
    '''
    CREATE TABLE IF NOT EXISTS vitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mrn TEXT NOT NULL,
        date TEXT NOT NULL,
        bp TEXT,
        pulse INTEGER,
        temp REAL,
        weight REAL,
        glucose INTEGER,
        created_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mrn) REFERENCES patients(mrn)
    )
    '''
]

medications_schema = [
    '''
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mrn TEXT NOT NULL,
        name TEXT NOT NULL,
        dosage TEXT NOT NULL,
        frequency TEXT NOT NULL,
        status TEXT DEFAULT 'Active',
        prescribed TEXT NOT NULL,
        prescriber TEXT NOT NULL,
        refills INTEGER DEFAULT 0,
        pharmacy TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mrn) REFERENCES patients(mrn)
    )
    '''
]

labs_schema = [
    '''
    CREATE TABLE IF NOT EXISTS labs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mrn TEXT NOT NULL,
        date TEXT NOT NULL,
        test TEXT NOT NULL,
        result TEXT NOT NULL,
        reference TEXT,
        status TEXT,
        ordering_provider TEXT,
        lab TEXT,
        created_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mrn) REFERENCES patients(mrn)
    )
    '''
]

imaging_schema = [
    '''
    CREATE TABLE IF NOT EXISTS imaging (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mrn TEXT NOT NULL,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        result TEXT NOT NULL,
        reason TEXT,
        radiologist TEXT,
        facility TEXT,
        notes TEXT,
        comparison TEXT,
        created_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mrn) REFERENCES patients(mrn)
    )
    '''
]

# Initialize all databases
databases = {
    'users': users_schema,
    'patients': patients_schema,
    'timeline': timeline_schema,
    'vitals': vitals_schema,
    'medications': medications_schema,
    'labs': labs_schema,
    'imaging': imaging_schema
}

for db_name, schema in databases.items():
    initialize_database(db_name, schema)

# Add sample users
def add_sample_users():
    conn = sqlite3.connect(os.path.join('data', 'users.db'))
    cursor = conn.cursor()
    
    # Admin user
    cursor.execute('''
        INSERT OR IGNORE INTO users (role, name, email, password, mrn)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin', 'Rajesh Kumar', 'admin@healthbridge.com', 
          generate_password_hash('admin123'), 'ADMIN' + secrets.token_hex(4).upper()))
    
    # Doctor users
    doctors = [
        ('doctor', 'Dr. Nishant Pratap', 'nishant.pratap@healthbridge.com', 'doc123', 'MC12345', 2015),
        ('doctor', 'Dr. Priya Patel', 'priya.patel@healthbridge.com', 'doc123', 'MC67890', 2018)
    ]
    
    for doctor in doctors:
        cursor.execute('''
            INSERT OR IGNORE INTO users (role, name, email, password, license, year, mrn)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (doctor[0], doctor[1], doctor[2], generate_password_hash(doctor[3]), 
              doctor[4], doctor[5], 'DR' + secrets.token_hex(4).upper()))
    
    # Lab technician users
    lab_techs = [
        ('lab', 'Ansh Arora', 'ansh.arora@healthbridge.com', 'lab123', 'LT54321'),
        ('lab', 'Divya Singh', 'divya.singh@healthbridge.com', 'lab123', 'LT98765')
    ]
    
    for tech in lab_techs:
        cursor.execute('''
            INSERT OR IGNORE INTO users (role, name, email, password, license, mrn)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tech[0], tech[1], tech[2], generate_password_hash(tech[3]), 
              tech[4], 'LB' + secrets.token_hex(4).upper()))
    
    # Patient users
    patients = [
        ('patient', 'Rohan Kardam', 'rohan.kardam@example.com', 'pat123', 'MRN12345'),
        ('patient', 'Aisha Khan', 'aisha.khan@example.com', 'pat123', 'MRN67890'),
        ('patient', 'Punit Sharma', 'punit.sharma@example.com', 'pat123', 'MRN24680'),
        ('patient', 'Meera Joshi', 'meera.joshi@example.com', 'pat123', 'MRN13579')
    ]
    
    for patient in patients:
        cursor.execute('''
            INSERT OR IGNORE INTO users (role, name, email, password, mrn)
            VALUES (?, ?, ?, ?, ?)
        ''', (patient[0], patient[1], patient[2], generate_password_hash(patient[3]), patient[4]))
    
    conn.commit()
    conn.close()
    print("Sample users added successfully")

# Add sample patient data
def add_sample_patients():
    conn = sqlite3.connect(os.path.join('data', 'patients.db'))
    cursor = conn.cursor()
    
    patients = [
        ('MRN12345', 'Rohan Kardam', '1992-05-15', 'Male', 'Dr. Nishant Pratap', 'Bajaj Allianz', 'Penicillin', 'Hypertension, Type 2 Diabetes'),
        ('MRN67890', 'Aisha Khan', '1995-11-23', 'Female', 'Dr. Priya Patel', 'ICICI Lombard', 'None', 'Asthma'),
        ('MRN24680', 'Punit Sharma', '1985-03-08', 'Male', 'Dr. Nishant Pratap', 'Star Health', 'Sulfa Drugs', 'COPD'),
        ('MRN13579', 'Meera Joshi', '1990-07-30', 'Female', 'Dr. Priya Patel', 'Apollo Munich', 'Latex', 'Anxiety')
    ]
    
    for patient in patients:
        cursor.execute('''
            INSERT OR IGNORE INTO patients (mrn, name, dob, gender, primaryCare, insurance, allergies, chronicConditions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', patient)
    
    conn.commit()
    conn.close()
    print("Sample patients added successfully")

# Add sample timeline data
def add_sample_timeline():
    conn = sqlite3.connect(os.path.join('data', 'timeline.db'))
    cursor = conn.cursor()
    
    timeline_data = [
        ('MRN12345', '2024-02-15', 'Annual Checkup', 'Routine physical examination', 'Dr. Nishant Pratap', 'EHR'),
        ('MRN12345', '2024-02-16', 'Prescription Filled', 'Metformin 500mg #30', 'Apollo Pharmacy', 'Pharmacy'),
        ('MRN12345', '2024-02-20', 'Lab Results', 'Comprehensive Metabolic Panel', 'Thyrocare', 'Laboratory'),
        ('MRN67890', '2024-01-10', 'Specialist Consult', 'Pulmonology evaluation', 'Dr. Sanjay Gupta', 'Specialist'),
        ('MRN67890', '2024-01-15', 'Chest X-ray', 'For asthma evaluation', 'Metropolis Radiology', 'Radiology'),
        ('MRN67890', '2024-01-20', 'Prescription Refill', 'Asthalin inhaler', 'Dr. Priya Patel', 'EHR')
    ]
    
    for item in timeline_data:
        cursor.execute('''
            INSERT INTO timeline (mrn, date, event, details, provider, system)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', item)
    
    conn.commit()
    conn.close()
    print("Sample timeline data added successfully")

# Add sample vitals data
def add_sample_vitals():
    conn = sqlite3.connect(os.path.join('data', 'vitals.db'))
    cursor = conn.cursor()
    
    vitals_data = [
        ('MRN12345', '2024-02-15', '130/85', 75, 98.6, 75.5, 128, 'Dr. Nishant Pratap'),
        ('MRN12345', '2024-01-12', '135/88', 78, 98.2, 76.0, 135, 'Nurse Ritu'),
        ('MRN67890', '2024-01-10', '118/75', 82, 98.8, 65.3, 95, 'Dr. Priya Patel'),
        ('MRN67890', '2023-12-05', '120/80', 80, 98.4, 64.1, 92, 'Nurse Amit')
    ]
    
    for vital in vitals_data:
        cursor.execute('''
            INSERT INTO vitals (mrn, date, bp, pulse, temp, weight, glucose, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', vital)
    
    conn.commit()
    conn.close()
    print("Sample vitals data added successfully")

# Add sample medications data
def add_sample_medications():
    conn = sqlite3.connect(os.path.join('data', 'medications.db'))
    cursor = conn.cursor()
    
    medications_data = [
        ('MRN12345', 'Metformin', '500mg', 'Twice daily', 'Active', '2024-01-15', 'Dr. Nishant Pratap', 3, 'Apollo Pharmacy', 'Take with meals'),
        ('MRN12345', 'Telmisartan', '40mg', 'Once daily', 'Active', '2024-01-15', 'Dr. Nishant Pratap', 5, 'Apollo Pharmacy', ''),
        ('MRN67890', 'Asthalin', '100mcg', 'As needed', 'Active', '2024-01-10', 'Dr. Priya Patel', 2, 'MedPlus', 'Use for asthma attacks'),
        ('MRN67890', 'Flixonase', '50mcg', 'Once daily', 'Active', '2024-01-10', 'Dr. Priya Patel', 1, 'MedPlus', 'Use in the morning')
    ]
    
    for med in medications_data:
        cursor.execute('''
            INSERT INTO medications (mrn, name, dosage, frequency, status, prescribed, prescriber, refills, pharmacy, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', med)
    
    conn.commit()
    conn.close()
    print("Sample medications data added successfully")

# Add sample lab data
def add_sample_labs():
    conn = sqlite3.connect(os.path.join('data', 'labs.db'))
    cursor = conn.cursor()
    
    labs_data = [
        ('MRN12345', '2024-02-20', 'HbA1c', '7.1%', '4.0-5.6%', 'Abnormal', 'Dr. Nishant Pratap', 'Thyrocare', 'Ansh Arora'),
        ('MRN12345', '2024-02-20', 'Cholesterol', '210 mg/dL', '<200 mg/dL', 'Abnormal', 'Dr. Nishant Pratap', 'Thyrocare', 'Ansh Arora'),
        ('MRN12345', '2024-02-20', 'HDL', '45 mg/dL', '>40 mg/dL', 'Normal', 'Dr. Nishant Pratap', 'Thyrocare', 'Ansh Arora'),
        ('MRN67890', '2024-01-12', 'CBC', 'WBC 7.5 K/uL', '4.5-11.0 K/uL', 'Normal', 'Dr. Priya Patel', 'SRL Diagnostics', 'Divya Singh'),
        ('MRN67890', '2024-01-12', 'CRP', '0.8 mg/L', '<1.0 mg/L', 'Normal', 'Dr. Priya Patel', 'SRL Diagnostics', 'Divya Singh')
    ]
    
    for lab in labs_data:
        cursor.execute('''
            INSERT INTO labs (mrn, date, test, result, reference, status, ordering_provider, lab, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', lab)
    
    conn.commit()
    conn.close()
    print("Sample lab data added successfully")

# Add sample imaging data
def add_sample_imaging():
    conn = sqlite3.connect(os.path.join('data', 'imaging.db'))
    cursor = conn.cursor()
    
    imaging_data = [
        ('MRN12345', '2024-01-25', 'Chest X-ray', 'Normal', 'Annual screening', 'Dr. Rahul Malhotra', 'Metropolis Radiology', 'No abnormalities detected', 'None', 'Dr. Rahul Malhotra'),
        ('MRN67890', '2024-01-15', 'Chest X-ray', 'Abnormal', 'Asthma evaluation', 'Dr. Sunita Rao', 'Metropolis Radiology', 'Mild hyperinflation consistent with asthma', 'Previous study from 2023-07-20', 'Dr. Sunita Rao')
    ]
    
    for img in imaging_data:
        cursor.execute('''
            INSERT INTO imaging (mrn, date, type, result, reason, radiologist, facility, notes, comparison, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', img)
    
    conn.commit()
    conn.close()
    print("Sample imaging data added successfully")

# Run sample data functions
add_sample_users()
add_sample_patients()
add_sample_timeline()
add_sample_vitals()
add_sample_medications()
add_sample_labs()
add_sample_imaging()

print("All database initialization and sample data creation complete!")