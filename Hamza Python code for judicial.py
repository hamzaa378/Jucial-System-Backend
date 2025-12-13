#1 st run the file creating tables in sql.sql
#it requires 2 modules werkzeug and mysql.connector which has to be installed using pip or any other method before the execution of the program
import getpass
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# ---------- DB CONFIG ----------
#Replace user with the user in your system and password as the password of the sql database environment
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_mysql_user',
    'password': 'your_mysql_password',
    'database': 'chef_court',
    'raise_on_warnings': True
}

# ---------- DB HELPERS ----------
def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def row_to_dict(cursor, row):
    if not row:
        return None
    return {col[0]: val for col, val in zip(cursor.description, row)}

# ---------- APP STATE ----------
current_user = None  # dict: id, username, role

# ---------- AUTH ----------
def signup():
    print("\n== Signup ==")
    username = input("Username: ").strip()
    if not username:
        print("Username required.")
        return
    while True:
        password = getpass.getpass("Password: ")
        password2 = getpass.getpass("Confirm Password: ")
        if password != password2:
            print("Passwords do not match. Try again.")
        elif len(password) < 4:
            print("Password too short (min 4 chars).")
        else:
            break
    print("Role options: defendant, plaintiff, juror, judge")
    role = input("Role: ").strip().lower()
    if role not in ('defendant','plaintiff','juror','judge'):
        print("Invalid role.")
        return
    pw_hash = generate_password_hash(password)
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
            (username, pw_hash, role)
        )
        conn.commit()
        print("User created. You may now login.")
    except mysql.connector.IntegrityError:
        conn.rollback()
        print("Username already exists.")
    finally:
        cur.close()
        conn.close()

def login():
    global current_user
    print("\n== Login ==")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, username, password_hash, role FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        if not user or not check_password_hash(user['password_hash'], password):
            print("Invalid credentials.")
            return
        current_user = {'id': user['id'], 'username': user['username'], 'role': user['role']}
        print(f"Logged in as {current_user['username']} ({current_user['role']})")
    finally:
        cur.close()
        conn.close()

def logout():
    global current_user
    if current_user:
        print(f"User {current_user['username']} logged out.")
    current_user = None

# ---------- CASES ----------
def submit_case():
    if not current_user or current_user['role'] not in ('defendant','plaintiff'):
        print("Only defendant/plaintiff can submit cases.")
        return
    title = input("Title: ").strip() or "Untitled"
    party_name = input("Party name (defendant/plaintiff name): ").strip()
    print("Enter content (end with a single line with just 'END'):")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    content = "\n".join(lines).strip()
    if not party_name or not content:
        print("party_name and content required.")
        return
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO cases (title, party_type, party_name, content, uploaded_by, status) VALUES (%s,%s,%s,%s,%s,'pending')",
            (title, current_user['role'], party_name, content, current_user['id'])
        )
        conn.commit()
        print(f"Case submitted with id {cur.lastrowid}. Status: pending (awaiting judge approval).")
    except Exception as e:
        conn.rollback()
        print("DB error:", e)
    finally:
        cur.close()
        conn.close()

def view_all_cases():
    if not current_user:
        print("Login required.")
        return
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        role = current_user['role']
        # Judge sees all
        if role == 'judge':
            cur.execute("SELECT * FROM cases ORDER BY created_at DESC")
            rows = cur.fetchall()
        #Juror can only see cases which are approved and are sorted ny their dates created in descending order means the case which is earlier created will be in the end
        elif role == 'juror':
            cur.execute("SELECT * FROM cases WHERE status='approved' ORDER BY created_at DESC")
            rows = cur.fetchall()
        else:  # defendant/plaintiff can only see cases which are approved or are uploaded by themselves only
            uid = current_user['id']
            cur.execute("SELECT * FROM cases WHERE status='approved' OR uploaded_by=%s ORDER BY created_at DESC", (uid,))
            rows = cur.fetchall()
        if not rows:
            print("No cases found.")
            return
        for r in rows:
            print("-"*40)
            print(f"ID: {r['id']}  Title: {r['title']}  Status: {r['status']}")
            print(f"Party ({r['party_type']}): {r['party_name']}")
            print(f"Uploaded by user id: {r['uploaded_by']}  Created: {r['created_at']}")
            print("Content:")
            print(r['content'][:1000])  # print up to some length
        print("-"*40)
    finally:
        cur.close()
        conn.close()

def edit_case():
    if not current_user or current_user['role'] != 'judge':
        print("Only judges can edit cases.")
        return
    try:
        cid = int(input("Case id to edit: "))
    except ValueError:
        print("Invalid id.")
        return
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM cases WHERE id=%s", (cid,))
        case = cur.fetchone()#if multiple cases with same id are there then only the 1st case will be changed in real life no 2 cases should have the same case id as it may cause confusion
        if not case:
            print("Case not found.")#occurs when the case id is entered wrong or it is not added to the sql table
            return
        print("Current title:", case['title'])
        new_title = input("New title (leave blank to keep): ").strip() or case['title']
        print("Current party_name:", case['party_name'])
        new_party = input("New party_name (blank to keep): ").strip() or case['party_name']
        print("Current content (first 200 chars):")
        print(case['content'][:200])
        print("Enter new content (end with single line 'END'; leave empty to keep):")
        lines = []
        first = input()
        if first.strip() == "END":
            new_content = case['content']
        else:
            lines.append(first)
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            new_content = "\n".join(lines).strip() or case['content']
        cur2 = conn.cursor()
        cur2.execute("UPDATE cases SET title=%s, party_name=%s, content=%s, updated_at=%s WHERE id=%s",
                     (new_title, new_party, new_content, datetime.utcnow(), cid))
        conn.commit()
        cur2.close()
        print("Case updated.")
    except Exception as e:
        conn.rollback()
        print("DB error:", e)
    finally:
        cur.close()
        conn.close()

def delete_case():
    if not current_user or current_user['role'] != 'judge':
        print("Only judges can delete cases.")
        return
    try:
        cid = int(input("Case id to delete: "))
    except ValueError:
        print("Invalid id.")
        return
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM cases WHERE id=%s", (cid,))
        conn.commit()
        print("Case deleted (if it existed).")
    except Exception as e:
        conn.rollback()
        print("DB error:", e)
    finally:
        cur.close()
        conn.close()

def approve_case():
    if not current_user or current_user['role'] != 'judge':
        print("Only judges can approve cases.")
        return
    try:
        cid = int(input("Case id to approve: "))
    except ValueError:
        print("Invalid id.")
        return
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE cases SET status='approved', updated_at=%s WHERE id=%s", (datetime.utcnow(), cid))
        conn.commit()
        print("Case approved.")
    except Exception as e:
        conn.rollback()
        print("DB error:", e)
    finally:
        cur.close()
        conn.close()

def reject_case():
    if not current_user or current_user['role'] != 'judge':
        print("Only judges can reject cases.")
        return
    try:
        cid = int(input("Case id to reject: "))
    except ValueError:
        print("Invalid id.")
        return
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE cases SET status='rejected', updated_at=%s WHERE id=%s", (datetime.utcnow(), cid))
        conn.commit()
        print("Case rejected.")
    except Exception as e:
        conn.rollback()
        print("DB error:", e)
    finally:
        cur.close()
        conn.close()

# ---------- JURY ----------
def juror_filter_by_name():
    if not current_user or current_user['role'] != 'juror':
        print("Only jurors can use this.")
        return
    name = input("Search party_name substring: ").strip()
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM cases WHERE status='approved' AND party_name LIKE %s ORDER BY created_at DESC", (f"%{name}%",))
        rows = cur.fetchall()
        if not rows:
            print("No matching approved cases.")
            return
        for r in rows:
            print("-"*40)
            print(f"ID: {r['id']} Title: {r['title']} Party: {r['party_name']}")
            print(r['content'][:1000])
    finally:
        cur.close()
        conn.close()

def juror_vote():
    if not current_user or current_user['role'] != 'juror':
        print("Only jurors can vote.")
        return
    try:
        cid = int(input("Case id to vote on: "))
    except ValueError:
        print("Invalid id.")
        return
    vote = input("Vote ('guilty' or 'not_guilty'): ").strip().lower()
    if vote not in ('guilty','not_guilty'):
        print("Invalid vote.")
        return
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        # check case existence and approved
        cur.execute("SELECT id, status FROM cases WHERE id=%s", (cid,))
        case = cur.fetchone()
        if not case:
            print("Case not found.")
            return
        if case['status'] != 'approved':
            print("Case not open for voting (must be approved).")
            return
        # prevent double voting
        cur.execute("SELECT id FROM votes WHERE case_id=%s AND juror_id=%s", (cid, current_user['id']))
        if cur.fetchone():
            print("You have already voted on this case.")
            return
        cur2 = conn.cursor()
        cur2.execute("INSERT INTO votes (case_id, juror_id, vote) VALUES (%s,%s,%s)", (cid, current_user['id'], vote))
        conn.commit()
        cur2.close()
        print("Vote recorded.")
    except mysql.connector.Error as e:
        conn.rollback()
        print("DB error:", e)
    finally:
        cur.close()
        conn.close()

def jury_results():
    if not current_user or current_user['role'] not in ('juror','judge'):
        print("Only judges and jurors can view results.")
        return
    try:
        cid = int(input("Case id to view results: "))
    except ValueError:
        print("Invalid id.")
        return
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, status FROM cases WHERE id=%s", (cid,))
        case = cur.fetchone()
        if not case:
            print("Case not found.")
            return
        if case['status'] != 'approved' and current_user['role'] == 'juror':
            print("Results not available (case not approved).")
            return
        cur.execute("SELECT vote, COUNT(*) AS cnt FROM votes WHERE case_id=%s GROUP BY vote", (cid,))
        rows = cur.fetchall()
        tally = {'guilty': 0, 'not_guilty': 0}
        for r in rows:
            tally[r['vote']] = r['cnt']
        total = tally['guilty'] + tally['not_guilty']
        print(f"Case {cid} results: total_votes={total}, guilty={tally['guilty']}, not_guilty={tally['not_guilty']}")
    finally:
        cur.close()
        conn.close()

# ---------- MAIN MENU ----------
def show_menu():
    print("\n=== Chef's Court CLI ===")
    if current_user:
        print(f"Logged in: {current_user['username']} ({current_user['role']})")
    else:
        print("Not logged in.")
    print("Options:")
    print("  1) Signup")
    print("  2) Login")
    print("  3) Logout")
    print("  4) Submit case (defendant/plaintiff)")
    print("  5) View all cases")
    print("  6) Edit case (judge)")
    print("  7) Delete case (judge)")
    print("  8) Approve case (judge)")
    print("  9) Reject case (judge)")
    print(" 10) Filter approved cases by party name (juror)")
    print(" 11) Vote (juror)")
    print(" 12) View jury results (judge/juror)")
    print("  0) Exit")

def main():
    while True:
        show_menu()
        choice = input("Choose: ").strip()
        if choice == '1':
            signup()
        elif choice == '2':
            login()
        elif choice == '3':
            logout()
        elif choice == '4':
            submit_case()
        elif choice == '5':
            view_all_cases()
        elif choice == '6':
            edit_case()
        elif choice == '7':
            delete_case()
        elif choice == '8':
            approve_case()
        elif choice == '9':
            reject_case()
        elif choice == '10':
            juror_filter_by_name()
        elif choice == '11':
            juror_vote()
        elif choice == '12':
            jury_results()
        elif choice == '0':
            print("Bye.")
            break
        else:
            print("Invalid choice.")

if __name__ == '__main__':
    main()
