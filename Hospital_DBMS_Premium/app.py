from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from functools import wraps
from decimal import Decimal, InvalidOperation
import sqlite3
import os
import csv
import io
from datetime import date
from werkzeug.exceptions import HTTPException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hospital.db")

app = Flask(__name__)
app.secret_key = "hospital-dbms-premium-college-secret"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) < 1000:
        with open(os.path.join(BASE_DIR, "database.sql"), "r", encoding="utf-8") as f:
            sql = f.read()
        conn = get_db()
        conn.executescript(sql)
        conn.commit()
        conn.close()

def query(sql, params=()):
    conn = get_db()
    cur = conn.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def one(sql, params=()):
    conn = get_db()
    row = conn.execute(sql, params).fetchone()
    result = dict(row) if row else None
    conn.close()
    return result

def execute(sql, params=()):
    conn = get_db()
    cur = conn.execute(sql, params)
    conn.commit()
    last = cur.lastrowid
    conn.close()
    return last

def multi(sql, rows):
    conn = get_db()
    conn.executemany(sql, rows)
    conn.commit()
    conn.close()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "Admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapper

def audit(action, entity, entity_id=None, details=""):
    if "user_id" in session:
        execute("""INSERT INTO audit_logs(user_id,action,entity,entity_id,details)
                   VALUES(?,?,?,?,?)""",
                (session["user_id"], action, entity, entity_id, details))

@app.context_processor
def globals():
    return {
        "current_date": date.today(),
        "app_name": "MediCore Hospital",
        "nav_count": {
            "pending": one("SELECT COUNT(*) c FROM appointments WHERE status='Scheduled'")["c"],
            "admitted": one("SELECT COUNT(*) c FROM admissions WHERE status='Admitted'")["c"]
        }
    }

@app.route("/")
def index():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = one("""SELECT user_id,username,full_name,role,department
                      FROM users WHERE username=? AND password=? AND is_active=1""",
                   (request.form.get("username","").strip(),
                    request.form.get("password","")))
        if user:
            session.update(user)
            audit("LOGIN","SYSTEM",None,"Successful login")
            flash(f"Welcome back, {user['full_name']}.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username/password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "patients": one("SELECT COUNT(*) c FROM patients WHERE status='Active'")["c"],
        "doctors": one("SELECT COUNT(*) c FROM doctors WHERE status='Active'")["c"],
        "today_appointments": one("SELECT COUNT(*) c FROM appointments WHERE appointment_date=date('now','localtime')")["c"],
        "admitted": one("SELECT COUNT(*) c FROM admissions WHERE status='Admitted'")["c"],
        "pending_bills": one("SELECT COUNT(*) c FROM bills WHERE payment_status='Pending'")["c"],
        "revenue": one("SELECT COALESCE(SUM(total_amount),0) c FROM bills WHERE payment_status='Paid'")["c"],
        "low_stock": one("SELECT COUNT(*) c FROM medicines WHERE quantity<=10 AND status='Active'")["c"],
        "critical_labs": one("SELECT COUNT(*) c FROM lab_tests WHERE result_status='Critical'")["c"]
    }
    today = query("""SELECT a.*,p.name patient_name,d.name doctor_name
                     FROM appointments a
                     JOIN patients p ON a.patient_id=p.patient_id
                     JOIN doctors d ON a.doctor_id=d.doctor_id
                     WHERE a.appointment_date=date('now','localtime')
                     ORDER BY a.appointment_time LIMIT 10""")
    recent = query("""SELECT * FROM (
                       SELECT 'Patient' kind, patient_id id, name title, created_at dt FROM patients
                       UNION ALL
                       SELECT 'Appointment',appointment_id id, 'Appointment with '||status, created_at FROM appointments
                       UNION ALL
                       SELECT 'Bill',bill_id id, 'Bill ₹'||printf('%.2f',total_amount), bill_date FROM bills
                     ) ORDER BY dt DESC LIMIT 8""")
    dept = query("""SELECT d.name, COUNT(p.doctor_id) total
                    FROM departments d LEFT JOIN doctors p ON p.department_id=d.department_id
                    GROUP BY d.department_id ORDER BY total DESC LIMIT 8""")
    return render_template("dashboard.html", stats=stats, today=today, recent=recent, dept=dept)

# ---------- Patients ----------
@app.route("/patients")
@login_required
def patients():
    q = request.args.get("q","").strip()
    status = request.args.get("status","")
    base = """SELECT p.*, d.name primary_doctor
              FROM patients p LEFT JOIN doctors d ON p.primary_doctor_id=d.doctor_id
              WHERE 1=1"""
    params=[]
    if q:
        base += " AND (p.name LIKE ? OR p.phone LIKE ? OR p.patient_code LIKE ?)"
        params += [f"%{q}%"]*3
    if status:
        base += " AND p.status=?"; params.append(status)
    base += " ORDER BY p.patient_id DESC"
    return render_template("patients/list.html", patients=query(base,params), q=q, status=status)

@app.route("/patients/add", methods=["GET","POST"])
@login_required
def add_patient():
    docs=query("SELECT doctor_id,name,specialization FROM doctors WHERE status='Active' ORDER BY name")
    if request.method=="POST":
        code="P"+str(one("SELECT COALESCE(MAX(patient_id),0)+1 c FROM patients")["c"]).zfill(5)
        pid=execute("""INSERT INTO patients(patient_code,name,dob,age,gender,blood_group,phone,email,
                      address,emergency_contact,allergies,primary_doctor_id,insurance_provider,status)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (code,request.form["name"],request.form.get("dob") or None,request.form["age"],
             request.form["gender"],request.form.get("blood_group",""),request.form.get("phone",""),
             request.form.get("email",""),request.form.get("address",""),
             request.form.get("emergency_contact",""),request.form.get("allergies",""),
             request.form.get("primary_doctor_id") or None,request.form.get("insurance_provider",""),
             "Active"))
        audit("CREATE","PATIENT",pid,code); flash("Patient registered successfully.","success")
        return redirect(url_for("patient_detail",patient_id=pid))
    return render_template("patients/form.html",patient=None,doctors=docs)

@app.route("/patients/edit/<int:patient_id>", methods=["GET","POST"])
@login_required
def edit_patient(patient_id):
    p=one("SELECT * FROM patients WHERE patient_id=?",(patient_id,))
    docs=query("SELECT doctor_id,name,specialization FROM doctors WHERE status='Active' ORDER BY name")
    if not p: flash("Patient not found.","danger"); return redirect(url_for("patients"))
    if request.method=="POST":
        execute("""UPDATE patients SET name=?,dob=?,age=?,gender=?,blood_group=?,phone=?,email=?,address=?,
                   emergency_contact=?,allergies=?,primary_doctor_id=?,insurance_provider=?,status=? WHERE patient_id=?""",
            (request.form["name"],request.form.get("dob") or None,request.form["age"],request.form["gender"],
             request.form.get("blood_group",""),request.form.get("phone",""),request.form.get("email",""),
             request.form.get("address",""),request.form.get("emergency_contact",""),
             request.form.get("allergies",""),request.form.get("primary_doctor_id") or None,
             request.form.get("insurance_provider",""),request.form.get("status","Active"),patient_id))
        audit("UPDATE","PATIENT",patient_id,p["patient_code"]); flash("Patient updated.","success")
        return redirect(url_for("patient_detail",patient_id=patient_id))
    return render_template("patients/form.html",patient=p,doctors=docs)

@app.route("/patients/delete/<int:patient_id>", methods=["POST"])
@login_required
def delete_patient(patient_id):
    execute("UPDATE patients SET status='Inactive' WHERE patient_id=?",(patient_id,))
    audit("ARCHIVE","PATIENT",patient_id,"Patient archived")
    flash("Patient archived instead of permanently deleting clinical history.","success")
    return redirect(url_for("patients"))

@app.route("/patients/<int:patient_id>")
@login_required
def patient_detail(patient_id):
    p=one("""SELECT p.*,d.name primary_doctor,d.specialization
             FROM patients p LEFT JOIN doctors d ON p.primary_doctor_id=d.doctor_id
             WHERE p.patient_id=?""",(patient_id,))
    if not p: flash("Patient not found.","danger"); return redirect(url_for("patients"))
    appointments=query("""SELECT a.*,d.name doctor_name,d.specialization
                          FROM appointments a JOIN doctors d ON a.doctor_id=d.doctor_id
                          WHERE a.patient_id=? ORDER BY a.appointment_date DESC,a.appointment_time DESC LIMIT 20""",(patient_id,))
    admissions=query("SELECT * FROM admissions WHERE patient_id=? ORDER BY admission_id DESC",(patient_id,))
    prescriptions=query("""SELECT pr.*,d.name doctor_name FROM prescriptions pr
                           JOIN doctors d ON pr.doctor_id=d.doctor_id WHERE pr.patient_id=?
                           ORDER BY pr.prescription_date DESC LIMIT 10""",(patient_id,))
    labs=query("""SELECT l.*,d.name doctor_name FROM lab_tests l
                  LEFT JOIN doctors d ON l.doctor_id=d.doctor_id
                  WHERE l.patient_id=? ORDER BY l.test_date DESC LIMIT 10""",(patient_id,))
    bills=query("SELECT * FROM bills WHERE patient_id=? ORDER BY bill_id DESC LIMIT 10",(patient_id,))
    vitals=query("SELECT * FROM vitals WHERE patient_id=? ORDER BY measured_at DESC LIMIT 10",(patient_id,))
    return render_template("patients/detail.html",patient=p,appointments=appointments,admissions=admissions,
                           prescriptions=prescriptions,labs=labs,bills=bills,vitals=vitals)

@app.route("/patients/<int:patient_id>/vitals", methods=["POST"])
@login_required
def add_vitals(patient_id):
    execute("""INSERT INTO vitals(patient_id,bp,heart_rate,temperature,spo2,weight,height,notes,measured_by)
               VALUES(?,?,?,?,?,?,?,?,?)""",(patient_id,request.form.get("bp"),request.form.get("heart_rate") or None,
                 request.form.get("temperature") or None,request.form.get("spo2") or None,
                 request.form.get("weight") or None,request.form.get("height") or None,
                 request.form.get("notes",""),session.get("full_name","Staff")))
    audit("CREATE","VITALS",patient_id,"Vitals recorded")
    flash("Vitals recorded.","success"); return redirect(url_for("patient_detail",patient_id=patient_id))

@app.route("/patients/export")
@login_required
def export_patients():
    rows=query("SELECT patient_code,name,age,gender,blood_group,phone,email,status FROM patients ORDER BY patient_id")
    sio=io.StringIO(); w=csv.writer(sio); w.writerow(rows[0].keys() if rows else
        ["patient_code","name","age","gender","blood_group","phone","email","status"])
    for r in rows: w.writerow(r.values())
    return Response(sio.getvalue(),mimetype="text/csv",
                    headers={"Content-Disposition":"attachment; filename=patients.csv"})

# ---------- Doctors ----------
@app.route("/doctors")
@login_required
def doctors():
    q=request.args.get("q","").strip()
    sql="""SELECT d.*,dep.name department_name FROM doctors d
           LEFT JOIN departments dep ON d.department_id=dep.department_id WHERE 1=1"""
    params=[]
    if q: sql+=" AND (d.name LIKE ? OR d.specialization LIKE ? OR dep.name LIKE ?)"; params=[f"%{q}%"]*3
    sql+=" ORDER BY d.doctor_id DESC"
    return render_template("doctors/list.html",doctors=query(sql,params),q=q)

@app.route("/doctors/add",methods=["GET","POST"])
@login_required
def add_doctor():
    deps=query("SELECT department_id,name FROM departments WHERE status='Active' ORDER BY name")
    if request.method=="POST":
        did=execute("""INSERT INTO doctors(name,specialization,department_id,phone,email,license_no,
                       consultation_fee,available_days,available_time,status)
                       VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (request.form["name"],request.form.get("specialization",""),request.form.get("department_id") or None,
             request.form.get("phone",""),request.form.get("email",""),request.form.get("license_no",""),
             request.form.get("consultation_fee") or 0,request.form.get("available_days",""),
             request.form.get("available_time",""),"Active"))
        audit("CREATE","DOCTOR",did); flash("Doctor added.","success"); return redirect(url_for("doctors"))
    return render_template("doctors/form.html",doctor=None,departments=deps)

@app.route("/doctors/edit/<int:doctor_id>",methods=["GET","POST"])
@login_required
def edit_doctor(doctor_id):
    d=one("SELECT * FROM doctors WHERE doctor_id=?",(doctor_id,)); deps=query("SELECT department_id,name FROM departments ORDER BY name")
    if not d: flash("Doctor not found.","danger"); return redirect(url_for("doctors"))
    if request.method=="POST":
        execute("""UPDATE doctors SET name=?,specialization=?,department_id=?,phone=?,email=?,license_no=?,
                   consultation_fee=?,available_days=?,available_time=?,status=? WHERE doctor_id=?""",
            (request.form["name"],request.form.get("specialization",""),request.form.get("department_id") or None,
             request.form.get("phone",""),request.form.get("email",""),request.form.get("license_no",""),
             request.form.get("consultation_fee") or 0,request.form.get("available_days",""),
             request.form.get("available_time",""),request.form.get("status","Active"),doctor_id))
        audit("UPDATE","DOCTOR",doctor_id); flash("Doctor updated.","success"); return redirect(url_for("doctors"))
    return render_template("doctors/form.html",doctor=d,departments=deps)

# ---------- Appointments ----------
@app.route("/appointments")
@login_required
def appointments():
    q=request.args.get("q","").strip()
    sql="""SELECT a.*,p.patient_code,p.name patient_name,d.name doctor_name,d.specialization
           FROM appointments a JOIN patients p ON a.patient_id=p.patient_id JOIN doctors d ON a.doctor_id=d.doctor_id WHERE 1=1"""
    params=[]
    if q: sql+=" AND (p.name LIKE ? OR d.name LIKE ? OR a.status LIKE ?)"; params=[f"%{q}%"]*3
    sql+=" ORDER BY a.appointment_date DESC,a.appointment_time DESC"
    return render_template("appointments/list.html",appointments=query(sql,params),q=q)

@app.route("/appointments/add",methods=["GET","POST"])
@login_required
def add_appointment():
    ps=query("SELECT patient_id,patient_code,name FROM patients WHERE status='Active' ORDER BY name")
    ds=query("SELECT doctor_id,name,specialization FROM doctors WHERE status='Active' ORDER BY name")
    if request.method=="POST":
        aid=execute("""INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason,status,priority,notes)
                       VALUES(?,?,?,?,?,?,?,?)""",(request.form["patient_id"],request.form["doctor_id"],request.form["appointment_date"],
                         request.form["appointment_time"],request.form.get("reason",""),"Scheduled",
                         request.form.get("priority","Normal"),request.form.get("notes","")))
        audit("CREATE","APPOINTMENT",aid); flash("Appointment booked.","success"); return redirect(url_for("appointments"))
    return render_template("appointments/form.html",patients=ps,doctors=ds)

@app.route("/appointments/status/<int:appointment_id>/<status>",methods=["POST"])
@login_required
def appointment_status(appointment_id,status):
    if status not in {"Scheduled","Completed","Cancelled","No Show"}: return redirect(url_for("appointments"))
    execute("UPDATE appointments SET status=? WHERE appointment_id=?",(status,appointment_id))
    audit("UPDATE","APPOINTMENT",appointment_id,status); flash("Appointment status updated.","success")
    return redirect(url_for("appointments"))

# ---------- Admissions / Rooms ----------
@app.route("/admissions")
@login_required
def admissions():
    rows=query("""SELECT a.*,p.patient_code,p.name patient_name FROM admissions a JOIN patients p ON a.patient_id=p.patient_id
                  ORDER BY CASE WHEN a.status='Admitted' THEN 0 ELSE 1 END,a.admission_id DESC""")
    return render_template("admissions/list.html",admissions=rows)

@app.route("/admissions/add",methods=["GET","POST"])
@login_required
def add_admission():
    ps=query("SELECT patient_id,patient_code,name FROM patients WHERE status='Active' ORDER BY name")
    rooms=query("""SELECT r.*, (SELECT COUNT(*) FROM admissions a WHERE a.room_id=r.room_id AND a.status='Admitted') occupied
                   FROM rooms r ORDER BY r.ward,r.room_no""")
    if request.method=="POST":
        rid=int(request.form["room_id"])
        room=one("SELECT * FROM rooms WHERE room_id=?",(rid,))
        occupied=one("SELECT COUNT(*) c FROM admissions WHERE room_id=? AND status='Admitted'",(rid,))["c"]
        if occupied>=room["capacity"]: flash("Selected room is full.","danger")
        else:
            aid=execute("""INSERT INTO admissions(patient_id,room_id,bed_no,admission_date,expected_discharge,attending_doctor_id,
                           diagnosis,status,notes) VALUES(?,?,?,?,?,?,?,?,?)""",
                (request.form["patient_id"],rid,request.form.get("bed_no",""),request.form["admission_date"],
                 request.form.get("expected_discharge") or None,request.form.get("attending_doctor_id") or None,
                 request.form.get("diagnosis",""),"Admitted",request.form.get("notes","")))
            audit("CREATE","ADMISSION",aid); flash("Patient admitted.","success"); return redirect(url_for("admissions"))
    ds=query("SELECT doctor_id,name FROM doctors WHERE status='Active' ORDER BY name")
    return render_template("admissions/form.html",patients=ps,rooms=rooms,doctors=ds)

@app.route("/admissions/discharge/<int:admission_id>",methods=["POST"])
@login_required
def discharge(admission_id):
    execute("UPDATE admissions SET discharge_date=date('now','localtime'),status='Discharged' WHERE admission_id=?",(admission_id,))
    audit("UPDATE","ADMISSION",admission_id,"Discharged"); flash("Patient discharged.","success")
    return redirect(url_for("admissions"))

@app.route("/rooms")
@login_required
def rooms():
    rows=query("""SELECT r.*,COALESCE((SELECT COUNT(*) FROM admissions a WHERE a.room_id=r.room_id AND a.status='Admitted'),0) occupied
                 FROM rooms r ORDER BY r.ward,r.room_no""")
    return render_template("rooms/list.html",rooms=rows)

# ---------- Prescriptions ----------
@app.route("/prescriptions")
@login_required
def prescriptions():
    rows=query("""SELECT pr.*,p.patient_code,p.name patient_name,d.name doctor_name
                  FROM prescriptions pr JOIN patients p ON pr.patient_id=p.patient_id JOIN doctors d ON pr.doctor_id=d.doctor_id
                  ORDER BY pr.prescription_id DESC""")
    return render_template("prescriptions/list.html",prescriptions=rows)

@app.route("/prescriptions/add",methods=["GET","POST"])
@login_required
def add_prescription():
    ps=query("SELECT patient_id,patient_code,name FROM patients WHERE status='Active' ORDER BY name")
    ds=query("SELECT doctor_id,name FROM doctors WHERE status='Active' ORDER BY name")
    ms=query("SELECT medicine_id,name,quantity,unit_price FROM medicines WHERE status='Active' ORDER BY name")
    if request.method=="POST":
        conn=get_db()
        try:
            conn.execute("BEGIN")
            pid=int(request.form["patient_id"]); did=int(request.form["doctor_id"])
            cur=conn.execute("""INSERT INTO prescriptions(patient_id,doctor_id,prescription_date,diagnosis,instructions,status)
                                VALUES(?,?,?,?,?,?)""",
                             (pid,did,request.form["prescription_date"],request.form.get("diagnosis",""),
                              request.form.get("instructions",""),"Active"))
            prid=cur.lastrowid
            med_ids=request.form.getlist("medicine_id")
            dosages=request.form.getlist("dosage")
            durations=request.form.getlist("duration_days")
            qtys=request.form.getlist("quantity")
            for i,mid in enumerate(med_ids):
                if not mid: continue
                q=int(qtys[i] or 0)
                conn.execute("""INSERT INTO prescription_items(prescription_id,medicine_id,dosage,duration_days,quantity)
                                VALUES(?,?,?,?,?)""",(prid,int(mid),dosages[i],int(durations[i] or 1),q))
            conn.commit()
            audit("CREATE","PRESCRIPTION",prid); flash("Prescription created.","success")
            return redirect(url_for("prescriptions"))
        except Exception as e:
            conn.rollback(); flash(f"Could not save prescription: {e}","danger")
        finally: conn.close()
    return render_template("prescriptions/form.html",patients=ps,doctors=ds,medicines=ms)

# ---------- Labs ----------
@app.route("/labs")
@login_required
def labs():
    rows=query("""SELECT l.*,p.patient_code,p.name patient_name,d.name doctor_name
                  FROM lab_tests l JOIN patients p ON l.patient_id=p.patient_id
                  LEFT JOIN doctors d ON l.doctor_id=d.doctor_id
                  ORDER BY l.lab_id DESC""")
    return render_template("labs/list.html",labs=rows)

@app.route("/labs/add",methods=["GET","POST"])
@login_required
def add_lab():
    ps=query("SELECT patient_id,patient_code,name FROM patients WHERE status='Active' ORDER BY name")
    ds=query("SELECT doctor_id,name FROM doctors WHERE status='Active' ORDER BY name")
    if request.method=="POST":
        lid=execute("""INSERT INTO lab_tests(patient_id,doctor_id,test_name,test_category,test_date,result_value,unit,reference_range,result_status,remarks)
                       VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (request.form["patient_id"],request.form.get("doctor_id") or None,request.form["test_name"],
             request.form.get("test_category",""),request.form["test_date"],request.form.get("result_value",""),
             request.form.get("unit",""),request.form.get("reference_range",""),request.form.get("result_status","Pending"),
             request.form.get("remarks","")))
        audit("CREATE","LAB",lid); flash("Lab test recorded.","success"); return redirect(url_for("labs"))
    return render_template("labs/form.html",patients=ps,doctors=ds)

# ---------- Medicines ----------
@app.route("/medicines")
@login_required
def medicines():
    rows=query("SELECT * FROM medicines ORDER BY quantity<=10 DESC,medicine_id DESC")
    return render_template("medicines/list.html",medicines=rows)

@app.route("/medicines/add",methods=["GET","POST"])
@login_required
def add_medicine():
    if request.method=="POST":
        mid=execute("""INSERT INTO medicines(name,category,quantity,unit_price,manufacturer,batch_no,expiry_date,reorder_level,status)
                       VALUES(?,?,?,?,?,?,?,?,?)""",(request.form["name"],request.form.get("category",""),
                         int(request.form["quantity"]),float(request.form["unit_price"] or 0),request.form.get("manufacturer",""),
                         request.form.get("batch_no",""),request.form["expiry_date"],int(request.form.get("reorder_level") or 10),"Active"))
        audit("CREATE","MEDICINE",mid); flash("Medicine added.","success"); return redirect(url_for("medicines"))
    return render_template("medicines/form.html",medicine=None)

@app.route("/medicines/stock/<int:medicine_id>",methods=["POST"])
@login_required
def adjust_stock(medicine_id):
    delta=int(request.form["delta"])
    execute("UPDATE medicines SET quantity=MAX(0,quantity+?) WHERE medicine_id=?",(delta,medicine_id))
    audit("STOCK","MEDICINE",medicine_id,f"Adjustment {delta:+d}")
    flash("Stock updated.","success"); return redirect(url_for("medicines"))

# ---------- Bills ----------
@app.route("/bills")
@login_required
def bills():
    rows=query("""SELECT b.*,p.patient_code,p.name patient_name FROM bills b JOIN patients p ON b.patient_id=p.patient_id
                  ORDER BY b.bill_id DESC""")
    return render_template("bills/list.html",bills=rows)

@app.route("/bills/add",methods=["GET","POST"])
@login_required
def add_bill():
    ps=query("SELECT patient_id,patient_code,name FROM patients WHERE status='Active' ORDER BY name")
    if request.method=="POST":
        vals=[]
        for k in ["consultation_charge","room_charge","medicine_charge","lab_charge","other_charge","discount"]:
            try: vals.append(Decimal(request.form.get(k) or 0))
            except InvalidOperation: vals.append(Decimal(0))
        total=sum(vals[:5])-vals[5]
        if total<0: total=Decimal(0)
        bid=execute("""INSERT INTO bills(patient_id,bill_date,consultation_charge,room_charge,medicine_charge,lab_charge,
                       other_charge,discount,total_amount,payment_status,payment_method,notes)
                       VALUES(?,date('now','localtime'),?,?,?,?,?,?,?,?,?,?)""",
            (request.form["patient_id"],*vals,total,request.form.get("payment_status","Pending"),
             request.form.get("payment_method","Cash"),request.form.get("notes","")))
        audit("CREATE","BILL",bid,f"₹{total:.2f}"); flash(f"Bill #{bid} created.","success"); return redirect(url_for("bills"))
    return render_template("bills/form.html",patients=ps)

@app.route("/bills/pay/<int:bill_id>",methods=["POST"])
@login_required
def pay_bill(bill_id):
    execute("UPDATE bills SET payment_status='Paid',payment_date=date('now','localtime') WHERE bill_id=?",(bill_id,))
    audit("PAYMENT","BILL",bill_id,"Marked paid"); flash("Payment recorded.","success"); return redirect(url_for("bills"))

# ---------- Blood Bank ----------
@app.route("/blood-bank")
@login_required
def blood_bank():
    rows=query("SELECT * FROM blood_bank ORDER BY blood_group")
    donors=query("SELECT * FROM blood_donors ORDER BY donor_id DESC LIMIT 25")
    return render_template("blood/list.html",banks=rows,donors=donors)

@app.route("/blood-bank/donor",methods=["POST"])
@login_required
def add_donor():
    execute("""INSERT INTO blood_donors(name,blood_group,phone,donation_date,units,screening_status)
               VALUES(?,?,?,?,?,?)""",(request.form["name"],request.form["blood_group"],request.form.get("phone",""),
                 request.form["donation_date"],int(request.form.get("units") or 1),request.form.get("screening_status","Passed")))
    flash("Donor record added.","success"); return redirect(url_for("blood_bank"))

# ---------- Staff ----------
@app.route("/staff")
@login_required
def staff():
    rows=query("SELECT * FROM staff ORDER BY name")
    return render_template("staff/list.html",staff=rows)

@app.route("/staff/add",methods=["GET","POST"])
@admin_required
def add_staff():
    if request.method=="POST":
        sid=execute("""INSERT INTO staff(name,designation,department,phone,email,shift,status)
                       VALUES(?,?,?,?,?,?,?)""",(request.form["name"],request.form["designation"],
                         request.form.get("department",""),request.form.get("phone",""),request.form.get("email",""),
                         request.form.get("shift","Day"),"Active"))
        audit("CREATE","STAFF",sid); flash("Staff member added.","success"); return redirect(url_for("staff"))
    return render_template("staff/form.html",staff=None)

# ---------- Departments ----------
@app.route("/departments")
@login_required
def departments():
    rows=query("""SELECT d.*,COUNT(doc.doctor_id) doctor_count FROM departments d
                  LEFT JOIN doctors doc ON doc.department_id=d.department_id GROUP BY d.department_id ORDER BY d.name""")
    return render_template("departments.html",departments=rows)

# ---------- Reports / Audit ----------
@app.route("/reports")
@login_required
def reports():
    monthly=query("""SELECT strftime('%Y-%m',bill_date) month, SUM(total_amount) revenue
                     FROM bills WHERE payment_status='Paid'
                     GROUP BY month ORDER BY month DESC LIMIT 12""")
    appt=query("SELECT status,COUNT(*) total FROM appointments GROUP BY status ORDER BY total DESC")
    dept=query("""SELECT dep.name,COUNT(p.patient_id) total FROM patients p
                  LEFT JOIN doctors d ON p.primary_doctor_id=d.doctor_id
                  LEFT JOIN departments dep ON d.department_id=dep.department_id
                  GROUP BY dep.name ORDER BY total DESC""")
    topdocs=query("""SELECT d.name,COUNT(a.appointment_id) appointments
                     FROM doctors d LEFT JOIN appointments a ON a.doctor_id=d.doctor_id
                     GROUP BY d.doctor_id ORDER BY appointments DESC LIMIT 10""")
    return render_template("reports.html",monthly=monthly,appt=appt,dept=dept,topdocs=topdocs)

@app.route("/audit-logs")
@admin_required
def audit_logs():
    rows=query("""SELECT a.*,u.full_name FROM audit_logs a LEFT JOIN users u ON a.user_id=u.user_id
                  ORDER BY a.log_id DESC LIMIT 250""")
    return render_template("audit.html",logs=rows)

@app.route("/api/dashboard")
@login_required
def api_dashboard():
    return jsonify({
        "patients": one("SELECT COUNT(*) c FROM patients WHERE status='Active'")["c"],
        "appointments_today": one("SELECT COUNT(*) c FROM appointments WHERE appointment_date=date('now','localtime')")["c"],
        "revenue": one("SELECT COALESCE(SUM(total_amount),0) c FROM bills WHERE payment_status='Paid'")["c"]
    })

@app.route("/favicon.ico")
def favicon():
    return ("", 204)

@app.errorhandler(404)
def page_not_found(err):
    return render_template("error.html", message="The requested page was not found."), 404


@app.errorhandler(Exception)
def handle_error(err):
    if isinstance(err, HTTPException):
        return err
    # Avoid exposing stack traces to users; log in server console.
    print("APPLICATION ERROR:", repr(err))
    return render_template("error.html", message="An application error occurred. Check the terminal for details."), 500

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
