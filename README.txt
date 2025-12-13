For the firs time first run the file creating tables in sql then followed by the python file

README for creating tables in sql

Chef’s Court of Justice – Database Schema

This document describes the database structure used by Chef’s Court of
Justice, a role‑based judicial simulation system.

------------------------------------------------------------------------

DATABASE OVERVIEW Three main tables are used: 1. users – Stores system
users and roles 2. cases – Stores arguments submitted by defendants or
plaintiffs 3. votes – Stores juror votes

------------------------------------------------------------------------

CREATE DATABASE

CREATE DATABASE IF NOT EXISTS chef_court; USE chef_court;

------------------------------------------------------------------------

USERS TABLE

Purpose: Stores registered users and their assigned roles.

Columns: - id: Unique user ID - username: Unique account name -
password_hash: Secure password hash - role: defendant, plaintiff, juror,
judge - created_at: Registration timestamp

SQL: CREATE TABLE IF NOT EXISTS users ( id INT AUTO_INCREMENT PRIMARY
KEY, username VARCHAR(100) NOT NULL UNIQUE, password_hash VARCHAR(255)
NOT NULL, role ENUM(‘defendant’,‘plaintiff’,‘juror’,‘judge’) NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP );

------------------------------------------------------------------------

CASES TABLE

Purpose: Stores case submissions with arguments/evidence.

Columns: - id: Unique case ID - title: Case title - party_type:
defendant or plaintiff - party_name: Name of submitting party - content:
Submission text - uploaded_by: ID of user who uploaded - status: pending
/ approved / rejected - created_at: Submission time - updated_at: Last
modified time

SQL: CREATE TABLE IF NOT EXISTS cases ( id INT AUTO_INCREMENT PRIMARY
KEY, title VARCHAR(255) NOT NULL, party_type
ENUM(‘defendant’,‘plaintiff’) NOT NULL, party_name VARCHAR(255) NOT
NULL, content TEXT NOT NULL, uploaded_by INT NOT NULL, status
ENUM(‘pending’,‘approved’,‘rejected’) DEFAULT ‘pending’, created_at
TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NULL, FOREIGN
KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE );

------------------------------------------------------------------------

VOTES TABLE

Purpose: Stores juror votes on approved cases.

Columns: - id: Unique vote ID - case_id: Case being voted on - juror_id:
Juror who voted - vote: guilty or not_guilty - voted_at: Timestamp of
vote

SQL: CREATE TABLE IF NOT EXISTS votes ( id INT AUTO_INCREMENT PRIMARY
KEY, case_id INT NOT NULL, juror_id INT NOT NULL, vote
ENUM(‘guilty’,‘not_guilty’) NOT NULL, voted_at TIMESTAMP DEFAULT
CURRENT_TIMESTAMP, UNIQUE KEY unique_juror_case (case_id, juror_id),
FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE, FOREIGN
KEY (juror_id) REFERENCES users(id) ON DELETE CASCADE );

------------------------------------------------------------------------

RELATIONSHIPS - One user can submit multiple cases. - One juror can vote
on many cases. - One case can have multiple votes.

------------------------------------------------------------------------

SUMMARY This schema supports: - User authentication - Role‑based
permissions - Case submission & moderation - Jury voting system

Suitable for CLI, API, or web applications.

README File for the python file

Chef's Court CLI - README
=========================

Overview
--------
Chef's Court is a command-line based court-case management system that allows users to sign up, log in, submit cases, review cases, vote as a juror, and manage legal submissions. It uses MySQL as the database backend and requires no Flask or web framework—everything runs directly in the terminal.

Roles
-----
The system supports four roles:
- Defendant
- Plaintiff
- Juror
- Judge

Each role has different permissions and menus inside the CLI.

Requirements
-----------
Install required Python packages:
    pip install mysql-connector-python werkzeug

Configure database settings by editing the DB_CONFIG dictionary in the code.

Database Tables Required
------------------------
You must create the following tables in MySQL:
1. users  
2. cases  
3. votes  

Main Features
-------------
1. Signup & Login
2. Case submission (defendant/plaintiff)
3. Case editing/approval/rejection (judge)
4. Case viewing (all roles)
5. Juror features:
   - Filter approved cases by party name
   - Vote guilty/not guilty
6. Jury result viewing (judge/juror)

Running the Program
-------------------
Run using:
    python main.py

Then follow the on-screen menu instructions.

Usage Notes
-----------
- Case content entry ends when the user types: END
- Judges alone can approve/edit/delete/reject cases.
- Jurors can only access approved cases.
- A juror cannot vote more than once on the same case.

Exit
----
Choose option 0 to exit the program.

