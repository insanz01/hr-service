import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    """Membuat koneksi ke database SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Menginisialisasi database dan membuat tabel jika belum ada"""
    try:
        conn = get_db_connection()

        # Membuat tabel users
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Membuat tabel todos
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT 0,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Membuat tabel documents untuk menyimpan file CV dan Project Report
        conn.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_type TEXT NOT NULL, -- 'cv' atau 'report'
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Membuat tabel jobs untuk evaluasi asinkron
        conn.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT,
                cv_id INTEGER,
                report_id INTEGER,
                status TEXT DEFAULT 'queued', -- queued | processing | completed | failed
                result_json TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cv_id) REFERENCES documents (id),
                FOREIGN KEY (report_id) REFERENCES documents (id)
            )
        ''')

        conn.commit()
        conn.close()
        print("Database berhasil diinisialisasi!")

    except Exception as e:
        print(f"Error menginisialisasi database: {e}")

def reset_db():
    """Menghapus dan membuat ulang database"""
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print("Database dihapus!")
    init_db()

def seed_db():
    """Menambahkan data contoh ke database"""
    try:
        conn = get_db_connection()

        # Tambah user contoh
        users = [
            ('John Doe', 'john@example.com'),
            ('Jane Smith', 'jane@example.com'),
            ('Ahmad Fadli', 'ahmad@example.com')
        ]

        for name, email in users:
            conn.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))

        # Tambah todo contoh
        todos = [
            ('Belajar Flask', 'Membuat REST API dengan Flask', 1, 0),
            ('Membaca buku', 'Selesai baca buku Python', 1, 1),
            ('Olahraga', 'Lari pagi 30 menit', 2, 0),
            ('Belanja', 'Belanja kebutuhan dapur', 3, 0),
            ('Coding Project', 'Membuat aplikasi web', 2, 0)
        ]

        for title, desc, user_id, completed in todos:
            conn.execute(
                'INSERT INTO todos (title, description, user_id, completed) VALUES (?, ?, ?, ?)',
                (title, desc, user_id, completed)
            )

        conn.commit()
        conn.close()
        print("Data contoh berhasil ditambahkan!")

    except Exception as e:
        print(f"Error menambahkan data contoh: {e}")

if __name__ == "__main__":
    init_db()
    seed_db()