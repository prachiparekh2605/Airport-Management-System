-- Airport Management System Database Schema & Initial Data
-- Database Name: airport_managment_system

CREATE DATABASE IF NOT EXISTS `airport_managment_system`
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `airport_managment_system`;

-- ========================================================
-- 1. Employee Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Employee` (
    `Employee_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Name` VARCHAR(100) NOT NULL,
    `Username` VARCHAR(50) UNIQUE NOT NULL,
    `Password` VARCHAR(255) NOT NULL,
    `Role` VARCHAR(50) NOT NULL,
    `Phone` VARCHAR(20),
    `Email` VARCHAR(100)
) ENGINE=InnoDB;

-- ========================================================
-- 2. Airline Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Airline` (
    `Airline_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Airline_Name` VARCHAR(100) NOT NULL,
    `Country` VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- ========================================================
-- 3. Terminal Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Terminal` (
    `Terminal_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Name` VARCHAR(50) NOT NULL,
    `Location` VARCHAR(100) NOT NULL,
    `Capacity` INT NOT NULL
) ENGINE=InnoDB;

-- ========================================================
-- 4. Gate Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Gate` (
    `Gate_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Gate_Number` VARCHAR(20) NOT NULL,
    `Terminal_ID` INT NOT NULL,
    FOREIGN KEY (`Terminal_ID`) REFERENCES `Terminal`(`Terminal_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ========================================================
-- 5. Flight Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Flight` (
    `Flight_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Flight_No` VARCHAR(20) NOT NULL,
    `Airline_ID` INT NOT NULL,
    `Source` VARCHAR(100) NOT NULL,
    `Destination` VARCHAR(100) NOT NULL,
    `Departure_Time` DATETIME NOT NULL,
    `Arrival_Time` DATETIME NOT NULL,
    `Aircraft_Type` VARCHAR(50) NOT NULL,
    `Status` VARCHAR(30) NOT NULL DEFAULT 'Scheduled',
    `Terminal_ID` INT NOT NULL,
    `Gate_ID` INT NOT NULL,
    FOREIGN KEY (`Airline_ID`) REFERENCES `Airline`(`Airline_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (`Terminal_ID`) REFERENCES `Terminal`(`Terminal_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (`Gate_ID`) REFERENCES `Gate`(`Gate_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ========================================================
-- 6. Passenger Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Passenger` (
    `Passenger_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Name` VARCHAR(100) NOT NULL,
    `Gender` VARCHAR(10) NOT NULL,
    `Age` INT NOT NULL,
    `Passport_No` VARCHAR(30) UNIQUE NOT NULL,
    `Phone` VARCHAR(20),
    `Email` VARCHAR(100),
    `Address` TEXT
) ENGINE=InnoDB;

-- ========================================================
-- 7. Booking Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Booking` (
    `Booking_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Passenger_ID` INT NOT NULL,
    `Flight_ID` INT NOT NULL,
    `Booking_Date` DATE NOT NULL,
    `Travel_Class` VARCHAR(30) NOT NULL,
    `Seat_No` VARCHAR(10) NOT NULL,
    `Booking_Status` VARCHAR(30) NOT NULL DEFAULT 'Confirmed',
    `Payment_Status` VARCHAR(30) NOT NULL DEFAULT 'Paid',
    `Fare` DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (`Passenger_ID`) REFERENCES `Passenger`(`Passenger_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (`Flight_ID`) REFERENCES `Flight`(`Flight_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ========================================================
-- 8. Check_In Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Check_In` (
    `CheckIn_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Booking_ID` INT NOT NULL,
    `Employee_ID` INT NOT NULL,
    `Counter_No` VARCHAR(20) NOT NULL,
    `CheckIn_Time` DATETIME NOT NULL,
    `Boarding_Pass_No` VARCHAR(50) UNIQUE NOT NULL,
    `Baggage_Count` INT NOT NULL DEFAULT 0,
    `Boarding_Status` VARCHAR(30) NOT NULL DEFAULT 'Checked-In',
    FOREIGN KEY (`Booking_ID`) REFERENCES `Booking`(`Booking_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (`Employee_ID`) REFERENCES `Employee`(`Employee_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ========================================================
-- 9. Baggage Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Baggage` (
    `Baggage_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Passenger_ID` INT NOT NULL,
    `Flight_ID` INT NOT NULL,
    `Employee_ID` INT NOT NULL,
    `Weight` DECIMAL(6, 2) NOT NULL,
    `Number_Of_Bags` INT NOT NULL,
    `Tag_No` VARCHAR(50) UNIQUE NOT NULL,
    `Status` VARCHAR(30) NOT NULL DEFAULT 'Checked',
    FOREIGN KEY (`Passenger_ID`) REFERENCES `Passenger`(`Passenger_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (`Flight_ID`) REFERENCES `Flight`(`Flight_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (`Employee_ID`) REFERENCES `Employee`(`Employee_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ========================================================
-- 10. Security_Check Table
-- ========================================================
CREATE TABLE IF NOT EXISTS `Security_Check` (
    `Security_ID` INT PRIMARY KEY AUTO_INCREMENT,
    `Passenger_ID` INT NOT NULL,
    `Employee_ID` INT NOT NULL,
    `Officer_Name` VARCHAR(100) NOT NULL,
    `Check_Time` DATETIME NOT NULL,
    `Status` VARCHAR(30) NOT NULL DEFAULT 'Cleared',
    `Remarks` TEXT,
    FOREIGN KEY (`Passenger_ID`) REFERENCES `Passenger`(`Passenger_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (`Employee_ID`) REFERENCES `Employee`(`Employee_ID`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ========================================================
-- Initial Seed Data: Employees
-- ========================================================
INSERT INTO `Employee` (`Employee_ID`, `Name`, `Username`, `Password`, `Role`, `Phone`, `Email`)
VALUES
(201, 'Rajesh Kumar', 'rajesh', 'Rajesh@123', 'Airport Administrator', '+91 98765 43210', 'rajesh.kumar@airportops.com'),
(202, 'Priya Singh',  'priya',  'Priya@123',  'Check-In Officer',      '+91 98765 43211', 'priya.singh@airportops.com'),
(203, 'Amit Verma',   'amit',   'Amit@123',   'Security Officer',      '+91 98765 43212', 'amit.verma@airportops.com'),
(204, 'Neha Patel',   'neha',   'Neha@123',   'Flight Coordinator',    '+91 98765 43213', 'neha.patel@airportops.com'),
(205, 'Vikram Shah',  'vikram', 'Vikram@123', 'Baggage Officer',       '+91 98765 43214', 'vikram.shah@airportops.com')
ON DUPLICATE KEY UPDATE `Name`=VALUES(`Name`), `Password`=VALUES(`Password`), `Role`=VALUES(`Role`);

-- ========================================================
-- Seed Data: Airlines, Terminals, Gates, Flights
-- ========================================================
INSERT INTO `Airline` (`Airline_ID`, `Airline_Name`, `Country`) VALUES
(1, 'Air India', 'India'),
(2, 'IndiGo', 'India'),
(3, 'Emirates', 'United Arab Emirates'),
(4, 'Singapore Airlines', 'Singapore'),
(5, 'Qatar Airways', 'Qatar')
ON DUPLICATE KEY UPDATE `Airline_Name`=VALUES(`Airline_Name`);

INSERT INTO `Terminal` (`Terminal_ID`, `Name`, `Location`, `Capacity`) VALUES
(1, 'Terminal 1 (Domestic)', 'North Wing', 5000),
(2, 'Terminal 2 (International)', 'South Wing', 12000),
(3, 'Terminal 3 (Cargo & VIP)', 'East Wing', 2500)
ON DUPLICATE KEY UPDATE `Name`=VALUES(`Name`);

INSERT INTO `Gate` (`Gate_ID`, `Gate_Number`, `Terminal_ID`) VALUES
(1, 'A1', 1),
(2, 'A2', 1),
(3, 'B1', 2),
(4, 'B2', 2),
(5, 'C1', 3)
ON DUPLICATE KEY UPDATE `Gate_Number`=VALUES(`Gate_Number`);

INSERT INTO `Flight` (`Flight_ID`, `Flight_No`, `Airline_ID`, `Source`, `Destination`, `Departure_Time`, `Arrival_Time`, `Aircraft_Type`, `Status`, `Terminal_ID`, `Gate_ID`) VALUES
(1, 'AI-101', 1, 'Delhi (DEL)', 'Mumbai (BOM)', '2026-09-20 08:30:00', '2026-09-20 10:45:00', 'Boeing 777', 'Scheduled', 1, 1),
(2, '6E-452', 2, 'Delhi (DEL)', 'Bengaluru (BLR)', '2026-09-20 09:15:00', '2026-09-20 12:00:00', 'Airbus A320', 'Boarding', 1, 2),
(3, 'EK-512', 3, 'Delhi (DEL)', 'Dubai (DXB)', '2026-09-20 14:00:00', '2026-09-20 16:30:00', 'Boeing 777-300ER', 'Scheduled', 2, 3),
(4, 'SQ-403', 4, 'Delhi (DEL)', 'Singapore (SIN)', '2026-09-20 21:50:00', '2026-09-21 06:10:00', 'Airbus A350', 'On Time', 2, 4)
ON DUPLICATE KEY UPDATE `Flight_No`=VALUES(`Flight_No`);

-- ========================================================
-- Seed Data: Sample Passenger, Booking, Check-In, Baggage, Security
-- ========================================================
INSERT INTO `Passenger` (`Passenger_ID`, `Name`, `Gender`, `Age`, `Passport_No`, `Phone`, `Email`, `Address`) VALUES
(1, 'Aarav Sharma', 'Male', 29, 'P12345678', '+91 99887 76655', 'aarav.sharma@example.com', 'Flat 402, Green Park, New Delhi'),
(2, 'Ananya Iyer', 'Female', 34, 'K87654321', '+91 98112 23344', 'ananya.iyer@example.com', '12, Indiranagar, Bengaluru'),
(3, 'Rohan Mehta', 'Male', 42, 'M98765432', '+91 97654 32109', 'rohan.mehta@example.com', 'A-89, Marine Lines, Mumbai')
ON DUPLICATE KEY UPDATE `Name`=VALUES(`Name`);

INSERT INTO `Booking` (`Booking_ID`, `Passenger_ID`, `Flight_ID`, `Booking_Date`, `Travel_Class`, `Seat_No`, `Booking_Status`, `Payment_Status`, `Fare`) VALUES
(1, 1, 1, '2026-09-10', 'Economy', '14B', 'Confirmed', 'Paid', 6500.00),
(2, 2, 2, '2026-09-12', 'Business', '2A', 'Confirmed', 'Paid', 14500.00),
(3, 3, 3, '2026-09-15', 'Economy', '28F', 'Confirmed', 'Paid', 22000.00)
ON DUPLICATE KEY UPDATE `Seat_No`=VALUES(`Seat_No`);

INSERT INTO `Check_In` (`CheckIn_ID`, `Booking_ID`, `Employee_ID`, `Counter_No`, `CheckIn_Time`, `Boarding_Pass_No`, `Baggage_Count`, `Boarding_Status`) VALUES
(1, 1, 202, 'C-04', '2026-09-20 06:45:00', 'BP-AI101-14B', 1, 'Boarded'),
(2, 2, 202, 'C-02', '2026-09-20 07:30:00', 'BP-6E452-2A', 2, 'Checked-In')
ON DUPLICATE KEY UPDATE `Boarding_Pass_No`=VALUES(`Boarding_Pass_No`);

INSERT INTO `Baggage` (`Baggage_ID`, `Passenger_ID`, `Flight_ID`, `Employee_ID`, `Weight`, `Number_Of_Bags`, `Tag_No`, `Status`) VALUES
(1, 1, 1, 205, 16.50, 1, 'TAG-AI-9001', 'Loaded'),
(2, 2, 2, 205, 23.00, 2, 'TAG-6E-9002', 'Screened')
ON DUPLICATE KEY UPDATE `Tag_No`=VALUES(`Tag_No`);

INSERT INTO `Security_Check` (`Security_ID`, `Passenger_ID`, `Employee_ID`, `Officer_Name`, `Check_Time`, `Status`, `Remarks`) VALUES
(1, 1, 203, 'Amit Verma', '2026-09-20 07:15:00', 'Cleared', 'Standard screening completed. Cabin baggage verified.'),
(2, 2, 203, 'Amit Verma', '2026-09-20 07:55:00', 'Cleared', 'Security checkpoint passed smoothly.')
ON DUPLICATE KEY UPDATE `Status`=VALUES(`Status`);
