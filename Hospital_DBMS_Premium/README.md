# MediCore Hospital Suite — Premium Hospital Database Management System

A feature-rich college project built with **Python, Flask and SQLite**.

## Why SQLite?
This edition intentionally uses SQLite so that the project needs **no MySQL server, no port 3306 and no Workbench setup**. SQLite is a relational DBMS and supports primary keys, foreign keys, JOINs, indexes, aggregate queries, constraints and transactions.

## Features
### Clinical
- Patient registry with patient code
- Patient profile/history
- Allergies, insurance, emergency contact
- Primary doctor linking
- Vitals recording
- Doctor directory
- Appointment scheduling with priorities
- Admissions and discharge
- Rooms and bed-capacity tracking
- Prescription management
- Prescription line items
- Laboratory test/result management

### Operations
- Medicine inventory
- Batch/expiry/reorder tracking
- Stock adjustment
- Billing with discounts
- Payment status/method
- Blood bank inventory
- Blood donor registry
- Staff directory
- Departments

### Analytics / DBMS
- Dashboard KPI cards
- Revenue report
- Appointment status report
- Department analysis
- Top doctors report
- Audit logs for admin
- CSV patient export
- Database indexes
- Foreign-key relationships
- Transactions
- Search/filter operations

## Run
Windows:
```bat
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open:
`http://127.0.0.1:5000`

Or just double-click:
`run_project.bat`

## Demo logins
- Admin: `admin / admin123`
- Staff: `staff / staff123`
- Pharmacy: `pharmacy / pharma123`

## Database
The live application database is:
`hospital.db`

Schema/sample SQL:
`database.sql`

Large benchmark database:
`performance_demo.db`

The benchmark DB contains synthetic data for DBMS performance/testing and is not required by the application.

## College Viva Points
- SQLite is a relational database.
- Primary keys uniquely identify rows.
- Foreign keys connect related tables.
- JOINs connect patients, doctors and appointments.
- GROUP BY supports reports.
- COUNT/SUM provide dashboard and finance totals.
- Indexes improve common search/filter queries.
- Transactions preserve consistency while creating prescriptions.
- Audit logging records important administrative actions.

## Security note
This is an academic demo. Passwords are intentionally simple for easy viva demonstration. Production systems should use salted password hashing, CSRF protection, secure sessions, validation and proper access control.
