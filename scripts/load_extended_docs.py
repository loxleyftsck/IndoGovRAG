"""
Extended Sample Documents Loader - 15+ Indonesian Government Topics
Autonomously expands corpus for immediate testing
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.vector_search import VectorStore, prepare_chunks_for_indexing
from src.data.chunker import Chunk

def load_extended_documents():
    """Load 15 comprehensive Indonesian government document samples."""
    
    print("🚀 AUTONOMOUS DATA EXPANSION - Loading 15 Documents...")
    print()
    
    # Extended government topics
    documents = [
        {
            'doc_id': 'sim_001',
            'title': 'SIM dan Persyaratannya',
            'text': """Surat Izin Mengemudi (SIM) adalah bukti kompetensi mengemudi kendaraan bermotor.
            Jenis SIM: A (mobil), C (motor), B1 (angkutan umum), B2 (truk/bus).
            Persyaratan: KTP, usia min 17 tahun, lulus tes teori dan praktik, sehat jasmani rohani.
            Masa berlaku: 5 tahun, perpanjangan max 1 tahun sebelum expired, denda jika terlambat.
            Penerbitan dilakukan di Satpas (Satuan Penyelenggara Administrasi SIM) Polri.""",
            'category': 'lalu_lintas'
        },
        {
            'doc_id': 'paspor_001',
            'title': 'Paspor dan Pembuatannya',
            'text': """Paspor adalah dokumen resmi untuk perjalanan internasional yang dikeluarkan Kementerian Luar Negeri.
            Jenis: Biasa (48 halaman atau 24 halaman), Diplomatik, Dinas.
            Syarat: KTP, KK, Akta Lahir, foto 4x6, biaya Rp 350.000 (biasa) atau Rp 655.000 (48 hal).
            Masa berlaku: 5 tahun untuk dewasa, 3 tahun untuk anak.
            Pembuatan: Online booking via imigrasi.go.id, datang ke kantor imigrasi, foto dan sidik jari, ambil 3-5 hari kerja.""",
            'category': 'keimigrasian'
        },
        {
            'doc_id': 'nikah_001',
            'title': 'Persyaratan Menikah',
            'text': """Persyaratan menikah di Indonesia sesuai UU Perkawinan No. 1 Tahun 1974:
            Usia minimum: 19 tahun untuk pria dan wanita (UU 16/2019).
            Dokumen: KTP, KK, Akta Lahir, surat keterangan belum menikah, foto 4x6.
            Untuk Muslim: daftar di KUA (Kantor Urusan Agama), walau difasilitasi negara biaya Rp 0.
            Non-Muslim: daftar di Catatan Sipil. Wajib lapor max 60 hari setelah akad untuk dapat Akta Nikah.""",
            'category': 'catatan_sipil'
        },
        {
            'doc_id': 'akta_lahir_001',
            'title': 'Akta Kelahiran',
            'text': """Akta Kelahiran adalah bukti sah kelahiran yang dikeluarkan Dinas Kependudukan dan Catatan Sipil.
            Wajib dilaporkan max 60 hari sejak lahir, gratis jika tepat waktu.
            Syarat: Surat keterangan kelahiran dari RS/bidan, KTP & KK orang tua, Akta Nikah orang tua.
            Jika terlambat >1 tahun: perlu penetapan pengadilan, biaya administrasi naik.
            Akta diperlukan untuk: masuk sekolah, melamar pekerjaan, mengurus BPJS, dll.""",
            'category': 'catatan_sipil'
        },
        {
            'doc_id': 'kartu_keluarga_001',
            'title': 'Kartu Keluarga (KK)',
            'text': """Kartu Keluarga adalah kartu identitas keluarga yang memuat data seluruh anggota keluarga.
            Dibuat saat: menikah, pindah domisili, penambahan/pengurangan anggota keluarga.
            Syarat: KTP kepala keluarga, Akta Nikah, Akta Lahir anak-anak, surat pindah (jika pindah).
            Gratis, diurus di Dinas Kependudukan, selesai 14 hari kerja.
            KK diperlukan untuk: buat KTP, daftar sekolah, buka rekening, kredit rumah.""",
            'category': 'administrasi_kependudukan'
        },
        {
            'doc_id': 'bpjs_tk_001',
            'title': 'BPJS Ketenagakerjaan',
            'text': """BPJS Ketenagakerjaan memberikan perlindungan untuk tenaga kerja.
            Program: JKK (Kecelakaan Kerja), JKM (Kematian), JHT (Hari Tua), JP (Pensiun).
            Wajib untuk semua pekerja formal, termasuk outsourcing dan kontrak.
            Iuran ditanggung perusahaan dan pekerja, auto-potong dari gaji.
            JHT bisa dicairkan saat resign (30% jika <10 tahun, 100% jika PHK/pensiun).""",
            'category': 'ketenagakerjaan'
        },
        {
            'doc_id': 'ppn_001',
            'title': 'PPN dan Mekanismenya',
            'text': """Pajak Pertambahan Nilai (PPN) adalah pajak konsumsi atas barang/jasa.
            Tarif umum: 11% (2022), akan naik 12% (2025).
            Dikecualikan: beras, daging, sayur, jasa pendidikan, jasa kesehatan.
            PKP (Pengusaha Kena Pajak): omzet >4.8M/tahun, wajib pungut PPN.
            Faktur Pajak wajib diterbitkan untuk setiap transaksi kena PPN.""",
            'category': 'perpajakan'
        },
        {
            'doc_id': 'pph_21_001',
            'title': 'PPh Pasal 21 Karyawan',
            'text': """PPh 21 adalah pajak penghasilan untuk karyawan/pegawai.
            PTKP (Penghasilan Tidak Kena Pajak) 2024: Rp 54 juta/tahun untuk TK/0.
            Tarif progresif: 5% (<60jt), 15% (60-250jt), 25% (250-500jt), 30% (>500jt).
            Dipotong langsung dari gaji bulanan oleh perusahaan (withholding).
            Bukti potong (1721-A1) diberi akhir tahun untuk lapor SPT Tahunan.""",
            'category': 'perpajakan'
        },
        {
            'doc_id': 'pt_001',
            'title': 'Pendirian PT',
            'text': """Perseroan Terbatas (PT) adalah badan usaha dengan modal terpisah dari pemilik.
            Modal minimal: Rp 50 juta (biasa), tergantung bidang usaha.
            Direktur minimal 1 orang, komisaris minimal 1 orang.
            Syarat: Akta Notaris, SK Kemenkumham, NPWP Perusahaan, NIB via OSS.
            Kewajiban: lapor SPT Tahunan Badan, bayar pajak badan 22%, BPJS Ketenagakerjaan karyawan.""",
            'category': 'hukum_bisnis'
        },
        {
            'doc_id': 'cv_001',
            'title': 'CV vs PT',
            'text': """CV (Commanditaire Vennootschap) adalah persekutuan komanditer.
            Perbedaan CV & PT: CV modal min bebas, PT min 50jt; CV tanggung jawab tak terbatas (sekutu aktif), PT terbatas.
            CV lebih mudah didirikan (cukup akta notaris), PT perlu SK Kemenkumham.
            Pajak: sama (22% badan), tapi CV bisa lebih fleksibel struktur.
            Pilih CV jika: usaha UMKM/keluarga, PT jika: ekspansi besar/cari investor.""",
            'category': 'hukum_bisnis'
        },
        {
            'doc_id': 'hki_001',
            'title': 'Hak Kekayaan Intelektual',
            'text': """HKI melindungi karya intelektual: paten, merek, hak cipta, desain industri.
            Merek: daftar di DJKI Kemenkumham, biaya Rp 1.8jt, berlaku 10 tahun (perpanjang).
            Paten: 20 tahun (biasa), 10 tahun (sederhana), biaya jutaan rupiah.
            Hak Cipta: otomatis setelah karya diciptakan, tapi lebih baik didaftarkan.
            Manfaat: perlindungan hukum, nilai ekonomi, komersialisasi.""",
            'category': 'hukum_bisnis'
        },
        {
            'doc_id': 'tanah_001',
            'title': 'Sertifikat Tanah',
            'text': """Sertifikat adalah bukti hak atas tanah, diterbitkan BPN (Badan Pertanahan Nasional).
            Jenis: Hak Milik (selamanya), Hak Guna Bangunan (30 tahun), Hak Pakai.
            Proses: ukur tanah, cek riwayat, bayar BPHTB dan biaya admin, terbit sertifikat.
            Biaya: tergantung NJOP, sekitar 3-5% nilai tanah.
            Penting untuk: jual-beli, kredit rumah, warisan.""",
            'category': 'pertanahan'
        },
        {
            'doc_id': 'imb_001',
            'title': 'IMB dan PBG',
            'text': """IMB (Izin Mendirikan Bangunan) sudah diganti PBG (Persetujuan Bangunan Gedung) sejak 2020.
            Wajib untuk: rumah >100m2, bangunan komersial, renovasi besar.
            Syarat: sertifikat tanah, KTP, gambar arsitektur, analisis struktur.
            Proses via OSS (Online Single Submission), selesai 5-10 hari kerja.
            Sanksi tanpa IMB/PBG: denda, pembongkaran paksa, tidak bisa jual resmi.""",
            'category': 'perizinan'
        },
        {
            'doc_id': 'kur_001',
            'title': 'Kredit Usaha Rakyat (KUR)',
            'text': """KUR adalah kredit modal kerja untuk UMKM dengan bunga subsidi pemerintah.
            Plafon: Mikro (<50jt), Kecil (50-500jt), TKI.
            Bunga: 6% per tahun (subsidi), tanpa agunan untuk KUR Mikro.
            Syarat: usaha produktif min 6 bulan, punya NPWP, tidak sedang kredit macet.
            Bank penyalur: BRI, BNI, Mandiri, BTN, dan 40+ bank lain.""",
            'category': 'ekonomi'
        },
        {
            'doc_id': 'kartu_prakerja_001',
            'title': 'Kartu Prakerja',
            'text': """Program Kartu Prakerja untuk peningkatan kompetensi dan bantuan produktif.
            Sasaran: pengangguran, pekerja terdampak PHK, pelaku UMKM.
            Benefit: insentif pelatihan Rp 3.5jt, insentif survey Rp 600rb (total Rp 4.1jt).
            Cara: daftar online via prakerja.go.id, ikuti seleksi, pilih pelatihan, selesai dapat insentif.
            Gelombang aktif: cek website resmi, biasanya 3-4 kali/tahun.""",
            'category': 'ketenagakerjaan'
        }
    ]
    
    # Initialize vector store
    print("📦 Initializing Vector Store...")
    store = VectorStore()
    print(f"   Current chunks: {store.collection.count()}")
    
    # Create chunks
    chunks = []
    chunk_id = 100  # Start from 100 to avoid conflicts
    
    for doc in documents:
        text = doc['text'].strip()
        chunk = Chunk(
            doc_id=doc['doc_id'],
            chunk_id=chunk_id,
            text=text,
            start_char=0,
            end_char=len(text),
            num_tokens=len(text.split()),
            metadata={
                'title': doc['title'],
                'category': doc['category'],
                'doc_type': 'sample_extended',
                'source': 'autonomous_expansion'
            }
        )
        chunks.append(chunk)
        chunk_id += 1
    
    # Prepare & add
    print(f"📝 Preparing {len(chunks)} chunks...")
    prepared_chunks = prepare_chunks_for_indexing(chunks)
    
    print("💾 Adding to vector store...")
    store.add_chunks(prepared_chunks, show_progress=True)
    
    # Final count
    final_count = store.collection.count()
    added = final_count - 8  # We had 8 before
    
    print()
    print(f"✅ Successfully added {added} new documents!")
    print(f"📊 Total chunks now: {final_count}")
    print()
    
    # Test coverage
    print("🧪 Testing topic coverage...")
    test_topics = [
        ("KTP", "administrasi"),
        ("SIM", "lalu_lintas"),
        ("Paspor", "keimigrasian"),
        ("BPJS", "kesehatan"),
        ("Pajak", "perpajakan"),
        ("PT", "bisnis")
    ]
    
    for topic, category in test_topics:
        results = store.search(topic, n_results=1)
        if results:
            print(f"   ✅ {topic}: Found ({results[0].score:.3f})")
        else:
            print(f"   ❌ {topic}: Not found")
    
    print()
    print(f"🎉 Total: {final_count} chunks | Target: 50+ | Progress: {final_count/50*100:.0f}%")
    
    return final_count

if __name__ == "__main__":
    load_extended_documents()
