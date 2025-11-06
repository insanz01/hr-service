from datetime import datetime
from database import get_db_connection

class User:
    """Model untuk tabel users"""

    def __init__(self, id=None, name=None, email=None, created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.created_at = created_at

    @staticmethod
    def create(name, email):
        """Membuat user baru"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id

    @staticmethod
    def get_all():
        """Mengambil semua users"""
        conn = get_db_connection()
        users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
        conn.close()
        return users

    @staticmethod
    def get_by_id(user_id):
        """Mengambil user berdasarkan ID"""
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        return user

    @staticmethod
    def update(user_id, name=None, email=None):
        """Update user"""
        conn = get_db_connection()

        # Ambil data lama dulu
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            conn.close()
            return None

        # Update dengan data baru
        name = name if name is not None else user['name']
        email = email if email is not None else user['email']

        conn.execute('UPDATE users SET name = ?, email = ? WHERE id = ?',
                    (name, email, user_id))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete(user_id):
        """Hapus user"""
        conn = get_db_connection()
        # Hapus todos terkait dulu
        conn.execute('DELETE FROM todos WHERE user_id = ?', (user_id,))
        # Hapus user
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def to_dict(user_row):
        """Convert row ke dictionary"""
        return {
            'id': user_row['id'],
            'name': user_row['name'],
            'email': user_row['email'],
            'created_at': user_row['created_at']
        }

class Todo:
    """Model untuk tabel todos"""

    def __init__(self, id=None, title=None, description=None, completed=False,
                 user_id=None, created_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.completed = completed
        self.user_id = user_id
        self.created_at = created_at

    @staticmethod
    def create(title, description, user_id, completed=False):
        """Membuat todo baru"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO todos (title, description, user_id, completed) VALUES (?, ?, ?, ?)',
            (title, description, user_id, completed)
        )
        conn.commit()
        todo_id = cursor.lastrowid
        conn.close()
        return todo_id

    @staticmethod
    def get_all(user_id=None):
        """Mengambil semua todos (dapat difilter berdasarkan user_id)"""
        conn = get_db_connection()

        if user_id:
            todos = conn.execute(
                'SELECT * FROM todos WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            ).fetchall()
        else:
            todos = conn.execute('SELECT * FROM todos ORDER BY created_at DESC').fetchall()

        conn.close()
        return todos

    @staticmethod
    def get_by_id(todo_id):
        """Mengambil todo berdasarkan ID"""
        conn = get_db_connection()
        todo = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
        conn.close()
        return todo

    @staticmethod
    def update(todo_id, title=None, description=None, completed=None):
        """Update todo"""
        conn = get_db_connection()

        # Ambil data lama dulu
        todo = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
        if not todo:
            conn.close()
            return None

        # Update dengan data baru
        title = title if title is not None else todo['title']
        description = description if description is not None else todo['description']
        completed = completed if completed is not None else todo['completed']

        conn.execute(
            'UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?',
            (title, description, completed, todo_id)
        )
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete(todo_id):
        """Hapus todo"""
        conn = get_db_connection()
        conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_by_user_id(user_id):
        """Mengambil todos berdasarkan user_id"""
        conn = get_db_connection()
        todos = conn.execute(
            'SELECT * FROM todos WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        conn.close()
        return todos

    @staticmethod
    def toggle_complete(todo_id):
        """Toggle status completed todo"""
        conn = get_db_connection()
        todo = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
        if todo:
            new_status = not todo['completed']
            conn.execute('UPDATE todos SET completed = ? WHERE id = ?',
                        (new_status, todo_id))
            conn.commit()
        conn.close()
        return todo is not None

    @staticmethod
    def to_dict(todo_row):
        """Convert row ke dictionary"""
        return {
            'id': todo_row['id'],
            'title': todo_row['title'],
            'description': todo_row['description'],
            'completed': bool(todo_row['completed']),
            'user_id': todo_row['user_id'],
            'created_at': todo_row['created_at']
        }

    @staticmethod
    def get_completed_count(user_id=None):
        """Menghitung jumlah todos yang sudah selesai"""
        conn = get_db_connection()

        if user_id:
            count = conn.execute(
                'SELECT COUNT(*) as count FROM todos WHERE user_id = ? AND completed = 1',
                (user_id,)
            ).fetchone()['count']
        else:
            count = conn.execute(
                'SELECT COUNT(*) as count FROM todos WHERE completed = 1'
            ).fetchone()['count']

        conn.close()
        return count

    @staticmethod
    def get_pending_count(user_id=None):
        """Menghitung jumlah todos yang belum selesai"""
        conn = get_db_connection()

        if user_id:
            count = conn.execute(
                'SELECT COUNT(*) as count FROM todos WHERE user_id = ? AND completed = 0',
                (user_id,)
            ).fetchone()['count']
        else:
            count = conn.execute(
                'SELECT COUNT(*) as count FROM todos WHERE completed = 0'
            ).fetchone()['count']

        conn.close()
        return count

# Model untuk documents
class Document:
    def __init__(self, id=None, doc_type=None, filename=None, path=None, created_at=None):
        self.id = id
        self.doc_type = doc_type
        self.filename = filename
        self.path = path
        self.created_at = created_at

    @staticmethod
    def create(doc_type, filename, path):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO documents (doc_type, filename, path) VALUES (?, ?, ?)',
            (doc_type, filename, path)
        )
        conn.commit()
        doc_id = cursor.lastrowid
        conn.close()
        return doc_id

    @staticmethod
    def get_by_id(doc_id):
        conn = get_db_connection()
        row = conn.execute('SELECT * FROM documents WHERE id = ?', (doc_id,)).fetchone()
        conn.close()
        return row

# Model untuk jobs
class Job:
    def __init__(self, id=None, job_title=None, cv_id=None, report_id=None, status='queued', result_json=None, error_message=None, created_at=None, updated_at=None):
        self.id = id
        self.job_title = job_title
        self.cv_id = cv_id
        self.report_id = report_id
        self.status = status
        self.result_json = result_json
        self.error_message = error_message
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(job_title, cv_id, report_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO jobs (job_title, cv_id, report_id, status) VALUES (?, ?, ?, ?)',
            (job_title, cv_id, report_id, 'queued')
        )
        conn.commit()
        job_id = cursor.lastrowid
        conn.close()
        return job_id

    @staticmethod
    def get_by_id(job_id):
        conn = get_db_connection()
        row = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
        conn.close()
        return row

    @staticmethod
    def update_status(job_id, status, result_json=None, error_message=None):
        conn = get_db_connection()
        conn.execute(
            'UPDATE jobs SET status = ?, result_json = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (status, result_json, error_message, job_id)
        )
        conn.commit()
        conn.close()
        return True