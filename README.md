# Flask API Minimalis

Project RESTful API minimalis menggunakan Flask dan database SQLite3.

## Fitur

- CRUD operations untuk Users
- CRUD operations untuk Todos
- Relasi antara User dan Todo
- Database SQLite3
- CORS support
- Error handling

## Struktur Project

```
flask-api/
├── main.py           # Flask app dan endpoints
├── database.py       # Konfigurasi database
├── models.py         # Model data
├── requirements.txt  # Dependencies
├── README.md         # Dokumentasi
├── database.db       # Database SQLite (otomatis dibuat)
├── templates/        # Folder templates
└── static/           # Folder static files
    ├── css/
    └── js/
```

## Instalasi

1. Clone atau download project ini
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Menjalankan Aplikasi

1. Inisialisasi database (otomatis dilakukan saat pertama kali menjalankan):
   ```bash
   python database.py
   ```

2. Jalankan Flask application:
   ```bash
   python main.py
   ```

Aplikasi akan berjalan di `http://localhost:5000`

## API Endpoints

### Users

- `GET /` - Info endpoint
- `GET /api/users` - Ambil semua users
- `POST /api/users` - Buat user baru
- `GET /api/users/<id>` - Ambil user berdasarkan ID
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Hapus user

### Todos

- `GET /api/todos` - Ambil semua todos (dapat difilter dengan ?user_id=<id>)
- `POST /api/todos` - Buat todo baru
- `PUT /api/todos/<id>` - Update todo
- `DELETE /api/todos/<id>` - Hapus todo

## Contoh Penggunaan

### Membuat User Baru

```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

### Ambil Semua Users

```bash
curl http://localhost:5000/api/users
```

### Membuat Todo Baru

```bash
curl -X POST http://localhost:5000/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Belajar Flask", "description": "Membuat REST API", "user_id": 1}'
```

### Ambil Todos User

```bash
curl "http://localhost:5000/api/todos?user_id=1"
```

### Update Todo

```bash
curl -X PUT http://localhost:5000/api/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

## Database Schema

### Users
- id (INTEGER, PRIMARY KEY)
- name (TEXT, NOT NULL)
- email (TEXT, NOT NULL, UNIQUE)
- created_at (TIMESTAMP)

### Todos
- id (INTEGER, PRIMARY KEY)
- title (TEXT, NOT NULL)
- description (TEXT)
- completed (BOOLEAN)
- user_id (INTEGER, FOREIGN KEY)
- created_at (TIMESTAMP)

## Error Response Format

```json
{
  "error": "Error message"
}
```

## Development Mode

Aplikasi berjalan dalam development mode dengan debug=True. Untuk production, ubah konfigurasi berikut:

```python
if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)
```

## Tambahan

- Database otomatis dibuat pada saat pertama kali aplikasi dijalankan
- Data contoh dapat ditambahkan dengan menjalankan `database.py`
- API menggunakan format JSON untuk request dan response