# Data Dictionary

## patients
patient_id PK, patient_code unique identifier, demographic/contact/clinical fields, primary_doctor_id FK.

## doctors
doctor_id PK, specialist information, department_id FK, license, fee and availability.

## appointments
appointment_id PK, patient_id FK, doctor_id FK, date/time, priority and status.

## admissions
admission_id PK, patient_id FK, room_id FK, attending doctor FK, dates, diagnosis and status.

## rooms
room_id PK, ward, unique room number, type, capacity and daily charge.

## prescriptions
prescription_id PK, patient/doctor FKs, date, diagnosis and instructions.

## prescription_items
item_id PK, prescription_id FK, medicine_id FK, dosage, days and quantity.

## lab_tests
lab_id PK, patient/doctor FKs, test/result/reference/status.

## bills
bill_id PK, patient FK, component charges, discount, total and payment fields.

## medicines
medicine_id PK, quantity, price, batch, expiry and reorder level.

## vitals
vital_id PK, patient FK, blood pressure, heart rate, temperature, SpO2, weight and height.

## audit_logs
log_id PK, user FK, action, entity and timestamp.
