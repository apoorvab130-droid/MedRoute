# MedRoute — Full-stack prototype

A responsive medical assistance finder built with Flask + SQLite. Includes a modern frontend, JSON API, database-backed facility search, saved demo emergency requests and an admin portal.

## Run on Windows / VS Code
1. Extract the ZIP and open this folder in VS Code.
2. Open Terminal → New Terminal.
3. Create environment: `py -m venv venv`
4. Activate: `venv\\Scripts\\activate` (Command Prompt) or `.\\venv\\Scripts\\Activate.ps1` (PowerShell).
5. Install packages: `pip install -r requirements.txt`
6. Run: `python app.py`
7. Open `http://127.0.0.1:5000`.

SQLite database `medroute.db` and sample facility records are created automatically on first run.

## Admin
Visit `http://127.0.0.1:5000/admin/login`
- Username: `admin`
- Password: `ChangeMe123!`

Change the demo password and secret key before deployment. Admin can add/delete facilities and review saved demonstration requests.

## API endpoints
- `GET /api/health`
- `GET /api/facilities`
- `GET /api/facilities?type=hospital`
- `GET /api/facilities?q=Kanpur`
- `GET /api/facilities?type=blood&area=GT%20Road`
- `GET /api/facilities/<id>`
- `POST /api/emergency-requests` JSON body: `{"emergency_type":"Accident","priority":"High","location":"Kanpur","requested_service":"hospital"}`

## Important
All included facility details are sample demonstration records and are not verified live data. The emergency form only saves a record to SQLite. It does not dispatch an ambulance or contact hospitals. For real emergencies in India, call 112. Do not deploy this as an operational emergency-response service without security, privacy, data-verification and reliability work.
