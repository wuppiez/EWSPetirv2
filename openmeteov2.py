"""
Early Warning System (EWS) Longsor - ADVANCED VERSION
Desa Petir, Dramaga, Bogor

Version 2.1 - Open-Meteo API Integration (FIXED)
Berdasarkan analisis data historis CHIRPS 2005-2025 (20.5 tahun)

Features:
- Multi-parameter risk scoring (5 parameters)
- Weighted scoring system
- Cumulative rainfall tracking (3-day, 7-day)
- Seasonal risk factors
- Data-driven thresholds
- Telegram auto-notification
- Real-time Open-Meteo API integration (FREE, NO API KEY!)

FIXED: Timezone comparison error pada cumulative rainfall calculation
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import os
import plotly.graph_objects as go
import plotly.express as px
from risk_scoring import LandslideRiskScorer

# Konfigurasi halaman
st.set_page_config(
    page_title="EWS Longsor v2.1 - Desa Petir",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS untuk styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stAlert {
        border-radius: 10px;
    }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-box {
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin: 15px 0;
        font-size: 1.2em;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .status-aman {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 3px solid #28a745;
        color: #155724;
    }
    .status-waspada {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 3px solid #ffc107;
        color: #856404;
    }
    .status-bahaya {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 3px solid #dc3545;
        color: #721c24;
    }
    .score-card {
        padding: 20px;
        border-radius: 12px;
        background-color: #ffffff;
        border-left: 5px solid #007bff;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .parameter-detail {
        padding: 15px;
        margin: 8px 0;
        border-radius: 8px;
        background-color: #f8f9fa;
        border-left: 4px solid #6c757d;
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi session state
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = []

if 'rainfall_history' not in st.session_state:
    st.session_state.rainfall_history = []

if 'notifications' not in st.session_state:
    st.session_state.notifications = []

if 'last_status' not in st.session_state:
    st.session_state.last_status = "AMAN"

if 'telegram_log' not in st.session_state:
    st.session_state.telegram_log = []

if 'risk_scorer' not in st.session_state:
    st.session_state.risk_scorer = LandslideRiskScorer()

# Koordinat Desa Petir, Dramaga, Bogor
LOCATION_LAT = -6.612778
LOCATION_LON = 106.725833

# Konfigurasi Telegram
TELEGRAM_BOT_TOKEN = "8443676707:AAH65PQmfs4lbinrrXWWw1UypuTT2B9t1Yc"
SUBSCRIBERS_FILE = "telegram_subscribers.json"
TELEGRAM_ENABLED = True

# ==================== FUNGSI UTILITY ====================

def load_subscribers():
    """Load daftar subscriber dari file JSON"""
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"subscribers": [], "metadata": {}}
    return {"subscribers": [], "metadata": {}}

def get_active_chat_ids():
    """Ambil semua Chat ID yang aktif"""
    data = load_subscribers()
    chat_ids = []
    for sub in data.get("subscribers", []):
        if sub.get("active", True):
            chat_ids.append(sub["chat_id"])
    return chat_ids

def send_telegram_message(message, parse_mode='HTML'):
    """Mengirim pesan ke semua subscriber yang terdaftar"""
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN:
        return False
    
    chat_ids = get_active_chat_ids()
    if not chat_ids:
        return False
    
    success_count = 0
    for chat_id in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                success_count += 1
        except Exception as e:
            continue
    
    return success_count > 0

def format_telegram_alert(risk_result, weather_data):
    """Format pesan alert untuk Telegram dengan scoring detail"""
    
    emoji = risk_result['risk_emoji']
    level = risk_result['risk_level']
    score = risk_result['adjusted_score']
    
    message = f"""
<b>🚨 PERINGATAN DINI LONGSOR - v2.1</b>
<b>Desa Petir, Dramaga, Bogor</b>

{emoji} <b>STATUS: {level}</b>
📊 <b>Risk Score: {score:.1f}/100</b>

<b>📈 ANALISIS PARAMETER:</b>
🌧️ Curah Hujan: {weather_data['curah_hujan']:.1f} mm/jam
   (Skor: {risk_result['parameters']['rainfall_hourly']['raw_score']:.1f})
💧 Kelembaban: {weather_data['kelembaban']:.1f}%
   (Skor: {risk_result['parameters']['humidity']['raw_score']:.1f})
💨 Kecepatan Angin: {weather_data['kecepatan_angin']:.1f} km/jam
   (Skor: {risk_result['parameters']['wind_speed']['raw_score']:.1f})
🌡️ Suhu: {weather_data['suhu']:.1f}°C
☁️ Kondisi: {weather_data['kondisi']}

<b>📊 AKUMULASI HUJAN:</b>
3 hari: {risk_result['parameters']['cumulative_3day']['value']:.1f} mm
7 hari: {risk_result['parameters']['cumulative_7day']['value']:.1f} mm

📅 {datetime.now().strftime('%d %B %Y, %H:%M:%S WIB')}
"""
    
    # Tambahkan rekomendasi
    scorer = st.session_state.risk_scorer
    recommendations = scorer.get_recommendations(level)
    
    if level == "BAHAYA":
        message += "\n<b>🚨 TINDAKAN SEGERA:</b>\n"
    elif level == "WASPADA":
        message += "\n<b>⚠️ TINDAKAN:</b>\n"
    else:
        message += "\n<b>✅ TINDAKAN:</b>\n"
    
    for rec in recommendations[:4]:
        message += f"• {rec}\n"
    
    message += "\n<b>📞 Kontak Darurat:</b>"
    message += "\n• BPBD: (0251) 8324000"
    message += "\n• SAR: 115"
    message += "\n• Ambulans: 118/119"
    
    return message

def get_weather_condition(weather_code):
    """
    Konversi WMO Weather Code ke deskripsi cuaca
    Referensi: https://open-meteo.com/en/docs
    """
    weather_descriptions = {
        0: "Cerah",
        1: "Cerah Sebagian",
        2: "Berawan Sebagian",
        3: "Berawan",
        45: "Berkabut",
        48: "Kabut Beku",
        51: "Gerimis Ringan",
        53: "Gerimis Sedang",
        55: "Gerimis Lebat",
        56: "Gerimis Beku Ringan",
        57: "Gerimis Beku Lebat",
        61: "Hujan Ringan",
        63: "Hujan Sedang",
        65: "Hujan Lebat",
        66: "Hujan Beku Ringan",
        67: "Hujan Beku Lebat",
        71: "Salju Ringan",
        73: "Salju Sedang",
        75: "Salju Lebat",
        77: "Butir Salju",
        80: "Hujan Ringan",
        81: "Hujan Sedang",
        82: "Hujan Deras",
        85: "Salju Ringan",
        86: "Salju Lebat",
        95: "Badai Petir",
        96: "Badai Petir dengan Hujan Es Ringan",
        99: "Badai Petir dengan Hujan Es Lebat"
    }
    return weather_descriptions.get(weather_code, "Tidak Diketahui")

def get_wind_direction(degrees):
    """Konversi derajat angin ke arah mata angin"""
    if degrees is None:
        return "N/A"
    directions = ['Utara', 'Timur Laut', 'Timur', 'Tenggara', 
                  'Selatan', 'Barat Daya', 'Barat', 'Barat Laut']
    index = round(degrees / 45) % 8
    return directions[index]

@st.cache_data(ttl=600)
def get_weather_data():
    """
    Ambil data cuaca dari Open-Meteo API dengan caching 10 menit
    Dokumentasi: https://open-meteo.com/en/docs
    
    FIXED: Timezone comparison error
    """
    try:
        # Open-Meteo API endpoint
        url = "https://api.open-meteo.com/v1/forecast"
        
        # Parameter sesuai dokumentasi Open-Meteo
        params = {
            'latitude': LOCATION_LAT,
            'longitude': LOCATION_LON,
            'current': ['temperature_2m', 'relative_humidity_2m', 'precipitation', 
                       'weather_code', 'wind_speed_10m', 'wind_direction_10m'],
            'hourly': ['precipitation'],
            'timezone': 'Asia/Jakarta',
            'past_days': 7,  # Untuk mendapatkan data 7 hari ke belakang
            'forecast_days': 1
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract current weather data
            current = data.get('current', {})
            hourly = data.get('hourly', {})
            
            # Current weather values
            suhu = current.get('temperature_2m', 0)
            kelembaban = current.get('relative_humidity_2m', 0)
            curah_hujan = current.get('precipitation', 0)
            weather_code = current.get('weather_code', 0)
            wind_speed = current.get('wind_speed_10m', 0)
            wind_direction = current.get('wind_direction_10m', 0)
            
            # Konversi kondisi cuaca dan arah angin
            kondisi = get_weather_condition(weather_code)
            arah_angin = get_wind_direction(wind_direction)
            
            # Hitung akumulasi hujan dari data hourly
            cumulative_3day = 0
            cumulative_7day = 0
            
            if 'time' in hourly and 'precipitation' in hourly:
                precipitation_hourly = hourly['precipitation']
                time_hourly = hourly['time']
                
                # Buat DataFrame untuk memudahkan perhitungan
                df_hourly = pd.DataFrame({
                    'time': pd.to_datetime(time_hourly),
                    'precipitation': precipitation_hourly
                })
                
                # FIXED: Hapus timezone info untuk menghindari comparison error
                df_hourly['time'] = df_hourly['time'].dt.tz_localize(None)
                
                # Waktu sekarang tanpa timezone
                now = pd.Timestamp.now()
                
                # Filter dan hitung akumulasi
                df_7days = df_hourly[df_hourly['time'] >= (now - pd.Timedelta(days=7))]
                df_3days = df_hourly[df_hourly['time'] >= (now - pd.Timedelta(days=3))]
                
                cumulative_7day = float(df_7days['precipitation'].sum())
                cumulative_3day = float(df_3days['precipitation'].sum())
            
            weather_result = {
                'success': True,
                'timestamp': datetime.now(),
                'suhu': float(suhu),
                'kelembaban': float(kelembaban),
                'curah_hujan': float(curah_hujan),
                'kondisi': kondisi,
                'weather_code': int(weather_code),
                'kecepatan_angin': float(wind_speed),
                'arah_angin': arah_angin,
                'arah_angin_derajat': float(wind_direction) if wind_direction is not None else 0,
                'cumulative_3day': cumulative_3day,
                'cumulative_7day': cumulative_7day,
                'lokasi': 'Desa Petir, Dramaga, Bogor',
                'source': 'Open-Meteo API',
                'latitude': data.get('latitude', LOCATION_LAT),
                'longitude': data.get('longitude', LOCATION_LON),
                'elevation': data.get('elevation', 0)
            }
            
            return weather_result
        
        else:
            return {
                'success': False,
                'message': f'HTTP Error {response.status_code}: {response.text}',
                'timestamp': datetime.now()
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'Request timeout - Open-Meteo API tidak merespons',
            'timestamp': datetime.now()
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'message': 'Connection error - Tidak dapat terhubung ke Open-Meteo API',
            'timestamp': datetime.now()
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now()
        }

def check_and_notify(risk_result, weather_data):
    """Cek perubahan status dan kirim notifikasi Telegram jika diperlukan"""
    current_status = risk_result['risk_level']
    
    # Kirim notifikasi jika status berubah atau status BAHAYA
    should_notify = (
        current_status != st.session_state.last_status or 
        current_status == "BAHAYA"
    )
    
    if should_notify:
        message = format_telegram_alert(risk_result, weather_data)
        success = send_telegram_message(message)
        
        # Log notifikasi
        log_entry = {
            'timestamp': datetime.now(),
            'status': current_status,
            'risk_score': risk_result['adjusted_score'],
            'sent': success,
            'message_preview': message[:100]
        }
        st.session_state.telegram_log.append(log_entry)
        
        # Update last status
        st.session_state.last_status = current_status
        
        return success
    
    return False

# ==================== MAIN APP ====================

st.title("🚨 Early Warning System Longsor v2.1")
st.markdown("### 📍 Desa Petir, Dramaga, Bogor")
st.markdown("---")

# Info box
st.info("🌐 **Menggunakan Open-Meteo API** - Gratis, tanpa API key, real-time data!")

# Auto-refresh setiap 5 menit
st.markdown("""
<script>
    setTimeout(function(){
        window.location.reload();
    }, 300000);
</script>
""", unsafe_allow_html=True)

# Ambil data cuaca
with st.spinner("📡 Mengambil data cuaca dari Open-Meteo..."):
    weather_data = get_weather_data()

if weather_data['success']:
    
    # Update rainfall history
    st.session_state.rainfall_history.append({
        'timestamp': weather_data['timestamp'],
        'rainfall': weather_data['curah_hujan']
    })
    
    # Limit rainfall history to 7 days
    cutoff_time = datetime.now() - timedelta(days=7)
    st.session_state.rainfall_history = [
        entry for entry in st.session_state.rainfall_history 
        if entry['timestamp'] >= cutoff_time
    ]
    
    # Hitung risk score
    scorer = st.session_state.risk_scorer
    
    # Gunakan data kumulatif dari Open-Meteo
    cum_3day = weather_data['cumulative_3day']
    cum_7day = weather_data['cumulative_7day']
    
    risk_result = scorer.calculate_risk_score(
        rainfall_hourly=weather_data['curah_hujan'],
        humidity=weather_data['kelembaban'],
        wind_speed=weather_data['kecepatan_angin'],
        cumulative_3day=cum_3day,
        cumulative_7day=cum_7day,
        current_month=weather_data['timestamp'].month
    )
    
    risk_score = risk_result['adjusted_score']
    tingkat_bahaya = risk_result['risk_level']
    
    # Cek dan kirim notifikasi jika perlu
    notification_sent = check_and_notify(risk_result, weather_data)
    
    if notification_sent:
        st.toast("📱 Notifikasi Telegram terkirim!", icon="✅")
    
    # Display status utama
    if tingkat_bahaya == "BAHAYA":
        st.markdown(f"""
            <div class="status-box status-bahaya">
                🔴 BAHAYA - EVAKUASI SEGERA!<br>
                Risk Score: {risk_score:.1f}/100
            </div>
        """, unsafe_allow_html=True)
    elif tingkat_bahaya == "WASPADA":
        st.markdown(f"""
            <div class="status-box status-waspada">
                🟡 WASPADA - TETAP SIAGA!<br>
                Risk Score: {risk_score:.1f}/100
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="status-box status-aman">
                🟢 AMAN - KONDISI NORMAL<br>
                Risk Score: {risk_score:.1f}/100
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Detail scoring
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📊 Detail Risk Scoring")
        
        st.markdown(f"""
        <div class="score-card">
            <h3 style="color: {risk_result['risk_color']}; margin-bottom: 10px;">
                {risk_result['risk_emoji']} {tingkat_bahaya}
            </h3>
            <h2 style="color: {risk_result['risk_color']}; margin: 5px 0;">
                {risk_score:.1f}/100
            </h2>
            <p style="color: #6c757d; font-size: 0.9em; margin: 5px 0;">
                Base Score: {risk_result['total_score']:.1f} | 
                Seasonal Factor: {risk_result['seasonal_multiplier']:.2f}x
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("##### 📈 Breakdown Parameter:")
        
        for param_name, param_data in risk_result['parameters'].items():
            label = scorer.thresholds.get(param_name, {}).get('description', param_name.replace('_', ' ').title())
            raw_score = param_data['raw_score']
            weight = param_data['weight']
            weighted = param_data['weighted_score']
            value = param_data.get('value', '-')
            
            # Tentukan warna berdasarkan score
            if raw_score < 40:
                color = "#28a745"
            elif raw_score < 70:
                color = "#ffc107"
            else:
                color = "#dc3545"
            
            st.markdown(f"""
                <div class="parameter-detail">
                    <strong>{label}</strong><br>
                    <span style="color: #6c757d; font-size: 0.85em;">
                        Nilai: {value} | Weight: {weight:.1%}
                    </span><br>
                    <span style="font-size: 0.9em;">
                        Raw: {raw_score:.1f} → Weighted: {weighted:.1f}
                    </span>
                    <div style="margin-top: 8px;">
                        <div style="background-color: #e9ecef; border-radius: 10px; height: 8px; overflow: hidden;">
                            <div style="background-color: {color}; height: 100%; width: {min(raw_score, 100)}%; transition: width 0.3s;"></div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 📋 Data Cuaca Real-Time")
        
        # Metrics
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("🌧️ Curah Hujan", f"{weather_data['curah_hujan']:.1f} mm/jam")
            st.metric("💧 Kelembaban", f"{weather_data['kelembaban']:.1f}%")
            st.metric("🌡️ Suhu", f"{weather_data['suhu']:.1f}°C")
        
        with metric_col2:
            st.metric("💨 Kec. Angin", f"{weather_data['kecepatan_angin']:.1f} km/jam")
            st.metric("🧭 Arah Angin", weather_data['arah_angin'])
            st.metric("☁️ Kondisi", weather_data['kondisi'])
        
        st.markdown("#### 📊 Akumulasi Hujan")
        st.metric("📈 3 Hari Terakhir", f"{cum_3day:.1f} mm")
        st.metric("📈 7 Hari Terakhir", f"{cum_7day:.1f} mm")
        
        # Timestamp
        st.caption(f"🕐 Update: {weather_data['timestamp'].strftime('%H:%M:%S WIB')}")
        st.caption(f"📡 Source: {weather_data['source']}")
        st.caption(f"📍 Koordinat: {weather_data['latitude']:.4f}°, {weather_data['longitude']:.4f}°")
        st.caption(f"⛰️ Elevasi: {weather_data['elevation']:.0f} m")
    
    st.divider()
    
    # Rekomendasi
    st.subheader("📋 Rekomendasi Tindakan")
    recommendations = scorer.get_recommendations(tingkat_bahaya)
    
    if tingkat_bahaya == "BAHAYA":
        with st.container():
            st.error("**⚠️ BAHAYA - SEGERA EVAKUASI!**")
            for rec in recommendations:
                st.markdown(f"- {rec}")
    elif tingkat_bahaya == "WASPADA":
        with st.container():
            st.warning("**⚠️ WASPADA - TETAP SIAGA!**")
            for rec in recommendations:
                st.markdown(f"- {rec}")
    else:
        with st.container():
            st.success("**✅ AMAN - KONDISI NORMAL**")
            for rec in recommendations:
                st.markdown(f"- {rec}")
    
    st.divider()
    
    # Grafik Gauge untuk Risk Score
    st.subheader("📊 Visualisasi Risk Score")
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = risk_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Risk Score", 'font': {'size': 24}},
        delta = {'reference': 50, 'increasing': {'color': "red"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': risk_result['risk_color']},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#d4edda'},
                {'range': [40, 70], 'color': '#fff3cd'},
                {'range': [70, 100], 'color': '#f8d7da'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig_gauge.update_layout(height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Historis data
    st.session_state.historical_data.append({
        'timestamp': weather_data['timestamp'],
        'curah_hujan': weather_data['curah_hujan'],
        'kelembaban': weather_data['kelembaban'],
        'suhu': weather_data['suhu'],
        'kecepatan_angin': weather_data['kecepatan_angin'],
        'risk_score': risk_score,
        'status': tingkat_bahaya,
        'cumulative_3day': cum_3day,
        'cumulative_7day': cum_7day
    })
    
    # Limit historical data
    if len(st.session_state.historical_data) > 100:
        st.session_state.historical_data = st.session_state.historical_data[-100:]
    
    # Grafik tren
    if len(st.session_state.historical_data) > 1:
        st.subheader("📈 Tren Data & Risk Score")
        
        df_hist = pd.DataFrame(st.session_state.historical_data)
        
        tab1, tab2, tab3 = st.tabs(["Risk Score & Curah Hujan", "Parameter Cuaca", "Akumulasi Hujan"])
        
        with tab1:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=df_hist['timestamp'],
                y=df_hist['risk_score'],
                name='Risk Score',
                mode='lines+markers',
                line=dict(color='red', width=3),
                yaxis='y1'
            ))
            fig1.add_trace(go.Scatter(
                x=df_hist['timestamp'],
                y=df_hist['curah_hujan'],
                name='Curah Hujan (mm/jam)',
                mode='lines',
                line=dict(color='blue', width=2),
                yaxis='y2'
            ))
            
            fig1.update_layout(
                title='Tren Risk Score vs Curah Hujan',
                xaxis=dict(title='Waktu'),
                yaxis=dict(title='Risk Score', side='left', range=[0, 100]),
                yaxis2=dict(title='Curah Hujan (mm/jam)', side='right', overlaying='y'),
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig1, use_container_width=True)
        
        with tab2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_hist['timestamp'], y=df_hist['kelembaban'], name='Kelembaban (%)', line=dict(color='cyan')))
            fig2.add_trace(go.Scatter(x=df_hist['timestamp'], y=df_hist['suhu'], name='Suhu (°C)', line=dict(color='orange')))
            fig2.add_trace(go.Scatter(x=df_hist['timestamp'], y=df_hist['kecepatan_angin'], name='Angin (km/jam)', line=dict(color='green')))
            
            fig2.update_layout(
                title='Parameter Cuaca',
                xaxis_title='Waktu',
                yaxis_title='Nilai',
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df_hist['timestamp'], y=df_hist['cumulative_3day'], name='3 Hari (mm)', line=dict(color='purple', width=2)))
            fig3.add_trace(go.Scatter(x=df_hist['timestamp'], y=df_hist['cumulative_7day'], name='7 Hari (mm)', line=dict(color='brown', width=2)))
            
            fig3.update_layout(
                title='Akumulasi Curah Hujan',
                xaxis_title='Waktu',
                yaxis_title='Akumulasi (mm)',
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig3, use_container_width=True)

else:
    st.error(f"❌ Gagal mengambil data dari Open-Meteo API")
    st.warning(f"**Detail Error:** {weather_data.get('message', 'Unknown error')}")
    
    # Tampilkan info debugging
    with st.expander("🔍 Debugging Info"):
        st.write("Endpoint yang digunakan:")
        st.code("https://api.open-meteo.com/v1/forecast")
        st.write("Parameter:")
        st.json({
            'latitude': LOCATION_LAT,
            'longitude': LOCATION_LON,
            'current': ['temperature_2m', 'relative_humidity_2m', 'precipitation', 
                       'weather_code', 'wind_speed_10m', 'wind_direction_10m'],
            'hourly': ['precipitation'],
            'timezone': 'Asia/Jakarta',
            'past_days': 7
        })

# Sidebar
with st.sidebar:
    st.title("⚙️ Sistem Info")
    
    st.markdown("### 🔬 Risk Scoring v2.1")
    st.info("""
    **Sistem Baru:**
    - 5 Parameter weighted
    - Data historis 20 tahun
    - Seasonal factors
    - Cumulative tracking
    - Skor 0-100
    
    **Tingkat Risiko:**
    - 🟢 AMAN: 0-40
    - 🟡 WASPADA: 41-70
    - 🔴 BAHAYA: 71-100
    """)
    
    st.divider()
    
    st.markdown("### 🌐 Open-Meteo API")
    st.success("""
    **✅ GRATIS & OPEN SOURCE**
    - Tanpa API key
    - Tanpa registrasi
    - Real-time data
    - Historical data 7 hari
    - Global coverage
    - Update setiap jam
    
    📚 [Dokumentasi](https://open-meteo.com/en/docs)
    """)
    
    st.divider()
    
    st.markdown("### 📱 Telegram Bot")
    if TELEGRAM_ENABLED:
        subscriber_data = load_subscribers()
        total_subs = len(subscriber_data.get('subscribers', []))
        st.success(f"✅ Aktif ({total_subs} subscriber)")
    else:
        st.warning("⚠️ Tidak Aktif")
    
    st.divider()
    
    st.markdown("### 📍 Lokasi")
    st.info(f"""
    **Desa Petir, Dramaga**
    Kabupaten Bogor
    
    Lat: {LOCATION_LAT:.6f}°S
    Lon: {LOCATION_LON:.6f}°E
    """)
    
    st.divider()
    
    st.markdown("### 📊 Statistik")
    if len(st.session_state.historical_data) > 0:
        df_stats = pd.DataFrame(st.session_state.historical_data)
        st.metric("Data Points", len(df_stats))
        st.metric("Avg Risk Score", f"{df_stats['risk_score'].mean():.1f}")
        st.metric("Max Risk Score", f"{df_stats['risk_score'].max():.1f}")
    
    if st.button("🗑️ Reset Data"):
        st.session_state.historical_data = []
        st.session_state.rainfall_history = []
        st.session_state.notifications = []
        st.success("Data direset!")
        time.sleep(1)
        st.rerun()

# Footer
st.divider()
st.caption("🔬 EWS Longsor v2.1 - Advanced Risk Scoring System with Open-Meteo API")
st.caption("📊 Berdasarkan analisis data historis CHIRPS 2005-2025 (20.5 tahun)")
st.caption("📡 Data real-time dari Open-Meteo API (FREE!) | 🤖 Telegram Auto-notification")
st.caption(f"💾 Cache: 10 menit | 📁 Historical data: {len(st.session_state.historical_data)} points")
st.caption("🌐 Open-Meteo: Open-source weather API by https://open-meteo.com")
st.caption("✅ FIXED: Timezone comparison error resolved")
