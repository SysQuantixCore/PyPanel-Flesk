import subprocess
import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="test"
    )

def start_mysql():
    subprocess.Popen("mysqld", shell=True)

def stop_mysql():
    subprocess.Popen("taskkill /F /IM mysqld.exe", shell=True)

def status_mysql():
    try:
        db = get_db()
        db.close()
        return "Online"
    except:
        return "Offline"

def get_tables():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    return [t[0] for t in cursor.fetchall()]

def create_table(name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"CREATE TABLE {name} (id INT AUTO_INCREMENT PRIMARY KEY)")
    db.commit()

def delete_table(name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"DROP TABLE {name}")
    db.commit()