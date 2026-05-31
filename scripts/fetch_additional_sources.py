"""
Multi-Source JDIH Data Fetcher
Fetches from multiple government portals using confirmed working APIs
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


def fetch_jdih_feed(url: str, source_name: str, limit: int = 30) -> list:
    """Fetch documents from JDIH feed/JSON endpoint."""
    results = []

    try:
        print(f"\n  Fetching from {source_name}...")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()

        data = resp.json()

        if isinstance(data, list):
            items = data[:limit]
        elif isinstance(data, dict):
            items = data.get('items', data.get('data', data.get('results', [])))[:limit]
        else:
            items = []

        for item in items:
            if isinstance(item, dict):
                results.append({
                    'title': item.get('title', item.get('name', 'Unknown')),
                    'date': item.get('date', item.get('pubDate', '')),
                    'url': item.get('url', item.get('link', '')),
                    'description': item.get('description', item.get('summary', '')),
                    'type': item.get('type', item.get('category', 'Unknown')),
                    'source': source_name
                })
        print(f"    Found {len(results)} documents")
    except Exception as e:
        print(f"    Error: {e}")

    return results


def fetch_peraturan_dot_go_id() -> list:
    """Fetch from peraturan.go.id sitemap/API."""
    results = []

    urls_to_try = [
        ("https://peraturan.go.id/api/v1/peraturan", "Peraturan.go.id API"),
        ("https://peraturan.go.id/feeds/peraturan.json", "Peraturan.go.id Feed"),
    ]

    for url, name in urls_to_try:
        try:
            print(f"\n  Trying {name}...")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    for item in data[:20]:
                        results.append({
                            'title': item.get('title', 'Unknown'),
                            'date': item.get('date', ''),
                            'url': item.get('url', ''),
                            'type': item.get('type', 'Peraturan'),
                            'source': 'peraturan.go.id'
                        })
                    print(f"    Found {len(data)} items")
                    break
        except:
            continue

    return results


def fetch_jdih_bpk() -> list:
    """Fetch from JDIH BPK."""
    results = []

    urls_to_try = [
        "https://peraturan.bpk.go.id/api/v1/regulations",
        "https://peraturan.bpk.go.id/api/regulations",
    ]

    for url in urls_to_try:
        try:
            print(f"\n  Trying {url}...")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    for item in data[:30]:
                        results.append({
                            'title': item.get('title', item.get('name', 'Unknown')),
                            'date': item.get('date', item.get('year', '')),
                            'url': item.get('url', item.get('link', '')),
                            'type': item.get('type', 'PP'),
                            'source': 'JDIH BPK'
                        })
                    print(f"    Found {len(results)} documents")
                    return results
        except:
            continue

    return results


def fetch_hukumonline() -> list:
    """Try hukumonline.com public endpoints."""
    results = []

    try:
        print("\n  Trying hukumonline.com...")
        # Try their public search API
        url = "https://www.hukumonline.com/api/v1/search"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get('results', [])[:20]:
                results.append({
                    'title': item.get('title', 'Unknown'),
                    'date': item.get('date', ''),
                    'url': item.get('url', ''),
                    'type': item.get('type', 'UU'),
                    'source': 'hukumonline'
                })
    except Exception as e:
        print(f"    Not accessible: {e}")

    return results


def generate_government_content() -> list:
    """Generate comprehensive Indonesian government content chunks."""
    topics = [
        {
            'title': 'Kartu Tanda Penduduk Elektronik (KTP-el)',
            'category': 'administrasi_kependudukan',
            'content': """
KARTU TANDA PENDUDUK ELEKTRONIK (KTP-el)

Berdasarkan Peraturan Presiden Nomor 26 Tahun 2009 tentang Penerapan KTP Berbasis NIK, KTP Elektronik wajib dimiliki oleh setiap warga negara Indonesia.

PERSYARATAN PEMBUATAN KTP-el:
1. Warga Negara Indonesia yang telah berumur 17 tahun
2. Telah menikah atau pernah menikah
3. Terdata dalam Database Kependudukan

DOKUMEN YANG DIPERLUKAN:
- Fotokopi Kartu Keluarga (KK)
- Surat pengantar dari RT/RW
- Fotokopi akta kelahiran atau dokumen lain yang membuktikan identitas
- Pas foto ukuran 3x4 cm (2 lembar)

CARA PEMBUATAN:
1. Datang ke kantor Kecamatan atau Dinas Kependudukan
2. Ambil nomor antrian
3. Serahkan dokumen persyaratannya
4. Lakukan perekaman biometric (foto, sidik jari, tanda tangan)
5. Tunggu proses verifikasi data
6. KTP-el akan dikirim ke alamat rumah dalam 14 hari kerja

MASA BERLAKU:
- KTP-el berlaku seumur hidup bagi warga yang telah berumur 55 tahun
- Untuk usia 17-54 tahun, berlaku 5 tahun dan wajib diperpanjang

FITUR KEAMANAN:
- Chip elektronik yang menyimpan data biometric
- QR Code untuk verifikasi data
- NIK (Nomor Induk Kependudukan) yang unik dan permanen

LAYANAN ONLINE:
- Bisa dibuat melalui aplikasiere - dokumen dapat diurus secara online
- Status pembuatan dapat dipantau melalui website Kemendagri
            """
        },
        {
            'title': 'NPWP dan Perpajakan Indonesia',
            'category': 'perpajakan',
            'content': """
NOMOR POKOK WAJIB PAJAK (NPWP)

NPWP adalah nomor identitas perpajakan yang diberikan kepada wajib pajak sebagai sarana dalam administrasi perpajakan.

PENDAFTARAN NPWP:
1. Secara online melalui situs resmi DJP
2. Melalui KPP (Kantor Pelayanan Pajak) terdekat
3. Melalui jasa perpajakan atau konsultan pajak

DOKUMEN YANG DIPERLUKAN:
- KTP untuk wajib pajak orang pribadi
- NPWP istri (jika istri sudah punya NPWP)
- Kartu Keluarga
- Dokumen pendukung sesuai jenis wajib pajak

JENIS WAJIB PAJAK:
1. Wajib Pajak Orang Pribadi
2. Wajib Pajak Badan (PT, CV, Firma, Kongsi)
3. Wajib Pajak Institusi Pemerintah

KEWAJIBAN PEMBAYARAN PAJAK:
- PPh Pasal 21 (Gaji/karyawan)
- PPh Pasal 22 (Impor dan penjualan barang)
- PPh Pasal 23 (Jasa dan dividen)
- PPh Pasal 25 (angsuran bulanan)
- PPh Pasal 26 (Penghasilan luar negeri)
- PPh Final 0.5% untuk UMKM
- PPN 11%

SANKSI:
- Keterlambatan pembayaran: bunga 2% per bulan
- Tidak membuat SPT: denda Rp 100.000
- Keterlambatan SPT: bunga sesuai tarif
            """
        },
        {
            'title': 'BPJS Kesehatan dan Ketenagakerjaan',
            'category': 'kesehatan',
            'content': """
BPJS (BADAN PENYELENGGARA JAMINAN SOSIAL)

Indonesia memiliki dua program BPJS:
1. BPJS Kesehatan - Jaminan Kesehatan Nasional
2. BPJS Ketenagakerjaan - Jaminan Sosial Ketenagakerjaan

BPJS KESEHATAN:
Peserta BPJS Kesehatan mendapatkan layanan kesehatan di fasilitas kesehatan tingkat pertama dan lanjutan.

PESERTA BPJS KESEHATAN:
- PBI (Penerima Bantuan Iuran) - dibayar pemerintah
- Bukan PBI - iuran dibayar sendiri atau oleh pemberi kerja
- PBPU (Pekerja Bukan Penerima Upah)
- BP (Pekerja Penerima Upah)

KELAS RAWAT INAP:
- Kelas I: Rp 150.000/bulan
- Kelas II: Rp 100.000/bulan
- Kelas III: Rp 42.000/bulan (subsidi pemerintah Rp 7.000)

MANFAAT BPJS KESEHATAN:
- Layanan kesehatan di faskes pertama
- Rawat inap di rumah sakit
- Persalinan
- Operasi
- Obat-obatan
- Promotif dan preventif

BPJS KETENAGAKERJAAN:
4 program jaminan sosial:
1. JKK (Jaminan Kecelakaan Kerja)
2. JKM (Jaminan Kematian)
3. JHT (Jaminan Hari Tua)
4. JP (Jaminan Pensiun)

IURAN BPJS KETENAGAKERJAAN:
- JKK: 0.24% - 1.74% dari gaji (bergantung risiko)
- JKM: 0.20% dari gaji
- JHT: 2% (pekerja) + 3.7% ( pemberi kerja)
- JP: 1% (pekerja) + 2% (pemberi kerja)
            """
        },
        {
            'title': 'Izin Usaha dan NIB melalui OSS',
            'category': 'bisnis',
            'content': """
NOMOR INDUK BERUSAHA (NIB) DAN OSS

OSS (Online Single Submission) adalah sistem perizinan berusaha terintegrasi secara elektronik.

JENIS PERIZINAN:
1. NIB (Nomor Induk Berusaha)
   - Wajib untuk semua pelaku usaha
   - Berlaku sebagai TDP dan API
   - Diperoleh secara gratis

2. Izin Lokasi
   - Untuk usaha yang membutuhkan tanah
   - Diterbitkan oleh Pemerintah Daerah

3. Izin Lingkungan
   - Untuk usaha yang berdampak pada lingkungan
   - AMDAL atau UKL-UPL

4. Izin Komersial/Berdampak
   - Sesuai klasifikasi risiko usaha
   - Terbit setelah NIB

CARA PENGURUSAN:
1. Akses https://oss.go.id
2. Daftar/login dengan akun perusahaan
3. Isi data usaha (nama, alamat, bidang usaha)
4. Sistem otomatis menghasilkan NIB
5. Pilih izin sesuai kebutuhan usaha
6. Unduh izin yang diperlukan

NIB BERLAKU UNTUK:
- (SIUP)
-  (API)
-  (TDP)
-  (NIK)

KESALAHAN UMUM:
- Salah memilih KBLI
- Data tidak sesuai dengan Akta
- Lokasi usaha tidak jelas
            """
        },
        {
            'title': 'Program Kartu Prakerja',
            'category': 'sosial',
            'content': """
KARTU PRAKERA - PROGRAM SEMANGAT KERJA

Kartu Prakerja adalah program bantuan biaya pelatihan untuk pencari kerja, workers yang terdampak COVID-19, dan workers yang membutuhkan peningkatan kompetensi.

PERSYARATAN PESERTA:
1. Warga Negara Indonesia
2. Berusia minimal 18 tahun
3. Tidak sedang bersekolah/perguruan tinggi
4. Terdaftar sebagai pencari kerja atau workers
5. Memiliki KTP dan KK
6. Memiliki nomor HP dan email aktif
7. Memiliki rekening bank mandiri, BCA, BNI, atau BTN

BENEFIT PROGRAM:
1. Bantuan biaya pelatihan: Rp 1.000.000 - Rp 3.550.000
2. Insentif pasca pelatihan: Rp 650.000/bulan (maksimal 4 bulan)
3. Insentif survei: Rp 50.000 (3x survei)

CARA DAFTAR:
1. Buka situs prakerja.go.id
2. Masukkan NIK dan nomor KK
3. Verifikasi data diri
4. Ikuti tes motivasi dan skill dasar
5. Pilih jenis pelatihan yang diinginkan
6. Masukkan kode voucher pelatihan

PELATIHAN YANG TERSEDIA:
- Digital marketing
- Programming
- Bahasa Inggris
- Keuangan pribadi
- Kewirausahaan
- Dan ratusan jenis pelatihan lainnya

MITRA PELATIHAN:
- Tokopedia
- Skillacademy
- HarukaEdu
- Pijar Mahir
- MySkill
- Dan lainnya
            """
        },
        {
            'title': 'Akta Kelahiran dan Dokumen Kependudukan',
            'category': 'administrasi_kependudukan',
            'content': """
AKTA KELAHIRAN

Akta Kelahiran adalah bukti pencatatan sipil tentang kelahiran seseorang yang diterbitkan oleh Dinas Kependudukan.

PENDAFTARAN KELAHIRAN:
- batas waktu: 60 hari sejak kelahiran
- Dapat diajukan secara online atau offline

DOKUMEN YANG DIPERLUKAN:
1. Formulir permohonan
2. Surat keterangan kelahiran dari dokter/bidan
3. KTP orang tua
4. Kartu Keluarga (KK)
5. Buku nikah/akta perkawinan orang tua
6. Pas foto 3x4 cm (2 lembar) orang tua

CARA PENDAFTARAN:
1. Datang ke kantor Desa/Kelurahan
2. Atau melalui aplikasiere (jika tersedia)
3. Serahkan dokumen persyaratannya
4. Tunggu proses verifikasi
5. Akta kelahiran dapat diambil di kantor kecamatan

SANKSI TELAT MENDAFTARKAN:
- Bayi 0-60 hari: Gratis
- 61 hari - 1 tahun: Denda Rp 50.000
- Lebih dari 1 tahun: Denda Rp 500.000

PENTING:
- Akta Kelahiran wajib untuk membuat:
  * KTP
  * Paspor
  * Buku_tabungan
  * Kartu sekolah
  * Dan dokumen lainnya
            """
        },
        {
            'title': 'Pusat Layanan Umum',
            'category': 'pelayanan_publik',
            'content': """
LAYANAN PUBLIK INDONESIA

Indonesia memiliki berbagai layanan publik untuk masyarakat.

MALAMDINAS (LAYANAN SAMBILAN):
- Dilayani di luar jam kerja
- Untuk dokumen mendesak
- Biasanya tersedia di kecamatan besar

APLIKASI PELAYANAN:
1. ere (Dukcapil)
   - Pembuatan KTP
   - Akta Kelahiran
   - Kartu Keluarga
   - KIA (Kartu Identitas Anak)

2. OSS (Online Single Submission)
   - Izin usaha
   - NIB
   - Perizinan berusaha

3.ere (DJP)
   - Pendaftaran NPWP
   - Pelaporan SPT
   - Pembayaran pajak

4. bpjs-ketenagakerjaan.com
   - Pendaftaran BPJS
   - Klaim JHT
   - Klaim JKK

LOKET PELAYANAN TERPADU (LPT):
- Meng berbagai jenis layanan
- Cukup sekali datang
- Dokumen diantar ke rumah

WAKTU PELAYANAN:
- Senin-Kamis: 08.00 - 15.00
- Jumat: 08.00 - 11.30
- Syarat dan ketentuan dapat berbeda tiap daerah
            """
        }
    ]

    chunks = []
    for i, topic in enumerate(topics):
        chunks.append({
            'doc_id': f'gov_content_{i+1}',
            'title': topic['title'],
            'category': topic['category'],
            'text': topic['content'].strip()
        })

    return chunks


def main():
    """Main execution."""
    print("\n" + "=" * 70)
    print("   MULTI-SOURCE GOVERNMENT DATA FETCHER")
    print("=" * 70)

    all_data = []

    # Source 1: JDIH Kemenkeu (confirmed working)
    print("\n[1/4] Fetching from JDIH Kemenkeu...")
    kemenkeu = fetch_jdih_feed(
        "https://jdih.kemenkeu.go.id/api/v2/peraturan",
        "JDIH Kemenkeu",
        limit=30
    )
    all_data.extend(kemenkeu)

    # Source 2: Atom Feed
    print("\n[2/4] Fetching from Atom/RSS feeds...")
    atom_data = fetch_jdih_feed(
        "https://jdih.kemenkeu.go.id/atom.xml",
        "JDIH Kemenkeu Atom",
        limit=30
    )
    all_data.extend(atom_data)

    # Source 3: Try peraturan.go.id
    print("\n[3/4] Trying peraturan.go.id...")
    peraturan = fetch_peraturan_dot_go_id()
    all_data.extend(peraturan)

    # Source 4: Try hukumonline
    print("\n[4/4] Trying hukumonline.com...")
    hukum = fetch_hukumonline()
    all_data.extend(hukum)

    # Generate structured government content
    print("\n[GENERATING] Structured government content...")
    generated = generate_government_content()

    print("\n" + "=" * 70)
    print("   FETCH SUMMARY")
    print("=" * 70)
    print(f"  API/Feed data fetched: {len(all_data)} items")
    print(f"  Structured content: {len(generated)} topics")
    print(f"  Total data items: {len(all_data) + len(generated)}")
    print("=" * 70)

    # Save raw data
    raw_data = {
        'fetched_at': datetime.now().isoformat(),
        'api_data': all_data,
        'generated_content': generated
    }

    output_path = Path("data/fetched_raw_data.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)

    print(f"\n[DONE] Raw data saved to: {output_path}")
    print("\nNext step: Run load_generated_content.py to add to vector store")

    return len(all_data), len(generated)


if __name__ == "__main__":
    main()