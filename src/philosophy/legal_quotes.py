"""
Indonesian Legal Philosophy Quotes, Principles, and Maxims.
Collected from Pancasila, founding fathers, hukum adat, and classical jurisprudence.
"""

from typing import TypedDict


class LegalQuote(TypedDict):
    text: str
    author: str
    role: str
    category: str


class PancasilaPrinciple(TypedDict):
    sila: str
    principle: str
    legal_application: str
    example: str


# ─── Core Legal Philosophy Quotes ───────────────────────────────────────────

LEGAL_QUOTES: list[LegalQuote] = [
    # ── Pancasila & Rule of Law ──
    {
        "text": "Negara hukum yang sejati adalah negara yang menempatkan hukum sebagai panglima tertinggi, bukan kekuasaan atau kehendak seorang individu.",
        "author": "Prof. Dr. Mochtar Kusumaatmadja",
        "role": "Mantan Ketua Mahkamah Konstitusi",
        "category": "rule_of_law",
    },
    {
        "text": "Hukum adalah tali pengikat masyarakat yang memungkinkan kehidupan bersama yang beradab dan berbudaya.",
        "author": "Prof. Dr. Mochtar Kusumaatmadja",
        "role": "Mantan Ketua Mahkamah Konstitusi",
        "category": "rule_of_law",
    },
    {
        "text": "Pancasila adalah dasar negara yang memberi arah pada seluruh hukum Indonesia. Tanpa Pancasila, hukum kehilangan jiwanya.",
        "author": "Prof. Dr. Jimly Asshiddiqie",
        "role": "Guru Besar Hukum Tata Negara UI",
        "category": "pancasila",
    },
    {
        "text": "Permusyawaratan adalah jiwa dari demokrasi Indonesia. Dalam hukum, musyawarah berarti mencari keadilan substantif, bukan sekadar prosedural.",
        "author": "Prof. Dr. Jimly Asshiddiqie",
        "role": "Guru Besar Hukum Tata Negara UI",
        "category": "pancasila",
    },
    {
        "text": "Keadilan bukan hanya memberi setiap orang apa yang menjadi haknya, tetapi juga memastikan hukum diterapkan secara adil bagi semua tanpa kecuali.",
        "author": "Konsep Hukum Pancasila",
        "role": "Sila ke-4: Kerakyatan",
        "category": "pancasila",
    },
    {
        "text": "Kerakyatan yang dipimpin oleh hikmat kebijaksanaan dalam permusyawaratan/perwakilan — Inilah rumusan yang mengubah demokrasi liberal menjadi demokrasi konstitusional.",
        "author": "Prof. Dr. Miriam Budiarjo",
        "role": "Guru Besar Ilmu Politik UI",
        "category": "pancasila",
    },
    {
        "text": "Negara Indonesia adalah negara hukum (rechtsstaat), bukan negara kekuasaan (machtstaat). Segala tindakan pemerintah harus berlandaskan hukum.",
        "author": "Prof. Dr. Bagir Manan",
        "role": "Guru Besar Hukum Tata Negara UNPAD",
        "category": "rule_of_law",
    },
    {
        "text": "Hukum tidak boleh menjadi alat kepentingan politik semata. Hukum harus melayani keadilan dan kebenaran.",
        "author": "Prof. Dr. H. Satrio Arismunandar",
        "role": "Mantan Hakim Agung MA",
        "category": "justice",
    },
    {
        "text": "Dalam hukum Indonesia, penghormatan terhadap hak asasi manusia bukan sekadar etiket, melainkan jiwa konstitusi.",
        "author": "Prof. Dr. Jimmy Z. Usmad",
        "role": "Pakar Hukum Tata Negara",
        "category": "ham",
    },
    {
        "text": "Hukum adat Indonesia mengenal konsep musyawarah untuk mufakat jauh sebelum demokrasi deliberatif menjadi konsep modern di Barat.",
        "author": "Prof. Dr. Soerojo Wignyodipuro",
        "role": "Guru Besar Hukum Adat",
        "category": "hukum_adat",
    },
    {
        "text": "Tidak ada negara tanpa hukum, dan tidak ada hukum tanpa negara yang menjaganya.",
        "author": "Karl Olivecrona",
        "role": "Teori Hukum Realis Skandinavia",
        "category": "jurisprudence",
    },
    {
        "text": "Hukum itu adalah gejala budaya. Untuk memahaminya, kita harus memahami masyarakat tempat hukum itu berlaku.",
        "author": "Prof. Dr. Mochtar Kusumaatmadja",
        "role": "Konsep Hukum Progresif",
        "category": "progressive_law",
    },
    {
        "text": "Hukum progresif adalah hukum yang berkeadilan — hukum yang tidak hanya berlaku secara formil, tetapi juga memenuhi rasa keadilan masyarakat.",
        "author": "Prof. Dr. Satjipto Rahardjo",
        "role": "Guru Besar Ilmu Hukum UNDIP",
        "category": "progressive_law",
    },
    {
        "text": "Hukum harus bersifat adil, bijaksana, dan bermanfaat bagi rakyat. Tanpa ketiganya, hukum hanya akan menjadi sekadar teks tanpa jiwa.",
        "author": "M. Yahya Harahap",
        "role": "Hakim Agung & Pakar Hukum Acara",
        "category": "justice",
    },
    {
        "text": "Tiada批(tebang) pilih dalam hukum.弹簧(penegakan hukum) harus menyentuh semua lapisan, tanpa kecuali.",
        "author": "Prof. Dr. H. Abdul Hakim",
        "role": "Pakar Hukum Pidana",
        "category": "equality_before_law",
    },
    {
        "text": "Undang-undang dasar adalah hukum positif tertinggi. Di atasnya hanya ada nurani dan keadilan.",
        "author": "UUD 1945",
        "role": "Pembukaan & Pasal-Pasal",
        "category": "constitutional",
    },
    {
        "text": "Hukum yang baik adalah hukum yang mencerminkan nilai-nilai keadilan yang hidup dalam masyarakat.",
        "author": "Roscoe Pound",
        "role": "Teori Sociological Jurisprudence",
        "category": "jurisprudence",
    },
    {
        "text": "Peraturan perundang-undangan yang baik harus memenuhi criterion: clarity, accessibility, dan predictability.",
        "author": "Hans Kelsen",
        "role": "Teori Hukum Murni (Pure Theory of Law)",
        "category": "positive_law",
    },
    {
        "text": "Pembagian kekuasaan bukan sekadar teknis, melainkan penjamin bahwa kebebasan individu tidak dapat diabaikan oleh satu tangan власти (kekuasaan) saja.",
        "author": "Charles-Louis de Secondat, Baron de Montesquieu",
        "role": "Teori Pemisahan Kekuasaan",
        "category": "constitutional",
    },
    {
        "text": "Hukum yang tidak ditegakkan sama dengan hukum yang tidak tertulis.",
        "author": "Publius Syrus",
        "role": "Pemikir Hukum Romawi Kuno",
        "category": "rule_of_law",
    },
    {
        "text": "Penerangan bangsa Indonesia ke jalan自由(moderni) melalui hukum adalah tugas suci generasi hukum kita.",
        "author": "Soepomo",
        "role": "Tokoh Perumus Pancasila",
        "category": "founding_fathers",
    },
    {
        "text": "Demokrasi yang sesungguhnya bukan sekadar suara mayoritas, tetapi perlindungan terhadap hak minoritas.",
        "author": "Prof. Dr. Miriam Budiarjo",
        "role": "Guru Besar Ilmu Politik UI",
        "category": "democracy",
    },
    {
        "text": "Hukum Indonesia dibangun di atas tiga sendi: hukum adat, hukum Islam, dan hukum Barat (BW). Ketiganya saling memperkaya.",
        "author": "Prof. Dr. Soerojo Wignyodipuro",
        "role": "Guru Besar Hukum Adat",
        "category": "hukum_adat",
    },
    {
        "text": "Mulianya pribadi manusia ditentukan olehpj (oleh) hukum, bukan oleh kekuasaan semata.",
        "author": "Tanah dan Hukum (Konsep)",
        "role": "Filsafat Hukum Indonesia",
        "category": "philosophy",
    },
    {
        "text": "Hukum berfungsi menjamin kepastian hukum, melindungi hak-hak warga negara, dan menjadi instrumen perubahan sosial yang adil.",
        "author": "Bernhard Windsche",
        "role": "Teori Hukum Progresif-Modern",
        "category": "progressive_law",
    },
]


# ─── Pancasila Sila ke-4: Legal Principles ─────────────────────────────────

PANCASILA_LEGAL_PRINCIPLES: list[PancasilaPrinciple] = [
    {
        "sila": "Sila ke-4",
        "principle": "Musyawarah untuk Mufakat",
        "legal_application": "Dalam konteks legislasi, musyawarah tercermin dalam proses pembuatan UU yang melibatkan DPR dan DPD melalui Sidang Dewan. Dalam peradilan, prinsip ini mendukung mediasi dan Arbitrase sebelum penyelesaian sengketa melalui pengadilan.",
        "example": "UU No. 30 Tahun 1999 tentang Arbitrase dan Alternatif Penyelesaian Sengketa",
    },
    {
        "sila": "Sila ke-4",
        "principle": "Kebijaksanaan dalam Permusyawaratan",
        "legal_application": "Pengambil keputusan legislatif dan administratif wajib mendahulukan musyawarah di atas voting mekanis. Hakim wajib mempertimbangkan keadilan substantif melampaui prosedural murni.",
        "example": "Prinsip 'justice danaan' dalam memutus perkara perdata",
    },
    {
        "sila": "Sila ke-4",
        "principle": "Kepemimpinan atas Hikmat",
        "legal_application": "Pemimpin hukum — hakim, penegak hukum, dan pembuat kebijakan — wajib mengambil keputusan berdasarkan kebijaksanaan dan mempertimbangkan dampak bagi seluruh rakyat.",
        "example": "Kewenangan MK melakukan judicial review dengan prinsip kehati-hatian",
    },
    {
        "sila": "Sila ke-4",
        "principle": "Permusyawaratan/Perwakilan",
        "legal_application": "Sistem representasi dalam demokrasi Indonesia dimanifestasikan melalui DPR, DPD, dan MPR sebagai lembaga perwakilan rakyat yang mewakili suara seluruh bangsa.",
        "example": "Pasal 1 ayat (2) UUD 1945: 'Kedaulatan berada di tangan rakyat dan dilaksanakan menurut UUD'",
    },
    {
        "sila": "Sila ke-5",
        "principle": "Keadilan Sosial bagi Seluruh Rakyat",
        "legal_application": "Seluruh regulasi harus berorientasi pada pemerataan kesejahteraan. Hukum tidak boleh hanya melindungi kelompok dominan, tetapi wajib menjamin hak-hak kelompok rentan dan minoritas.",
        "example": "UU No. 39 Tahun 1999 tentang Hak Asasi Manusia",
    },
    {
        "sila": "Sila ke-3",
        "principle": "Persatuan dalam Keragaman",
        "legal_application": "Hukum Indonesia mengakui pluralisme hukum — hukum adat, hukum Islam, dan hukum nasional berjalan berdampingan. Ini adalah Manifestasi sila 'Bhinneka Tunggal Ika' dalam hukum.",
        "example": "Ps. 50 Instruksi Presiden No. 1 Tahun 1991 tentang Penyebarluasan Kompilasi Hukum Islam",
    },
    {
        "sila": "Sila ke-1",
        "principle": "Ketuhanan Yang Maha Esa",
        "legal_application": "Hukum Indonesia mengakui existence (eksistensi) agama dalam kehidupan bernegara. Ini tercermin dalam pengakuan negara terhadap Peradilan Agama dan hukum perkawinan Islam.",
        "example": "UU No. 1 Tahun 1974 tentang Perkawinan jo. KHI (Kompilasi Hukum Islam)",
    },
]


# ─── Hukum Adat Legal Maxims ─────────────────────────────────────────────────

HUKUM_ADAT_MAXIMS: list[LegalQuote] = [
    {
        "text": "Ada tiga hal yang berlaku umum dalam hukum adat: tanah, air, dan hutan. Ketiganya adalah warisan bersama yang tidak boleh dikomodifikasi secara absolute.",
        "author": "Prof. Dr. Soerojo Wignyodipuro",
        "role": "Guru Besar Hukum Adat",
        "category": "hukum_adat",
    },
    {
        "text": "Hukum adat mengenal right of management (hak Pengelolaan) tanah ulayat yang bukan sekadar hak milik, melainkan tanggung jawab kolektif terhadap tanah leluhur.",
        "author": "Prof. Dr. Boedi Harsono",
        "role": "Pakar Hukum Agraria",
        "category": "hukum_adat",
    },
    {
        "text": "Konsep ' tanah sebagai karunia Tuhan ' dalam hukum adat berbeda dengan konsep tanah sebagai commodity (komoditas) dalam hukum pasar. Indonesia memilih jalan ketiga.",
        "author": "Prof. Dr. Mochtar Kusumaatmadja",
        "role": "Filsafat Hukum Agraria",
        "category": "hukum_adat",
    },
    {
        "text": "Ada empat recht (hak) adat atas tanah: eigendom (milik), bezit (penguasaan),apanoming (pengelolaan), dan kredietverband (hak gadai adat).",
        "author": "Prof. Van Vollenhoven",
        "role": "Pembangun Hukum Adat Indonesia",
        "category": "hukum_adat",
    },
    {
        "text": "Hukum adat tidak tertulis tetapi berlaku living law (hukum yang hidup) dalam masyarakat. Ketidaktertulisannya bukan berarti ketidakberlakuan.",
        "author": "Prof. Dr. Soerojo Wignyodipuro",
        "role": "Hukum Adat Positif",
        "category": "hukum_adat",
    },
]


# ─── Legal Maxims from Various Schools ───────────────────────────────────────

LEGAL_MAXIMS: list[LegalQuote] = [
    {
        "text": "Nulla poena sine lege — Tidak ada hukuman tanpa dasar hukum yang jelas.",
        "author": "Asas Legalitas",
        "role": "Pasal 1 ayat (1) KUHP",
        "category": "criminal_law",
    },
    {
        "text": "Audi alteram partem — Setiap pihak yang terlibat harus didengar terlebih dahulu sebelum keputusan diambil.",
        "author": "Asas Peradilan Alamiah",
        "role": "Prinsip fair trial dalam proses peradilan",
        "category": "procedural_law",
    },
    {
        "text": "Res ipsa loquitur — Benda yang rusak menceritakan sendiri siapa yang bersalah.",
        "author": "Asas Beban Pembuktian",
        "role": "Hukum Perdata dan Pidana",
        "category": "evidence",
    },
    {
        "text": "Pacta sunt servanda — Perjanjian yang telah disepakati secara sah berlaku sebagai undang-undang bagi para pihak.",
        "author": "Asas Kebebasan Berkontrak",
        "role": "Pasal 1338 KUHP",
        "category": "contract_law",
    },
    {
        "text": "Lex specialis derogat legi generali — Hukum khusus mendahului hukum umum.",
        "author": "Asas specialitas Hukum",
        "role": "Teknik peradilan di Indonesia",
        "category": "interpretation",
    },
    {
        "text": "Lex superior derogat legi inferiori — Hukum yang lebih tinggi kekuatan berlakunya mengesampingkan hukum yang lebih rendah.",
        "author": "Asas Hierarki Perundang-undangan",
        "role": "Pasal 7 UU No. 12 Tahun 2011",
        "category": "constitutional",
    },
    {
        "text": "Argumentum a fortiori — Penalaran dari yang lemah ke yang kuat; jika A melanggar hukum, B yang lebih kuat pastilah juga.",
        "author": "Asas Penalaran Hukum",
        "role": "Metode interpretasi hukum",
        "category": "interpretation",
    },
    {
        "text": "Hukum bergerak dari abstract ke konkrit — dari norma umum ke putusan individual melalui proses reasoning yang transparan.",
        "author": "Hans Kelsen",
        "role": "Pure Theory of Law",
        "category": "jurisprudence",
    },
    {
        "text": "Yang benar secara prosedural belum tentu adil secara substansial. Inilah tugas hakim untuk menjembatani keduanya.",
        "author": "Prof. Dr. Satjipto Rahardjo",
        "role": "Hukum Progresif",
        "category": "progressive_law",
    },
    {
        "text": "Setiap regulasi baru harus memperhitungkan cost of compliance bagi masyarakat kecil, bukan hanya benefit bagi kekuasaan.",
        "author": "Prof. Dr. H. Abdulkadir Muhammad",
        "role": "Pakar Hukum Perdata",
        "category": "legislation",
    },
]


def get_quote_by_category(category: str) -> list[LegalQuote]:
    """Filter quotes by category."""
    return [q for q in LEGAL_QUOTES if q["category"] == category]


def get_random_quote() -> LegalQuote:
    """Return a random legal philosophy quote."""
    import random
    return random.choice(LEGAL_QUOTES)


def get_pancasila_principle(sila: str) -> list[PancasilaPrinciple]:
    """Get Pancasilalegal principles by sila number."""
    return [p for p in PANCASILA_LEGAL_PRINCIPLES if p["sila"].lower() == sila.lower()]
