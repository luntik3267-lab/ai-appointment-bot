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
        appointment_date TEXT,
        appointment_time TEXT DEFAULT '',
        phone TEXT
    )
    """)

    try:
        cursor.execute("""
        ALTER TABLE appointments
        ADD COLUMN appointment_time TEXT DEFAULT ''
        """)
    except:
        pass

    conn.commit()
    conn.close()


def add_appointment(name, service, appointment_date, appointment_time, phone):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO appointments (
        name,
        service,
        appointment_date,
        appointment_time,
        phone
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        service,
        appointment_date,
        appointment_time,
        phone
    ))

    conn.commit()
    conn.close()


def get_appointments():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        name,
        service,
        appointment_date,
        appointment_time,
        phone
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
            "date": row[3],
            "time": row[4],
            "phone": row[5]
        })

    return appointments


def is_slot_busy(appointment_date, appointment_time):
    appointments = get_appointments()

    for appointment in appointments:
        same_date = (
            appointment["date"].strip().lower()
            == appointment_date.strip().lower()
        )

        same_time = (
            appointment["time"].strip().lower()
            == appointment_time.strip().lower()
        )

        if same_date and same_time:
            return True

    return False


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