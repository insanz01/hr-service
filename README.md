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

## Screening (Case Study)

Endpoint untuk proses screening kandidat berbasis dokumen CV dan Project Report.

### Endpoints
- `POST /upload` — Unggah dua file via form-data dengan key `cv` dan `report`. Mengembalikan `cv_id` dan `report_id`.
- `POST /evaluate` — Kirim JSON berisi `job_title`, `cv_id`, `report_id`. Mengembalikan `id` job dan status awal `queued`.
- `GET /result/<id>` — Ambil status job (`queued|processing|completed|failed`). Jika `completed`, mengembalikan objek `result`.

### Contoh

Upload dokumen:
```bash
curl -X POST http://localhost:5000/upload \
  -F "cv=@/path/to/CV.pdf" \
  -F "report=@/path/to/ProjectReport.pdf"
# Response: {"cv_id": 1, "report_id": 2}
```

Trigger evaluasi:
```bash
curl -X POST http://localhost:5000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"job_title":"Backend Engineer","cv_id":1,"report_id":2}'
# Response: {"id": 10, "status": "queued"}
```

Cek hasil:
```bash
curl http://localhost:5000/result/10
# Response saat proses: {"id":10,"status":"processing"}
# Response selesai: {"id":10,"status":"completed","result":{...}}
# Response gagal: {"id":10,"status":"failed","error":"..."}
```

### Catatan Teknis
- File disimpan di folder `uploads/` dengan nama aman (secure_filename).
- Pipeline evaluasi berjalan di background thread sederhana.
- Ekstraksi teks PDF menggunakan `PyPDF2`; fallback membaca sebagai teks jika bukan PDF.
- Skor/feedback saat ini masih mock untuk keperluan demo.

## Background Worker dengan Celery (Opsional)

Untuk pemrosesan upload (ekstraksi + ingest RAG) dan evaluasi job yang lebih andal, Anda dapat menjalankan Celery worker.

- Tambahkan/cek environment:
  - `REDIS_URL=redis://localhost:6379/0`
  - `REDIS_BACKEND=redis://localhost:6379/1`

- Jalankan Redis (contoh Docker):
  ```bash
  docker run -p 6379:6379 redis:7-alpine
  ```

- Jalankan Celery worker:
  ```bash
  celery -A celery_app.celery worker -l info --concurrency 4
  ```

Endpoint `/upload` dan `/evaluate` akan mencoba mengirim tugas ke Celery. Jika broker tidak tersedia, aplikasi akan otomatis fallback ke thread/queue lokal.