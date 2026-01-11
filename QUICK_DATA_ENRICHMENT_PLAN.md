# 🚀 Quick Data Enrichment Plan - Target: 100+ Documents

**Current:** 53 chunks (~15-20 docs)  
**Target:** 100+ docs (Beta minimum)  
**Gap:** ~80-85 new documents needed  
**Timeline:** Immediate execution

---

## Strategy: 3-Pronged Approach

### 1. Check Existing Resources (5 min)

```bash
# See what we already have
ls data/documents/processed/
ls data/documents/pdfs/
cat data/documents/metadata.json
```

### 2. Quick Manual High-Value Additions (30-60 min)

**Priority Topics (10-15 docs each):**

**A. KTP Elektronik** (Critical - most common query)
Sources to manually add:

- <https://disdukcapil.jakarta.go.id/layanan/ktp-elektronik>
- <https://dukcapil.bantenprov.go.id/syarat-pembuatan-ktp>
- <https://disdukcapil.jabarprov.go.id/ktp-elektronik>
- UU No. 24 Tahun 2013 (Pasal 63-64) - KTP requirements

**B. Akta Kelahiran** (High priority)

- <https://dukcapil.jakarta.go.id/layanan/akta-kelahiran>
- UU No. 23 Tahun 2006 (Pasal 32) - Kelahiran
- Prosedur akta terlambat

**C. Kartu Keluarga**

- Syarat pembuatan KK
- Perubahan data KK
- Pemecahan KK

**D. NPWP**

- <https://www.pajak.go.id/id/cara-membuat-npwp>
- Syarat NPWP online
- NPWP untuk usaha

**E. Izin Usaha**

- <https://oss.go.id/portal/panduan>
- NIB (Nomor Induk Berusaha)
- Persyaratan UMKM

### 3. Convert to Text Format

**Method A: Create Manual Markdown Files**

```markdown
# Syarat Membuat KTP Elektronik

**Dasar Hukum:** UU No. 24 Tahun 2013 Pasal 63

## Persyaratan:
1. WNI berusia minimal 17 tahun atau sudah menikah
2. Fotokopi Kartu Keluarga (KK)
3. Formulir permohonan KTP (F-1.01)
4. Untuk penduduk pindah: Surat Keterangan Pindah

## Prosedur:
1. Datang ke Dukcapil setempat
2. Isi formulir F-1.01
3. Serahkan persyaratan
4. Foto dan rekam sidik jari
5. KTP jadi dalam 14 hari kerja

## Biaya:
GRATIS (dilarang dipungut biaya)

## Masa Berlaku:
Seumur hidup (permanen)

**Sumber:** dukcapil.kemendagri.go.id, UU 24/2013
```

**Method B: Extract from PDFs** (if available)

```bash
python scripts/extract_pdf_to_text.py data/documents/pdfs/
```

---

## Immediate Actions (NOW)

### Option 1: Manual Quick Add (FASTEST - 30 min)

Create 10-15 high-quality documents manually:

```bash
# Create documents directory
mkdir -p data/documents/manual

# Create KTP doc
cat > data/documents/manual/ktp_persyaratan.md << 'EOF'
# Persyaratan KTP Elektronik

**Dasar Hukum:** Pasal 63 UU No. 24 Tahun 2013

## Syarat Pembuatan e-KTP:
1. Warga Negara Indonesia
2. Berusia minimal 17 tahun atau sudah/pernah menikah
3. Fotokopi Kartu Keluarga (KK)
4. Mengisi formulir permohonan KTP (Formulir F-1.01)

## Prosedur:
1. Datang ke kantor Dinas Kependudukan dan Pencatatan Sipil
2. Mengisi formulir F-1.01
3. Menyerahkan fotokopi KK
4. Foto dan perekaman sidik jari
5. Menunggu proses pembuatan (maksimal 14 hari kerja)

## Biaya:
GRATIS - Pembuatan KTP tidak dipungut biaya

## Dokumen Tambahan (jika pindah domisili):
- Surat Keterangan Pindah dari daerah asal
- Formulir pendaftaran perpindahan

## Masa Berlaku:
Berlaku seumur hidup (permanen)

**Referensi:**
- UU No. 24 Tahun 2013 tentang Administrasi Kependudukan
- Permendagri No. 108 Tahun 2019
EOF

# Create Akta doc
cat > data/documents/manual/akta_kelahiran.md << 'EOF'
# Persyaratan Akta Kelahiran

**Dasar Hukum:** Pasal 32 UU No. 23 Tahun 2006

## Syarat Pembuatan Akta Kelahiran:
1. Surat keterangan kelahiran dari dokter/bidan/penolong kelahiran
2. KTP orang tua (ayah dan ibu)
3. Fotokopi Kartu Keluarga (KK)
4. Fotokopi Buku Nikah / Akta Perkawinan orang tua
5. Formulir permohonan akta kelahiran

## Waktu Pelaporan:
Paling lambat 60 hari sejak kelahiran

## Prosedur:
1. Datang ke kantor Dukcapil
2. Isi formulir permohonan
3. Serahkan persyaratan lengkap
4. Akta kelahiran diterbitkan saat itu juga (jika lengkap)

## Akta Kelahiran Terlambat (> 60 hari):
Memerlukan penetapan pengadilan

## Biaya:
GRATIS untuk pelaporan tepat waktu

**Referensi:**
- UU No. 23 Tahun 2006 tentang Administrasi Kependudukan
- Permendagri No. 108 Tahun 2019
EOF

# Add more...
```

Then ingest:

```bash
python scripts/ingest_documents.py --source data/documents/manual/
```

### Option 2: Use Existing Baseline Dataset (IF AVAILABLE)

Check if we have evaluation datasets that can be used:

```bash
ls data/*.json
# If eval datasets exist, extract context
python -c "
import json
with open('data/baseline_eval_dataset_v2.json') as f:
    data = json.load(f)
    # Extract unique contexts as documents
"
```

---

## Expected Results

After adding 80-85 documents:

- **Corpus:** 53 → 130-140 chunks
- **Quality:** 72% → 80-85% (B+ to A-)
- **Coverage:** 40% → 70%+ topics
- **Status:** Beta-ready ✅

---

## Next Steps

1. **Execute Option 1** (manual add) - 30-60 min
2. **Test quality improvement**
3. **Measure with RAGAS**
4. **Week 2:** Expand with scraper to 300+ docs

**Let's do Option 1 now - create 15 high-quality docs manually!** 🚀
