import sqlite3


def connect():
    return sqlite3.connect("appointments.db")


def init_db():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        service TEXT,
        barber TEXT DEFAULT '',
        appointment_date TEXT,
        appointment_time TEXT DEFAULT '',
        phone TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blacklist (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       phone TEXT UNIQUE
    )
    """)

    try:
     cursor.execute("""
    ALTER TABLE appointments
    ADD COLUMN telegram_id TEXT DEFAULT ''
    """)
    except:
     pass

    try:
        cursor.execute("""
        ALTER TABLE appointments
        ADD COLUMN appointment_time TEXT DEFAULT ''
        """)
    except:
        pass

    try:
     cursor.execute("""
     ALTER TABLE appointments
     ADD COLUMN barber TEXT DEFAULT ''
     """)
    except:
      pass

    conn.commit()
    conn.close()

def add_appointment(name, service, barber, appointment_date, appointment_time, phone, telegram_id=""):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO appointments (
        name,
        service,
        barber,
        appointment_date,
        appointment_time,
        phone,
        telegram_id
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        service,
        barber,
        appointment_date,
        appointment_time,
        phone,
        telegram_id
    ))

    appointment_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return appointment_id


def get_appointments():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        name,
        service,
        barber,
        appointment_date,
        appointment_time,
        phone,
        telegram_id
    FROM appointments
    ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    appointments = []

    for row in rows:
        appointments.append({
            "id": row[0],
            "name": row[1],
            "service": row[2],
            "barber": row[3],
            "date": row[4],
            "time": row[5],
            "phone": row[6],
            "telegram_id": row[7]
        })

    return appointments


def is_slot_busy(appointment_date, appointment_time, barber):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM appointments
    WHERE appointment_date = ?
    AND appointment_time = ?
    AND barber = ?
    """, (appointment_date, appointment_time, barber))

    result = cursor.fetchone()

    conn.close()

    return result is not None


def get_busy_slots(appointment_date):
    appointments = get_appointments()

    busy_slots = []

    for appointment in appointments:
        if appointment["date"].strip().lower() == appointment_date.strip().lower():
            busy_slots.append(appointment["time"])

    return busy_slots

def delete_appointment(appointment_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM appointments WHERE id=?",
        (appointment_id,)
    )

    conn.commit()
    conn.close()

def delete_appointment(appointment_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM appointments WHERE id = ?",
        (appointment_id,)
    )

    conn.commit()
    conn.close()


def find_appointments_by_phone(phone_query):
    appointments = get_appointments()

    results = []

    for appointment in appointments:
        if phone_query in appointment["phone"]:
            results.append(appointment)

    return results

def get_finance_stats():
    appointments = get_appointments()

    haircut = 0
    beard = 0
    combo = 0

    for appointment in appointments:

        service = appointment["service"]

        if "Стрижка" in service:
            haircut += 15

        elif "Борода" in service:
            beard += 10

        elif "Комплекс" in service:
            combo += 20

    total = haircut + beard + combo

    return {
        "haircut": haircut,
        "beard": beard,
        "combo": combo,
        "total": total
    }

def get_all_clients():
    appointments = get_appointments()

    clients = {}

    for appointment in appointments:
        clients[appointment["phone"]] = appointment["name"]

    return clients

def clear_appointments():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM appointments")

    conn.commit()
    conn.close()

def get_appointments_by_date(date):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM appointments WHERE date = ?",
        (date,)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows

def get_client_history(phone):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        service,
        barber,
        appointment_date,
        appointment_time
    FROM appointments
    WHERE phone = ?
    ORDER BY id DESC
    """, (phone,))

    rows = cursor.fetchall()
    conn.close()

    return rows
def add_to_blacklist(phone):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO blacklist (phone) VALUES (?)",
        (phone,)
    )

    conn.commit()
    conn.close()


def remove_from_blacklist(phone):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM blacklist WHERE phone = ?",
        (phone,)
    )

    conn.commit()
    conn.close()


def is_blacklisted(phone):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM blacklist WHERE phone = ?",
        (phone,)
    )

    result = cursor.fetchone()
    conn.close()

    return result is not None


def get_blacklist():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT phone FROM blacklist ORDER BY id DESC")

    rows = cursor.fetchall()
    conn.close()

    return rows