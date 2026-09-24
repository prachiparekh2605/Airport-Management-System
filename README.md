# SkyOps Hub - Airport Staff Management System

A full-stack, college database project built with **Python Flask**, **MySQL**, and modern **Bootstrap 5 / HTML5 / CSS3 / JavaScript**.

---

## 🗄️ Database Architecture (`airport_managment_system`)

The system directly connects to and manages the 10 relational tables of `airport_managment_system`:

1. **`Employee`**: Airport personnel with role-based credentials.
2. **`Airline`**: Operating commercial carriers and partner airlines.
3. **`Terminal`**: Airport terminal facilities, wings, and hourly capacity.
4. **`Gate`**: Boarding gates linked to specific terminals (`1:N`).
5. **`Flight`**: Scheduled flights with relationships to Airlines, Terminals, and Gates (`1:N`).
6. **`Passenger`**: Registered passengers and passport documentation.
7. **`Booking`**: Ticket reservations linked to Passengers and Flights (`1:N`).
8. **`Check_In`**: Boarding pass processing linked to Bookings and Staff (`1:N`).
9. **`Baggage`**: Checked luggage with tag tracking linked to Passengers, Flights, and Staff (`1:N`).
10. **`Security_Check`**: Security screening records linked to Passengers and Staff (`1:N`).

---

## 👥 Default Employee Credentials

| Employee ID | Name | Username | Password | Role / Access Level |
|---|---|---|---|---|
| **201** | Rajesh Kumar | `rajesh` | `Rajesh@123` | **Airport Administrator** (Full Admin) |
| **202** | Priya Singh | `priya` | `Priya@123` | **Check-In Officer** |
| **203** | Amit Verma | `amit` | `Amit@123` | **Security Officer** |
| **204** | Neha Patel | `neha` | `Neha@123` | **Flight Coordinator** |
| **205** | Vikram Shah | `vikram` | `Vikram@123` | **Baggage Officer** |

---

## 🚀 Getting Started

### 1. Configure MySQL in `.env`
Open the `.env` file in the project folder and update your MySQL connection details if needed:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password_here
MYSQL_DB=airport_managment_system
SECRET_KEY=airport_management_super_secret_key_2026
```

*(If you ever need to create or inspect the database schema or seed records, the exact script is located in `database/airport.sql`)*.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Application
```bash
python run.py
```
Or:
```bash
python app.py
```

### 4. Open in Browser
Visit **http://127.0.0.1:5000** in your browser.
Log in with username `rajesh` and password `Rajesh@123`.

---

## 🌟 Key Features

- **Staff Authentication**: Secure login verifying credentials directly against the `Employee` table in MySQL.
- **Operations Dashboard**: Real-time counter cards showing total Employees, Passengers, Airlines, Flights, Bookings, and Gates, plus a live flight board.
- **Role-Based Access**: Sensitive employee modifications are restricted to `Airport Administrator`.
- **Foreign Key Dropdowns**: All forms use readable dropdowns (e.g. Airline name, Terminal name, Gate number, Passenger name) instead of forcing manual foreign-key entry.
- **Auto-Assigned Staff ID**: Check-In, Baggage, and Security operations automatically tag the currently logged-in employee ID.
- **Passenger 360° View**: Unified relational view showing a passenger's complete lifecycle across Bookings, Flights, Check-in, Baggage, and Security screening.
- **Search & Filtering**: Real-time instant filtering across every data table.
- **Safe SQL Execution**: 100% parameterized queries (`%s`) preventing SQL injection.
