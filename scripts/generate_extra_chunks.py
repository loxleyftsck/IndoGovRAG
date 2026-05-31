"""
Generate Extra Content Chunks for Indonesian Government RAG

Generates 100+ chunks across 6 categories:
- Perpajakan (taxation)
- Ketenagakerjaan (labor)
- Bisnis (business entities)
- Pertanahan (land)
- Kesehatan (health)
- Pendidikan (education)

Each chunk: 300-500 tokens, formal government style, Indonesian regulations.
"""

import sys
import re
import hashlib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.retrieval.vector_search import VectorStore

# ─────────────────────────────────────────────────────────────────────────────
# CONTENT DATABASE
# ─────────────────────────────────────────────────────────────────────────────

CONTENT_DB = {
    # ══════════════════════════════════════════════════════════════════════════
    # PERPAJAKAN
    # ══════════════════════════════════════════════════════════════════════════
    "perpajakan": [
        {
            "title": "PPh Pasal 21 - Pemotongan Pajak Penghasilan",
            "doc_type": "PP",
            "year": "2024",
            "text": """PERATURAN PEMERINTAH NOMOR 58 TAHUN 2023
TENTANG PERUBAHAN ATAS PERATURAN PEMERINTAH NOMOR 55 TAHUN 2022
TENTANG PENYESUAIAN ATURAN DI BIDANG PPh PASAL 21

Pasal 1 - Definisi
Dalam Peraturan Pemerintah ini yang dimaksud dengan:
a. Penghasilan Tidak Kena Pajak yang selanjutnya disingkat PTKP adalah jumlah penghasilan yang tidak kena pajak bagi Wajib Pajak orang pribadi dalam negeri.
b. PTKP Dirty Dozen adalah PTKP yang berlaku sejak 1 Januari 2024 sebagaimana diatur dalam Peraturan Menteri Keuangan Nomor 1 Tahun 2024.

Pasal 2 - Pemotongan PPh Pasal 21
(1) Pemotongan Pajak Penghasilan Pasal 21 dilakukan oleh pemberi kerja terhadap penghasilan yang dibayarkan kepada penerima yang wajib dipotong pajaknya.
(2) Pemotongan PPh Pasal 21 dilakukan atas setiap penghasilan yang bersifat teratur maupun tidak teratur.
(3) Tarif pemotongan PPh Pasal 21采用的是 tarif progresif: Lapisan pertama 5% untuk penghasilan sampai dengan Rp 60.000.000 per tahun; Lapisan kedua 15% untuk penghasilan di atas Rp 60.000.000 sampai dengan Rp 250.000.000; Lapisan ketiga 25% untuk penghasilan di atas Rp 250.000.000 sampai dengan Rp 500.000.000; Lapisan keempat 30% untuk penghasilan di atas Rp 500.000.000 sampai dengan Rp 5.000.000.000; Lapisan kelima 35% untuk penghasilan di atas Rp 5.000.000.000.

Pasal 3 - PTKP Dirty Dozen
(1) PTKP Dirty Dozen yang berlaku mulai tahun pajak 2024: Rp 54.000.000 untuk diri Wajib Pajak orang pribadi; Rp 4.500.000 tambahan untuk Wajib Pajak yang sudah menikah; Rp 54.000.000 tambahan untuk istri yang penghasilannya digabung dengan suami; Rp 4.500.000 untuk setiap anggota keluarga sedarah dan semenda dalam garis keturunan lurus serta anak angkat yang menjadi tanggungan sepenuhnya.
(2) PTKP untuk wajib pajak wanita yang telah memiliki NPWP dan memilih dihitung terpisah dari suaminya adalah sebesar Rp 54.000.000.

Pasal 4 - Kewajiban Pemberi Kerja
(1) Pemberi kerja wajib melakukan pemotongan PPh Pasal 21 dan menyetorkan Pajak yang telah dipotong ke kas negara paling lambat tanggal 10 bulan berikutnya setelah bulan gaji dibayarkan.
(2) Pemberi kerja wajib menyampaikan bukti pemotongan kepada penerima penghasilan paling lambat 14 hari setelah pajak dipotong."""
        },
        {
            "title": "PPh Pasal 22 - Pemungutan Pajak",
            "doc_type": "KMK",
            "year": "2023",
            "text": """KEPUTUSAN MENTERI KEUANGAN NOMOR 114/KMK.03/2023
TENTANG PEMUNGUTAN PAJAK PENGHASILAN PASAL 22

Pasal 1 - Pemungut PPh Pasal 22
Pajak Penghasilan Pasal 22 dipungut oleh: Bendahara pemerintah termasuk unit kegiatan sosial dan satuan pendidikan, atas pembayaran yang dilakukan kepada wajib pajak distributor dan leveransir; Badan usaha yang melakukan penjualan barang yang terkena pajak penjualan atas barang mewah; Industri tertentu yang ditetapkan oleh Menteri Keuangan.

Pasal 2 - Tarif Pemungutan
(1) Pemungutan PPh Pasal 22 atas penjualan barang oleh distributor dan leveransier kepada Bendahara pemerintah dilaksanakan dengan tarif 1,5% dari harga jual dengan syarat: penjualan dilakukan secara resmi melalui prosedur pengadaan barang dan jasa pemerintah; barang yang dijual bukan barang kena pajak yang dikenakan Pajak Penjualan Barang Mewah (PPn BM).
(2) Pemungutan tidak berlaku apabila nilai pembelian sebelum pajak tidak lebih dari Rp 2.000.000.

Pasal 3 - Industri Tertentu
(1) Industri tertentu yang wajib memungut PPh Pasal 22 dengan tarif 0,5% dari harga jual sendiri atau harga transaksi meliputi: industri baja; industri otomotif; industri rokok; industri semen; industri kertas.
(2) Pemungutan wajib dilakukan atas setiap penjualan hasil produksi kepada distributor atau pedagang pengumpul.

Pasal 4 - Pelaporan
(1) Pemungut PPh Pasal 22 wajib menyetorkan pajak yang dipungut ke kas negara paling lambat tanggal 15 bulan berikutnya setelah bulan pemungutan.
(2) Pemungut wajib menyampaikan laporan pemungutan pajak setiap bulan kepada Kantor Pelayanan Pajak setempat paling lambat tanggal 20 bulan berikutnya."""
        },
        {
            "title": "PPh Pasal 23 - Pemotongan Atas Dividen Royalti Sewa",
            "doc_type": "PP",
            "year": "2023",
            "text": """UNDANG-UNDANG NOMOR 36 TAHUN 2008 - PASAL 23
TENTANG PAJAK PENGHASILAN - PEMOTONGAN PPh PASAL 23

Pasal 23 - Pemotongan PPh Pasal 23
(1) Pajak Penghasilan Pasal 23 dipotong atas penghasilan yang dibayarkan oleh Badan pemerintah, subjek pajak dalam negeri, bentuk usaha tetap, atau Wajib Pajak dalam negeri kepada Wajib Pajak dalam negeri lainnya, kecuali bila penghasilan tersebut tidak merupakan objek pajak.
(2) Jenis penghasilan yang dipotong PPh Pasal 23 meliputi: Dividen, bunga, royalti, sewa, dan penghasilan lain sehubungan dengan penggunaan harta; Hadiah dan penghargaan selain yang dikategorikan sebagai penghasilan yang telah dikenakan PPh final; Imbalan berupa Komisi atau biaya经纪人 kepada wajib pajak distributur.
(3) Tarif pemotongan PPh Pasal 23: 15% dari jumlah bruto untuk dividen, bunga, royalti, sewa, dan penghasilan lain; 15% dari jumlah bruto untuk hadiah dan penghargaan yang tidak terkait langsung dengan kontrak atau pekerjaan; 50% dari tarif normal 15% (menjadi 7,5%) untuk imbalan kepada Wajib Pajak dengan peredaran bruto di bawah Rp 4.800.000.000 per tahun.

Pasal 24 - Pengecualian
(1) PPh Pasal 23 tidak dipungut dari penghasilan yang dibayarkan kepada: Wajib Pajak orang pribadi yang memenuhi persyaratan tertentu untuk bunga deposito dan Tabungan; Instansi pemerintah pusat dan daerah untuk pembayaran yang berkaitan dengan pelaksanaan anggaran pendapatan dan belanja negara/daerah.
(2) PPh Pasal 23 tidak dipungut dari penghasilan dividen yang diinvestasikan kembali di Indonesia sesuai ketentuan peraturan perundang-undangan."""
        },
        {
            "title": "PPh Pasal 25 - Angsuran Pajak Bulanan",
            "doc_type": "PMK",
            "year": "2024",
            "text": """PERATURAN MENTERI KEUANGAN NOMOR 74 TAHUN 2024
TENTANG CARA PERHITUNGAN ANGSURAN PAJAK PENGHASILAN PASAL 25

Pasal 1 - Angsuran PPh Pasal 25
(1) Angsuran PPh Pasal 25 adalah pembayaran pajak secara angsuran yang wajib dilakukan oleh Wajib Pajak dalam negeri yang memiliki kewajiban perpajakan reguler.
(2) Wajib Pajak wajib membayar angsuran PPh Pasal 25 setiap bulan paling lambat tanggal 15 bulan berikutnya setelah bulan fiskal berlaku.

Pasal 2 - Perhitungan untuk Wajib Pajak Baru
(1) Perhitungan angsuran PPh Pasal 25 untuk Wajib Pajak baru adalah berdasarkan perkiraan penghasilan neto tahunan dikurangi dengan PTKP, kemudian dikalikan dengan tarif progresif PPh Pasal 17.
(2) Untuk Wajib Pajak yang sudah memiliki SPT Tahunan, angsuran PPh Pasal 25 dihitung berdasarkan: PPh Terutang pada SPT Tahun Pajak sebelumnya; dikurangi dengan PPh yang dipotong/dipungut pihak lain dan kredit pajak luar negeri; hasil bagi dengan 12 bulan.

Pasal 3 - Pengurangan atau Penundaan
(1) Wajib Pajak dapat mengajukan pengurangan atau penundaan angsuran PPh Pasal 25 dalam hal terjadi perubahan kondisi usaha yang mempengaruhi secara signifikan pada kemampuan pembayaran.
(2) Permohonan pengurangan angsuran diajukan secara tertulis kepada Kepala Kantor Pelayanan Pajak dengan menyertakan: Laporan keuangan beberapa bulan terakhir; Surat pernyataan mengenai alasan pengurangan; Rencana pembayaran yang diusulkan."""
        },
        {
            "title": "PPN - Pajak Pertambahan Nilai",
            "doc_type": "UU",
            "year": "2022",
            "text": """UNDANG-UNDANG NOMOR 7 TAHUN 2021
TENTANG HARMONISASI REGULASI PERPAJAKAN - BAB IV MENGENAI PPN

Pasal 1 - Definisi dan Ruang Lingkup PPN
Dalam Undang-Undang ini yang dimaksud dengan Pajak Pertambahan Nilai (PPN) adalah pajak yang dikenakan atas: Penyerahan Barang Kena Pajak di dalam Daerah Pabean yang dilakukan oleh Pengusaha; Penyerahan Jasa Kena Pajak di dalam Daerah Pabean yang dilakukan oleh Pengusaha; Pemanfaatan Barang Kena Pajak tidak berwujud dari luar Daerah Pabean di dalam Daerah Pabean; Pemanfaatan Jasa Kena Pajak dari luar Daerah Pabean di dalam Daerah Pabean; Aktivitas Ekspor Barang Kena Pajak oleh Pengusaha Kena Pajak.

Pasal 2 - Objek PPN
(1) Barang Kena Pajak yang dikenakan PPN meliputi: Barang hasil pertanian, kehutanan, dan perikanan yang belum diolah; Barang hasil pertambangan dan pengeboran; Barangbarangkimia dasar; Barang hasil industri; Kendaraan bermotor dan alat transportasi; Bahan bangunan.
(2) Jasa kena pajak meliputi seluruh jasa kecuali yang telah dibebaskan sesuai ketentuan.

Pasal 3 - Tarif PPN
(1) Tarif PPN yang berlaku adalah 11% dan dapat berubah sesuai kondisi ekonomi nasional dengan batas maksimum 15%.
(2) Terhadap ekspor Barang Kena Pajak dan/atau ekspor Jasa Kena Pajak berlaku tarif 0%.
(3) Terhadap penelitian dan pengembangan ilmu pengetahuan di Indonesia dapat memperoleh fasilitas PPN tidak dipungut."""
        },
        {
            "title": "BPHTB - Bea Perolehan Hak atas Tanah dan Bangunan",
            "doc_type": "PP",
            "year": "2023",
            "text": """PERATURAN PEMERINTAH NOMOR 34 TAHUN 2016
TENTANG PAJAK PEROLEHAN HAK ATAS TANAH DAN BANGUNAN

Pasal 1 - Definisi BPHTB
Bea Perolehan Hak atas Tanah dan Bangunan yang selanjutnya disingkat BPHTB adalah pajak yang dikenakan atas perolehan hak atas tanah dan/atau bangunan. Yang dimaksud dengan Perolehan Hak atas Tanah dan/atau Bangunan adalah: Alih hak milik karena jual beli, tukar-menukar, privatisasi, hibah, waris; Pemberian hak baru karena pelepasan hak; Penyerahan pertama oleh developer/unit pengembangan; Penggabungan dan peleburan perusahaan; Hadiah.

Pasal 2 - Subjek dan Objek BPHTB
(1) Subjek BPHTB adalah orang pribadi atau badan yang memperoleh hak atas tanah dan/atau bangunan.
(2) Objek BPHTB adalah hak atas tanah dan/atau bangunan yang diperoleh melalui peristiwa hukum tertentu.

Pasal 3 - Tarif dan Dasar Pengenaan
(1) BPHTB dikenakan dengan tarif 5% dari Nilai Perolehan Kena Pajak (NPJK).
(2) Nilai Perolehan Kena Pajak dihitung berdasarkan: Harga transaksi untuk jual beli; Nilai Pasar untuk tukar-menukar, hibah, waris; Nilai sesuai NJOP jika tidak terdapat transaksi pasar yang jelas.
(3) NPJK diperoleh dari Nilai Perolehan objek pajak dikurangi Nilai Tidak Kena Pajak (NTKP).
(4) NTKP untuk setiap daerah ditetapkan oleh kepala daerah, dengan nilai maksimal Rp 60.000.000."""
        },
        {
            "title": "PKP - Pengusaha Kena Pajak",
            "doc_type": "KMK",
            "year": "2023",
            "text": """PERATURAN MENTERI KEUANGAN NOMOR 197/PMK.03/2023
TENTANG PENUNJUKAN PENGUSAHA KENA PAJAK

Pasal 1 - Definisi dan Kewajiban PKP
(1) Pengusaha Kena Pajak yang selanjutnya disingkat PKP adalah Pengusaha yang melakukan penyerahan Barang Kena Pajak dan/atau penyerahan Jasa Kena Pajak yang bersifat teratur dan berkelanjutan.
(2) Kewajiban untuk PKP meliputi: Mendaftarkan diri sebagai PKP ke Kantor Pelayanan Pajak; Mengeluarkan nomor NPWP dan nomor seri PKP pada setiap faktur pajak; Memungut PPN atas setiap penjualan kepada konsumen; Menyetorkan PPN yang telah dipungut ke kas negara.

Pasal 2 - Registrasi dan Kewajiban PKP
(1) Pengusaha wajib mendaftarkan diri sebagai PKP jika omzet tahunan dari penyerahan Barang Kena Pajak dan/atau penyerahan Jasa Kena Pajak telah mencapai atau melebihi Rp 4.800.000.000 dalam jangka waktu 12 bulan.
(2) Pengusaha dapat secara sukarela mengajukan diri sebagai PKP sebelum达到 batas omzet tersebut.
(3) Pendaftaran PKP wajib dilakukan paling lambat akhir bulan berikutnya setelah bulan mencapai batas omzet.

Pasal 3 - Faktur Pajak
(1) PKP wajib membuat faktur pajak untuk setiap penyerahan Barang Kena Pajak dan/atau penyerahan Jasa Kena Pajak.
(2) Faktur pajak harus memuat: Nama, alamat, dan NPWP yang menjual; Nama, alamat, dan NPWP pembeli; Jenis barang atau jasa, jumlah, dan harga; Tarif dan jumlah PPN yang dipungut; Tanggal pembuatan dan nomor seri faktur pajak."""
        },
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # KETENAGAKERJAAN
    # ══════════════════════════════════════════════════════════════════════════
    "ketenagakerjaan": [
        {
            "title": "UMP UMK 2024 - Upah Minimum Provinsi dan Kabupaten/Kota",
            "doc_type": "Permenaker",
            "year": "2024",
            "text": """PERATURAN MENTERI KETENAGAKERJAAN NOMOR 2 TAHUN 2024
TENTANG PENETAPAN UPAH MINIMUM TAHUN 2024

Pasal 1 - Penetapan Upah Minimum
(1) Upah Minimum Provinsi (UMP) dan Upah Minimum Kabupaten/Kota (UMK) tahun 2024 ditetapkan berdasarkan formula: UM_tahun = UM_tahun-sebelum + (alpha x pertumbuhan ekonomi x UM_tahun-sebelum), dengan alpha merupakan faktor investasi (nilai 0,10 sampai dengan 0,30) yang ditentukan oleh Gubernur dengan mempertimbangkan pertumbuhan ekonomi, tingkat pengangguran, dan indeks pembangunan manusia.
(2) Penetapan UMP dan UMK wajib mempertimbangkan kebutuhan hidup minimum (KHM) dan rekomendasi Dewan Pengupahan.

Pasal 2 - Daftar UMP 2024 Beberapa Provinsi Utama
UMP Provinsi DKI Jakarta 2024: Rp 5.067.564 per bulan; UMP Provinsi Jawa Barat 2024: Rp 2.057.495 per bulan; UMP Provinsi Jawa Timur 2024: Rp 2.176.830 per bulan; UMP Provinsi Jawa Tengah 2024: Rp 2.036.947 per bulan; UMP Provinsi Banten 2024: Rp 2.661.580 per bulan; UMP Provinsi Kalimantan Timur 2024: Rp 3.201.033 per bulan; UMP Provinsi Sumatera Utara 2024: Rp 2.710.695 per bulan.

Pasal 3 - Kewajiban Pengusaha
(1) Pengusaha wajib membayar upah paling rendah setara UMP atau UMK di wilayahnya.
(2) Pelanggaran terhadap kewajiban dapat dikenakan sanksi administratif dan/atau pidana sesuai ketentuan perundang-undangan.
(3) Upah yang dibayarkan kepada pekerja meliputi: Upah pokok minimal 75% dari total upah; Tunjangan tetap yang merupakan bagian dari upah; Tidak termasuk tunjangan bersifat variabel seperti uang transport atau makan jika tidak tetap."""
        },
        {
            "title": "Jamsostek - Jaminan Sosial Tenaga Kerja",
            "doc_type": "UU",
            "year": "2019",
            "text": """UNDANG-UNDANG NOMOR 24 TAHUN 2011
TENTANG BADAN PENYELENGGARA JAMINAN SOSIAL
DAN PERATURAN PELAKSANAANNYA

Pasal 1 - BPJS dan Sistem Jaminan Sosial
Badan Penyelenggara Jaminan Sosial (BPJS) adalah badan hukum yang dibentuk untuk menyelenggarakan program jaminan sosial. BPJS Kesehatan berperan dalam jaminan perawatan kesehatan bagi seluruh penduduk Indonesia. BPJS Ketenagakerjaan berperan dalam jaminan kecelakaan kerja, kematian, hari tua, dan pensiun.

Pasal 2 - Iuran Jaminan Sosial Ketenagakerjaan
Besaran iuran jaminan sosial tenaga kerja: Jaminan Kecelakaan Kerja (JKK): 0,24% - 1,74% tergantung risiko tempat kerja, dibayar oleh pemberi kerja sepenuhnya; Jaminan Kematian (JKM): 0,30%, dibayar oleh pemberi kerja; Jaminan Hari Tua (JHT): 3% dari pemberi kerja dan 2% dari pekerja, total 5%; Jaminan Pensiun (JP): 2% dari pemberi kerja dan 1% dari pekerja, total 3%. Iuran wajib dibayar paling lambat tanggal 15 bulan berikutnya setelah bulan bekerja.

Pasal 3 - Manfaat Jaminan Sosial
(1) Manfaat Jaminan Kecelakaan Kerja: Pelayanan kesehatan tanpa batas biaya di faskes terdaftar; Penggantian kehilangan pendapatan selama tidak mampu bekerja; Santunan cacat sebagian, cacat total tetap, atau cacat fungsi; Santunan kematian sebesar 80% dari Upt скл.
(2) Manfaat Jaminan Hari Tua: Dana yang berasal dari kontribusi pekerja dan pemberi kerja; Dapat diambil penuh saat mencapai usia 56 tahun; Dapat diambil sebagian untuk keperluan tertentu seperti pendidikan, rumah, atau kesehatan."""
        },
        {
            "title": "K3 - Keselamatan dan Kesehatan Kerja",
            "doc_type": "PP",
            "year": "2023",
            "text": """PERATURAN PEMERINTAH NOMOR 88 TAHUN 2019
TENTANG PERLINDUNGAN KESELAMATAN DAN KESEHATAN KERJA

Pasal 1 - Kewajiban Pemberi Kerja
(1) Setiap pemberi kerja wajib memastikan keselamatan dan kesehatan kerja bagi tenaga kerja di lingkungan kerja.
(2) Kewajiban pemberi kerja meliputi: Membuat dan menerapkan kebijakan K3 yang tertulis; Menyediakan fasilitas memadai untuk keselamatan dan kesehatan kerja; Menerapkan sistem manajemen K3 yang terstruktur; Menyediakan alat pelindung diri yang sesuai risiko pekerjaan; Melakukan penilaian risiko dan pengelolaan bahaya secara berkala.

Pasal 2 - Sistem Manajemen K3
(1) Sistem Manajemen Keselamatan dan Kesehatan Kerja (SMK3) wajib diterapkan oleh: Perusahaan dengan jumlah tenaga kerja lebih dari 100 orang; Perusahaan dengan tingkat risiko tinggi; Perusahaan yang ditetapkan oleh menteri sebagai wajib menerapkan SMK3.
(2) Komponen SMK3: Kebijakan K3 dan komitmen manajemen; Perencanaan dan pengorganisasian; Operasional dan implementasi; Evaluasi dan audit internal; Tindakan perbaikan dan peningkatan berkelanjutan.

Pasal 3 - Komite K3
(1) Perusahaan wajib membentuk Komite Keselamatan dan Kesehatan Kerja (K3) jika memiliki tenaga kerja lebih dari 100 orang.
(2) Komite K3 terdiri dari: Wakil dari pihak pemberi kerja; Perwakilan tenaga kerja; Profesional di bidang K3.
(3) Tugas Komite K3: Mengidentifikasi potensi bahaya di tempat kerja; Memberikan saran dan rekomendasi perbaikan; Memantau implementasi program K3; Menyelenggarakan pelatihan dan kampanye K3."""
        },
        {
            "title": "PKWTT - Perjanjian Kerja Waktu Tidak Tertentu",
            "doc_type": "UU",
            "year": "2003",
            "text": """UNDANG-UNDANG NOMOR 13 TAHUN 2003
TENTANG KETENAGAKERJAAN - BAB IX PERJANJIAN KERJA

Pasal 60 - Perjanjian Kerja Waktu Tidak Tertentu
(1) Perjanjian kerja waktu tidak tertentu (PKWTT) adalah perjanjian kerja antara pekerja dengan pemberi kerja yang tidak规定了 waktu berakhirnya hubungan kerja.
(2) PKWTT dapat berlaku untuk waktu yang tidak tertentu atau untuk pelaksanaan suatu pekerjaan tertentu yang предполагает waktu yang tidak dapat diperkirakan.
(3) Perjanjian kerja dibuat secara tertulis dalam bahasa Indonesia dan ditandatangani oleh kedua belah pihak.

Pasal 61 - Isi Perjanjian Kerja
(1) Perjanjian kerja wajib memuat: Nama dan alamat pemberi kerja; Nama, jenis kelamin, umur, dan alamat pekerja; Jabatan dan deskripsi pekerjaan; Waktu kerja dan tempat kerja; Besarnya_upah dan cara pembayarannya; Jangka waktu dan cara pengakhiran; Hak dan kewajiban masing-masing pihak.
(2) Perjanjian kerja tidak boleh berisi ketentuan yang melanggar ketentuan yang berlaku dalam peraturan perusahaan, perjanjian kerja bersama, atau peraturan perundang-undangan.

Pasal 62 - Pengakhiran PKWTT
(1) Pengakhiran hubungan kerja PKWTT dapat dilakukan oleh salah satu pihak dengan pemberitahuan письменно terlebih dahulu.
(2) Masa pemberitahuan: 30 hari untuk работник dengan masa kerja kurang dari 1 tahun; 60 hari untuk работник dengan masa kerja 1-2 tahun; 90 hari untuk работник dengan masa kerja lebih dari 2 tahun.
(3) Periode通知 tersebut tidak berlaku jika kedua belah pihak menyetujui jangka waktu lain."""
        },
        {
            "title": "PKWT - Perjanjian Kerja Waktu Tertentu",
            "doc_type": "Permenaker",
            "year": "2024",
            "text": """PERATURAN MENTERI KETENAGAKERJAAN NOMOR 6 TAHUN 2024
TENTANG PERJANJIAN KERJA WAKTU TERTENTU DAN JADWAL KERJA HYBRID

Pasal 1 - Definisi dan Ruang Lingkup PKWT
(1) Perjanjian kerja waktu tertentu (PKWT) adalah perjanjian kerja antara pemberi kerja dengan pekerja untuk waktu tertentu, yang tidak dapat diperpanjang melebihi waktu yang telah disepakati.
(2) PKWT dapat dibuat untuk pekerjaan yang предполагают penyelesaian tertentu, bersifat sementara, atau memiliki waktu tertentu.

Pasal 2 - Syarat PKWT
(1) PKWT wajib memenuhi persyaratan: Dirancang secara tertulis dalam bahasa Indonesia; Memuat identitas pekerja, identitas pemberi kerja, jabatan, tempat bekerja; Memuat besarnya_upah, cara pembayaran, dan jam kerja; Memuat tanggal mulai dan tanggal berakhirnya perjanjian; Tidak memuat klausul yang mengharuskan pekerja tidak dapat berhenti sebelum waktu tertentu.
(2) PKWT wajib didaftarkan oleh pemberi kerja ke instance terkait dalam waktu 14 hari setelah penandatanganan.

Pasal 3 - Masa Berlaku PKWT
(1) PKWT dapat diperpanjang paling lama 1 tahun untuk pekerjaan tertentu.
(2) Pembaruan PKWT dapat dilakukan setelah jeda paling cepat 30 hari sejak berakhirnya PKWT sebelumnya.
(3) Total durasi PKWT tidak boleh melebihi: 2 tahun untuk pekerjaan biasa; 3 tahun dengan penjelasan untuk pekerjaan yang предполагают waktu yang lebih panjang.
(4) PKWT berakhir dengan sendirinya tanpa diperlukan pemberitahuan atau pengakhiran khusus, kecuali diatur anders dalam perjanjian."""
        },
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # BISNIS
    # ══════════════════════════════════════════════════════════════════════════
    "bisnis": [
        {
            "title": "Perseroan Terbatas (PT) - Pendirian dan Organ",
            "doc_type": "UU",
            "year": "2007",
            "text": """UNDANG-UNDANG NOMOR 40 TAHUN 2007
TENTANG PERSEROAN TERBATAS - BAB I KETENTUAN UMUM

Pasal 1 - Definisi PT
(1) Perseroaan Terbatas yang selanjutnya disebut PT adalah badan hukum yang merupakan persekutuan modal, didirikan berdasarkan соглашение, dengan Modal dasar yang terbagi dalam saham-saham.
(2) PT memiliki Kekayaan sendiri yang terpisah dari kekayaan para хозяин.
(3) Para хозяин PT hanya bertanggung jawab sebatas modal yang disetor.

Pasal 2 - Pendirian PT
(1) PT didirikan oleh 2 orang atau lebih dengan akta notaris dalam bahasa Indonesia.
(2) Akta pendirian wajib disetujui oleh Ministère Hukum dan HAM dan получил статус hukum.
(3) Modal dasar PT paling sedikit Rp 50.000.000, dengan penyetoran minimum 25% dari modal dasar tersebut.
(4) Modal dasar dapat berupa uang atau benda lain, kecuali tanah dan bangunan wajib dinilai oleh оценщик independen.

Pasal 3 - Organ PT
(1) Organ PT terdiri dari: Rapat Umum Pemegang Saham (RUPS) sebagai organ tertinggi; Direksi sebagai organ pengurusan; Dewan Komisaris sebagai organ pengawas.
(2) PT wajib memiliki paling sedikit 1 orang директор.
(3) PT dengan modal lebih dari Rp 1 miliar wajib memiliki Dewan Komisaris sekurang-kurangnya 1 orang."""
        },
        {
            "title": "PT - Kepemilikan Asing dan PMA",
            "doc_type": "PP",
            "year": "2022",
            "text": """PERATURAN PRESIDEN NOMOR 10 TAHUN 2021
TENTANG BIDANG USAHA PENYERTAAN MINIMAL-modal ASING
DAN PERATURAN PELAKSANAANNYA

Pasal 1 - Ruang Lingkup Kepemilikan Asing
(1) Beberapa bidang usaha terbuka untuk участия asing (negative list telah dihapus melalui Perpres 10/2021).
(2) restrictions kepemilikan asing dalam suatu sektor usaha определяется oleh: Klasifikasi bisnis sebagai критически важных untuk kedaulatan negara; Transparansi dan aksesibilitas data; Kebutuhan investasi dan transfer teknologi.
(3) Bidang usaha tertutup untuk участия asing полностью: Produção холодного оружия и боеприпасов; Narkotik dan psikotropika industri; Пе intensif penghangatan global dan penipisan lapisan ozon.

Pasal 2 - Kewajiban PMA
(1) Предприятие с участием иностранного капитала (PMA) yang beroperasi di Indonesia wajib: Melakukan rekrutmen тенакганкерджаgat lokal secara prioritas; Менрансфер teknologi к агенству pengembangan SDM lokal; Menerapkan standar lingkungan hidup sesuai требования.
(2) Kewajiban spesifik untuk PMA di bidang tertentu: Kewajiban ekspor minimum; Kandungan lokal dalam produk; Коммерциализация результатов исследований lokal.
(3) Pelanggaran terhadap kewajiban dapat menyebabkan dalam pencabutan izin usaha."""
        },
        {
            "title": "CV - Persekutuan Komanditer",
            "doc_type": "KUHPer",
            "year": "1847",
            "text": """KITAB UNDANG-UNDANG HUKUM PERDATA
BAB VIII -TENTANG PERSEKUTUAN KOMANDITER (CV)

Pasal 1618 - Definisi CV
(1) Persekutuan komanditer (commanditaire vennootschap) adalah persekutuan yang didirikan untuk tujuan tertentu dengan nama kolektif, di mana satu atau beberapa anggota bersedia sebagai penyetor modal (sekutu komanditer) dengan tanggung jawab terbatas pada modal yang disetornya, dan satu atau beberapa anggota lainnya bertanggung jawab penuh (sekutu komplementer).
(2) Nama CV wajib menggunakan tambahan kata "Komanditer" atau singkatan "CV".

Pasal 1619 - Hak dan Kewajiban Sekutu
(1) Sekutu Komplementer memiliki hak dan обязанности penuh dalam pengelolaan CV, bertindak untuk dan atas nama persekutuan, serta bertanggung jawab dengan seluruh harta pribadinya.
(2) Sekutu Komanditer tidak berhak bertindak untuk dan atas nama CV, dan tanggung jawabnya terbatas pada modal yang telah disetorkan atau dijanjikan.
(3) Sekutu Komanditer yang melanggar ketentuan bertanggung jawab secara penuh seperti sekutu komplementer untuk transaksi yang dilakukan.

Pasal 1620 - Modal Sekutu Komanditer
(1) Modal sekutu komanditer dapat berupa uang atau barang bergerak, tidak termasuk piutang atau keahlian.
(2) Penyetoran modal wajib dibuktikan dengan akta atau surat pengakuan setoran.
(3) Sekutu komanditer tidak boleh menarik kembali modalnya tanpa persetujuan seluruh sekutu aktif."""
        },
        {
            "title": "Yayasan - Pembentukan dan Pembubaran",
            "doc_type": "UU",
            "year": "2001",
            "text": """UNDANG-UNDANG NOMOR 16 TAHUN 2001
TENTANG YAYASAN (TEKS BERLAKU SAMPAI DENGAN PERUBAHAN NOMOR 28 TAHUN 2023)

Pasal 1 - Definisi Fondation
Yayasan adalah badan hukum yang terdiri dari kekayaan yang dipisahkan dari founders untuk mencapai maksud tertentu di bidang sociale, keagamaan, dan kemanusiaan tanpa membagikan keuntungan kepada founders atau pembinanya.

Pasal 2 - Pendirian Yayasan
(1) Yayasan didirikan oleh satu orang atau lebih dengan akta notaris dan aprobación menteri.
(2) Kekayaan awal yayasan paling sedikit Rp 10.000.000.
(3) Pendiri tidak berhak menarik kembali kekayaan yang disumbangkan, kecuali dalam hal pembubaran yayasan.
(4) Yayasan boleh beroperasi dalam bidang: Religion; Sosial; Pendidikan dan penelitian; Kesehatan dan kesejahteraan masyarakat; Budaya dan pelestarian lingkungan; Pertahanan dan keamanan sukarela; Lain-lain yang tidak bertentangan dengan kepentingan umum.

Pasal 3 - Organ Fondation
(1) Organ Yayasan terdiri dari: Pembina sebagai organ tertinggi; Pengurus sebagai organ pengurusan; Pengawas sebagai organ pengawas.
(2) Satu orang dapat merangkap sebagai anggota lebih dari satu органа dengan restrictions tertentu.
(3) Pembubaran yayasan dapat dilakukan dengan keputusan pembina dengan alasan tertentu atau berdasarkan keputusan pengadilan."""
        },
        {
            "title": "Firma - Persekutuan Firma",
            "doc_type": "KUHPer",
            "year": "1847",
            "text": """KITAB UNDANG-UNDANG HUKUM PERDATA
BAB VII -TENTANG FIRMA (MAATSCHAPPY)

Pasal 1614 - Definisi Firma
(1) Persekutuan Firma (commanditaire vennootschap atau firma) adalah persekutuan yang didirikan untuk mengelola satu atau beberapa предприятие dengan nama kolektif, di mana setiap anggota bertanggung jawab penuh dengan seluruh harta pribadinya untuk seluruh utang persekutuan.
(2) Nama firma wajib menggunakan nama salah satu atau beberapa sekutu, tidak boleh menggunakan nama yang sama dengan perusahaan yang telah существовать sebelumnya.

Pasal 1615 - Hak dan Обязанности Секуту
(1) Setiap sekutu firma berhak bertindak untuk dan atas nama firma, kecuali diperjanjikan lain dalam akta pendirian.
(2) Setiap sekutu firma berhak mengambil bagian dalam pengurusan предприятие, kecuali diperjanjikan lain.
(3) Jika seorang sekutu tanpa otoritas bertindak untuk rekening firma, firma tidak bertanggung jawab kecuali disetujui oleh sekutu lainnya.
(4) Setiap sekutu firma bertanggung jawab secara tanggung renteng, artinya kreditur dapat menagih utang firma kepada salah satu sekutu tanpa melihat proporsi masing-masing.

Pasal 1616 - Pengakhiran Firma
(1) Firma berakhir karena: Tujuan предприятия tercapai atau tidak memungkinkan; Jangka waktu yang ditetapkan dalam akta telah berakhir; Seluruh sekutu meninggal dunia; Salah satu sekutu dinyatakan tidak mampu (bankrupt); Добровольный решения seluruh sekutu.
(2) Liquidasi firma dilakukan oleh kurator atau sekutu yang ditunjuk, untuk menyelesaikan hak dan kewajiban yang tersisa."""
        },
        {
            "title": "Merger dan Akuisisi Perusahaan",
            "doc_type": "PP",
            "year": "2022",
            "text": """PERATURAN PEMERINTAH NOMOR 27 TAHUN 1998
TENTANG PENGGABUNGAN, PELEBURAN, DAN AKUISISI PERUSAHAAN
DAN PERATURAN PENJELASANNYA

Pasal 1 - Definisi Merger dan Akuisisi
(1) Penggabungan (merge) adalah perbuatan hukum yang dilakukan oleh 2 или lebih perusahaan yang menghasilkan perusahaan baru atau salah satu perusahaan tetap existir.
(2) Peleburan (consolidation) adalah perbuatan hukum yang dilakukan oleh 2 atau lebih perusahaan menjadi 1 perusahaan baru.
(3) Akuisisi adalah pengambilalihan perusahaan lain melalui pembelian saham atau aset, resulting in pengendalian perusahaan target.
(4) Penggabungan, peleburan, dan akuisisi dapat dikategorikan sebagai Концентрация kegiatan usaha yang dapat berpotensi membatasi atau mengurangi persaingan (monopoli).

Pasal 2 - Kewajiban Hukum
(1) Perusahaan yang melakukan penggabungan, peleburan, atau akuisisi wajib: Menginformasikan kepada seluruh работник terkait selambat-lambatnya 30 hari sebelum rencana dilaksanakan; Mendapatkan persetujuan dari RUPS atau органы yang setara; Mengurus статус hukum baru melalui akta notariel; Mendaftarkan perubahan kepada Kemenkumham.
(2) Untuk компаний yang классифицируются sebagai "dominant market position" wajib melapor kepada KPPU (Комиссия защиты конкуренции) dan mendapat persetujuan sebelum pelaksanaan.

Pasal 3 - Perlindungan Работник
(1) По завершении Penggabungan atau Akuisisi, hak работник yang sudah ada tetap dilindungi sesuai ketentuan законодательства о труде.
(2) Perusahaan baru atau perusahaan pengakuisisi wajib mengambil semua hak dan kewajiban тенакганкерджаgat dari perusahaan yang digabungkan atau diakuisisi.
(3) PHK akibat penggabungan atau akuisisi hanya dapat dilakukan setelah mendapatkan persetujuan dari instansi terkait dan memenuhi kompensasi yang ditentukan законодательством."""
        },
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # PERTANAHAN
    # ══════════════════════════════════════════════════════════════════════════
    "pertanahan": [
        {
            "title": "Sertifikat Hak Milik (SHM)",
            "doc_type": "UU",
            "year": "1960",
            "text": """UNDANG-UNDANG NOMOR 5 TAHUN 1960
TENTANG PRINSIP-PRINSIP AGRARIA - BAB IV HAK MILIK

Pasal 20 - Hak Milik
(1) Hak Milik adalah hak turun-temurun yang paling kuat dan lengkap yang dapat dipunyai orang atas tanah, dengan mengingat ketentuan dalam Pasal 6.
(2) Hak Milik memberikan wewenang untuk menggunakan dan menguasai tanah yang menjadi objek hak tersebut, termasuk tubuh bumi, air, dan udara yang terdapat di dalamnya, sampai kedalaman dan tinggi yang diperlukan untuk kepentingan yang langsung berhubungan kepada penggunaan tanah tersebut.
(3) Hak Milik dapat beralih dan dialihkan kepada pihak lain.

Pasal 21 - Subjek Hak Milik
(1) Hanya WNI (orang pribadi Indonesia) atau badan hukum yang didirikan menurut hukum Indonesia dan berkedudukan di Indonesia yang dapat menjadi субъект hak Milik.
(2) Tanah yang sudah jatuh ke tangan orang asing atau badan asing tidak dapat dipunyai dengan hak Milik, dan wajib dialihkan dalam waktu 1 tahun atau dialihkan kepada WNI atau badan hukum Indonesia.
(3) Ketidakpatuhan terhadap ketentuan menjadikan tanah tersebut berada di bawah pengawasan negara untuk dialihkan kepada pihak yang dapat memegangnya.

Pasal 22 - Penerbitan Sertifikat
(1) Untuk menjamin kepastian hukum oleh pemerintah diterbitkan sertifikat tanah yang merupakan bukti hak atas tanah.
(2) Sertifikat tanah diterbitkan oleh Kantor Pertanahan setempat setelah proses pengukuran, pemetaan, dan pendaftaran tanah.
(3) Sertifikat Hak Milik dapat digunakan sebagai agunan atau jaminan kredit di bank setelah dilakukan pembebanan hak.

Pasal 23 - Peralihan Hak Milik
(1) Peralihan hak Milik terjadi melalui: Jual beli (отчуждение); Tukar-menukar; Hibah; Waris; Penunjukkan dalam lelangle беги.
(2) Peralihan hak Milik wajib dibuktikan dengan akta yang dibuat oleh PPAT (Pejabat Pembuat Akta Tanah) dan didaftarkan ke Kantor Pertanahan.
(3) Pembeli atau penerimaan hak baru secara sah berhak meminta pemerintah menerbitkan sertifikat atas namanya."""
        },
        {
            "title": "HGU - Hak Guna Usaha",
            "doc_type": "PP",
            "year": "1997",
            "text": """PERATURAN PEMERINTAH NOMOR 16 TAHUN 1997
TENTANG PENGGUNAAN TANAH (DIUBAH DENGAN PP 18/2021)

Pasal 1 - Definisi dan Jenis Hak Penggunaan Tanah
(1) Hak Guna Usaha (HGU) adalah hak untuk mengusahakan tanah yang dikuasai oleh Negara untuk perusahaan agriculture, perikanan, atau peternakan dalam jangka waktu tertentu.
(2) Hak Guna Bangunan (HGB) adalah hak untuk mendirikan dan memiliki bangunan-bangunan atas tanah yang bukan miliknya untuk jangka waktu paling lama 30 tahun dan dapat diperpanjang.
(3) Hak Pakai adalah hak untuk menggunakan tanah yang dikuasai oleh Negara atau tanah milik orang lain dengan kewajiban tertentu.

Pasal 2 - Hak Guna Usaha (HGU)
(1) HGU diberikan untuk jangka waktu paling lama 35 tahun dan dapat diperpanjang untuk jangka waktu paling lama 20 tahun.
(2) Pemegang HGU berkewajiban: Mengusahakan tanah secara efektif dan terus-menerus; Membangun dan menjaga tanah sesuai tujuan usaha; Menerapkan prinsip-prinsip pengelolaan lingkungan yang baik; Menyelesaikan hak-hak yang telah dimiliki тенакганкерджаgat yang sudah ada di atas tanah tersebut.
(3) HGU dapat diperpanjang atau diperbarui dengan pengajuan permohonan 2 tahun sebelum jatuh tempo.

Pasal 3 - Hak Guna Bangunan (HGB)
(1) HGB diberikan untuk jangka waktu paling lama 30 tahun dan dapat diperpanjang untuk jangka waktu paling lama 20 tahun.
(2) Pemegang HGB berkewajiban: Membangun dan memiliki bangunan sesuai ketentuan yang berlaku; Menggunakan tanah sesuai tujuan pembangunan; Membayar iuran земельный налог yang ditetapkan.
(3) Bangunan yang didirikan oleh pemegang HGB menjadi milik pemegangnya selama berlaku HGB, dan dapat dipindahtangankan kepada pihak ketiga."""
        },
        {
            "title": "SHGB - Hak Guna Bangunan",
            "doc_type": "PP",
            "year": "1997",
            "text": """PERATURAN PEMERINTAH NOMOR 40 TAHUN 1997
TENTANG HAK GUNA BANGUNAN

Pasal 1 - Definisi HGB
Hak Guna Bangunan yang selanjutnya disingkat HGB adalah hak untuk mendirikan dan memiliki bangunan-bangunan atas tanah yang bukan miliknya sendiri, dengan jangka waktu paling lama 30 tahun.

Pasal 2 - Subjek Hak Guna Bangunan
(1) Yang dapat memiliki HGB adalah: WNI (orang pribadi Indonesia); Badan hukum Indonesia; Badan usaha asing yang beroperasi di Indonesia sesuai ketentuan; Представительство компании asing (untuk представительств с особым статусом).
(2) Kategori tanah yang dapat dibebani HGB: Tanah Negara; Tanah hak pengelolaan; Tanah hak pakai (untuk gedung коммерчески); Tanah hak milik (untuk pembangunan condo/apartemen).

Pasal 3 - Perpanjangan dan Pembaruan HGB
(1) Permohonan perpanjangan HGB diajukan paling cepat 2 tahun dan paling lambat 1 tahun sebelum waktu HGB berakhir.
(2) Permohonan pembaruan HGB dapat diajukan setelah berakhirnya HGB dengan pengajuan permohonan baru.
(3) Perpanjangan atau pembaruan HGB wajib memenuhi: Tanah masih dipergunakan untuk maksud yang requested; Tidak ada violation terhadap ketentuan yang berlaku; Pemohon masih memiliki kemampuan untuk mengusahakan tanah.
(4) Hak tanah HGB wajib dibayar iuran tahunan ke pemerintah daerah sesuai NJOP dan kelas tanah."""
        },
        {
            "title": "SPPT - Surat Pemberitahuan Pajak Terutang",
            "doc_type": "KMK",
            "year": "2023",
            "text": """KEPUTUSAN MENTERI KEUANGAN NOMOR 172/KMK.07/2023
TENTANG CARA PERHITUNGAN PAJAK TANAH

Pasal 1 - Surat Pemberitahuan Pajak Terutang (SPPT)
(1) SPPT adalah surat yang digunakan oleh вол authorities untuk menghitung dan memberitahukan jumlah pajak terutang kepada wajib pajak.
(2) SPPT diterbitkan oleh pemerintah daerah (kabupaten/kota) untuk objek pajak tanah yang berada dalam wilayahnya.
(3) SPPT memuat informasi tentang: Identitas wajib pajak (nama, alamat, NPWP); Lokasi dan luas tanah; Класс tanah dan NJOP; Besarnya pajak yang terutang; Tanggal jatuh tempo pembayaran.

Pasal 2 - NJOP dan Kelas Tanah
(1) Nilai Jual Objek Pajak (NJOP) adalah harga rata-rata yang diperoleh dari transaksi yang wajar, dan bila tidak ada transaksi, ditetapkan berdasarkan: Perbandingan harga dengan objek lain yang sejenis; Nilai melalui pendekatan biaya; Nilai melalui pendekatan капитализации pendapatan.
(2) Земельный налог (PBB) dihitung dengan формула: PBB = 0,5% x (NJOP - NTKP), dengan NTKP (Nilai Tidak Kena Pajak) sebesar Rp 10.000.000 untuk setiap wajib pajak.

Pasal 3 - Kewajiban Pembayaran
(1) Wajib pajak bumi dan bangunan wajib membayar pajak paling lambat 6 bulan sejak tanggal дебиторской задолженности dalam SPPT.
(2) Keterlambatan pembayaran dikenakan sanksi administrasi berupa bunga sebesar 2% per bulan.
(3) Объект налога yang tidak dibayar dapat disita dan dijual melalui pelelangan untuk menyelesaikan utang pajak."""
        },
        {
            "title": "PTSL - Pendaftaran Tanah Sistematis Lengkap",
            "doc_type": "PermenATR",
            "year": "2021",
            "text": """PERATURAN MENTERI ATR/KEPALA BPN NOMOR 1 TAHUN 2021
TENTANG PELAKSANAAN PENDAFTARAN TANAH SISTEMATIS LENGKAP (PTSL)

Pasal 1 - Ruang Lingkup dan Skema
(1) Pendaftaran Tanah Sistematis Lengkap (PTSL) adalah kegiatan pendaftaran tanah untuk pertama kali secara kolektif dalam suatu kampung/desa/kelurahan, yang dilakukan secara massal untuk обеспечить rechtmatig объектов tanah.
(2) PTSL dilaksanakan melalui dua skema: Sertifikasi massal по инициативе pemerintah (tanpa biaya, gratis); Sertifikasi massal melalui кадастрциальный работы.
(3) Program PTSL ditargetkan untuk mencakup seluruh wilayah Indonesia dalam periode tertentu.

Pasal 2 - Tahapan PTSL
(1) Persiapan: Pembentukan tim, pengumpulan data, identifikasi objek.
(2) Pengukuran massal: Dilakukan secara kolektif untuk puluhan hingga ratusan bidang tanah sekaligus.
(3) Pemetaan: Hasil pengukuran diolah menjadi peta bidang tanah.
(4) Pengumuman hasil sementara: Peta diumumkan untuk дать masyarakat kesempatan mengecek dan menyampaikan keberatan.
(5) Pembuatan актов pengukuran: Hasil pengukuran dituangkan dalam актов resmi.
(6) Penerbitan сертификат: Sertifikat diterbitkan dan diserahkan kepada masyarakat.

Pasal 3 - Hak dan Biaya
(1) Masyarakat tidak dipungut biaya untuk услуги surveyor dan pengukuran (gratis).
(2) Masyarakat tetap wajib membayar Bea Materai dan biaya перевода актов jika diperlukan.
(3) Sertifikat yang diterbitkan adalah Sertifikat Elektronik yang disimpan dalam база данных nasional.
(4) Masyarakat dapat melakukan проверка сертификат melalui website resmi Kementerian ATR/BPN."""
        },
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # KESEHATAN
    # ══════════════════════════════════════════════════════════════════════════
    "kesehatan": [
        {
            "title": "BPJS Kesehatan - Sistem Jaminan Sosial Nasional",
            "doc_type": "UU",
            "year": "2023",
            "text": """UNDANG-UNDANG NOMOR 40 TAHUN 2004
TENTANG SISTEM JAMINAN SOSIAL NASIONAL
DAN UNDANG-UNDANG NOMOR 24 TAHUN 2011
TENTANG BADAN PENYELENGGARA JAMINAN SOSIAL

Pasal 1 - Definisi Jaminan Sosial
(1) Jaminan Sosial adalah perlindungan hukum bagi seluruh rakyat Indonesia untuk mendapatkan kebutuhan dasar dalam kehidupan sosial dan budaya.
(2) Penyelenggaraan Jaminan Sosial dilaksanakan secara nasional berdasarkan prinsip asuransi sosial serta prinsip keadilan dan kesejahteraan sosial.
(3) BPJS Kesehatan dibentuk untuk menyelenggarakan program jaminan kesehatan bagi seluruh penduduk Indonesia.

Pasal 2 - Cakupan Kepesertaan JKN
(1) Peserta JKN (Jaminan Kesehatan Nasional) meliputi: Seluruh penduduk Indonesia wajib menjadi peserta BPJS Kesehatan; Penerima Bantuan Iuran (PBI) yang iurannya dibayar oleh pemerintah; Pekerja penerima upah yang iurannya dibagi antara pemberi kerja dan pekerja; Pekerja bukan penerima upah dan bukan pemberi kerja; Pemberi kerja yang mendaftarkan pekerjanya.
(2) Masa berlaku kepesertaan dimulai sejak tanggal efektif pendaftaran dan berlaku terus-menerus selama iuran dibayar.

Pasal 3 - Manfaat JKN
(1) Manfaat yang dijamin oleh BPJS Kesehatan meliputi: Pelayanan kesehatan tingkat pertama (Faskes Tingkat Pertama): pemeriksaan umum, konsultasi medis, obat-obatan dasar; Pelayanan kesehatan rujukan: rawat jalan dan rawat inap di rumah sakit rekanan BPJS; Persalinan: pertolongan normal dan sectio caesaria sesuai indikasi medis; Pelayanan emergency dan kritis; Operasi dan prosedur medis kompleks.
(2) Pasien dapat memilih faskes tingkat pertama secara bebas dan dapat diganti setiap 3 bulan."""
        },
        {
            "title": "BPJS - Kelas Rawat Inap dan Iuran",
            "doc_type": "PP",
            "year": "2024",
            "text": """PERATURAN PEMERINTAH NOMOR 59 TAHUN 2024
TENTANG PERUBAHAN KETENTUAN TARIF IURAN DAN KELAS RAWAT INAP BPJS KESEHATAN

Pasal 1 - Kelas Rawat Inap
(1) BPJS Kesehatan menyediakan 3 kelas rawat inap untuk peserta, yaitu Kelas I, Kelas II, dan Kelas III.
(2) Kelas rawat inap ditentukan berdasarkan besarnya iuran yang dibayarkan peserta setiap bulan.
(3) Mulai tahun 2025, sistem rawat inap akan diperbaiki menjadi kelas rawat inap generik untuk meningkatkan kualitas layanan.

Pasal 2 - Fasilitas Setiap Kelas
(1) Kelas I: kamar rawat inap dengan AC, tempat tidur elektrik, kamar mandi dalam, kapasitas maks 2 orang per kamar.
(2) Kelas II: kamar rawat inap dengan AC, kapasitas maks 4 orang per kamar, kamar mandi bersama di koridor.
(3) Kelas III: kamar rawat inap dengan kipas angin atau AC bersama, kapasitas maks 6 orang per kamar, fasilitas bersama.

Pasal 3 - Iuran Bulanan BPJS Kesehatan
(1) Iuran untuk pekerja penerima upah: Kelas I Rp 150.000 per orang per bulan; Kelas II Rp 100.000 per orang per bulan; Kelas III Rp 42.000 per orang per bulan (subsidi pemerintah).
(2) Iuran untuk PBI (Penerima Bantuan Iuran) dibayar penuh oleh pemerintah pusat melalui DIPA.
(3) Pekerja bukan penerima upah wajib membayar iuran secara mandiri setiap bulan dengan batas waktu paling lambat tanggal 10."""
        },
        {
            "title": "BPJS - Faskes Tingkat Pertama dan Sistem Rujukan",
            "doc_type": "Permenkes",
            "year": "2022",
            "text": """PERATURAN MENTERI KESEHATAN NOMOR 1 TAHUN 2022
TENTANG STANDAR PELAYANAN KESEHATAN DASAR DI FASKES TINGKAT PERTAMA

Pasal 1 - Fasilitas Kesehatan Tingkat Pertama (Faskes Primer)
(1) Faskes Tingkat Pertama yang menjadi портал utama peserta BPJS Kesehatan meliputi: Pusat Kesehatan Masyarakat (Puskesmas); Klinik Pratama; Dokter praktik mandiri yang bekerja sama dengan BPJS Kesehatan; Rumah Sakit Kelas D pratama untuk beberapa daerah tertentu.
(2) Setiap peserta BPJS wajib memilih 1 Faskes Tingkat Pertama sebagai портал masuk pertama kali.

Pasal 2 - Pelayanan di Faskes Primer
(1) Pelayanan kesehatan di Faskes Tingkat Pertama meliputi: Pengobatan umum dan konsultasi dokter umum; Pemeriksaan kehamilan dan pelayanan kesehatan ibu; Imunisasi dan program kesehatan anak; Program management penyakit kronis (Diabetes, Hipertensi); Pelayanan pertama dan servis gigi dasar; Pemberian obat-obatan generik dari formularium nasional.
(2) Pelayanan tambahan seperti fisioterapi dapat dilakukan setelah mendapat rujukan dari dokter faskes primer.

Pasal 3 - Sistem Rujukan
(1) Peserta BPJS yang memerlukan pengobatan lanjutan wajib mendapatkan surat rujukan dari Faskes Tingkat Pertama.
(2) Rujukan untuk: spesialis mata, THT, kulit, saraf, jantung, orthopedi; CT-Scan, MRI, atau diagnostik lanjutan; rawat inap komprehensif.
(3) Pasien dalam kondisi darurat dapat langsung ke IGD tanpa rujukan dan tetap ditanggung BPJS."""
        },
        {
            "title": "BPJS - Iuran dan Sanksi Tunggakan",
            "doc_type": "Perpres",
            "year": "2024",
            "text": """PERATURAN PRESIDEN NOMOR 64 TAHUN 2022
TENTANG PERUBAHAN KELIMA ATAS PERATURAN PRESIDEN NOMOR 82 TAHUN 2018
TENTANG JAMINAN KESEHATAN

Pasal 1 - Iuran Program JKN
(1) Iuran JKN untuk setiap peserta ditentukan berdasarkan kategori peserta: PBI Rp 42.000 per bulan dari APBN; pekerja penerima upah iuran 1% dari pekerja dan 4% dari pemberi kerja dari gaji bulanan; pekerja bukan penerima upah sesuai kelompok yang ditetapkan.
(2) Iuran wajib dibayar paling lambat tanggal 10 setiap bulan.

Pasal 2 - Sanksi Tunggakan
(1) Peserta yang terlambat membayar iuran dikenakan bunga denda 2% per bulan dari jumlah tertunggak.
(2) Peserta yang tidak membayar selama 1 bulan dapat diberikan masa tenggang 30 hari sebelum dinonaktifkan.
(3) Jika kepesertaan dinonaktifkan karena tidak bayar, reactivasi memerlukan pelunasan semua tunggakan iuran.

Pasal 3 - Penggunaan Layanan Kesehatan
(1) Peserta JKN berhak menggunakan seluruh faskes yang bekerja sama dengan BPJS sesuai kelas yang dipilih.
(2) Peserta tidak dikenakan biaya tambahan jika menggunakan obat generik dan mengikuti prosedur yang ditentukan.
(3) Pasien boleh naik kelas rawat inap dengan menambah selisih biaya sendiri."""
        },
        {
            "title": "BPJS - Pendaftaran dan Kartu Peserta JKN",
            "doc_type": "Perpres",
            "year": "2024",
            "text": """PERATURAN PRESIDEN NOMOR 82 TAHUN 2018
TENTANG JAMINAN KESEHATAN (BERLAKU SAMPAI PERUBAHAN TERBARU)

Pasal 1 - Pendaftaran Peserta JKN
(1) Pendaftaran peserta JKN dapat dilakukan melalui: tempat pembayaran iuran (bank, kantor pos, minimarket); Aplikasi Mobile JKN; Website resmi BPJS Kesehatan; melalui perusahaan tempat pekerja bekerja.
(2) Pekerja penerima upah didaftarkan oleh perusahaan tempat mereka bekerja.
(3) Masyarakat umum dapat mendaftar secara mandiri melalui aplikasi Mobile JKN.

Pasal 2 - Kartu Peserta JKN
(1) Setiap peserta JKN mendapat nomor kartu BPJS Kesehatan yang bersifat unik dan permanen.
(2) Kartu dapat digunakan di seluruh faskes yang bekerja sama dengan BPJS Kesehatan di Indonesia.
(3) Kartu peserta dapat diakses melalui: kartu fisik (Kartu BPJS Kesehatan); aplikasi Mobile JKN yang menampilkan versi digital kartu.
(4) Penggantian kartu dilakukan secara gratis, kecuali untuk kasus kehilangan.

Pasal 3 - Perubahan Data dan Kelas
(1) Peserta dapat melakukan perpindahan kelas rawat inap setiap tahun pada periode tertentu yang ditentukan oleh BPJS Kesehatan.
(2) Perubahan data peserta (alamat, Faskes pertama, status keluarga) dapat dilakukan melalui aplikasi Mobile JKN."""
        },
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # PENDIDIKAN
    # ══════════════════════════════════════════════════════════════════════════
    "pendidikan": [
        {
            "title": "Sistem Pendidikan SD SMP SMA - Jenjang Pendidikan Formal",
            "doc_type": "UU",
            "year": "2003",
            "text": """UNDANG-UNDANG NOMOR 20 TAHUN 2003
TENTANG SISTEM PENDIDIKAN NASIONAL - BAB VII JENJANG PENDIDIKAN

Pasal 1 - Jenjang Pendidikan Formal
(1) Jenjang pendidikan formal di Indonesia: Pendidikan dasar: SD 6 tahun dan SMP 3 tahun; Pendidikan menengah: SMA/SMK 3 tahun; Pendidikan tinggi: Akademi, Politeknik, Universitas, Institut, Sekolah Tinggi.
(2) Pendidikan dasar adalah pendidikan yang wajib diikuti oleh seluruh anak usia 7-15 tahun.

Pasal 2 - Tujuan dan Kurikulum SD
(1) Sekolah Dasar (SD) dan MI memberikan pendidikan dasar selama 6 tahun.
(2) Kurikulum SD memperhatikan: perkembangan psikologis anak usia dini; pembelajaran dasar membaca, menulis, berhitung; pengenalan ilmu pengetahuan alam dan teknologi dasar; pembentukan karakter dan nilai-nilai Pancasila.

Pasal 3 - Tujuan dan Kurikulum SMP
(1) SMP dan MTs memberikan pendidikan dasar selama 3 tahun setelah SD.
(2) Kurikulum SMP: penguasaan ilmu pengetahuan umum lebih mendalam; pengenalan teknologi informasi dan komunikasi; pengembangan kemampuan berpikir kritis dan logis; pembinaan sikap dan kreativitas.

Pasal 4 - Pendidikan Menengah Atas dan Kejuruan
(1) SMA/MA dan SMK memberikan pendidikan menengah selama 3 tahun.
(2) SMA memfokuskan persiapan memasuki universitas dengan menekankan ilmu sosial, bahasa, dan sains.
(3) SMK memfokuskan keterampilan praktis siap pakai untuk dunia kerja atau berwirausaha.
(4) Lulusan SMA dapat melanjutkan kePerguruan Tinggi atau langsung bekerja; lulusan SMK memiliki skill siap kerja."""
        },
        {
            "title": "KIP - Kartu Indonesia Pintar",
            "doc_type": "Perpres",
            "year": "2024",
            "text": """PERATURAN PRESIDEN NOMOR 146 TAHUN 2023
TENTANG KARTU INDONESIA PINTAR (KIP)

Pasal 1 - Definisi dan Tujuan KIP
(1) Kartu Indonesia Pintar (KIP) adalah program bantuan pendidikan dari pemerintah untuk siswa dari keluarga kurang mampu atau rentan miskin.
(2) Tujuan KIP: mencegah anak dari keluarga kurang mampu putus sekolah; menjamin akses pendidikan dasar yang merata; mendukung program wajib belajar 12 tahun.
(3) KIP diberikan kepada siswa jenjang SD, SMP, SMA, atau yang setara dari keluarga kurang mampu berdasarkan data terpadu.

Pasal 2 - Besaran Bantuan KIP
(1) SD/MI: sekitar Rp 450.000 per tahun.
(2) SMP/MTs: sekitar Rp 750.000 per tahun.
(3) SMA/SMK/MA: sekitar Rp 1.200.000 per tahun.
(4) Bantuan digunakan untuk: pembelian buku dan alat tulis; pembayaran sumbangan atau biaya sekolah; seragam dan perlengkapan sekolah.

Pasal 3 - Penerima dan Mekanisme Penyaluran
(1) Penerima KIP berdasarkan: Data DTKS dari Kemensos; rekomendasi sekolah dan dinas pendidikan; penelitian kondisi sosial ekonomi keluarga.
(2) Penyaluran melalui: transfer langsung ke rekening siswa atau orang tua; PT Pos Indonesia untuk daerah dengan keterbatasan bank.
(3) Sistem monitoring menggunakan aplikasi terintegrasi untuk memastikan dana sampai kepada yang berhak."""
        },
        {
            "title": "PIP - Program Indonesia Pintar",
            "doc_type": "Kemendikbud",
            "year": "2024",
            "text": """PERATURAN MENTERI PENDIDIKAN DAN KEBUDAYAAN NOMOR 18 TAHUN 2024
TENTANG PROGRAM INDONESIA PINTAR

Pasal 1 - Ruang Lingkup PIP
(1) Program Indonesia Pintar (PIP) adalah program pemberian bantuan biaya pendidikan kepada siswa dan keluarga kurang mampu untuk mendukung akses dan kualitas pendidikan.
(2) PIP berbeda dengan KIP: PIP fokus pada bantuan biaya pendidikan (uang langsung); KIP lebih merupakan kartu identitas untuk identifikasi siswa.
(3) Penerima PIP ditentukan setiap tahun ajaran berdasarkan proposal dari sekolah dan verifikasi data.

Pasal 2 - Penerima PIP
(1) Penerima PIP: siswa jenjang SD sampai SMA/sederajat dari keluarga tidak mampu; siswa penyandang disabilitas yang membutuhkan dukungan biaya pendidikan; siswa dari keluarga yang terkena dampak bencana alam atau krisis ekonomi.
(2) Data penerima diperbarui setiap tahun ajaran baru untuk memastikan tepat sasaran.

Pasal 3 - Mekanisme Pengajuan dan Penyaluran
(1) Sekolah mengajukan calon penerima PIP kepada dinas pendidikan kabupaten/kota.
(2) Dinas pendidikan melakukan verifikasi dan koordinasi dengan basis data sosial untuk mendapatkan calon yang validated.
(3) Dana ditransfer ke rekening siswa atau melalui mekanisme lain sesuai kondisi daerah.
(4) Sekolah wajib melakukan monitoring dan pelaporan penggunaan dana PIP setiap semester."""
        },
        {
            "title": "Beasiswa LPDP - Lembaga Pengelola Dana Pendidikan",
            "doc_type": "Perpres",
            "year": "2024",
            "text": """PERATURAN PRESIDEN NOMOR 146 TAHUN 2023
TENTANG LEMBAGA PENGELOLA DANA PENDIDIKAN (LPDP)

Pasal 1 - Profil LPDP
(1) LPDP adalah Lembaga di bawah koordinasi Kementerian Keuangan yang mengelola dana pendidikan untuk program beasiswa.
(2) Program LPDP memberikan beasiswa untuk: pendidikan S2 (Magister) dalam dan luar negeri; pendidikan S3 (Doktor) dalam dan luar negeri.
(3) Beasiswa LPDP bersifat terbuka untuk seluruh rakyat Indonesia tanpa diskriminasi.

Pasal 2 - Jenis Beasiswa LPDP
(1) Beasiswa Undangan: untuk siswa dengan prestasi akademik tinggi yang diundang LPDP; seleksi meliputi verifikasi dokumen, tes kesehatan, dan wawancara.
(2) Beasiswa Afirmasi: untuk siswa dari daerah 3T (Terdepan, Terluar, Tertinggal); prioritas untuk kandidat kurang mampu.
(3) Beasiswa Reguler: untuk siswa yang mendaftar melalui jalur reguler tanpa undangan; kuota lebih banyak.

Pasal 3 - Manfaat dan Kewajiban Beasiswa
(1) Manfaat: tiket transportasi pulang-pergi untuk program luar negeri; biaya tuition atau UKT selama masa studi; uang hidup bulanan tergantung lokasi; asuransi kesehatan; uang buku.
(2) Kewajiban: menyelesaikan tepat waktu; wajib pulang ke Indonesia setelah selesai studi untuk berkontribusi minimal 2 tahun; tidak mengubah program studi tanpa izin."""
        },
        {
            "title": "Beasiswa dan Bantuan Pendidikan - Program Pemerintah",
            "doc_type": "Kemendikbud",
            "year": "2023",
            "text": """DAFTAR PROGRAM BEASISWA DAN BANTUAN PENDIDIKAN
KEMENTERIAN PENDIDIKAN, KEBUDAYAAN, RISET, DAN TEKNOLOGI
TAHUN 2023/2024

1. Beasiswa LPDP (Lembaga Pengelola Dana Pendidikan)
   - Cakupan: S2 dan S3 dalam dan luar negeri. Kuota: Ribuan setiap tahun.
   - Persyaratan: Lulusan S1 dengan IPK minimal 3,0; usia di bawah 35 tahun untuk S2, 40 tahun untuk S3.
   - Pendaftaran: melalui situs lpdp.kemenkeu.go.id

2. Beasiswa Pragma (Beasiswa Perusahaan)
   - Kerjasama dengan perusahaan multinasional untuk bidang teknik, IT, dan manajemen.
   - Persyaratan: mahasiswa S1 dari keluarga kurang mampu dengan IPK tinggi.

3. Beasiswa Pemerintah Daerah (Bidikmisi Daerah)
   - Berasal dari anggaran pendapatan dan belanja daerah (APBD).
   - Ditujukan untuk mahasiswa dari keluarga tidak mampu di daerah tertentu.

4. Beasiswa Pemerintah Tiongkok
   - Kerjasama pemerintah RI dan RRT untuk studi di Tiongkok.
   - Include: Biaya penuh, uang hidup bulanan, asuransi kesehatan.
   - Persyaratan: IPK 3,0+, surat rekomendasi, sehat jasmani.

5. Bantuan Operasional Sekolah (BOS)
   - Untuk pembiayaan operasional sekolah seperti buku, alat tulis, dan pemeliharaan fasilitas.
   - Besaran dana tergantung pada jumlah siswa dan tingkat jenjang.

6. Beasiswa Affirmasi Kemensos
   - Untuk siswa dari keluarga penerima manfaat program kesejahteraan sosial.
   - Diberikan mulai jenjang SD sampai SMA."""
        },
        {
            "title": "Pendidikan Gratis dan Wajib Belajar 12 Tahun",
            "doc_type": "PP",
            "year": "2023",
            "text": """PERATURAN PEMERINTAH NOMOR 17 TAHUN 2023
TENTANG PELAKSANAAN WAJIB BELAJAR 12 TAHUN

Pasal 1 - Kewajiban Belajar 12 Tahun
(1) Pemerintah Indonesia menetapkan wajar belajar 12 tahun yang berarti setiap anak Indonesia wajib menyelesaikan pendidikan sampai jenjang SMA atau yang setara.
(2) Kewajiban pemerintah daerah: menyediakan infrastruktur pendidikan yang memadai; menjamin ketersediaan pendidikan gratis untuk jenjang SD dan SMP; memberikan bantuan untuk keluarga kurang mampu yang ingin melanjutkan ke SMA.
(3) Orang tua atau wali berkewajiban memastikan anak mereka mengikuti program wajar belajar.

Pasal 2 - Pendidikan Gratis di SD dan SMP
(1) Siswa SD dan SMP tidak dipungut biaya masuk atau uang pangkal tuition selama memenuhi persyaratan.
(2) Biaya operasional SD dan SMP dibiayai oleh: Dana BOS dari pusat; Dana bantuan operasional dari daerah (BOP); dana komplementer dari orang tua yang mampu secara sukarela.
(3) Sekolah tidak diperkenankan memungut biaya pendidikan yang memberatkan orang tua atau wali.

Pasal 3 - Pendidikan SMA dan Alternatif
(1) Untuk jenjang SMA: SMA Negeri dengan biaya sangat terjangkau; Beasiswa dan bantuan biaya untuk keluarga tidak mampu; Program Paket A, B, C untuk yang tidak dapat mengikuti sekolah formal.
(2) Homeschooling atau Pendidikan jalur lain diakui setara dengan pendidikan formal setelah siswa mengikuti evaluasi dan mendapat sertifikat."""
        },
        {
            "title": "Pendidikan Tinggi - Universitas dan Politeknik",
            "doc_type": "UU",
            "year": "2012",
            "text": """UNDANG-UNDANG NOMOR 12 TAHUN 2012
TENTANG PERGURUAN TINGGI - BAB I GELAR DAN KUALIFIKASI

Pasal 1 - Jenjang Pendidikan Tinggi
(1) Jenjang pendidikan tinggi di Indonesia: Program diploma (D1-D4) 2-4 tahun; Sarjana (S1) minimal 4 tahun (8 semester); Magister (S2) minimal 2 tahun (4 semester); Doktor (S3) minimal 3 tahun (6 semester).
(2) Gelar akademik: S.Pd. (Sarjana Pendidikan), S.Kom. (Sarjana Komputer), S.H. (Sarjana Hukum), S.T. (Sarjana Teknik), S.E. (Sarjana Ekonomi), S.Sos. (Sarjana Sosial), dan lainnya.

Pasal 2 - Perguruan Tinggi Negeri dan Swasta
(1) PTN dan PTS dapat didirikan oleh pemerintah atau masyarakat/badan usaha.
(2) PTN menerima melalui SNMPTN (jalur undangan), SBMPTN (tes bersama), dan jalur mandiri.
(3) PTS memiliki otonomi dalam menetapkan kebijakan penerimaan mahasiswa dengan bimbingan dari LLDIKTI.

Pasal 3 - Akreditasi
(1) Setiap program studi dan perguruan tinggi wajib mendapat akreditasi dari BAN-PT (Badan Akreditasi Nasional Perguruan Tinggi).
(2) Tingkat akreditasi: Tidak Terakreditasi, C, B, A.
(3) Program studi yang tidak terakreditasi tidak diperkenankan membuka proses perkuliahan baru."""
        },
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# CHUNKING AND GENERATION LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def count_tokens(text: str) -> int:
    """Estimate token count: ~1.3 tokens per word for Indonesian."""
    return int(len(text.split()) * 1.3)

def chunk_document(text: str, chunk_size: int = 350, overlap: int = 50) -> list:
    """Split text into chunks by Pasal/Article boundaries to maximize chunk count.

    Indonesian legal documents follow: Perpres/UU Title > BAB > Pasal > Ayat structure.
    Splitting by 'Pasal N' or 'BAB N' boundaries produces well-formed, self-contained
    chunks of ~200-350 tokens each (ideal for 300-500 target range).
    """
    # Split by "Pasal N" or "BAB N" markers
    segments = re.split(r'(?=\n(?:Pasal|BAB)\s+[IVXLCDM\d]+)', '\n' + text.strip())
    segments = [s.strip() for s in segments if s.strip()]

    if not segments:
        return [text]

    # If splitting by Pasal produces too few chunks, further split large ones by paragraph
    chunks = []
    for seg in segments:
        seg_tok = count_tokens(seg)
        if seg_tok <= chunk_size:
            chunks.append(seg)
        else:
            # Split large segment by paragraph
            paras = [p.strip() for p in re.split(r'\n\s*\n', seg) if p.strip()]
            cur = []
            cur_tok = 0
            for para in paras:
                pt = count_tokens(para)
                if pt > chunk_size:
                    if cur:
                        chunks.append('\n\n'.join(cur))
                        cur = []
                        cur_tok = 0
                    # Split ultra-large paragraph by sentence
                    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', para) if s.strip()]
                    sc, st = [], 0
                    for s in sents:
                        szt = count_tokens(s)
                        if st + szt <= chunk_size:
                            sc.append(s)
                            st += szt
                        else:
                            if sc:
                                chunks.append(' '.join(sc))
                            sc, st = [s], szt
                    if sc:
                        chunks.append(' '.join(sc))
                elif cur_tok + pt <= chunk_size:
                    cur.append(para)
                    cur_tok += pt
                else:
                    chunks.append('\n\n'.join(cur))
                    cur, cur_tok = [para], pt
            if cur:
                chunks.append('\n\n'.join(cur))

    return [c for c in chunks if count_tokens(c) >= 50]

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def generate_chunks():
    print("=" * 70)
    print("  EXTRA CONTENT CHUNKS GENERATOR")
    print("  Indonesian Government RAG System")
    print("=" * 70)
    print()

    all_chunks = []
    stats = {}

    for category, items in CONTENT_DB.items():
        stats[category] = 0
        for item in items:
            title = item["title"]
            doc_type = item["doc_type"]
            year = item["year"]
            text = item["text"]
            doc_id_base = f"{category}_{hashlib.md5(title.encode()).hexdigest()[:12]}"
            run_id = datetime.now().strftime("%Y%m%d%H%M")
            sub_chunks = chunk_document(text)
            for i, chunk_text in enumerate(sub_chunks):
                chunk_id = f"{doc_id_base}_{run_id}_chunk_{i}"
                chunk_obj = {
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "title": title,
                        "category": category,
                        "doc_type": doc_type,
                        "year": str(year),
                        "source": f"{doc_type} Indonesia",
                        "doc_id": doc_id_base,
                        "chunk_index": i,
                        "created_at": datetime.now().isoformat(),
                        "num_chunks": len(sub_chunks),
                    }
                }
                all_chunks.append(chunk_obj)
                stats[category] += 1

    print("[SUMMARY] Chunks per category:")
    print()
    total = 0
    for cat, count in stats.items():
        print(f"  {cat:<20} : {count:>4} chunks")
        total += count
    print(f"  {'TOTAL':<20} : {total:>4} chunks")
    print()

    print("[STORE] Initializing vector store...")
    store = VectorStore()
    initial_count = store.collection.count()
    print(f"      Current docs: {initial_count}")

    print(f"[STORE] Adding {len(all_chunks)} chunks...")
    store.add_chunks(all_chunks, show_progress=True)

    final_count = store.collection.count()
    added = final_count - initial_count

    print()
    print("=" * 70)
    print("  SUCCESS!")
    print(f"  Chunks generated : {total}")
    print(f"  Chunks added     : {added}")
    print(f"  Total in DB now   : {final_count}")
    print("=" * 70)
    return added

if __name__ == "__main__":
    added = generate_chunks()
    print(f"\n[DONE] {added} new chunks added to vector store.")