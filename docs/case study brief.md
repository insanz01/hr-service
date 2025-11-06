Berikut adalah arahan langkah demi langkah agar kamu bisa menyelesaikannya dengan efektif dan terstruktur:

---

## 🧭 Tahapan Utama Pengerjaan

### 1. **Pahami Tujuan Proyek**
Kamu diminta membangun backend service yang:
- Menerima CV dan laporan proyek dari kandidat.
- Mengevaluasi keduanya menggunakan AI berdasarkan job description dan case study brief.
- Menghasilkan laporan evaluasi terstruktur.

---

### 2. **Rancang Struktur API**
Buat tiga endpoint utama:

| Endpoint | Fungsi |
|---------|--------|
| `POST /upload` | Terima file CV dan laporan proyek, simpan, dan kembalikan ID masing-masing. |
| `POST /evaluate` | Terima ID file dan job title, jalankan pipeline AI secara async, kembalikan job ID. |
| `GET /result/{id}` | Ambil status dan hasil evaluasi berdasarkan job ID. |

Gunakan job queue (misalnya Celery, BullMQ, atau background worker) untuk proses asynchronous.

---

### 3. **Bangun Pipeline Evaluasi AI**
Pipeline ini terdiri dari tiga tahap:

#### 🔹 CV Evaluation
- Parse CV jadi data terstruktur (gunakan PDF parser seperti PyMuPDF atau pdfplumber).
- Ambil konteks dari Job Description dan CV Scoring Rubric via RAG (vector DB seperti ChromaDB).
- Gunakan LLM untuk menghasilkan `cv_match_rate` dan `cv_feedback`.

#### 🔹 Project Report Evaluation
- Parse laporan proyek.
- Ambil konteks dari Case Study Brief dan Project Scoring Rubric.
- Gunakan LLM untuk menghasilkan `project_score` dan `project_feedback`.

#### 🔹 Final Analysis
- Gabungkan hasil dari dua tahap sebelumnya.
- Gunakan LLM untuk menghasilkan `overall_summary`.

---

### 4. **Integrasi RAG (Retrieval-Augmented Generation)**
- Ingest dokumen referensi ke vector DB.
- Gunakan embedding model (OpenAI ada yang gratis, atau HuggingFace).
- Lakukan retrieval berdasarkan query spesifik untuk setiap tahap evaluasi.

---

### 5. **Prompt Design & LLM Chaining**
- Buat prompt yang berbeda untuk:
  - Evaluasi CV
  - Evaluasi laporan proyek
  - Ringkasan akhir
- Gunakan chaining: output dari satu tahap jadi input untuk tahap berikutnya.

Contoh prompt:
```text
Berdasarkan CV kandidat dan job description berikut, berikan penilaian match rate (0-1) dan feedback singkat.
```

---

### 6. **Penanganan Proses Lama & Error**
- `POST /evaluate` langsung kembalikan job ID.
- Simpan status job: `queued`, `processing`, `completed`, `failed`.
- Implementasi retry dan backoff untuk API LLM.
- Kontrol randomness dengan mengatur `temperature` rendah (misalnya 0.2–0.4).

---

### 7. **Skoring Berdasarkan Rubrik**
Gunakan bobot dari rubrik untuk menghitung:
- CV Match Rate (dikonversi ke skala 0–1)
- Project Score (skala 1–5)
- Overall Summary (3–5 kalimat)

---

### 8. **Dokumentasi & Submission**
- Buat README yang menjelaskan:
  - Arsitektur sistem
  - Alasan pemilihan teknologi
  - Strategi prompt dan RAG
  - Penanganan error dan edge cases
- Ikuti template submission PDF yang disediakan.

---

## 🔧 Tools & Teknologi yang Direkomendasikan

| Komponen | Rekomendasi |
|----------|-------------|
| Backend Framework | Django, FastAPI, Express.js |
| Vector DB | ChromaDB, Qdrant |
| LLM Provider | OpenAI (GPT-3.5), Gemini, OpenRouter |
| Job Queue | Celery (Python), BullMQ (Node.js) |
| PDF Parsing | PyMuPDF, pdfplumber, pdf.js |
| Embedding Model | OpenAI ada yang gratis, atau HuggingFace |

---
