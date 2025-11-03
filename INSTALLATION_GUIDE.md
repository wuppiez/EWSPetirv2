# 🚀 Panduan Instalasi Cepat - EWS Longsor v2.0

## ⚡ Quick Start (5 Menit)

### Step 1: Install Dependencies
```bash
pip install streamlit requests pandas plotly python-telegram-bot openpyxl
```

### Step 2: Download Semua File
Pastikan Anda memiliki file berikut dalam satu folder:
- ✅ `bogor_v2_advanced.py` (Dashboard utama)
- ✅ `risk_scoring.py` (Modul scoring)
- ✅ `telegram_bot_listener.py` (Bot listener)

### Step 3: Setup Telegram Bot

#### 3a. Buat Bot di Telegram
1. Buka Telegram, cari: `@BotFather`
2. Kirim: `/newbot`
3. Masukkan nama bot: `EWS Petir Bot` (contoh)
4. Masukkan username: `ews_petir_bot` (contoh, harus unique)
5. **COPY TOKEN** yang diberikan (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### 3b. Masukkan Token ke File
Edit **KEDUA file** ini dan ganti token-nya:

**File 1: `bogor_v2_advanced.py`** (sekitar baris 106)
```python
TELEGRAM_BOT_TOKEN = "PASTE_TOKEN_ANDA_DISINI"
```

**File 2: `telegram_bot_listener.py`** (sekitar baris 34)
```python
TELEGRAM_BOT_TOKEN = "PASTE_TOKEN_ANDA_DISINI"
```

### Step 4: Jalankan Sistem

#### Terminal 1 - Bot Listener (Harus Running Terus)
```bash
python telegram_bot_listener.py
```

Akan muncul:
```
🤖 TELEGRAM BOT LISTENER - EWS LONGSOR
📍 Desa Petir, Dramaga, Bogor
⏰ Started at: 2025-11-03 10:30:00
🎯 Waiting for commands...
```

**JANGAN TUTUP TERMINAL INI!** Bot harus running untuk menerima `/start` dari user.

#### Terminal 2 - Dashboard
```bash
streamlit run bogor_v2_advanced.py
```

Browser akan otomatis terbuka di `http://localhost:8501`

### Step 5: Test Subscribe

1. Buka bot di Telegram (search username yang Anda buat tadi)
2. Kirim: `/start`
3. Bot akan reply dengan pesan konfirmasi
4. Cek terminal bot listener - akan ada log subscriber baru
5. Dashboard akan otomatis kirim notifikasi saat status berubah

---

## ✅ Checklist Verifikasi

Setelah instalasi, pastikan:

- [ ] Dashboard terbuka di browser
- [ ] Status cuaca muncul (hijau/kuning/merah)
- [ ] Risk score tampil (0-100)
- [ ] Bot listener running di terminal
- [ ] Bot bisa menerima `/start` di Telegram
- [ ] Subscriber count bertambah di sidebar dashboard

---

## 🐛 Troubleshooting

### Problem 1: ModuleNotFoundError
**Error**: `ModuleNotFoundError: No module named 'streamlit'`

**Solusi**:
```bash
pip install --upgrade streamlit requests pandas plotly python-telegram-bot openpyxl
```

### Problem 2: Bot Tidak Merespon
**Error**: User kirim `/start` tapi bot tidak reply

**Solusi**:
1. Pastikan bot listener running (cek terminal 1)
2. Pastikan token sudah benar di `telegram_bot_listener.py`
3. Test token dengan curl:
```bash
curl https://api.telegram.org/bot<TOKEN>/getMe
```
Replace `<TOKEN>` dengan token Anda. Harus return info bot.

### Problem 3: Gagal Ambil Data BMKG
**Error**: "❌ Gagal mengambil data dari BMKG API"

**Solusi**:
1. Cek koneksi internet
2. BMKG API kadang slow, tunggu 30 detik dan refresh
3. Cache 10 menit, jadi error sesekali tidak masalah

### Problem 4: Notification Tidak Terkirim
**Error**: Alert tidak masuk ke Telegram

**Solusi**:
1. Pastikan subscriber sudah kirim `/start` ke bot
2. Cek sidebar dashboard: "Subscribers: X user" (harus > 0)
3. Pastikan bot listener masih running
4. Cek file `telegram_subscribers.json` ada dan isinya valid

---

## 🔧 Konfigurasi Lanjutan

### Mengubah Lokasi
Edit file `bogor_v2_advanced.py`:
```python
# Baris 101-103
LOCATION_LAT = -6.612778  # Ganti dengan koordinat Anda
LOCATION_LON = 106.725833
KODE_WILAYAH_ADM4 = "32.01.30.2005"  # Cari di data.bmkg.go.id
```

### Mengubah Threshold
Edit file `risk_scoring.py`, fungsi `_get_default_config()`:
```python
"rainfall_hourly": {
    "aman": {"max": 5, "score_range": [0, 30]},  # Ubah angka di sini
    "waspada": {"min": 5, "max": 15, ...},
    ...
}
```

### Mengubah Weight Parameter
Edit file `risk_scoring.py`:
```python
"weights": {
    "rainfall_hourly": 0.30,     # Ubah bobot di sini
    "cumulative_3day": 0.25,     # Total harus = 1.0
    "cumulative_7day": 0.15,
    "humidity": 0.20,
    "wind_speed": 0.10
}
```

---

## 📱 Panduan User (Untuk Warga)

### Cara Subscribe Notifikasi

**Langkah 1**: Download Telegram
- Android: Google Play Store
- iOS: App Store

**Langkah 2**: Cari Bot
- Buka Telegram
- Search: `@username_bot_anda` (sesuai yang dibuat)
- Atau klik link yang diberikan admin

**Langkah 3**: Kirim `/start`
- Ketik: `/start`
- Enter
- Bot akan kirim pesan konfirmasi

**Langkah 4**: Terima Notifikasi
- Otomatis dapat alert saat:
  - Status BAHAYA 🔴
  - Status WASPADA 🟡
  - Status kembali AMAN 🟢

### Command yang Bisa Digunakan
- `/start` - Daftar notifikasi
- `/stop` - Berhenti notifikasi
- `/status` - Cek status registrasi
- `/info` - Info sistem EWS
- `/help` - Bantuan

---

## 🖥️ Deployment (Production)

### Opsi 1: Local Server 24/7
Untuk PC/server yang always-on:
```bash
# Install screen atau tmux
sudo apt-get install screen

# Jalankan bot di background
screen -S ews-bot
python telegram_bot_listener.py
# Ctrl+A, D untuk detach

# Jalankan dashboard di background
screen -S ews-dashboard
streamlit run bogor_v2_advanced.py --server.port 8501 --server.address 0.0.0.0
# Ctrl+A, D untuk detach
```

### Opsi 2: VPS/Cloud
Untuk deployment di VPS (Digital Ocean, AWS, dll):

1. Upload semua file ke VPS
2. Install dependencies
3. Gunakan systemd service:

**File: `/etc/systemd/system/ews-bot.service`**
```ini
[Unit]
Description=EWS Telegram Bot Listener
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ews
ExecStart=/usr/bin/python3 telegram_bot_listener.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**File: `/etc/systemd/system/ews-dashboard.service`**
```ini
[Unit]
Description=EWS Dashboard
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ews
ExecStart=/usr/local/bin/streamlit run bogor_v2_advanced.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable dan start:
```bash
sudo systemctl enable ews-bot
sudo systemctl enable ews-dashboard
sudo systemctl start ews-bot
sudo systemctl start ews-dashboard
```

### Opsi 3: Docker (Recommended untuk Production)

**File: `Dockerfile`**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "bogor_v2_advanced.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**File: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  bot-listener:
    build: .
    command: python telegram_bot_listener.py
    volumes:
      - ./telegram_subscribers.json:/app/telegram_subscribers.json
    restart: always
    
  dashboard:
    build: .
    command: streamlit run bogor_v2_advanced.py --server.port=8501 --server.address=0.0.0.0
    ports:
      - "8501:8501"
    volumes:
      - ./telegram_subscribers.json:/app/telegram_subscribers.json
    restart: always
    depends_on:
      - bot-listener
```

Run dengan:
```bash
docker-compose up -d
```

---

## 📊 Monitoring & Maintenance

### Log Checking
```bash
# Check bot listener logs
tail -f logs/bot_listener.log

# Check dashboard logs
tail -f logs/dashboard.log
```

### Database Backup
```bash
# Backup subscribers
cp telegram_subscribers.json telegram_subscribers.$(date +%Y%m%d).backup.json

# Backup config
cp risk_scoring_config.json risk_scoring_config.$(date +%Y%m%d).backup.json
```

### Update Token (Jika Bot Kompromis)
1. Generate token baru di @BotFather
2. Update di kedua file (bogor_v2_advanced.py dan telegram_bot_listener.py)
3. Restart kedua service
4. User tidak perlu `/start` ulang, Chat ID masih tersimpan

---

## 🎓 Training & Dokumentasi

### Untuk Admin/Operator
1. Baca `README_EWS_v2.md` untuk pemahaman sistem
2. Pahami scoring system di `risk_scoring.py`
3. Test dengan berbagai scenario
4. Monitor log secara berkala

### Untuk Developer
1. Study `risk_scoring.py` untuk logic scoring
2. Lihat `bogor_v2_advanced.py` untuk integration
3. Eksperimen dengan threshold berbeda
4. Validasi dengan data historis lokal jika ada

---

## 📞 Support

Jika ada masalah atau pertanyaan:
1. Cek troubleshooting section di atas
2. Review log files
3. Test individual components
4. Hubungi tim pengembang

---

## ✨ Tips & Best Practices

### Performance
- Dashboard: Refresh otomatis setiap 10 menit (cache BMKG)
- Bot: Selalu running untuk instant response
- Bandwidth: ~1-2 MB/jam untuk kedua service

### Security
- Jangan share bot token di public
- Backup `telegram_subscribers.json` berkala
- Gunakan HTTPS untuk production dashboard
- Restrict dashboard access dengan firewall jika perlu

### Reliability
- Use systemd/supervisor untuk auto-restart
- Monitor disk space (logs & data)
- Setup alert jika service down
- Test recovery procedure

---

## 🏆 Success Criteria

Sistem dianggap berhasil jika:
- ✅ Bot merespon `/start` dalam < 1 detik
- ✅ Dashboard update setiap 10 menit
- ✅ Notification terkirim < 5 detik setelah status change
- ✅ Uptime > 99% (max downtime 7 jam/bulan)
- ✅ Risk score akurat sesuai kondisi lapangan

---

**Selamat Menggunakan EWS Longsor v2.0! 🚀**

Untuk dokumentasi lengkap, baca `README_EWS_v2.md`
