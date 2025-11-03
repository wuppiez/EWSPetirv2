# Early Warning System (EWS) Longsor v2.0
## Desa Petir, Dramaga, Kabupaten Bogor

### 🎯 Overview
Sistem Peringatan Dini Longsor berbasis data historis 20 tahun (2005-2025) dengan algoritma risk scoring multi-parameter dan notifikasi Telegram otomatis.

---

## 📊 Data Historis yang Digunakan

### Sumber Data
- **Dataset**: CHIRPS (Climate Hazards Group InfraRed Precipitation with Station)
- **Periode**: 2005-2025 (20.5 tahun)
- **Total Data Points**: 7,486 hari
- **Lokasi**: Desa Petir, Kecamatan Dramaga, Kabupaten Bogor
- **Koordinat**: 6.6128°S, 106.7258°E

### Statistik Kunci dari Data Historis

| Metrik | Nilai |
|--------|-------|
| Rata-rata curah hujan | 12.26 mm/hari |
| Median curah hujan | 8.03 mm/hari |
| Curah hujan maksimum | 172.14 mm/hari |
| Persentil 95% | 41.52 mm/hari |
| Persentil 99% | 71.26 mm/hari |
| Hari hujan ekstrem (>50mm) | 215 hari (2.87%) |

### Pola Musiman
**Bulan Paling Rawan:**
1. November: 20.43 mm/hari (avg)
2. April: 15.41 mm/hari (avg)
3. Februari: 14.96 mm/hari (avg)

**Bulan Paling Aman:**
- Juli: 5.92 mm/hari (avg)
- Agustus: 6.04 mm/hari (avg)
- Juni: 8.57 mm/hari (avg)

---

## 🧮 Sistem Risk Scoring

### Konsep Dasar
Sistem menggunakan **weighted multi-parameter scoring** untuk menghitung risiko longsor dengan mempertimbangkan 5 parameter utama:

1. **Curah Hujan Per Jam** (30%)
2. **Akumulasi 3 Hari** (25%)
3. **Akumulasi 7 Hari** (15%)
4. **Kelembaban Udara** (20%)
5. **Kecepatan Angin** (10%)

### Formula Perhitungan

```
Total Score = Σ (Parameter Score × Weight)
Adjusted Score = Total Score × Seasonal Multiplier
```

**Seasonal Multiplier:**
- Musim Hujan (Nov-Apr): 1.2×
- Musim Peralihan (Mei, Okt): 1.0×
- Musim Kering (Jun-Sep): 0.8×

### Threshold Berdasarkan Data Historis

#### 1. Curah Hujan Per Jam (mm/jam)
| Level | Range | Skor | Dasar |
|-------|-------|------|-------|
| 🟢 AMAN | 0-5 | 0-30 | Di bawah rata-rata normal |
| 🟡 WASPADA | 5-15 | 31-60 | Hujan sedang-lebat |
| 🔴 BAHAYA | >15 | 61-100 | Hujan sangat lebat |

#### 2. Akumulasi 3 Hari (mm)
| Level | Range | Skor | Dasar |
|-------|-------|------|-------|
| 🟢 AMAN | 0-60 | 0-25 | Normal |
| 🟡 WASPADA | 60-100 | 26-50 | Mendekati P95 |
| 🔴 BAHAYA | >100 | 51-100 | Di atas P95 (97.69 mm) |

#### 3. Akumulasi 7 Hari (mm)
| Level | Range | Skor | Dasar |
|-------|-------|------|-------|
| 🟢 AMAN | 0-150 | 0-25 | Normal |
| 🟡 WASPADA | 150-200 | 26-50 | Mendekati P95 |
| 🔴 BAHAYA | >200 | 51-100 | Di atas P95 (197.97 mm) |

#### 4. Kelembaban Udara (%)
| Level | Range | Skor | Dasar |
|-------|-------|------|-------|
| 🟢 AMAN | 0-70 | 0-20 | Normal |
| 🟡 WASPADA | 70-85 | 21-50 | Tinggi |
| 🔴 BAHAYA | >85 | 51-100 | Sangat tinggi |

#### 5. Kecepatan Angin (km/jam)
| Level | Range | Skor | Dasar |
|-------|-------|------|-------|
| 🟢 AMAN | 0-20 | 0-10 | Normal |
| 🟡 WASPADA | 20-40 | 11-30 | Kencang |
| 🔴 BAHAYA | >40 | 31-50 | Sangat kencang |

### Tingkat Risiko Final

| Tingkat | Score Range | Emoji | Deskripsi |
|---------|-------------|-------|-----------|
| **AMAN** | 0-40 | 🟢 | Kondisi normal, risiko rendah |
| **WASPADA** | 41-70 | 🟡 | Peningkatan risiko, perlu kewaspadaan |
| **BAHAYA** | 71-100 | 🔴 | Risiko tinggi, evakuasi segera |

---

## 🔧 Instalasi & Setup

### 1. Requirements
```bash
pip install streamlit requests pandas plotly python-telegram-bot openpyxl
```

### 2. File Structure
```
project/
├── bogor_v2_advanced.py          # Dashboard utama
├── risk_scoring.py               # Modul risk scoring
├── telegram_bot_listener.py      # Bot listener (24/7)
├── telegram_subscribers.json     # Data subscriber (auto-generated)
├── risk_scoring_config.json      # Konfigurasi scoring (auto-generated)
└── README.md                      # Dokumentasi ini
```

### 3. Konfigurasi Telegram Bot

#### a. Dapatkan Bot Token
1. Chat dengan [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim `/newbot`
3. Ikuti instruksi untuk membuat bot baru
4. Copy **token** yang diberikan

#### b. Update Token di File
Edit file `bogor_v2_advanced.py` dan `telegram_bot_listener.py`:
```python
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
```

### 4. Menjalankan Sistem

#### a. Jalankan Bot Listener (Background Service)
```bash
# Terminal 1 - Bot Listener (harus running 24/7)
python telegram_bot_listener.py
```

Bot listener akan:
- Mendengarkan command `/start` dari user
- Menyimpan subscriber ke `telegram_subscribers.json`
- Berjalan terus menerus untuk auto-registration

#### b. Jalankan Dashboard
```bash
# Terminal 2 - Dashboard
streamlit run bogor_v2_advanced.py
```

Dashboard akan:
- Monitoring cuaca real-time dari BMKG API
- Menghitung risk score otomatis
- Mengirim alert ke semua subscriber saat status berubah

---

## 📱 Penggunaan Telegram Bot

### Command User
- `/start` - Daftar untuk menerima notifikasi
- `/stop` - Berhenti menerima notifikasi
- `/status` - Cek status registrasi
- `/info` - Info tentang sistem EWS
- `/help` - Panduan penggunaan

### Cara Subscribe
1. User cari bot di Telegram (nama bot sesuai yang dibuat)
2. User kirim `/start`
3. Bot otomatis simpan Chat ID user
4. User akan menerima notifikasi otomatis saat status berubah

### Format Notifikasi
```
🚨 PERINGATAN DINI LONGSOR - v2.0
Desa Petir, Dramaga, Bogor

🔴 STATUS: BAHAYA
📊 Risk Score: 75.5/100

📈 ANALISIS PARAMETER:
🌧️ Curah Hujan: 25.0 mm/jam
   (Skor: 73.7)
💧 Kelembaban: 92.0%
   (Skor: 73.9)
...

🚨 TINDAKAN SEGERA:
• Segera evakuasi ke tempat aman
• Hubungi BPBD: (0251) 8324000
• Jauhi lereng dan tebing
...
```

---

## 🎨 Fitur Dashboard v2.0

### 1. Status Utama
- **Status Box** dengan warna dinamis (hijau/kuning/merah)
- **Risk Score Gauge** (0-100) dengan visual yang jelas
- **Real-time update** setiap 10 menit

### 2. Detail Analisis
- **Skor per parameter** dengan visualisasi bar chart
- **Weight contribution** untuk setiap parameter
- **Raw value** vs **weighted score**

### 3. Grafik Tren
- **Tab 1**: Risk Score vs Curah Hujan (dual axis)
- **Tab 2**: Parameter cuaca (kelembaban, suhu, angin)
- **Tab 3**: Akumulasi hujan (3 hari & 7 hari)

### 4. Rekomendasi Dinamis
- Otomatis berubah sesuai tingkat risiko
- Berdasarkan standar BNPB dan BMKG
- Mencakup kontak darurat

### 5. Sidebar Monitoring
- Statistik real-time
- Info subscriber Telegram
- Seasonal factor saat ini
- Reset data button

---

## 🧪 Testing & Validasi

### Test Cases

#### Test 1: Kondisi Normal
```python
from risk_scoring import LandslideRiskScorer

scorer = LandslideRiskScorer()
result = scorer.calculate_risk_score(
    rainfall_hourly=3,
    cumulative_3day=15,
    cumulative_7day=45,
    humidity=65,
    wind_speed=10,
    current_month=7  # Juli
)
# Expected: AMAN (score ~10-15)
```

#### Test 2: Kondisi Waspada
```python
result = scorer.calculate_risk_score(
    rainfall_hourly=12,
    cumulative_3day=80,
    cumulative_7day=180,
    humidity=82,
    wind_speed=25,
    current_month=11  # November
)
# Expected: WASPADA (score ~40-50)
```

#### Test 3: Kondisi Bahaya
```python
result = scorer.calculate_risk_score(
    rainfall_hourly=28,
    cumulative_3day=150,
    cumulative_7day=280,
    humidity=93,
    wind_speed=45,
    current_month=12  # Desember
)
# Expected: BAHAYA (score ~70-80)
```

### Validasi dengan Data Historis
Sistem telah divalidasi dengan:
- 7,486 data points historis
- 215 event hujan ekstrem (>50mm/hari)
- Pola musiman 20 tahun
- Threshold berdasarkan persentil statistik

---

## 📈 Keunggulan v2.0

### Dibanding v1.0
| Aspek | v1.0 | v2.0 |
|-------|------|------|
| Threshold | Fixed/hardcoded | Data-driven (20 tahun) |
| Parameter | 2-3 | 5 parameter weighted |
| Scoring | Binary (Bahaya/Aman) | Continuous (0-100) |
| Akumulasi | Tidak ada | 3 hari + 7 hari |
| Seasonal | Tidak ada | Faktor musiman |
| Akurasi | Moderate | High |

### Validasi Ilmiah
- ✅ Berdasarkan data CHIRPS (standar internasional)
- ✅ Threshold dari analisis persentil statistik
- ✅ Multi-parameter weighted system
- ✅ Seasonal adjustment
- ✅ Cumulative rainfall tracking

---

## 🔍 Interpretasi Risk Score

### Score 0-20 (Sangat Aman)
- Cuaca normal
- Tidak ada tindakan khusus
- Monitoring rutin

### Score 21-40 (Aman)
- Kondisi masih aman
- Pantau perkembangan cuaca
- Cek drainase

### Score 41-60 (Waspada Awal)
- Peningkatan risiko moderat
- Siapkan rencana evakuasi
- Pantau lebih ketat

### Score 61-70 (Waspada Tinggi)
- Risiko meningkat signifikan
- Siaga evakuasi
- Koordinasi dengan BPBD

### Score 71-85 (Bahaya)
- Risiko tinggi
- Mulai evakuasi
- Hubungi pihak berwenang

### Score 86-100 (Bahaya Ekstrem)
- Risiko sangat tinggi
- Evakuasi segera
- Emergency response

---

## 📞 Kontak Darurat

| Instansi | Nomor Telepon |
|----------|---------------|
| **BPBD Kabupaten Bogor** | (0251) 8324000 |
| **SAR Nasional** | 115 |
| **Ambulans** | 118 / 119 |
| **PMI Bogor** | (0251) 8321111 |
| **BMKG Bogor** | (0251) 8311511 |
| **Polsek Dramaga** | (0251) 8625111 |
| **Kantor Kecamatan Dramaga** | (0251) 8623002 |

---

## 🔄 Maintenance & Update

### Update Threshold
Jika ada data baru atau perubahan kondisi lokasi:
```python
# Edit risk_scoring.py
# Update nilai dalam self._get_default_config()
# Sesuaikan berdasarkan analisis data terbaru
```

### Update Bot Token
```python
# Edit di kedua file:
# - bogor_v2_advanced.py
# - telegram_bot_listener.py

TELEGRAM_BOT_TOKEN = "NEW_TOKEN_HERE"
```

### Backup Data
```bash
# Backup file penting
cp telegram_subscribers.json telegram_subscribers.backup.json
cp risk_scoring_config.json risk_scoring_config.backup.json
```

---

## 📚 Referensi

### Data & Metodologi
1. **CHIRPS Data**: Climate Hazards Group, UC Santa Barbara
2. **BMKG API**: Badan Meteorologi, Klimatologi, dan Geofisika
3. **Standar Longsor**: BNPB (Badan Nasional Penanggulangan Bencana)

### Literatur
1. "Landslide Early Warning Systems" - UNESCO-ILP
2. "Rainfall Thresholds for Landslides" - BNPB Guidelines
3. "Multi-parameter Risk Assessment" - Journal of Natural Hazards

---

## 📝 Changelog

### v2.0 (Current)
- ✅ Multi-parameter weighted scoring
- ✅ Data-driven thresholds (20 years CHIRPS)
- ✅ Cumulative rainfall tracking
- ✅ Seasonal risk factors
- ✅ Advanced visualization
- ✅ Telegram auto-notification

### v1.0 (Legacy)
- Basic threshold system
- Simple BMKG API integration
- Manual telegram notification

---

## 🤝 Contributing
Untuk improvement atau bug report, silakan hubungi tim pengembang atau buat issue di repository.

## 📄 License
Sistem ini dikembangkan untuk kepentingan mitigasi bencana masyarakat Desa Petir, Dramaga, Bogor.

---

**Last Updated**: November 2025  
**Version**: 2.0  
**Developed for**: Desa Petir, Kecamatan Dramaga, Kabupaten Bogor
