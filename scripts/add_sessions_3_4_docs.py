"""
Add Sessions 3 & 4 documents to vector store
Expanding to reach 20+ quality documents
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.simple_vector_store import SimpleVectorStore

# Initialize vector store
vector_store = SimpleVectorStore()

# Sessions 3 & 4: 12 more documents
new_documents = [
    # PAJAK & BISNIS (Session 3)
    {
        'title': 'Pajak Penghasilan (PPh) Orang Pribadi',
        'text': '''Pajak Penghasilan (PPh) dikenakan terhadap Orang Pribadi yang memiliki penghasilan di atas Penghasilan Tidak Kena Pajak (PTKP).

Tarif PPh Orang Pribadi (UU Harmonisasi Peraturan Perpajakan):
- 0 s.d Rp 60 juta/tahun: 5%
- > Rp 60 s.d Rp 250 juta/tahun: 15%
- > Rp 250 s.d Rp 500 juta/tahun: 25%
- > Rp 500 s.d Rp 5 miliar/tahun: 30%
- > Rp 5 miliar/tahun: 35%

PTKP Terbaru:
- Wajib Pajak sendiri: Rp 54.000.000
- Tambahan status kawin: Rp 4.500.000
- Tambahan per tanggungan (maks 3): Rp 4.500.000

Pelaporan:
SPT Tahunan wajib dilaporkan paling lambat tanggal 31 Maret setiap tahunnya melalui e-Filing.''',
        'metadata': {'category': 'pajak', 'source': 'UU HPP No. 7 Tahun 2021'}
    },
    {
        'title': 'Pajak Pertambahan Nilai (PPN)',
        'text': '''PPN adalah pajak yang dikenakan atas konsumsi Barang Kena Pajak atau Jasa Kena Pajak di dalam Daerah Pabean.

Tarif PPN:
- Berlaku sejak 1 April 2022: 11%
- Direncanakan naik menjadi 12% paling lambat pada 1 Januari 2025.

Objek PPN:
- Penyerahan Barang/Jasa Kena Pajak oleh pengusaha.
- Impor Barang Kena Pajak.
- Pemanfaatan Jasa dari luar luar negeri di dalam negeri.
- Ekspor oleh Pengusaha Kena Pajak (Tarif 0%).''',
        'metadata': {'category': 'pajak', 'source': 'UU HPP No. 7 Tahun 2021'}
    },
    {
        'title': 'Online Single Submission (OSS)',
        'text': '''OSS (Online Single Submission) adalah sistem perizinan berusaha terintegrasi secara elektronik yang dikelola oleh Lembaga OSS (BKPM).

Tingkat Risiko Usaha (OSS RBA):
1. Risiko Rendah: Cukup NIB (Nomor Induk Berusaha).
2. Risiko Menengah Rendah: NIB + Sertifikat Standar (Self-declare).
3. Risiko Menengah Tinggi: NIB + Sertifikat Standar (Verifikasi).
4. Risiko Tinggi: NIB + Izin (Persetujuan Pemerintah).

Keuntungan menggunakan OSS:
- Mempermudah pengurusan berbagai izin usaha.
- Proses lebih cepat dan transparan.
- Terintegrasi dengan kementerian/lembaga terkait.''',
        'metadata': {'category': 'bisnis', 'source': 'PP No. 5 Tahun 2021'}
    },
    {
        'title': 'Nomor Induk Berusaha (NIB)',
        'text': '''NIB adalah identitas setiap pelaku usaha yang diterbitkan oleh Lembaga OSS setelah pelaku usaha melakukan registrasi.

Fungsi NIB:
1. Sebagai identitas perusahaan atau pelaku usaha.
2. Berlaku sebagai Tanda Daftar Perusahaan (TDP).
3. Berlaku sebagai Angka Pengenal Importir (API).
4. Berlaku sebagai Akses Kepabeanan.
5. Syarat untuk mendapatkan izin operasional maupun izin komersial.

Cara mendapatkan NIB:
Pendaftaran dilakukan melalui portal oss.go.id dengan menggunakan NIK (untuk perseorangan) atau pengesahan badan usaha (untuk PT/CV).''',
        'metadata': {'category': 'bisnis', 'source': 'PP No. 24 Tahun 2018'}
    },
    {
        'title': 'Kredit Usaha Rakyat (KUR)',
        'text': '''KUR adalah program pembiayaan/kredit dengan subsidi bunga dari pemerintah untuk membantu permodalan bagi UMKM.

Jenis KUR:
- KUR Super Mikro: Plafon sampai Rp 10 juta.
- KUR Mikro: Plafon > Rp 10 juta s.d Rp 100 juta.
- KUR Kecil: Plafon > Rp 100 juta s.d Rp 500 juta.

Suku Bunga:
Umumnya 6% efektif per tahun (mendapat subsidi bunga dari pemerintah).

Persyaratan:
1. Memiliki usaha layak yang sudah berjalan minimal 6 bulan.
2. Tidak sedang menerima kredit produktif dari perbankan (kecuali kredit konsumtif seperti KPR/KKB).
3. NIB atau Surat Keterangan Usaha (SKU).
4. KTP dan Kartu Keluarga.''',
        'metadata': {'category': 'ekonomi', 'source': 'Permenko Perekonomian'}
    },

    # KESEHATAN & PENDIDIKAN (Session 4)
    {
        'title': 'Pendaftaran BPJS Penduduk Mandiri',
        'text': '''Pendaftaran Peserta Bukan Penerima Upah (PBPU) atau Peserta Mandiri dapat dilakukan secara online melalui aplikasi Mobile JKN atau secara offline.

Dokumen yang diperlukan:
1. Kartu Keluarga (KK).
2. KTP Elektronik.
3. Buku Tabungan (untuk autodebit: BNI, BRI, Mandiri, atau BCA).
4. Alamat email dan nomor HP aktif.

Iuran Bulanan (per orang):
- Kelas I: Rp 150.000
- Kelas II: Rp 100.000
- Kelas III: Rp 42.000 (disubsidi pemerintah Rp 7.000, sehingga peserta bayar Rp 35.000).

Pembayaran iuran paling lambat tanggal 10 setiap bulannya.''',
        'metadata': {'category': 'kesehatan', 'source': 'Perpres No. 64 Tahun 2020'}
    },
    {
        'title': 'Kartu Indonesia Pintar (KIP) Kuliah',
        'text': '''KIP Kuliah adalah bantuan biaya pendidikan dari pemerintah bagi lulusan SMA/sederajat yang memiliki potensi akademik baik tetapi memiliki keterbatasan ekonomi.

Manfaat KIP Kuliah:
1. Pembebasan biaya pendaftaran seleksi masuk perguruan tinggi.
2. Pembebasan biaya kuliah (langsung ke perguruan tinggi).
3. Bantuan biaya hidup yang disesuaikan dengan indeks harga daerah.

Persyaratan:
- Penerima KIP SMA/Sederajat atau berasal dari keluarga peserta Program Keluarga Harapan (PKH).
- Berasal dari keluarga dengan total penghasilan kotor gabungan orang tua/wali maksimal Rp 4.000.000/bulan atau jika dibagi jumlah anggota keluarga maksimal Rp 750.000/orang.''',
        'metadata': {'category': 'pendidikan', 'source': 'Permendikbud No. 10 Tahun 2020'}
    },
    {
        'title': 'Program Keluarga Harapan (PKH)',
        'text': '''PKH adalah program pemberian bantuan sosial bersyarat kepada Keluarga Miskin (KM) yang ditetapkan sebagai keluarga penerima manfaat PKH.

Komponen Bantuan:
1. Kesehatan: Ibu hamil dan anak usia dini (0-6 tahun).
2. Pendidikan: Anak SD, SMP, dan SMA.
3. Kesejahteraan Sosial: Lanjut usia (70+ tahun) dan penyandang disabilitas berat.

Kewajiban Peserta:
- Memeriksakan kesehatan ibu hamil/balita di Faskes.
- Memastikan kehadiran anak sekolah minimal 85% hari sekolah.
- Mengikuti pertemuan peningkatan kemampuan keluarga (P2K2).''',
        'metadata': {'category': 'sosial', 'source': 'Permensos No. 1 Tahun 2018'}
    },
    {
        'title': 'Bantuan Pangan Non-Tunai (BPNT)',
        'text': '''BPNT atau Program Sembako adalah bantuan sosial pangan dalam bentuk non-tunai dari pemerintah kepada Keluarga Penerima Manfaat (KPM).

Mekanisme:
- Bantuan disalurkan melalui Kartu Keluarga Sejahtera (KKS).
- Nilai bantuan adalah Rp 200.000/bulan per KPM.
- Saldo dapat ditukarkan dengan bahan pangan (beras, telur, kacang-kacangan, daging) di e-warong atau agen bank yang ditunjuk.

Penyaluran:
Biasanya dirapel per dua atau tiga bulan sekali langsung ke rekening KKS masing-masing penerima.''',
        'metadata': {'category': 'sosial', 'source': 'Perpres No. 63 Tahun 2017'}
    }
]

print(f"📚 Adding {len(new_documents)} new documents (Sessions 3 & 4)...")

# Add all documents at once
vector_store.add_documents([{
    'text': doc['text'],
    'metadata': doc['metadata'] | {'title': doc['title']}
} for doc in new_documents])

print(f"✅ Successfully added {len(new_documents)} documents!")
print(f"✅ Total documents in database: {vector_store.count()}")
print("🎉 Sessions 3 & 4 documents added successfully!")
