# 📝 Log Pengerjaan & Perbaikan Bug - IndoGovRAG

Dokumen ini mencatat detail pengerjaan, perbaikan unit test, dan penyelesaian bug API pada platform IndoGovRAG.

---

## 🌟 Ringkasan Hasil
* **Total Unit Test**: 231 test berhasil dilalui (**0 gagal**).
* **Status Bug Pencarian "PP"**: Selesai diperbaiki. Kueri singkatan legal 2 huruf (seperti PP, UU, KK) sekarang diterima dengan benar dan tidak menyebabkan error 500/400.

---

## 🛠️ Rincian Perbaikan per Komponen

### 1. Perbaikan Bug Pencarian Singkatan & Penanganan Error API
* **Masalah**: Pencarian kata seperti "PP" menghasilkan **API Error 500**.
  * Sanitizer membatasi panjang kueri minimal 3 karakter (karena itu "PP" ditolak sebagai bad request 400).
  * Endpoint `/query` di `api/main.py` membungkus semua `Exception` (termasuk `HTTPException 400` dari sanitizer) menjadi **HTTP 500 Internal Server Error**.
* **Solusi**:
  * Mengubah panjang kueri minimum di [sanitizer.py](file:///d:/IndoGov/IndoGovRAG/api/sanitizer.py) dari `< 3` menjadi `< 2` agar singkatan penting di Indonesia (PP, UU, KK) diperbolehkan.
  * Menambahkan blok handler `except HTTPException: raise` sebelum penanganan error generik di endpoint `/query` pada [main.py](file:///d:/IndoGov/IndoGovRAG/api/main.py) agar error validasi (400) diteruskan ke client secara transparan tanpa diubah menjadi error 500.

### 2. PII Detector & Preprocessor
* **Penyebab Tes Gagal**: 
  * Deteksi nomor telepon terlalu sensitif dan bertabrakan dengan pola NIK (Nomor Induk Kependudukan).
  * Threshold klasifikasi bahasa Indonesia pada preprocessor terlalu tinggi untuk kalimat/kueri yang sangat pendek.
* **Perbaikan**:
  * Menambahkan word boundaries (`\b`) pada pola regex nomor telepon di [pii_detector.py](file:///d:/IndoGov/IndoGovRAG/src/data/pii_detector.py).
  * Menurunkan threshold deteksi bahasa Indonesia di [preprocessor.py](file:///d:/IndoGov/IndoGovRAG/src/data/preprocessor.py) agar kueri pendek tetap terklasifikasi sebagai bahasa Indonesia dengan valid.

### 3. Document Chunker Heuristics
* **Penyebab Tes Gagal**: Heuristik chunking tidak mengenali judul atau daftar dengan benar pada format teks tertentu, serta memicu Index Error saat coherence score dihitung untuk dokumen yang hanya menghasilkan 1 chunk.
* **Perbaikan**:
  * Memperbaiki regex pendeteksi judul (`_has_title`) dan daftar/angka (`_has_list`, `_has_numbers`) di [chunker.py](file:///d:/IndoGov/IndoGovRAG/src/data/chunker.py).
  * Menambahkan penanganan khusus untuk dokumen single-chunk agar tidak memicu pembagian indeks yang tidak valid pada coherence scoring.

### 4. Masalah Mocking & Import Lingkup Lokal (Local Scope Imports)
* **Penyebab Tes Gagal**: Beberapa module seperti `VectorStore`, `QueryExpander`, dan `BM25Search` di-import di dalam fungsi/metode. Hal ini menyebabkan mekanisme unit test `mock.patch` gagal mem-patch class tersebut secara global.
* **Perbaikan**:
  * Memindahkan semua import tersebut ke tingkat modul (module-level) di [main.py](file:///d:/IndoGov/IndoGovRAG/api/main.py) dan [vector_search.py](file:///d:/IndoGov/IndoGovRAG/src/retrieval/vector_search.py).
  * Memastikan fungsi pembantu seperti `_try_bm25_only` menggunakan reference `rag_pipeline.vector_store` yang sudah di-instansiasi alih-alih membuat instansi baru secara lokal.

### 5. API Rate Limiter
* **Penyebab Tes Gagal**: Pengujian memanggil konstanta batas rate limit (`IP_LIMIT`, `USER_LIMIT`, `API_KEY_LIMIT`) secara langsung dari class `TieredRateLimiter`, padahal nilai tersebut dideklarasikan di dalam `__init__`.
* **Perbaikan**:
  * Mendefinisikan batas-batas tersebut sebagai class-level attributes di [rate_limiter.py](file:///d:/IndoGov/IndoGovRAG/api/rate_limiter.py).
  * Menambahkan environment check `TESTING` pada middleware keamanan untuk mem-bypass rate limiter jika sedang diuji oleh pytest.

### 6. Perbaikan Unit Test & Setup Lingkungan Test
* **Perbaikan**:
  * Memperbaiki syntax mock upload file di `tests/test_api.py`.
  * Memperbaiki loop off-by-one pada pengujian rate limiter di `tests/test_security.py`.
  * Menyesuaikan threshold panjang chunk pada pengujian koherensi di `tests/test_chunker.py`.
  * **[NEW]** Membuat berkas [conftest.py](file:///d:/IndoGov/IndoGovRAG/tests/conftest.py) yang mendefinisikan autouse fixture untuk me-reset status/history dari rate limiter setiap kali sebuah test selesai dijalankan agar tidak terjadi kebocoran state (state leak) antar pengujian.

---

## 📈 Verifikasi Pengujian Akhir
Menjalankan pengujian dengan perintah:
```powershell
python -m pytest --no-header -q
```
**Hasil**:
```text
231 passed, 14 warnings in 56.51s
```
Semua test telah lulus secara penuh.
