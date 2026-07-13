import sqlite3
from datetime import datetime 

DB_PATH = "vida_incidents.db"


def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False
    )

    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    return conn


def init_incident_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            camera_id INTEGER,
            incident_id TEXT,
            timestamp TEXT,
            client_name TEXT,
            site_name TEXT,
            zone_name TEXT,
            alert_level TEXT,
            persons_count INTEGER,
            intrusion_duration REAL,
            pdf_path TEXT,
            image_path TEXT,
            video_path TEXT,
            status TEXT DEFAULT 'OPEN',
            start_time TEXT,
            last_seen TEXT,
            end_time TEXT,
            images_count INTEGER DEFAULT 1,
            videos_count INTEGER DEFAULT 1,
            last_detection INTEGER DEFAULT 0
        )
    """)

    migrations = [
        ("user_id", "INTEGER"),
        ("camera_id", "INTEGER"),
        ("status", "TEXT DEFAULT 'OPEN'"),
        ("start_time", "TEXT"),
        ("last_seen", "TEXT"),
        ("end_time", "TEXT"),
        ("images_count", "INTEGER DEFAULT 1"),
        ("videos_count", "INTEGER DEFAULT 1"),
        ("last_detection", "INTEGER DEFAULT 0"),
    ]

    cursor.execute("PRAGMA table_info(incidents)")
    existing_columns = {
        row[1] for row in cursor.fetchall()
    }

    for column_name, column_definition in migrations:
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE incidents "
                f"ADD COLUMN {column_name} {column_definition}"
            )

    conn.commit()
    conn.close()

def save_incident(
    user_id,
    camera_id,
    incident_id,
    timestamp,
    client_name,
    site_name,
    zone_name,
    alert_level,
    persons_count,
    intrusion_duration,
    pdf_path,
    image_path,
    video_path
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO incidents (
                user_id,
                camera_id,
                incident_id,
                timestamp,
                client_name,
                site_name,
                zone_name,
                alert_level,
                persons_count,
                intrusion_duration,
                pdf_path,
                image_path,
                video_path,
                status,
                start_time,
                last_seen,
                images_count,
                videos_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            camera_id,
            incident_id,
            timestamp,
            client_name,
            site_name,
            zone_name,
            alert_level,
            persons_count,
            intrusion_duration,
            pdf_path,
            image_path,
            video_path,
            "OPEN",
            timestamp,
            timestamp,
            1,
            1
        ))

        conn.commit()

    except Exception as e:

        conn.rollback()
        print("ERREUR SQLITE :", e)
        raise

    finally:

        conn.close()

def find_open_incident(user_id, zone_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM incidents
        WHERE user_id = ?
        AND zone_name = ?
        AND status = 'OPEN'
        LIMIT 1
    """, (
        user_id,
        zone_name
    ))

    incident = cursor.fetchone()

    conn.close()

    return incident

def update_last_detection(incident_id):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE incidents
        SET last_seen = ?
        WHERE id = ?
    """, (
        now,
        incident_id
    ))

    conn.commit()
    conn.close()

def close_old_incidents():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE incidents
        SET
            status = 'CLOSED',
            end_time = datetime('now')
        WHERE
            status = 'OPEN'
            AND datetime(last_seen)
                <= datetime('now', '-2 minutes')
    """)

    print("Incidents fermés :", cursor.rowcount)

    conn.commit()
    conn.close()
