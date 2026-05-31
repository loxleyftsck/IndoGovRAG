"""
Metadata about Indonesian Legal Philosophy Schools and Schools of Thought.
Maps major legal traditions, figures, and concepts to their Indonesian context.
"""

from typing import TypedDict


class LegalSchoolFigure(TypedDict):
    name: str
    role: str
    contribution: str
    key_work: str


class LegalSchool(TypedDict):
    name: str
    indonesian_name: str
    description: str
    origin: str
    key_principles: list[str]
    indonesian_applications: list[str]
    key_figures: list[LegalSchoolFigure]
    related_statutes: list[str]
    modern_relevance: str


LEGAL_SCHOOLS: dict[str, LegalSchool] = {
    "natural_law": {
        "name": "Natural Law Theory",
        "indonesian_name": "Teori Hukum Alam",
        "description": (
            "Natural law theory posits that certain rights and principles are inherent "
            "to human nature and can be discovered through reason, independent of "
            "positive law. In Indonesia, natural law is reflected in the constitutional "
            "recognition of human rights (HAM) that pre-exist the state."
        ),
        "origin": "Western philosophy (Aristotle, Aquinas, Locke, Rousseau)",
        "key_principles": [
            "Hak asasi manusia melekat pada setiap individu sejak lahir",
            "Hukum positif yang bertentangan dengan keadilan alam tidak memiliki validitas moral",
            "Nilai-nilai moral objektif dapat ditemukan melalui penalaran manusia",
        ],
        "indonesian_applications": [
            "Pengakuan HAM dalam UUD 1945 (Pasal 28A-28J)",
            "Konsep keadilan substantif melampaui prosedural",
            "Pembukaan UUD 1945 Alinea IV: 'Melindungi segenap bangsa Indonesia...'",
        ],
        "key_figures": [
            {
                "name": "Prof. Dr. Jimly Asshiddiqie",
                "role": "Guru Besar Hukum Tata Negara UI",
                "contribution": "Mengkontekstualisasikan natural law dalam kerangka hukum Indonesia modern",
                "key_work": "Penghubung Hukum Tata Negara dan Filsafat Hukum",
            },
            {
                "name": "Prof. Dr. Satjipto Rahardjo",
                "role": "Guru Besar Ilmu Hukum UNDIP",
                "contribution": "Mengembangkan teori hukum progresif yang melampaui positivisme hukum",
                "key_work": "Ilmu Hukum (multiple editions), Hukum Progresif",
            },
        ],
        "related_statutes": [
            "UUD 1945 Bab XA (HAM)",
            "UU No. 39 Tahun 1999 tentang HAM",
            "UU No. 40 Tahun 1999 tentang Anti Diskriminasi Rasial",
        ],
        "modern_relevance": (
            "Sangat relevan dalam judicial review di MK, perlindungan hak minoritas, "
            "dan evaluasi regulasi yang membatasi kebebasan sipil."
        ),
    },

    "positive_law": {
        "name": "Legal Positivism",
        "indonesian_name": "Positivisme Hukum / Hukum Positif",
        "description": (
            "Legal positivism holds that law is a set of rules created by competent "
            "authorities (legislature, executive), distinct from moral law. Law's "
            "validity comes from its source, not its content. Indonesia's entire "
            "legislative hierarchy is built on this paradigm."
        ),
        "origin": "John Austin, Hans Kelsen, H.L.A. Hart",
        "key_principles": [
            "Hukum adalah perintah dari penguasa yang berdaulat",
            "Validitas hukum ditentukan oleh sumbernya (authority), bukan isinya",
            "Hukum adalah fakta sosial, bukan penilaian moral",
            "Prinsip stare decisis (mengikuti preseden)",
        ],
        "indonesian_applications": [
            "Hierarki peraturan perundang-undangan (UU No. 12 Tahun 2011)",
            "Sistem pembentukan UU melalui DPR-MPR",
            "Teori分级(stufenbau) Hans Kelsen dalam sistem peradilan Indonesia",
            "Semua regulasi harus memiliki dasar hukum (wetmatigheid)",
        ],
        "key_figures": [
            {
                "name": "Hans Kelsen",
                "role": "Teoretikus Hukum Austria",
                "contribution": "Pure Theory of Law — memurnikan hukum dari ideologi politik",
                "key_work": "Reine Rechtslehre (Teori Hukum Murni), 1934",
            },
            {
                "name": "C.S.T. Kansil",
                "role": "Pakar Hukum Indonesia",
                "contribution": "Membakukan terminologi hukum Indonesia dan sistem perundang-undangan nasional",
                "key_work": "Pengantar Ilmu Hukum dan Perundang-undangan Indonesia",
            },
        ],
        "related_statutes": [
            "UU No. 12 Tahun 2011 tentang Pembentukan Peraturan Perundang-undangan",
            "UU No. 15 Tahun 2019 (pengecualian) tentang Pembentukan Peraturan Perundang-undangan",
            "Peraturan Presiden tentang JDIHN (Jaringan Dokumentasi dan Informasi Hukum Nasional)",
        ],
        "modern_relevance": (
            "Foundation seluruh sistem legislasi Indonesia. Namun, positivisme murni "
            "terkadang gagal menangkap keadilan substantif — inilah mengapa teori "
            "hukum progresif dan natural law tetap diperlukan sebagai koreksi."
        ),
    },

    "marhaen_legal": {
        "name": "Marhaen Legal Philosophy",
        "indonesian_name": "Filsafat Hukum Marhaen",
        "description": (
            "Marhaenisme adalah filsafat politik dan hukum yang dikembangkan oleh "
            "Soekarno, berlandaskan konsep 'marhaen' — petani kecil yang memiliki "
            "alat produksi sendiri. Dalam hukum, marhaenisme berarti hukum harus "
            "melindungi kaum lemah dan tertindas dari penindasan kaum资本(kapitalis)."
        ),
        "origin": "Pemikiran Ir. Soekarno, dipengaruhi Marxisme, nasionalisme, dan Islam",
        "key_principles": [
            "Hukum harus berkeadilan sosial — melindungi yang lemah dari yang kuat",
            "Bangsa Indonesia adalah nation yang beradab, bukan sekadar kumpulan individu",
            "Musyawarah untuk mufakat sebagai metode pengambilan keputusan hukum",
            "Anti kolonialisme dalam hukum: hukum yang dibuat penjajah tidak beriktikad baik",
            "Pancasila sebagai dasar filosofis tunggal Indonesia",
        ],
        "indonesian_applications": [
            "Dasar konstitusionalisme Indonesia dalam Pembukaan UUD 1945",
            "Perlindungan hukum terhadap работник (pekerja/buruh) dalam UU Ketenagakerjaan",
            "Konsepwzelfbeschikkingsrecht (hak untuk menentukan nasib sendiri) bangsa",
            "Agrarian reform sebagai instrumen keadilan sosial",
        ],
        "key_figures": [
            {
                "name": "Ir. Soekarno",
                "role": "Proklamator & Presiden Pertama RI",
                "contribution": "Merumuskan marhaenisme sebagai dasar filsafat politik Indonesia dan hubungan negara-hukum",
                "key_work": "Pidato-pidato politik, Dibawah Bendera Revolusi",
            },
            {
                "name": "Soepomo",
                "role": "Tokoh Perumus Pancasila",
                "contribution": "Merumuskan konsep negara integralistik yang mempengaruhi hukum tata negara Indonesia",
                "key_work": "Teori Negara Integralistik",
            },
        ],
        "related_statutes": [
            "UUD 1945 (Pembukaan & Batang Tubuh)",
            "UU No. 13 Tahun 2003 tentang Ketenagakerjaan",
            "UU No. 2 Tahun 1960 tentang Perjanjian Bagi Hasap (agrarian justice)",
            "UU No. 5 Tahun 1960 tentang Peraturan Dasar Pokok Agraria (UUPA)",
        ],
        "modern_relevance": (
            "Tetap relevan dalam kebijakan protektif bagi pekerja, perlindungan UMKM, "
            "dan kritik terhadap hukum yang semata-mata pro-pasar. Menjawab pertanyaan: "
            "'Untuk siapa hukum ini dibuat?'"
        ),
    },

    "hukum_adat": {
        "name": "Adat Law (Hukum Adat)",
        "indonesian_name": "Hukum Adat Indonesia",
        "description": (
            "Hukum adat adalah sistem hukum yang tumbuh dan berkembang dalam "
            "masyarakat Indonesia secara turun-temurun, tidak dibuat oleh negara. "
            "Hukum adat bersifat konkret, lokal, dan dinamis — berbeda dengan hukum "
            "positif yang abstrak dan universal. Indonesia secara resmi mengakui "
            "keberadaan hukum adat sepanjang tidak bertentangan dengan statutory law."
        ),
        "origin": "Territory of Indonesia — developed organically in villages and chiefdoms",
        "key_principles": [
            "Hukum adat tidak tertulis tetapi berlaku living law (hukum yang hidup)",
            "Pluralisme hukum: berbagai suku memiliki hukum adat masing-masing",
            "Tanah ulayat sebagai property (kekayaan) komunal yang tidak dapat dialienasi secara sepihak",
            "Musyawarah sebagai metode penyelesaian sengketa adat",
            "Konsep gotong royong dan tanggung jawab kolektif",
        ],
        "indonesian_applications": [
            "Pengakuan hak ulayat dalam UUPA 1960 (Pasal 3)",
            "Peradilan Adat dalam penyelesaian sengketa tanah di berbagai daerah",
            "Kompilasi Hukum Islam sebagai hukum adat umat Islam Indonesia",
            "Konsep 'rechtspluralisme' yang diakui secara yuridis",
            "Hukum waris adat yang berbeda-beda antar daerah",
        ],
        "key_figures": [
            {
                "name": "Prof. Van Vollenhoven",
                "role": "Sarjana Hukum Adat Belanda",
                "contribution": "Memetakan dan mempublikasikan hukum adat seluruh Nusantara",
                "key_work": "Adatrecht van Nederlandsch-Indië (8 volumes)",
            },
            {
                "name": "Prof. Dr. Soerojo Wignyodipuro",
                "role": "Guru Besar Hukum Adat",
                "contribution": "Mengkontekstualisasikan hukum adat dalam kerangka hukum nasional Indonesia",
                "key_work": "Hukum Adat (beberapa edisi)",
            },
            {
                "name": "Prof. Dr. Mochtar Kusumaatmadja",
                "role": "Guru Besar Hukum Internasional",
                "contribution": "Mengembangkan pendekatan rechtspluralisme dan hukum progresif",
                "key_work": "Filsafat Hukum Agraria, Konsep Otonomi Daerah",
            },
        ],
        "related_statutes": [
            "UU No. 5 Tahun 1960 tentang UUPA",
            "UU No. 32 Tahun 2004 tentang Pemerintahan Daerah",
            "UU No. 23 Tahun 2014 tentang Pemerintahan Daerah (revisi)",
            "Kompilasi Hukum Islam (KHI) Tahun 1991",
            "Peraturan daerah tentang pengakuan hak ulayat",
        ],
        "modern_relevance": (
            "Sangat relevan dalam penanganan sengketa tanah adat, konservasi lingkungan "
            "berbasis masyarakat (community-based conservation), dan pengakuan hak "
            "masyarakat hukum adat (MHA) dalam era desentralisasi."
        ),
    },

    "progressive_law": {
        "name": "Progressive Law Theory",
        "indonesian_name": "Teori Hukum Progresif",
        "description": (
            "Hukum Progresif adalah aliran yang dikembangkan oleh Prof. Satjipto Rahardjo "
            "dan dikembangkan lebih lanjut oleh Bernhard Windsche. Aliran ini menolak "
            "positivisme hukum yang kaku dan menegaskan bahwa hukum ada untuk manusia, "
            "bukan manusia untuk hukum. Hukum harus progressive (bergerak maju) menuju "
            "keadilan substantif."
        ),
        "origin": "Indonesia, dikembangkan oleh Prof. Satjipto Rahardjo (UNDIP)",
        "key_principles": [
            "Hukum tidak boleh menjadi 'mesin' yang mekanis — hukum harus berjiwa",
            "Kepastian hukum penting, tetapi bukan satu-satunya nilai hukum",
            "Hakim bukan sekadar aplicator (penerap) undang-undang, tetapi juga pembaru",
            "Hukum harus bersifat emansipatoris — membebaskan manusia dari penindasan",
            "Progressive law is law that liberates, not oppresses",
        ],
        "indonesian_applications": [
            "Putusan-putusan MK yang progressive (misalnya: dynamic pricing, judicial activism)",
            "Prinsip 'keadilan substantiate' melampaui 'kepastian formil'",
            "Perlindungan hukum terhadap korban pelanggaran HAM berat",
            "Hukum yang berpihak pada kelompok rentan dan minoritas",
            "Penegakan hukum lingkungan hidup yang progressive",
        ],
        "key_figures": [
            {
                "name": "Prof. Dr. Satjipto Rahardjo",
                "role": "Guru Besar Ilmu Hukum UNDIP",
                "contribution": "Pendiri teori hukum progresif di Indonesia",
                "key_work": "Ilmu Hukum (2000), Hukum Progresif (2006), Biarkan Hukum Mengalir (2007)",
            },
            {
                "name": "Bernhard Windsche",
                "role": "Pakar Hukum",
                "contribution": "Mengembangkan dan mempopulerkan teori hukum progresif di praktiknya",
                "key_work": "Berbagai tulisan tentang hukum progresif dan peradaban hukum Indonesia",
            },
        ],
        "related_statutes": [
            "UU No. 48 Tahun 2009 tentang Kekuasaan Kehakiman (pasal 4: jaminan profesionalisme hakim)",
            "UU No. 31 Tahun 1997 tentang Peradilan Milituer (dengan perspektif progressive)",
            "Putusan-putusan MK tentang Hak Asasi Manusia dan Keadilan Sosial",
        ],
        "modern_relevance": (
            "Sangat relevan dalam era di mana teknologi (AI, big data, cyber law) "
            "menciptakan situasi baru yang belum diatur oleh hukum positif. Hukum "
            "progresif memberikan kerangka untuk mengisi kekosongan hukum dengan "
            "nilai-nilai keadilan."
        ),
    },

    "rechtsstaat": {
        "name": "Rechtsstaat (Negara Hukum)",
        "indonesian_name": "Negara Hukum Indonesia (Rechtsstaat)",
        "description": (
            "Rechtsstaat adalah konsep negara hukum yang menekankan bahwa seluruh "
            "tindakan negara harus berdasarkan hukum. Indonesia secara eksplisit "
            "mengadopsi konsep ini sebagaimana tercantum dalam Pasal 1 ayat (3) UUD 1945: "
            "'Negara Indonesia adalah negara hukum.' Rechtsstaat berbeda dari machtstaat "
            "(negara kekuasaan) yang bertindak sewenang-wenang."
        ),
        "origin": "German-Dutch legal tradition (Paul Scholten, Logemann)",
        "key_principles": [
            "Supreme rule of law — hukum tertinggi di atas semua warga negara dan pemerintah",
            "Asas legalitas — setiap tindakan harus memiliki dasar hukum",
            "Pembagian kekuasaan (trias politica: legislatif, eksekutif, yudikatif)",
            "Jaminan hak asasi manusia",
            "Peradilan bebas dan tidak memihak (independen)",
            "Administrative law — pemerintahan terikat pada hukum administrasi",
        ],
        "indonesian_applications": [
            "Pasal 1 ayat (3) UUD 1945: 'Negara Indonesia adalah negara hukum'",
            "Pembagian kekuasaan vertikal: Pemerintah Pusat dan Daerah",
            "Pembagian kekuasaan horizontal: Executivo, Legislativo, Yudikatif",
            "Prinsip checks and balances antar lembaga negara",
            "Pengawasan administrative melalui PTUN (Peradilan Tata Negara Umum)",
        ],
        "key_figures": [
            {
                "name": "Prof. Dr. Bagir Manan",
                "role": "Guru Besar Hukum Tata Negara UNPAD",
                "contribution": "Merumuskan konsep rechtsstaat Indonesia secara komprehensif",
                "key_work": "Konsep Negara Hukum Indonesia, Hukum sebagai Sistem Kontrol Sosial",
            },
            {
                "name": "Jimly Asshiddiqie",
                "role": "Guru Besar Hukum Tata Negara UI",
                "contribution": "Membakukan konsepsi negara hukum Indonesia dalam praktik ketatanegaraan",
                "key_work": "Konstitusi dan Konstitusionalisme Indonesia, Pengantar Ilmu Hukum",
            },
        ],
        "related_statutes": [
            "UUD 1945 (seluruhnya)",
            "UU No. 48 Tahun 2009 tentang Kekuasaan Kehakiman",
            "UU No. 30 Tahun 2014 tentang Administrasi Pemerintahan",
            "UU No. 5 Tahun 1986 tentang PTUN (sebagaimana telah diubah)",
        ],
        "modern_relevance": (
            "Foundation seluruh sistem hukum Indonesia. Dengan makin kompleksnya "
            "tata kelola negara, prinsip rechtsstaat menjadi pengingat bahwa bahkan "
            "kekuasaan tertinggi pun terikat pada hukum."
        ),
    },
}


# ─── Legal Philosophy Glossary ────────────────────────────────────────────────

LEGAL_GLOSSARY: dict[str, str] = {
    "rechtsstaat": "Negara hukum — sistem pemerintahan di mana seluruh tindakan negara terikat pada hukum.",
    "machtstaat": "Negara kekuasaan — sistem pemerintahan yang bertindak berdasarkan kekuatan, bukan hukum.",
    "wetmatigheid": "Asas legalitas — setiap tindakan pemerintahan harus memiliki dasar hukum.",
    "rechtsvinding": "Pencarian hukum — proses menemukan hukum yang applicable untuk suatu kasus konkret.",
    "rechtsontwikkeling": "Perkembangan hukum — hukum berkembang seiring dengan perkembangan masyarakat.",
    "rechtspluralisme": "Pluralisme hukum — coexistence (koeksistensi) berbagai sistem hukum dalam satu wilayah.",
    "hukum progresif": "Aliran hukum yang menegaskan hukum harus progressive (bergerak maju) menuju keadilan substantif.",
    "musyawarah mufakat": "Prinsip pengambilan keputusan melalui dialogue dan consensus, bukan voting mekanis.",
    "tanah ulayat": "Tanah milik komunal masyarakat adat yang dikuasai secara kolektif.",
    "wetgevende": "Kekuasaan legislatif — kewenangan membentuk undang-undang.",
    "wetten": "Undang-undang (peraturan yang dibentuk oleh lembaga legislatif).",
    "straf": "Hukuman/sanksi dalam hukum pidana.",
    "burgerlijk recht": "Hukum perdata — mengatur hubungan hukum antara subjek-subyek hukum privat.",
    "strafrecht": "Hukum pidana — mengatur pelanggaran terhadap kepentingan umum dan memberikan sanksi.",
    "staatsrecht": "Hukum tata negara — hukum yang mengatur organisasi dan职能 (fungsi) negara.",
    "volkenrecht": "Hukum internasional — hukum yang mengatur hubungan antar negara.",
    "lex specialis": "Hukum khusus yang mendahului hukum umum dalam hal terdapat konflik norma.",
    "lex superior": "Hukum yang lebih tinggi dalam hierarki mengesampingkan hukum yang lebih rendah.",
    "ius constituens": "Hukum yang sedang dibentuk —UU dasar, konstitusi.",
    "ius constitutum": "Hukum yang telah berlaku — hukum positif yang sedang berlaku.",
}


def get_school(slug: str) -> LegalSchool | None:
    """Get a legal school by its key slug."""
    return LEGAL_SCHOOLS.get(slug)


def get_all_schools() -> list[str]:
    """Return all available legal school keys."""
    return list(LEGAL_SCHOOLS.keys())


def get_glossary_term(term: str) -> str | None:
    """Look up a legal term in the glossary."""
    return LEGAL_GLOSSARY.get(term.lower())
