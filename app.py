from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os
app = Flask(__name__)
app.secret_key = os.environ.get('MEDROUTE_SECRET_KEY', 'change-this-before-deployment')
DB = os.path.join(os.path.dirname(__file__), 'medroute.db')

def connect():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=connect()
    c.executescript('''CREATE TABLE IF NOT EXISTS facilities(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,type TEXT NOT NULL,address TEXT NOT NULL,area TEXT NOT NULL,phone TEXT NOT NULL,status TEXT NOT NULL,services TEXT,blood_groups TEXT,latitude REAL,longitude REAL,verified INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS emergency_requests(id INTEGER PRIMARY KEY AUTOINCREMENT,emergency_type TEXT NOT NULL,priority TEXT NOT NULL,location TEXT NOT NULL,requested_service TEXT NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE,password_hash TEXT NOT NULL);''')
    if c.execute('SELECT COUNT(*) FROM facilities').fetchone()[0]==0:
        rows=[('Regency Hospital','hospital','A-2, Sarvodaya Nagar','Sarvodaya Nagar, Kanpur','1800-123-4567','Demo listing — call to verify','Emergency care, Trauma, ICU','',26.4867,80.3000),('LLR Hospital','hospital','Swaroop Nagar','Swaroop Nagar, Kanpur','0512-233-3333','Demo listing — call to verify','Emergency care, Trauma','',26.4775,80.3249),('Apollo Spectra','hospital','Kanpur South','Kanpur South','0512-400-0000','Demo listing — call to verify','Emergency care, Surgery','',26.4200,80.3500),('Kanpur Emergency Ambulance','ambulance','Civil Lines','Civil Lines, Kanpur','108','Demo listing — availability unverified','Emergency transport','',26.4700,80.3350),('Rapid Care Ambulance','ambulance','Kakadeo','Kakadeo, Kanpur','102','Demo listing — availability unverified','Patient transport, Oxygen support','',26.4850,80.3150),('Regional Blood Centre','blood','GT Road','GT Road, Kanpur','0512-255-5555','Demo listing — call to confirm stock','Donation and issue centre','A+, B+, O+ (sample only)',26.4630,80.3160),('Red Cross Blood Bank','blood','Mall Road','Mall Road, Kanpur','0512-230-1111','Demo listing — call to confirm stock','Blood bank and donation','A+, B+, AB+ (sample only)',26.4740,80.3420)]
        c.executemany('INSERT INTO facilities(name,type,address,area,phone,status,services,blood_groups,latitude,longitude) VALUES(?,?,?,?,?,?,?,?,?,?)',rows)
    if not c.execute('SELECT id FROM admins WHERE username=?',('admin',)).fetchone():
        c.execute('INSERT INTO admins(username,password_hash) VALUES(?,?)',('admin',generate_password_hash(os.environ.get('MEDROUTE_ADMIN_PASSWORD','ChangeMe123!'))))
    c.commit(); c.close()

@app.get('/')
def home(): return render_template('index.html')
@app.get('/api/health')
def health(): return jsonify(status='ok',service='MedRoute API')
@app.get('/api/facilities')
def facilities():
    kind=request.args.get('type','').strip(); q=request.args.get('q','').strip(); area=request.args.get('area','').strip()
    sql='SELECT * FROM facilities WHERE 1=1'; args=[]
    if kind in ('hospital','ambulance','blood'): sql+=' AND type=?'; args.append(kind)
    if q: sql+=' AND (name LIKE ? OR area LIKE ? OR address LIKE ? OR services LIKE ?)'; args += [f'%{q}%']*4
    if area: sql+=' AND area LIKE ?'; args.append(f'%{area}%')
    sql+=' ORDER BY name COLLATE NOCASE'; c=connect(); rows=[dict(r) for r in c.execute(sql,args).fetchall()]; c.close()
    return jsonify(count=len(rows),data=rows,notice='Demonstration records only; verify all information by phone.')
@app.get('/api/facilities/<int:fid>')
def facility(fid):
    c=connect(); r=c.execute('SELECT * FROM facilities WHERE id=?',(fid,)).fetchone(); c.close()
    return (jsonify(dict(r)),200) if r else (jsonify(error='Facility not found'),404)
@app.post('/api/emergency-requests')
def create_request():
    d=request.get_json(silent=True) or {}; kind=str(d.get('emergency_type','')).strip(); loc=str(d.get('location','')).strip(); priority=d.get('priority','High'); service=d.get('requested_service','hospital')
    if not kind or not loc: return jsonify(error='Emergency type and location are required'),400
    if priority not in ('High','Medium','Normal') or service not in ('hospital','ambulance','blood'): return jsonify(error='Invalid priority or service'),400
    c=connect(); cur=c.execute('INSERT INTO emergency_requests(emergency_type,priority,location,requested_service) VALUES(?,?,?,?)',(kind,priority,loc,service)); c.commit(); rid=cur.lastrowid; c.close()
    return jsonify(message='Demo request saved',request_id=rid,notice='No emergency service was contacted or dispatched.'),201
@app.route('/admin/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        c=connect(); u=c.execute('SELECT * FROM admins WHERE username=?',(request.form.get('username',''),)).fetchone(); c.close()
        if u and check_password_hash(u['password_hash'],request.form.get('password','')): session['admin']=u['username']; return redirect('/admin')
        flash('Incorrect username or password.')
    return render_template('login.html')
@app.get('/admin/logout')
def logout(): session.clear(); return redirect('/')
@app.get('/admin')
def admin():
    if not session.get('admin'): return redirect('/admin/login')
    c=connect(); rows=c.execute('SELECT * FROM facilities ORDER BY id DESC').fetchall(); reqs=c.execute('SELECT * FROM emergency_requests ORDER BY id DESC LIMIT 15').fetchall(); stats=[c.execute('SELECT COUNT(*) FROM facilities').fetchone()[0]]+[c.execute('SELECT COUNT(*) FROM facilities WHERE type=?',(t,)).fetchone()[0] for t in ('hospital','ambulance','blood')]+[c.execute('SELECT COUNT(*) FROM emergency_requests').fetchone()[0]]; c.close()
    return render_template('admin.html',rows=rows,reqs=reqs,stats=stats)
@app.post('/admin/save')
def save():
    if not session.get('admin'): return redirect('/admin/login')
    d=request.form
    if not all(d.get(k,'').strip() for k in ('name','type','address','area','phone')): flash('Complete all required fields.'); return redirect('/admin')
    c=connect(); c.execute('INSERT INTO facilities(name,type,address,area,phone,status,services,blood_groups,latitude,longitude,verified) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(d['name'].strip(),d['type'],d['address'].strip(),d['area'].strip(),d['phone'].strip(),d.get('status','Unverified'),d.get('services',''),d.get('blood_groups',''),float(d['latitude']) if d.get('latitude') else None,float(d['longitude']) if d.get('longitude') else None,1 if d.get('verified') else 0)); c.commit(); c.close(); flash('Facility added.'); return redirect('/admin')
@app.post('/admin/delete/<int:fid>')
def delete(fid):
    if not session.get('admin'): return redirect('/admin/login')
    c=connect(); c.execute('DELETE FROM facilities WHERE id=?',(fid,)); c.commit(); c.close(); flash('Facility deleted.'); return redirect('/admin')
init_db()
if __name__=='__main__': app.run(debug=True,port=5000)
