import os
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
from db import query_db, execute_db, test_connection, format_db_error

app = Flask(__name__)
app.config.from_object(Config)

# =========================================================================
# Authentication Decorators
# =========================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_id' not in session:
            flash("Please sign in with your employee credentials to access this section.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'Airport Administrator':
            flash("Access Restricted: Only Airport Administrators are permitted to perform this action.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to inject active_page or default values
@app.context_processor
def inject_globals():
    return {
        'now': datetime.now(),
        'db_name': Config.MYSQL_DB
    }

# =========================================================================
# Authentication & Root Routes
# =========================================================================

@app.route('/')
def index():
    if 'employee_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return render_template('login.html')

        try:
            # Query employee table by username and password
            employee = query_db(
                "SELECT Employee_ID, Name, Username, Role FROM employee WHERE Username = %s AND Password = %s;",
                (username, password),
                one=True
            )

            if employee:
                session.clear()
                session['employee_id'] = employee['Employee_ID']
                session['name'] = employee['Name']
                session['username'] = employee['Username']
                session['role'] = employee['Role']
                flash(f"Welcome back, {employee['Name']}! Signed in as {employee['Role']}.", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid Username or Password", "danger")
        except Exception as e:
            flash(format_db_error(e), "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    name = session.get('name', 'Staff member')
    session.clear()
    flash(f"Logged out successfully. Have a great day, {name}!", "info")
    return redirect(url_for('login'))

# =========================================================================
# Dashboard
# =========================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_employees': 0,
        'total_passengers': 0,
        'total_airlines': 0,
        'total_flights': 0,
        'total_bookings': 0,
        'total_gates': 0
    }
    recent_flights = []
    recent_bookings = []

    try:
        emp_res = query_db("SELECT COUNT(*) AS cnt FROM employee;", one=True)
        stats['total_employees'] = emp_res['cnt'] if emp_res else 0

        p_res = query_db("SELECT COUNT(*) AS cnt FROM passenger;", one=True)
        stats['total_passengers'] = p_res['cnt'] if p_res else 0

        a_res = query_db("SELECT COUNT(*) AS cnt FROM airline;", one=True)
        stats['total_airlines'] = a_res['cnt'] if a_res else 0

        f_res = query_db("SELECT COUNT(*) AS cnt FROM flight;", one=True)
        stats['total_flights'] = f_res['cnt'] if f_res else 0

        b_res = query_db("SELECT COUNT(*) AS cnt FROM booking;", one=True)
        stats['total_bookings'] = b_res['cnt'] if b_res else 0

        g_res = query_db("SELECT COUNT(*) AS cnt FROM gate;", one=True)
        stats['total_gates'] = g_res['cnt'] if g_res else 0

        # Recent scheduled flights with joins
        recent_flights = query_db("""
            SELECT f.Flight_ID, f.Flight_No, f.Source, f.Destination, f.Departure_Time, f.Status,
                   COALESCE(a.airline_name, 'Unknown Airline') AS Airline_Name,
                   COALESCE(t.terminal_name, CONCAT('Terminal #', f.Terminal_ID)) AS Terminal_Name,
                   COALESCE(g.gate_no, CONCAT('Gate #', f.Gate_ID)) AS Gate_Number
            FROM flight f
            LEFT JOIN airline a ON f.Airline_ID = a.airline_id
            LEFT JOIN terminal t ON f.Terminal_ID = t.terminal_id
            LEFT JOIN gate g ON f.Gate_ID = g.gate_id
            ORDER BY f.Departure_Time ASC
            LIMIT 6;
        """)

        # Recent bookings with joins
        recent_bookings = query_db("""
            SELECT b.booking_id AS Booking_ID, b.seat_no AS Seat_No, b.booking_status AS Booking_Status, b.passenger_id AS Passenger_ID,
                   COALESCE(p.name, 'Passenger') AS Passenger_Name,
                   COALESCE(f.Flight_No, 'Flight') AS Flight_No
            FROM booking b
            LEFT JOIN passenger p ON b.passenger_id = p.passenger_id
            LEFT JOIN flight f ON b.flight_id = f.Flight_ID
            ORDER BY b.booking_id DESC
            LIMIT 5;
        """)
    except Exception as e:
        flash(format_db_error(e), "danger")

    return render_template('dashboard.html', active_page='dashboard', stats=stats, recent_flights=recent_flights, recent_bookings=recent_bookings)

# =========================================================================
# Employee Module (Admins only for write)
# =========================================================================

@app.route('/employees')
@login_required
def employees():
    try:
        employee_list = query_db("SELECT Employee_ID, Name, Username, Role, Phone, Email FROM employee ORDER BY Employee_ID ASC;")
    except Exception as e:
        flash(format_db_error(e), "danger")
        employee_list = []
    return render_template('employees.html', active_page='employees', employees=employee_list)

@app.route('/employees/add', methods=['POST'])
@admin_required
def add_employee():
    name = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()

    try:
        execute_db(
            "INSERT INTO employee (Name, Username, Password, Role, Phone, Email) VALUES (%s, %s, %s, %s, %s, %s);",
            (name, username, password, role, phone, email)
        )
        flash(f"Employee '{name}' added successfully.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('employees'))

@app.route('/employees/edit/<int:employee_id>', methods=['POST'])
@admin_required
def edit_employee(employee_id):
    name = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()

    try:
        if password:
            execute_db(
                "UPDATE employee SET Name=%s, Username=%s, Password=%s, Role=%s, Phone=%s, Email=%s WHERE Employee_ID=%s;",
                (name, username, password, role, phone, email, employee_id)
            )
        else:
            execute_db(
                "UPDATE employee SET Name=%s, Username=%s, Role=%s, Phone=%s, Email=%s WHERE Employee_ID=%s;",
                (name, username, role, phone, email, employee_id)
            )
        flash(f"Employee record #{employee_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('employees'))

@app.route('/employees/delete/<int:employee_id>', methods=['POST'])
@admin_required
def delete_employee(employee_id):
    if employee_id == session.get('employee_id'):
        flash("Action prohibited: You cannot delete your currently active account.", "warning")
        return redirect(url_for('employees'))
    try:
        execute_db("DELETE FROM employee WHERE Employee_ID = %s;", (employee_id,))
        flash(f"Employee #{employee_id} removed successfully.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('employees'))

# =========================================================================
# Airline Module
# =========================================================================

@app.route('/airlines')
@login_required
def airlines():
    try:
        airline_list = query_db("""
            SELECT airline_id AS Airline_ID, airline_name AS Airline_Name, country AS Country,
                   COALESCE(headquarters, '') AS Headquarters, COALESCE(contact_no, '') AS Contact_No
            FROM airline
            ORDER BY airline_id ASC;
        """)
    except Exception as e:
        flash(format_db_error(e), "danger")
        airline_list = []
    return render_template('airlines.html', active_page='airlines', airlines=airline_list)

@app.route('/airlines/add', methods=['POST'])
@login_required
def add_airline():
    name = request.form.get('airline_name', '').strip()
    country = request.form.get('country', '').strip()
    try:
        execute_db("INSERT INTO airline (airline_name, country) VALUES (%s, %s);", (name, country))
        flash(f"Airline '{name}' created successfully.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('airlines'))

@app.route('/airlines/edit/<int:airline_id>', methods=['POST'])
@login_required
def edit_airline(airline_id):
    name = request.form.get('airline_name', '').strip()
    country = request.form.get('country', '').strip()
    try:
        execute_db("UPDATE airline SET airline_name = %s, country = %s WHERE airline_id = %s;", (name, country, airline_id))
        flash(f"Airline #{airline_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('airlines'))

@app.route('/airlines/delete/<int:airline_id>', methods=['POST'])
@login_required
def delete_airline(airline_id):
    try:
        execute_db("DELETE FROM airline WHERE airline_id = %s;", (airline_id,))
        flash(f"Airline #{airline_id} deleted successfully.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('airlines'))

# =========================================================================
# Terminal Module
# =========================================================================

@app.route('/terminals')
@login_required
def terminals():
    try:
        terminal_list = query_db("""
            SELECT terminal_id AS Terminal_ID, terminal_name AS Name,
                   location AS Location, capacity AS Capacity,
                   COALESCE(number_of_gates, 0) AS Number_Of_Gates,
                   COALESCE(facilities, '') AS Facilities,
                   COALESCE(status, 'Active') AS Status
            FROM terminal
            ORDER BY terminal_id ASC;
        """)
    except Exception as e:
        flash(format_db_error(e), "danger")
        terminal_list = []
    return render_template('terminals.html', active_page='terminals', terminals=terminal_list)

@app.route('/terminals/add', methods=['POST'])
@login_required
def add_terminal():
    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    capacity = request.form.get('capacity', 0)
    try:
        execute_db("INSERT INTO terminal (terminal_name, location, capacity) VALUES (%s, %s, %s);", (name, location, int(capacity)))
        flash(f"Terminal '{name}' created.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('terminals'))

@app.route('/terminals/edit/<int:terminal_id>', methods=['POST'])
@login_required
def edit_terminal(terminal_id):
    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    capacity = request.form.get('capacity', 0)
    try:
        execute_db("UPDATE terminal SET terminal_name = %s, location = %s, capacity = %s WHERE terminal_id = %s;", (name, location, int(capacity), terminal_id))
        flash(f"Terminal #{terminal_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('terminals'))

@app.route('/terminals/delete/<int:terminal_id>', methods=['POST'])
@login_required
def delete_terminal(terminal_id):
    try:
        execute_db("DELETE FROM terminal WHERE terminal_id = %s;", (terminal_id,))
        flash(f"Terminal #{terminal_id} deleted.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('terminals'))

# =========================================================================
# Gate Module
# =========================================================================

@app.route('/gates')
@login_required
def gates():
    try:
        gate_list = query_db("""
            SELECT g.gate_id AS Gate_ID, g.gate_no AS Gate_Number, g.termianl_no AS Terminal_ID,
                   COALESCE(t.terminal_name, CONCAT('Terminal #', g.termianl_no)) AS Terminal_Name,
                   COALESCE(t.location, 'N/A') AS Terminal_Location
            FROM gate g
            LEFT JOIN terminal t ON g.termianl_no = t.terminal_id
            ORDER BY g.gate_id ASC;
        """)
        terminal_list = query_db("SELECT terminal_id AS Terminal_ID, terminal_name AS Name, location AS Location FROM terminal ORDER BY terminal_name ASC;")
    except Exception as e:
        flash(format_db_error(e), "danger")
        gate_list = []
        terminal_list = []
    return render_template('gates.html', active_page='gates', gates=gate_list, terminals=terminal_list)

@app.route('/gates/add', methods=['POST'])
@login_required
def add_gate():
    gate_number = request.form.get('gate_number', '').strip()
    terminal_id = request.form.get('terminal_id')
    try:
        execute_db("INSERT INTO gate (gate_no, termianl_no) VALUES (%s, %s);", (gate_number, int(terminal_id)))
        flash(f"Gate {gate_number} registered successfully.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('gates'))

@app.route('/gates/edit/<int:gate_id>', methods=['POST'])
@login_required
def edit_gate(gate_id):
    gate_number = request.form.get('gate_number', '').strip()
    terminal_id = request.form.get('terminal_id')
    try:
        execute_db("UPDATE gate SET gate_no = %s, termianl_no = %s WHERE gate_id = %s;", (gate_number, int(terminal_id), gate_id))
        flash(f"Gate #{gate_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('gates'))

@app.route('/gates/delete/<int:gate_id>', methods=['POST'])
@login_required
def delete_gate(gate_id):
    try:
        execute_db("DELETE FROM gate WHERE gate_id = %s;", (gate_id,))
        flash(f"Gate #{gate_id} deleted.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('gates'))

# =========================================================================
# Flight Module
# =========================================================================

@app.route('/flights')
@login_required
def flights():
    try:
        flight_list = query_db("""
            SELECT f.Flight_ID, f.Flight_No, f.Airline_ID, f.Source, f.Destination,
                   f.Departure_Time, f.Arrival_Time, f.Aircraft_Type, f.Status,
                   f.Terminal_ID, f.Gate_ID,
                   COALESCE(a.airline_name, 'Unknown Airline') AS Airline_Name,
                   COALESCE(t.terminal_name, CONCAT('Terminal #', f.Terminal_ID)) AS Terminal_Name,
                   COALESCE(g.gate_no, CONCAT('Gate #', f.Gate_ID)) AS Gate_Number
            FROM flight f
            LEFT JOIN airline a ON f.Airline_ID = a.airline_id
            LEFT JOIN terminal t ON f.Terminal_ID = t.terminal_id
            LEFT JOIN gate g ON f.Gate_ID = g.gate_id
            ORDER BY f.Departure_Time ASC;
        """)
        airlines_list = query_db("SELECT airline_id AS Airline_ID, airline_name AS Airline_Name, country AS Country FROM airline ORDER BY airline_name ASC;")
        terminals_list = query_db("SELECT terminal_id AS Terminal_ID, terminal_name AS Name, location AS Location FROM terminal ORDER BY terminal_name ASC;")
        gates_list = query_db("""
            SELECT g.gate_id AS Gate_ID, g.gate_no AS Gate_Number,
                   COALESCE(t.terminal_name, CONCAT('Terminal #', g.termianl_no)) AS Terminal_Name
            FROM gate g
            LEFT JOIN terminal t ON g.termianl_no = t.terminal_id
            ORDER BY g.gate_no ASC;
        """)
    except Exception as e:
        flash(format_db_error(e), "danger")
        flight_list = []
        airlines_list = []
        terminals_list = []
        gates_list = []
    return render_template('flights.html', active_page='flights', flights=flight_list, airlines=airlines_list, terminals=terminals_list, gates=gates_list)

@app.route('/flights/add', methods=['POST'])
@login_required
def add_flight():
    flight_no = request.form.get('flight_no', '').strip()
    airline_id = request.form.get('airline_id')
    source = request.form.get('source', '').strip()
    destination = request.form.get('destination', '').strip()
    departure_time = request.form.get('departure_time')
    arrival_time = request.form.get('arrival_time')
    aircraft_type = request.form.get('aircraft_type', '').strip()
    status = request.form.get('status', 'Scheduled')
    terminal_id = request.form.get('terminal_id')
    gate_id = request.form.get('gate_id')

    try:
        execute_db("""
            INSERT INTO flight (Flight_No, Airline_ID, Source, Destination, Departure_Time, Arrival_Time, Aircraft_Type, Status, Terminal_ID, Gate_ID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (flight_no, int(airline_id), source, destination, departure_time, arrival_time, aircraft_type, status, int(terminal_id), int(gate_id)))
        flash(f"Flight {flight_no} successfully scheduled.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('flights'))

@app.route('/flights/edit/<int:flight_id>', methods=['POST'])
@login_required
def edit_flight(flight_id):
    flight_no = request.form.get('flight_no', '').strip()
    airline_id = request.form.get('airline_id')
    source = request.form.get('source', '').strip()
    destination = request.form.get('destination', '').strip()
    departure_time = request.form.get('departure_time')
    arrival_time = request.form.get('arrival_time')
    aircraft_type = request.form.get('aircraft_type', '').strip()
    status = request.form.get('status')
    terminal_id = request.form.get('terminal_id')
    gate_id = request.form.get('gate_id')

    try:
        execute_db("""
            UPDATE flight 
            SET Flight_No=%s, Airline_ID=%s, Source=%s, Destination=%s, Departure_Time=%s,
                Arrival_Time=%s, Aircraft_Type=%s, Status=%s, Terminal_ID=%s, Gate_ID=%s
            WHERE Flight_ID=%s;
        """, (flight_no, int(airline_id), source, destination, departure_time, arrival_time, aircraft_type, status, int(terminal_id), int(gate_id), flight_id))
        flash(f"Flight #{flight_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('flights'))

@app.route('/flights/delete/<int:flight_id>', methods=['POST'])
@login_required
def delete_flight(flight_id):
    try:
        execute_db("DELETE FROM flight WHERE Flight_ID = %s;", (flight_id,))
        flash(f"Flight #{flight_id} deleted.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('flights'))

# =========================================================================
# Passenger Module & 360° View
# =========================================================================

@app.route('/passengers')
@login_required
def passengers():
    try:
        passenger_list = query_db("""
            SELECT passenger_id AS Passenger_ID, name AS Name, gender AS Gender, age AS Age,
                   passport_no AS Passport_No, phone AS Phone, email AS Email, address AS Address
            FROM passenger
            ORDER BY passenger_id ASC;
        """)
    except Exception as e:
        flash(format_db_error(e), "danger")
        passenger_list = []
    return render_template('passengers.html', active_page='passengers', passengers=passenger_list)

@app.route('/passengers/<int:passenger_id>')
@login_required
def passenger_details(passenger_id):
    """
    Passenger 360° View:
    Displays passenger profile + bookings + flights + check-in + baggage + security check.
    """
    try:
        passenger = query_db("""
            SELECT passenger_id AS Passenger_ID, name AS Name, gender AS Gender, age AS Age,
                   passport_no AS Passport_No, phone AS Phone, email AS Email, address AS Address
            FROM passenger
            WHERE passenger_id = %s;
        """, (passenger_id,), one=True)
        if not passenger:
            flash(f"Passenger #{passenger_id} not found.", "warning")
            return redirect(url_for('passengers'))

        # Fetch Bookings with linked Flight, Airline, Terminal, and Gate info
        bookings = query_db("""
            SELECT b.booking_id AS Booking_ID, b.booking_date AS Booking_Date, b.travel_class AS Travel_Class,
                   b.seat_no AS Seat_No, b.booking_status AS Booking_Status, b.payment_status AS Payment_Status, b.fare AS Fare,
                   f.Flight_ID, f.Flight_No, f.Source, f.Destination, f.Departure_Time, f.Arrival_Time,
                   COALESCE(a.airline_name, 'N/A') AS Airline_Name,
                   COALESCE(t.terminal_name, 'N/A') AS Terminal_Name,
                   COALESCE(g.gate_no, 'N/A') AS Gate_Number
            FROM booking b
            LEFT JOIN flight f ON b.flight_id = f.Flight_ID
            LEFT JOIN airline a ON f.Airline_ID = a.airline_id
            LEFT JOIN terminal t ON f.Terminal_ID = t.terminal_id
            LEFT JOIN gate g ON f.Gate_ID = g.gate_id
            WHERE b.passenger_id = %s
            ORDER BY b.booking_date DESC;
        """, (passenger_id,))

        # Fetch Check-In records for this passenger's bookings
        checkins = query_db("""
            SELECT c.CheckIn_ID, c.Counter_No, c.CheckIn_Time, c.Boarding_Pass_No, c.Baggage_Count, c.Boarding_Status,
                   COALESCE(e.Name, 'Staff') AS Employee_Name, COALESCE(e.Role, 'Check-In') AS Employee_Role,
                   b.booking_id AS Booking_ID, f.Flight_No, b.seat_no AS Seat_No
            FROM check_in c
            LEFT JOIN booking b ON c.Booking_ID = b.booking_id
            LEFT JOIN flight f ON b.flight_id = f.Flight_ID
            LEFT JOIN employee e ON c.Employee_ID = e.Employee_ID
            WHERE b.passenger_id = %s
            ORDER BY c.CheckIn_Time DESC;
        """, (passenger_id,))

        # Fetch Baggage registered for this passenger
        baggage_items = query_db("""
            SELECT bg.Baggage_ID, bg.Weight, bg.Number_Of_Bags, bg.Tag_No, bg.Status,
                   f.Flight_No, COALESCE(e.Name, 'Staff') AS Employee_Name
            FROM baggage bg
            LEFT JOIN flight f ON bg.Flight_ID = f.Flight_ID
            LEFT JOIN employee e ON bg.Employee_ID = e.Employee_ID
            WHERE bg.Passenger_ID = %s
            ORDER BY bg.Baggage_ID DESC;
        """, (passenger_id,))

        # Fetch Security Checks conducted on this passenger
        security_checks = query_db("""
            SELECT s.Security_ID, s.Officer_Name, s.Check_Time, s.Status, s.Remarks,
                   s.Employee_ID, COALESCE(e.Name, s.Officer_Name, 'Security Staff') AS Staff_Employee_Name
            FROM security_check s
            LEFT JOIN employee e ON s.Employee_ID = e.Employee_ID
            WHERE s.Passenger_ID = %s
            ORDER BY s.Check_Time DESC;
        """, (passenger_id,))

        all_passengers = query_db("SELECT passenger_id AS Passenger_ID, name AS Name, passport_no AS Passport_No FROM passenger ORDER BY name ASC;")

        return render_template(
            'passenger_details.html',
            active_page='passengers',
            passenger=passenger,
            bookings=bookings,
            checkins=checkins,
            baggage_items=baggage_items,
            security_checks=security_checks,
            all_passengers=all_passengers
        )
    except Exception as e:
        flash(format_db_error(e), "danger")
        return redirect(url_for('passengers'))

@app.route('/passengers/add', methods=['POST'])
@login_required
def add_passenger():
    name = request.form.get('name', '').strip()
    gender = request.form.get('gender', 'Male')
    age = request.form.get('age', 0)
    passport_no = request.form.get('passport_no', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()

    try:
        execute_db("""
            INSERT INTO passenger (name, gender, age, passport_no, phone, email, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (name, gender, int(age), passport_no, phone, email, address))
        flash(f"Passenger '{name}' registered successfully.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('passengers'))

@app.route('/passengers/edit/<int:passenger_id>', methods=['POST'])
@login_required
def edit_passenger(passenger_id):
    name = request.form.get('name', '').strip()
    gender = request.form.get('gender')
    age = request.form.get('age', 0)
    passport_no = request.form.get('passport_no', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()

    try:
        execute_db("""
            UPDATE passenger
            SET name=%s, gender=%s, age=%s, passport_no=%s, phone=%s, email=%s, address=%s
            WHERE passenger_id=%s;
        """, (name, gender, int(age), passport_no, phone, email, address, passenger_id))
        flash(f"Passenger #{passenger_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('passengers'))

@app.route('/passengers/delete/<int:passenger_id>', methods=['POST'])
@login_required
def delete_passenger(passenger_id):
    try:
        execute_db("DELETE FROM passenger WHERE passenger_id = %s;", (passenger_id,))
        flash(f"Passenger #{passenger_id} deleted.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('passengers'))

# =========================================================================
# Booking Module
# =========================================================================

@app.route('/bookings')
@login_required
def bookings():
    try:
        booking_list = query_db("""
            SELECT b.booking_id AS Booking_ID, b.passenger_id AS Passenger_ID, b.flight_id AS Flight_ID,
                   b.booking_date AS Booking_Date, b.travel_class AS Travel_Class, b.seat_no AS Seat_No,
                   b.booking_status AS Booking_Status, b.payment_status AS Payment_Status, b.fare AS Fare,
                   COALESCE(p.name, 'Unknown') AS Passenger_Name, COALESCE(p.passport_no, 'N/A') AS Passport_No,
                   COALESCE(f.Flight_No, 'N/A') AS Flight_No, f.Source, f.Destination
            FROM booking b
            LEFT JOIN passenger p ON b.passenger_id = p.passenger_id
            LEFT JOIN flight f ON b.flight_id = f.Flight_ID
            ORDER BY b.booking_id DESC;
        """)
        passengers_list = query_db("SELECT passenger_id AS Passenger_ID, name AS Name, passport_no AS Passport_No FROM passenger ORDER BY name ASC;")
        flights_list = query_db("SELECT Flight_ID, Flight_No, Source, Destination FROM flight ORDER BY Flight_No ASC;")
    except Exception as e:
        flash(format_db_error(e), "danger")
        booking_list = []
        passengers_list = []
        flights_list = []
    return render_template('bookings.html', active_page='bookings', bookings=booking_list, passengers=passengers_list, flights=flights_list)

@app.route('/bookings/add', methods=['POST'])
@login_required
def add_booking():
    passenger_id = request.form.get('passenger_id')
    flight_id = request.form.get('flight_id')
    booking_date = request.form.get('booking_date')
    travel_class = request.form.get('travel_class', 'Economy')
    seat_no = request.form.get('seat_no', '').strip()
    booking_status = request.form.get('booking_status', 'Confirmed')
    payment_status = request.form.get('payment_status', 'Paid')
    fare = request.form.get('fare', 0)

    try:
        execute_db("""
            INSERT INTO booking (passenger_id, flight_id, booking_date, travel_class, seat_no, booking_status, payment_status, fare)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (int(passenger_id), int(flight_id), booking_date, travel_class, seat_no, booking_status, payment_status, float(fare)))
        flash("Flight booking created successfully.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('bookings'))

@app.route('/bookings/edit/<int:booking_id>', methods=['POST'])
@login_required
def edit_booking(booking_id):
    passenger_id = request.form.get('passenger_id')
    flight_id = request.form.get('flight_id')
    booking_date = request.form.get('booking_date')
    travel_class = request.form.get('travel_class')
    seat_no = request.form.get('seat_no', '').strip()
    booking_status = request.form.get('booking_status')
    payment_status = request.form.get('payment_status')
    fare = request.form.get('fare', 0)

    try:
        execute_db("""
            UPDATE booking
            SET passenger_id=%s, flight_id=%s, booking_date=%s, travel_class=%s,
                seat_no=%s, booking_status=%s, payment_status=%s, fare=%s
            WHERE booking_id=%s;
        """, (int(passenger_id), int(flight_id), booking_date, travel_class, seat_no, booking_status, payment_status, float(fare), booking_id))
        flash(f"Booking #{booking_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('bookings'))

@app.route('/bookings/delete/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    try:
        execute_db("DELETE FROM booking WHERE booking_id = %s;", (booking_id,))
        flash(f"Booking #{booking_id} deleted.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('bookings'))

# =========================================================================
# Check-In Module (Auto uses session['employee_id'])
# =========================================================================

@app.route('/checkin')
@login_required
def checkin():
    try:
        checkin_list = query_db("""
            SELECT c.CheckIn_ID, c.Booking_ID, c.Employee_ID, c.Counter_No, c.CheckIn_Time,
                   c.Boarding_Pass_No, c.Baggage_Count, c.Boarding_Status,
                   p.passenger_id AS Passenger_ID, COALESCE(p.name, 'Passenger') AS Passenger_Name,
                   COALESCE(p.passport_no, 'N/A') AS Passport_No,
                   COALESCE(f.Flight_No, 'Flight') AS Flight_No, f.Source, f.Destination,
                   b.seat_no AS Seat_No,
                   COALESCE(e.Name, 'Staff') AS Employee_Name
            FROM check_in c
            LEFT JOIN booking b ON c.Booking_ID = b.booking_id
            LEFT JOIN passenger p ON b.passenger_id = p.passenger_id
            LEFT JOIN flight f ON b.flight_id = f.Flight_ID
            LEFT JOIN employee e ON c.Employee_ID = e.Employee_ID
            ORDER BY c.CheckIn_ID DESC;
        """)

        # Available bookings for check-in
        bookings_list = query_db("""
            SELECT b.booking_id AS Booking_ID, b.seat_no AS Seat_No,
                   COALESCE(p.name, 'Passenger') AS Passenger_Name,
                   COALESCE(f.Flight_No, 'Flight') AS Flight_No
            FROM booking b
            LEFT JOIN passenger p ON b.passenger_id = p.passenger_id
            LEFT JOIN flight f ON b.flight_id = f.Flight_ID
            ORDER BY b.booking_id DESC;
        """)
    except Exception as e:
        flash(format_db_error(e), "danger")
        checkin_list = []
        bookings_list = []
    return render_template('checkin.html', active_page='checkin', checkins=checkin_list, bookings=bookings_list)

@app.route('/checkin/add', methods=['POST'])
@login_required
def add_checkin():
    booking_id = request.form.get('booking_id')
    counter_no = request.form.get('counter_no', '').strip()
    checkin_time = request.form.get('checkin_time')
    boarding_pass_no = request.form.get('boarding_pass_no', '').strip()
    baggage_count = request.form.get('baggage_count', 0)
    boarding_status = request.form.get('boarding_status', 'Checked-In')
    # Automatically associate currently logged-in employee ID
    employee_id = session.get('employee_id')

    try:
        execute_db("""
            INSERT INTO check_in (Booking_ID, Employee_ID, Counter_No, CheckIn_Time, Boarding_Pass_No, Baggage_Count, Boarding_Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (int(booking_id), int(employee_id), counter_no, checkin_time, boarding_pass_no, int(baggage_count), boarding_status))
        flash(f"Check-In processed. Boarding Pass {boarding_pass_no} issued successfully.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('checkin'))

@app.route('/checkin/edit/<int:checkin_id>', methods=['POST'])
@login_required
def edit_checkin(checkin_id):
    booking_id = request.form.get('booking_id')
    counter_no = request.form.get('counter_no', '').strip()
    checkin_time = request.form.get('checkin_time')
    boarding_pass_no = request.form.get('boarding_pass_no', '').strip()
    baggage_count = request.form.get('baggage_count', 0)
    boarding_status = request.form.get('boarding_status')

    try:
        execute_db("""
            UPDATE check_in
            SET Booking_ID=%s, Counter_No=%s, CheckIn_Time=%s, Boarding_Pass_No=%s,
                Baggage_Count=%s, Boarding_Status=%s
            WHERE CheckIn_ID=%s;
        """, (int(booking_id), counter_no, checkin_time, boarding_pass_no, int(baggage_count), boarding_status, checkin_id))
        flash(f"Check-In record #{checkin_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('checkin'))

@app.route('/checkin/delete/<int:checkin_id>', methods=['POST'])
@login_required
def delete_checkin(checkin_id):
    try:
        execute_db("DELETE FROM check_in WHERE CheckIn_ID = %s;", (checkin_id,))
        flash(f"Check-In record #{checkin_id} deleted.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('checkin'))

# =========================================================================
# Baggage Module (Auto uses session['employee_id'])
# =========================================================================

@app.route('/baggage')
@login_required
def baggage():
    try:
        baggage_list = query_db("""
            SELECT bg.Baggage_ID, bg.Passenger_ID, bg.Flight_ID, bg.Employee_ID,
                   bg.Weight, bg.Number_Of_Bags, bg.Tag_No, bg.Status,
                   COALESCE(p.name, 'Passenger') AS Passenger_Name, COALESCE(p.passport_no, 'N/A') AS Passport_No,
                   COALESCE(f.Flight_No, 'Flight') AS Flight_No, f.Source, f.Destination,
                   COALESCE(e.Name, 'Staff') AS Employee_Name
            FROM baggage bg
            LEFT JOIN passenger p ON bg.Passenger_ID = p.passenger_id
            LEFT JOIN flight f ON bg.Flight_ID = f.Flight_ID
            LEFT JOIN employee e ON bg.Employee_ID = e.Employee_ID
            ORDER BY bg.Baggage_ID DESC;
        """)
        passengers_list = query_db("SELECT passenger_id AS Passenger_ID, name AS Name, passport_no AS Passport_No FROM passenger ORDER BY name ASC;")
        flights_list = query_db("SELECT Flight_ID, Flight_No, Source, Destination FROM flight ORDER BY Flight_No ASC;")
    except Exception as e:
        flash(format_db_error(e), "danger")
        baggage_list = []
        passengers_list = []
        flights_list = []
    return render_template('baggage.html', active_page='baggage', baggage_list=baggage_list, passengers=passengers_list, flights=flights_list)

@app.route('/baggage/add', methods=['POST'])
@login_required
def add_baggage():
    passenger_id = request.form.get('passenger_id')
    flight_id = request.form.get('flight_id')
    weight = request.form.get('weight', 0)
    number_of_bags = request.form.get('number_of_bags', 1)
    tag_no = request.form.get('tag_no', '').strip()
    status = request.form.get('status', 'Checked')
    # Automatically associate currently logged-in employee ID
    employee_id = session.get('employee_id')

    try:
        execute_db("""
            INSERT INTO baggage (Passenger_ID, Flight_ID, Employee_ID, Weight, Number_Of_Bags, Tag_No, Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (int(passenger_id), int(flight_id), int(employee_id), float(weight), int(number_of_bags), tag_no, status))
        flash(f"Baggage record created with Tag #{tag_no}.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('baggage'))

@app.route('/baggage/edit/<int:baggage_id>', methods=['POST'])
@login_required
def edit_baggage(baggage_id):
    passenger_id = request.form.get('passenger_id')
    flight_id = request.form.get('flight_id')
    weight = request.form.get('weight', 0)
    number_of_bags = request.form.get('number_of_bags', 1)
    tag_no = request.form.get('tag_no', '').strip()
    status = request.form.get('status')

    try:
        execute_db("""
            UPDATE baggage
            SET Passenger_ID=%s, Flight_ID=%s, Weight=%s, Number_Of_Bags=%s, Tag_No=%s, Status=%s
            WHERE Baggage_ID=%s;
        """, (int(passenger_id), int(flight_id), float(weight), int(number_of_bags), tag_no, status, baggage_id))
        flash(f"Baggage #{baggage_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('baggage'))

@app.route('/baggage/delete/<int:baggage_id>', methods=['POST'])
@login_required
def delete_baggage(baggage_id):
    try:
        execute_db("DELETE FROM baggage WHERE Baggage_ID = %s;", (baggage_id,))
        flash(f"Baggage record #{baggage_id} deleted.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('baggage'))

# =========================================================================
# Security Check Module (Auto uses session['employee_id'])
# =========================================================================

@app.route('/security')
@login_required
def security():
    try:
        security_list = query_db("""
            SELECT s.Security_ID, s.Passenger_ID, s.Employee_ID, s.Officer_Name,
                   s.Check_Time, s.Status, s.Remarks,
                   COALESCE(p.name, 'Passenger') AS Passenger_Name, COALESCE(p.passport_no, 'N/A') AS Passport_No,
                   COALESCE(e.Name, s.Officer_Name, 'Security Staff') AS Employee_Name
            FROM security_check s
            LEFT JOIN passenger p ON s.Passenger_ID = p.passenger_id
            LEFT JOIN employee e ON s.Employee_ID = e.Employee_ID
            ORDER BY s.Security_ID DESC;
        """)
        passengers_list = query_db("SELECT passenger_id AS Passenger_ID, name AS Name, passport_no AS Passport_No FROM passenger ORDER BY name ASC;")
    except Exception as e:
        flash(format_db_error(e), "danger")
        security_list = []
        passengers_list = []
    return render_template('security.html', active_page='security', security_logs=security_list, passengers=passengers_list)

@app.route('/security/add', methods=['POST'])
@login_required
def add_security():
    passenger_id = request.form.get('passenger_id')
    officer_name = request.form.get('officer_name', '').strip()
    check_time = request.form.get('check_time')
    status = request.form.get('status', 'Cleared')
    remarks = request.form.get('remarks', '').strip()
    # Automatically associate currently logged-in employee ID
    employee_id = session.get('employee_id')

    try:
        execute_db("""
            INSERT INTO security_check (Passenger_ID, Employee_ID, Officer_Name, Check_Time, Status, Remarks)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (int(passenger_id), int(employee_id), officer_name, check_time, status, remarks))
        flash("Security screening record saved.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('security'))

@app.route('/security/edit/<int:security_id>', methods=['POST'])
@login_required
def edit_security(security_id):
    passenger_id = request.form.get('passenger_id')
    officer_name = request.form.get('officer_name', '').strip()
    check_time = request.form.get('check_time')
    status = request.form.get('status')
    remarks = request.form.get('remarks', '').strip()

    try:
        execute_db("""
            UPDATE security_check
            SET Passenger_ID=%s, Officer_Name=%s, Check_Time=%s, Status=%s, Remarks=%s
            WHERE Security_ID=%s;
        """, (int(passenger_id), officer_name, check_time, status, remarks, security_id))
        flash(f"Security screening #{security_id} updated.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('security'))

@app.route('/security/delete/<int:security_id>', methods=['POST'])
@login_required
def delete_security(security_id):
    try:
        execute_db("DELETE FROM security_check WHERE Security_ID = %s;", (security_id,))
        flash(f"Security record #{security_id} deleted.", "success")
    except Exception as e:
        flash(format_db_error(e), "danger")
    return redirect(url_for('security'))

# =========================================================================
# Error Handlers
# =========================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', content="<div class='text-center py-5'><h2>404 - Page Not Found</h2><p class='text-secondary'>The requested operations endpoint does not exist.</p><a href='/dashboard' class='btn btn-primary-custom'>Return to Dashboard</a></div>"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', content=f"<div class='text-center py-5'><h2 class='text-danger'>500 - Internal Server Error</h2><p class='text-secondary'>{str(e)}</p><a href='/dashboard' class='btn btn-secondary-custom'>Return to Dashboard</a></div>"), 500

if __name__ == '__main__':
    # Print database test connection status on startup
    ok, msg = test_connection()
    if ok:
        print(f"[SkyOps] Connected to MySQL database '{Config.MYSQL_DB}' successfully.")
    else:
        print(f"[SkyOps Warning] MySQL connection attempt: {msg}")
        print("[SkyOps Tip] Verify your MySQL server is running and .env credentials are correct.")

    app.run(host='0.0.0.0', port=5000, debug=True)
