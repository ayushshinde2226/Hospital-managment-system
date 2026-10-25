PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS vitals;
DROP TABLE IF EXISTS prescription_items;
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS lab_tests;
DROP TABLE IF EXISTS bills;
DROP TABLE IF EXISTS admissions;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS medicines;
DROP TABLE IF EXISTS blood_donors;
DROP TABLE IF EXISTS blood_bank;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS users;

CREATE TABLE users(
 user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
 full_name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN('Admin','Staff')), department TEXT,
 is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE departments(
 department_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, floor TEXT, head_name TEXT,
 phone TEXT, status TEXT DEFAULT 'Active'
);

CREATE TABLE doctors(
 doctor_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, specialization TEXT, department_id INTEGER,
 phone TEXT,email TEXT,license_no TEXT,consultation_fee REAL DEFAULT 0,
 available_days TEXT,available_time TEXT,status TEXT DEFAULT 'Active',
 FOREIGN KEY(department_id) REFERENCES departments(department_id)
);

CREATE TABLE patients(
 patient_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 dob TEXT, age INTEGER NOT NULL, gender TEXT NOT NULL, blood_group TEXT, phone TEXT,email TEXT,address TEXT,
 emergency_contact TEXT,allergies TEXT,primary_doctor_id INTEGER,insurance_provider TEXT,
 status TEXT DEFAULT 'Active',created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(primary_doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE appointments(
 appointment_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL,doctor_id INTEGER NOT NULL,
 appointment_date TEXT NOT NULL,appointment_time TEXT NOT NULL,reason TEXT,status TEXT DEFAULT 'Scheduled',
 priority TEXT DEFAULT 'Normal',notes TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
 FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
);

CREATE TABLE rooms(
 room_id INTEGER PRIMARY KEY AUTOINCREMENT,ward TEXT NOT NULL,room_no TEXT UNIQUE NOT NULL,
 room_type TEXT,capacity INTEGER DEFAULT 1,daily_charge REAL DEFAULT 0,status TEXT DEFAULT 'Available'
);

CREATE TABLE admissions(
 admission_id INTEGER PRIMARY KEY AUTOINCREMENT,patient_id INTEGER NOT NULL,room_id INTEGER NOT NULL,
 bed_no TEXT,admission_date TEXT NOT NULL,expected_discharge TEXT,discharge_date TEXT,
 attending_doctor_id INTEGER,diagnosis TEXT,status TEXT DEFAULT 'Admitted',notes TEXT,
 FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
 FOREIGN KEY(room_id) REFERENCES rooms(room_id), FOREIGN KEY(attending_doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE medicines(
 medicine_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,category TEXT,quantity INTEGER DEFAULT 0,
 unit_price REAL DEFAULT 0,manufacturer TEXT,batch_no TEXT,expiry_date TEXT,reorder_level INTEGER DEFAULT 10,
 status TEXT DEFAULT 'Active'
);

CREATE TABLE prescriptions(
 prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,patient_id INTEGER NOT NULL,doctor_id INTEGER NOT NULL,
 prescription_date TEXT NOT NULL,diagnosis TEXT,instructions TEXT,status TEXT DEFAULT 'Active',
 FOREIGN KEY(patient_id) REFERENCES patients(patient_id),FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE prescription_items(
 item_id INTEGER PRIMARY KEY AUTOINCREMENT,prescription_id INTEGER NOT NULL,medicine_id INTEGER NOT NULL,
 dosage TEXT,duration_days INTEGER,quantity INTEGER,
 FOREIGN KEY(prescription_id) REFERENCES prescriptions(prescription_id) ON DELETE CASCADE,
 FOREIGN KEY(medicine_id) REFERENCES medicines(medicine_id)
);

CREATE TABLE lab_tests(
 lab_id INTEGER PRIMARY KEY AUTOINCREMENT,patient_id INTEGER NOT NULL,doctor_id INTEGER,test_name TEXT NOT NULL,
 test_category TEXT,test_date TEXT NOT NULL,result_value TEXT,unit TEXT,reference_range TEXT,
 result_status TEXT DEFAULT 'Pending',remarks TEXT,
 FOREIGN KEY(patient_id) REFERENCES patients(patient_id),FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE bills(
 bill_id INTEGER PRIMARY KEY AUTOINCREMENT,patient_id INTEGER NOT NULL,bill_date TEXT NOT NULL,
 consultation_charge REAL DEFAULT 0,room_charge REAL DEFAULT 0,medicine_charge REAL DEFAULT 0,
 lab_charge REAL DEFAULT 0,other_charge REAL DEFAULT 0,discount REAL DEFAULT 0,total_amount REAL DEFAULT 0,
 payment_status TEXT DEFAULT 'Pending',payment_method TEXT,payment_date TEXT,notes TEXT,
 FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

CREATE TABLE blood_bank(
 blood_id INTEGER PRIMARY KEY AUTOINCREMENT,blood_group TEXT UNIQUE NOT NULL,units_available INTEGER DEFAULT 0,
 last_updated TEXT DEFAULT CURRENT_TIMESTAMP,status TEXT DEFAULT 'Normal'
);

CREATE TABLE blood_donors(
 donor_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,blood_group TEXT NOT NULL,phone TEXT,
 donation_date TEXT NOT NULL,units INTEGER DEFAULT 1,screening_status TEXT
);

CREATE TABLE staff(
 staff_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,designation TEXT NOT NULL,department TEXT,
 phone TEXT,email TEXT,shift TEXT,status TEXT DEFAULT 'Active'
);

CREATE TABLE vitals(
 vital_id INTEGER PRIMARY KEY AUTOINCREMENT,patient_id INTEGER NOT NULL,bp TEXT,heart_rate INTEGER,
 temperature REAL,spo2 INTEGER,weight REAL,height REAL,notes TEXT,measured_by TEXT,measured_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

CREATE TABLE audit_logs(
 log_id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,action TEXT,entity TEXT,entity_id INTEGER,
 details TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_patients_phone ON patients(phone);
CREATE INDEX idx_patients_code ON patients(patient_code);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX idx_admissions_status ON admissions(status);
CREATE INDEX idx_bills_status ON bills(payment_status);
CREATE INDEX idx_lab_status ON lab_tests(result_status);
CREATE INDEX idx_audit_date ON audit_logs(created_at);

INSERT INTO users(username,password,full_name,role,department) VALUES
('admin','admin123','Hospital Administrator','Admin','Administration'),
('staff','staff123','Front Desk Staff','Staff','Reception'),
('pharmacy','pharma123','Pharmacy Staff','Staff','Pharmacy');

INSERT INTO departments(name,floor,head_name,phone) VALUES
('Cardiology','1','Dr. Anil Mehta','022-40001001'),('Dermatology','2','Dr. Neha Joshi','022-40001002'),
('General Medicine','1','Dr. Rohan Desai','022-40001003'),('Pediatrics','3','Dr. Pooja Shah','022-40001004'),
('Pathology','B1','Dr. Kavita Rao','022-40001005'),('Emergency','Ground','Dr. Sameer Kulkarni','022-40001006');

INSERT INTO doctors(name,specialization,department_id,phone,email,license_no,consultation_fee,available_days,available_time) VALUES
('Dr. Anil Mehta','Cardiologist',1,'9000000001','anil@medicore.local','MC-10001',800,'Mon,Wed,Fri','10:00 - 14:00'),
('Dr. Neha Joshi','Dermatologist',2,'9000000002','neha@medicore.local','MC-10002',600,'Tue,Thu,Sat','11:00 - 15:00'),
('Dr. Rohan Desai','General Physician',3,'9000000003','rohan@medicore.local','MC-10003',400,'Mon-Sat','09:00 - 13:00'),
('Dr. Pooja Shah','Pediatrician',4,'9000000004','pooja@medicore.local','MC-10004',500,'Mon,Tue,Thu','14:00 - 18:00'),
('Dr. Kavita Rao','Pathologist',5,'9000000005','kavita@medicore.local','MC-10005',300,'Mon-Sat','08:00 - 16:00');

INSERT INTO patients(patient_code,name,dob,age,gender,blood_group,phone,email,address,emergency_contact,allergies,primary_doctor_id,insurance_provider) VALUES
('P00001','Rahul Sharma','1994-06-14',32,'Male','B+','9876543210','rahul@example.com','Mumbai, Maharashtra','9876500001','None',1,'Star Health'),
('P00002','Priya Patil','1999-02-20',27,'Female','O+','9876543211','priya@example.com','Palghar, Maharashtra','9876500002','Dust',2,'HDFC Ergo'),
('P00003','Amit Kulkarni','1981-11-05',45,'Male','A+','9876543212','amit@example.com','Thane, Maharashtra','9876500003','Penicillin',3,'ICICI Lombard'),
('P00004','Sneha More','2004-08-12',21,'Female','AB+','9876543213','sneha@example.com','Vasai, Maharashtra','9876500004','None',4,''),
('P00005','Vikram Singh','1979-04-27',47,'Male','O-','9876543214','vikram@example.com','Navi Mumbai','9876500005','None',3,'Star Health');

INSERT INTO rooms(ward,room_no,room_type,capacity,daily_charge,status) VALUES
('General Ward','G-101','General',4,1200,'Available'),('General Ward','G-102','General',4,1200,'Available'),
('Private','P-201','Private',1,3500,'Available'),('Private','P-202','Private',1,3500,'Available'),
('ICU','ICU-01','ICU',1,8000,'Available'),('Emergency','ER-01','Emergency',2,2500,'Available');

INSERT INTO medicines(name,category,quantity,unit_price,manufacturer,batch_no,expiry_date,reorder_level,status) VALUES
('Paracetamol 500mg','Tablet',100,2.50,'ABC Pharma','P500-01',date('now','localtime','+18 months'),20,'Active'),
('Amoxicillin 500mg','Capsule',50,7.00,'MediCare','AMX-22',date('now','localtime','+14 months'),15,'Active'),
('Cetirizine 10mg','Tablet',8,3.00,'HealthPlus','CTZ-09',date('now','localtime','+9 months'),10,'Active'),
('ORS Sachet','Powder',40,12.00,'Wellness Labs','ORS-30',date('now','localtime','+12 months'),10,'Active'),
('Atorvastatin 10mg','Tablet',35,5.50,'CardioMed','ATV-11',date('now','localtime','+16 months'),10,'Active');

INSERT INTO blood_bank(blood_group,units_available) VALUES
('A+',12),('A-',4),('B+',9),('B-',3),('AB+',2),('AB-',1),('O+',15),('O-',5);

INSERT INTO staff(name,designation,department,phone,email,shift) VALUES
('Meena Joshi','Senior Nurse','Nursing','9000010001','meena@medicore.local','Day'),
('Rakesh Yadav','Lab Technician','Pathology','9000010002','rakesh@medicore.local','Day'),
('Asha Pawar','Receptionist','Reception','9000010003','asha@medicore.local','Evening'),
('Kunal Shah','Pharmacist','Pharmacy','9000010004','kunal@medicore.local','Day');

INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason,status,priority,notes) VALUES
(1,1,date('now','localtime'),'10:30','Cardiac consultation','Scheduled','High','Bring previous ECG'),
(2,2,date('now','localtime'),'12:00','Skin consultation','Scheduled','Normal',''),
(3,3,date('now','localtime','-1 day'),'11:00','Fever and weakness','Completed','Normal','Follow-up in 7 days'),
(4,4,date('now','localtime','+2 day'),'15:30','General check-up','Scheduled','Normal','');

INSERT INTO admissions(patient_id,room_id,bed_no,admission_date,expected_discharge,attending_doctor_id,diagnosis,status) VALUES
(3,1,'B-2',date('now','localtime'),date('now','localtime','+3 day'),3,'Viral fever','Admitted');

INSERT INTO prescriptions(patient_id,doctor_id,prescription_date,diagnosis,instructions) VALUES
(3,3,date('now','localtime'),'Viral fever','Take medicines after food and rest.');

INSERT INTO prescription_items(prescription_id,medicine_id,dosage,duration_days,quantity) VALUES
(1,1,'1 tablet twice daily',5,10),(1,4,'1 sachet as required',3,6);

INSERT INTO lab_tests(patient_id,doctor_id,test_name,test_category,test_date,result_value,unit,reference_range,result_status,remarks) VALUES
(3,5,'CBC','Hematology',date('now','localtime','-1 day'),'12.4','g/dL','13-17','Pending','Awaiting platelet result'),
(1,5,'Lipid Profile','Biochemistry',date('now','localtime','-5 day'),'185','mg/dL','<200','Normal','');

INSERT INTO bills(patient_id,bill_date,consultation_charge,room_charge,medicine_charge,lab_charge,other_charge,discount,total_amount,payment_status,payment_method,payment_date,notes)
VALUES
(1,date('now','localtime'),800,0,150,0,50,0,1000,'Paid','UPI',date('now','localtime'),'OPD consultation'),
(3,date('now','localtime'),400,1200,350,500,0,0,2450,'Pending','Cash',NULL,'Admission package');

INSERT INTO vitals(patient_id,bp,heart_rate,temperature,spo2,weight,height,notes,measured_by) VALUES
(1,'128/82',76,98.4,98,68,174,'Stable','Meena Joshi'),
(3,'136/88',92,100.8,96,72,171,'Fever noted','Meena Joshi');
