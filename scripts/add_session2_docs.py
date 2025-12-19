"""
Add more sample documents to vector store
Expanding from 5 to 20+ documents for better coverage
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.simple_vector_store import SimpleVectorStore

# Initialize vector store
vector_store = SimpleVectorStore()

# Session 2: Add 15 more documents
new_documents = [
    # IDENTITAS (5 new)
    {
        'title': 'SIM (Surat Izin Mengemudi)',
        'text': '''Surat Izin Mengemudi (SIM) adalah bukti registrasi dan identifikasi yang diberikan oleh Polri kepada seseorang yang telah memenuhi persyaratan administrasi, sehat jasmani dan rohani, memahami peraturan lalu lintas dan terampil mengemudikan kendaraan bermotor.

Jenis SIM:
- SIM A: untuk mengemudikan mobil penumpang dan barang dengan jumlah berat yang diperbolehkan tidak melebihi 3.500 kg
- SIM B I: untuk mengemudikan mobil penumpang dan barang dengan jumlah berat yang diperbolehkan lebih dari 3.500 kg  
- SIM B II: untuk mengemudikan kendaraan alat berat, traktor, atau kendaraan bermotor dengan menarik kereta tempelan atau gandengan
- SIM C: untuk mengemudikan sepeda motor
- SIM D: untuk mengemudikan kendaraan khusus bagi penyandang disabilitas

Persyaratan membuat SIM:
1. Usia minimal 17 tahun
2. Lulus tes kesehatan
3. Lulus tes tertulis dan praktik mengemudi
4. Membawa KTP asli dan fotokopi
5. Pas foto berwarna terbaru ukuran 4x6 (3 lembar)

Masa berlaku SIM: 5 tahun dan dapat diperpanjang.''',
        'metadata': {'category': 'identitas', 'source': 'UU No. 22 Tahun 2009'}
    },
    
    {
        'title': 'Paspor Indonesia',
        'text': '''Paspor adalah dokumen resmi yang dikeluarkan oleh pejabat yang berwenang dari suatu negara yang memuat identitas pemegangnya dan berlaku untuk melakukan perjalanan antar negara.

Jenis Paspor:
1. Paspor Biasa (Hijau): untuk perjalanan umum
2. Paspor Diplomatik (Hitam): untuk pejabat diplomatik
3. Paspor Dinas (Biru): untuk perjalanan dinas pemerintah

Persyaratan Paspor Biasa:
1. KTP asli dan fotokopi
2. Kartu Keluarga asli dan fotokopi
3. Akta Kelahiran atau Ijazah
4. Pas foto 4x6 cm (3 lembar) latar belakang putih
5. Surat Nikah (jika sudah menikah)

Biaya pembuatan:
- Paspor 24 halaman: Rp 100.000
- Paspor 48 halaman: Rp 150.000  
- Paspor elektronik 24 halaman: Rp 350.000
- Paspor elektronik 48 halaman: Rp 655.000

Masa berlaku: 5 tahun
Waktu pembuatan: 3-5 hari kerja''',
        'metadata': {'category': 'identitas', 'source': 'UU No. 6 Tahun 2011'}
    },
    
    {
        'title': 'SKCK (Surat Keterangan Catatan Kepolisian)',
        'text': '''SKCK adalah surat keterangan resmi yang diterbitkan oleh Polri melalui fungsi Intelkam sebagai hasil penelitian tentang ada atau tidaknya catatan seseorang yang pernah terlibat dengan perkara pidana.

Kegunaan SKCK:
1. Melamar pekerjaan
2. Pencalonan anggota legislatif
3. Pencalonan kepala daerah
4. Kepemilikan senjata api
5. Adopsi anak
6. Visa ke luar negeri
7. Pendaftaran sekolah/kuliah tertentu

Persyaratan SKCK:
1. Fotokopi KTP/SIM/Paspor
2. Fotokopi Kartu Keluarga
3. Pas foto 4x6 cm (6 lembar) latar merah
4. Fotokopi akta kelahiran/ijazah
5. Sidik jari (dilakukan di tempat)

Biaya: Gratis (sejak 2018)

Masa berlaku: 6 bulan

Tempat pengurusan:
- Polsek (untuk keperluan lokal)
- Polres (untuk keperluan antar kota/kabupaten)
- Polda (untuk keperluan nasional)
- Mabes Polri (untuk keperluan internasional)''',
        'metadata': {'category': 'identitas', 'source': 'Perkap No. 18 Tahun 2014'}
    },
    
    {
        'title': 'Nomor Induk Kependudukan (NIK)',
        'text': '''NIK adalah nomor identitas penduduk yang bersifat unik atau khas, tunggal, dan melekat pada seseorang yang terdaftar sebagai penduduk Indonesia.

Karakteristik NIK:
- Terdiri dari 16 digit angka
- Berlaku seumur hidup
- Tidak berubah meskipun pindah domisili
- Terintegrasi dalam KTP Elektronik

Format NIK (16 digit):
- 6 digit pertama: Kode wilayah (provinsi, kab/kota, kecamatan)
- 6 digit tengah: Tanggal lahir (DDMMYY, +40 untuk perempuan)
- 4 digit terakhir: Nomor urut registrasi

Fungsi NIK:
1. Dasar penerbitan Paspor
2. Dasar penerbitan SIM
3. Pembayaran Pajak
4. Pembuatan NPWP
5. Pembukaan rekening bank
6. Pembuatan BPJS
7. Semua pelayanan publik

NIK mulai digunakan sejak implementasi KTP Elektronik tahun 2011.

Data NIK tersimpan dalam sistem Dukcapil (Dinas Kependudukan dan Pencatatan Sipil).''',
        'metadata': {'category': 'identitas', 'source': 'UU No. 24 Tahun 2013'}
    },
    
    {
        'title': 'Kartu Keluarga (KK)',
        'text': '''Kartu Keluarga (KK) adalah kartu identitas keluarga yang memuat data tentang susunan, hubungan, dan jumlah anggota keluarga.

Isi Kartu Keluarga:
1. Nomor Kartu Keluarga (16 digit)
2. Nama lengkap Kepala Keluarga
3. Alamat lengkap
4. Data setiap anggota keluarga:
   - NIK
   - Nama lengkap
   - Jenis kelamin
   - Tempat/tanggal lahir
   - Agama
   - Pendidikan
   - Pekerjaan
   - Status perkawinan
   - Status hubungan dalam keluarga
   - Kewarganegaraan

Fungsi Kartu Keluarga:
- Syarat membuat KTP
- Syarat menikah
- Syarat mengurus akta kelahiran
- Syarat mendaftar sekolah
- Mengurus berbagai administrasi kependudukan

Pengurusan KK Baru:
1. Untuk keluarga baru (menikah)
2. Karena pindah alamat
3. Karena hilang/rusak
4. Karena ada perubahan data

Masa berlaku: Tidak ada, berlaku selama tidak ada perubahan data

Tempat pengurusan: Kantor Dinas Kependudukan dan Catatan Sipil (Disdukcapil)''',
        'metadata': {'category': 'identitas', 'source': 'UU No. 23 Tahun 2006'}
    },
    
    # KELUARGA (3 new)
    {
        'title': 'Akta Kelahiran',
        'text': '''Akta Kelahiran adalah akta catatan sipil hasil pencatatan terhadap peristiwa kelahiran seseorang.

Fungsi Akta Kelahiran:
1. Bukti sah identitas anak
2. Syarat membuat KTP (17 tahun)
3. Pendaftaran sekolah
4. Syarat ikut ujian nasional
5. Melamar pekerjaan
6. Mengurus dokumen (paspor, SIM)
7. Mendapatkan warisan

Persyaratan:
Untuk bayi (0-60 hari):
1. Surat keterangan lahir dari dokter/bidan
2. KK orang tua
3. KTP orang tua
4. Buku nikah orang tua

Untuk anak (>60 hari):
Tambahan: Surat keterangan terlambat dari kelurahan

Biaya:
- Pembuatan pertama: GRATIS
- Terlambat (>60 hari): Rp 25.000 - 50.000 (denda)
- Duplikat karena hilang: Sesuai Perda

Tempat pengurusan:
- Dinas Kependudukan dan Catatan Sipil (Disdukcapil)
- Bisa online di dukc apil.kemendagri.go.id

Waktu pembuatan: 1-7 hari kerja''',
        'metadata': {'category': 'keluarga', 'source': 'UU No. 24 Tahun 2013'}
    },
    
    {
        'title': 'Akta Perkawinan',
        'text': '''Akta Perkawinan adalah akta autentik yang memuat informasi lengkap tentang peristiwa perkawinan seseorang.

Fungsi Akta Nikah:
1. Bukti sah perkawinan
2. Syarat mengurus Kartu Keluarga
3. Mengurus akta kelahiran anak
4. Mengurus BPJS Kesehatan (tambah tanggungan)
5. Klaim asuransi
6. Mengurus warisan
7. Pengurusan administrasi di kantor
8. Membuat paspor (status married)

Dokumen yang diperlukan:
Dari KUA (pernikahan Islam):
1. Buku Nikah asli dari KUA
2. KTP suami-istri
3. KK suami-istri
4. Pas foto 4x6 (4 lembar)

Dari Catatan Sipil (non-Islam):
1. Surat keterangan nikah dari tempat ibadah
2. KTP suami-istri  
3. KK suami-istri
4. Akta kelahiran suami-istri
5. Pas foto 4x6

Biaya: GRATIS

Tempat pengurusan:
- Islam: KUA (Kantor Urusan Agama) lalu ke Disdukcapil
- Non-Islam: Disdukcapil langsung

Waktu pembuatan: 1-3 hari kerja setelah menikah''',
        'metadata': {'category': 'keluarga', 'source': 'UU No. 1 Tahun 1974'}
    },
    
    {
        'title': 'Akta Perceraian',
        'text': '''Akta Perceraian adalah akta autentik yang memuat keterangan mengenai peristiwa perceraian.

Fungsi Akta Cerai:
1. Bukti sah status janda/duda
2. Mengurus perubahan status di KTP
3. Perubahan KK
4. Menikah lagi (syarat)
5. Hak asuh anak
6. Pembagian harta gonseng
7. Mengurus tunjangan mantan pasangan

Cara mendapatkan:
1. Putusan pengadilan yang telah berkekuatan hukum tetap
2. Mengajukan ke Disdukcapil dengan membawa:
   - Salinan putusan cerai dari pengadilan
   - KTP asli
   - KK asli
   - Akta Perkawinan
   - Pas foto 4x6 (4 lembar)

Biaya: GRATIS

Proses:
Islam: Gugatan cerai di Pengadilan Agama
Non-Islam: Gugatan cerai di Pengadilan Negeri

Setelah putusan cerai inkracht (final), baru bisa urus akta cerai di Disdukcapil.

Waktu: 3-7 hari kerja setelah putusan inkracht''',
        'metadata': {'category': 'keluarga', 'source': 'UU No. 1 Tahun 1974'}
    },
]

print(f"📚 Adding {len(new_documents)} new documents...")

# Add all documents at once
vector_store.add_documents([{
    'text': doc['text'],
    'metadata': doc['metadata'] | {'title': doc['title']}
} for doc in new_documents])

print(f"✅ Successfully added {len(new_documents)} documents!")
print(f"✅ Total documents in database: {vector_store.count()}")
print("🎉 Session 2 documents added successfully!")
