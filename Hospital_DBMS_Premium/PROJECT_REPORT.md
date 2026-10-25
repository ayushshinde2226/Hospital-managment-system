# MEDICORE HOSPITAL SUITE
## Hospital Database Management System — Project Report

### Abstract
MediCore Hospital Suite is a web-based Hospital Database Management System developed using Python, Flask and SQLite. The system integrates multiple hospital operations into a normalized relational database and provides a responsive management interface.

### Objectives
1. Maintain centralized patient records.
2. Manage doctors and departments.
3. Schedule and track appointments.
4. Manage admissions, rooms and discharge.
5. Record prescriptions, laboratory tests and vitals.
6. Manage pharmacy stock and blood bank inventory.
7. Generate bills and track payments.
8. Provide reports and administrative audit logs.

### Modules
Patients, Doctors, Appointments, Admissions, Rooms, Prescriptions, Laboratory, Pharmacy, Billing, Blood Bank, Staff, Departments, Reports and Audit Logs.

### Database Tables
users, departments, doctors, patients, appointments, rooms, admissions, medicines, prescriptions, prescription_items, lab_tests, bills, blood_bank, blood_donors, staff, vitals, audit_logs.

### Relationships
- One department → many doctors.
- One doctor → many appointments.
- One patient → many appointments.
- One patient → many admissions.
- One patient → many prescriptions.
- One prescription → many prescription items.
- One medicine → many prescription items.
- One patient → many lab tests.
- One patient → many bills.
- One patient → many vitals.
- One room → many admission records over time.

### DBMS Concepts
DDL, DML, primary key, foreign key, constraints, indexes, JOIN, GROUP BY, COUNT, SUM, ORDER BY, LIKE, transactions and referential integrity.

### Future Scope
Online patient portal, secure password hashing, SMS/email reminders, prescription PDF generation, payment gateway, insurance claim processing, multi-branch support and advanced analytics.

### Conclusion
The system demonstrates practical use of Python with a relational DBMS in a healthcare scenario and covers core database design and application integration requirements for an academic project.
