"""
Early Warning System (EWS) Longsor - ADVANCED VERSION
Desa Petir, Dramaga, Bogor

Version 2.0 - Integrated Risk Scoring System
Berdasarkan analisis data historis CHIRPS 2005-2025 (20.5 tahun)

Features:
- Multi-parameter risk scoring (5 parameters)
- Weighted scoring system
- Cumulative rainfall tracking (3-day, 7-day)
- Seasonal risk factors
- Data-driven thresholds
- Telegram auto-notification
- Real-time BMKG API integration
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
    page_title="EWS Longsor v2.0 - Desa Petir",
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
    st.session_state.rainfall_history = []  # Untuk tracking kumulatif

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
KODE_WILAYAH_ADM4 = "32.01.30.2005"

# Konfigurasi Telegram
TELEGRAM_BOT_TOKEN = "8271915231:AAGyCe7dKqbZMmrAs4_XHlfes-JaHNPJTeE"
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
<b>🚨 PERINGATAN DINI LONGSOR - v2.0</b>
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
    
    for rec in recommendations[:4]:  # Limit 4 rekomendasi untuk Telegram
        message += f"• {rec}\n"
    
    message += "\n<b>📞 Kontak Darurat:</b>"
    message += "\n• BPBD: (0251) 8324000"
    message += "\n• SAR: 115"
    message += "\n• Ambulans: 118/119"
    
    return message

@st.cache_data(ttl=600)
def get_weather_data():
    """Ambil data cuaca dari BMKG API dengan caching 10 menit"""
    try:
        url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={KODE_WILAYAH_ADM4}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'data' in data and len(data['data']) > 0:
                lokasi_data = data['data'][0]
                
                if 'cuaca' in lokasi_data and len(lokasi_data['cuaca']) > 0:
                    cuaca_list = lokasi_data['cuaca'][0]
                    
                    if len(cuaca_list) > 0:
                        cuaca_now = cuaca_list[0]
                        
                        # Ekstrak data dengan default values
                        curah_hujan = float(cuaca_now.get('ch', 0))
                        kelembaban = float(cuaca_now.get('hu', 0))
                        suhu = float(cuaca_now.get('t', 0))
                        kecepatan_angin = float(cuaca_now.get('ws', 0))
                        arah_angin = cuaca_now.get('wd_to', 'N/A')
                        kondisi = cuaca_now.get('weather_desc', 'N/A')
                        
                        return {
                            'success': True,
                            'curah_hujan': curah_hujan,
                            'kelembaban': kelembaban,
                            'suhu': suhu,
                            'kecepatan_angin': kecepatan_angin,
                            'arah_angin': arah_angin,
                            'kondisi': kondisi,
                            'timestamp': datetime.now(),
                            'raw_data': cuaca_now
                        }
        
        return {
            'success': False,
            'message': f'Response code: {response.status_code}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def update_rainfall_history(rainfall_mm):
    """Update history curah hujan untuk tracking kumulatif"""
    st.session_state.rainfall_history.append({
        'timestamp': datetime.now(),
        'rainfall': rainfall_mm
    })
    
    # Keep only last 7 days
    if len(st.session_state.rainfall_history) > 168:  # 7 days * 24 hours
        st.session_state.rainfall_history = st.session_state.rainfall_history[-168:]

def calculate_cumulative_rainfall(hours):
    """Hitung curah hujan kumulatif untuk N jam terakhir"""
    if not st.session_state.rainfall_history:
        return 0
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_data = [
        entry['rainfall'] 
        for entry in st.session_state.rainfall_history 
        if entry['timestamp'] >= cutoff_time
    ]
    
    return sum(recent_data)

# ==================== MAIN APP ====================

# Header
st.title("🚨 Early Warning System Longsor v2.0")
st.markdown("### 📍 Desa Petir, Kecamatan Dramaga, Kabupaten Bogor")
st.caption("🔬 Advanced Risk Scoring - Berdasarkan Data Historis 20 Tahun (2005-2025)")

st.divider()

# Ambil data cuaca
weather_data = get_weather_data()

if weather_data['success']:
    
    # Update rainfall history
    update_rainfall_history(weather_data['curah_hujan'])
    
    # Hitung kumulatif
    cum_3day = calculate_cumulative_rainfall(72)  # 3 days
    cum_7day = calculate_cumulative_rainfall(168)  # 7 days
    
    # Hitung risk score menggunakan model baru
    scorer = st.session_state.risk_scorer
    risk_result = scorer.calculate_risk_score(
        rainfall_hourly=weather_data['curah_hujan'],
        cumulative_3day=cum_3day,
        cumulative_7day=cum_7day,
        humidity=weather_data['kelembaban'],
        wind_speed=weather_data['kecepatan_angin'],
        current_month=datetime.now().month
    )
    
    tingkat_bahaya = risk_result['risk_level']
    risk_score = risk_result['adjusted_score']
    
    # Tampilkan Status Utama dengan Score
    col_status1, col_status2 = st.columns([2, 1])
    
    with col_status1:
        status_class = f"status-{tingkat_bahaya.lower()}"
        st.markdown(f"""
            <div class="{status_class} status-box">
                <div style="font-size: 2.5em;">{risk_result['risk_emoji']}</div>
                <div style="font-size: 1.8em; margin: 10px 0;">STATUS: {tingkat_bahaya}</div>
                <div style="font-size: 1.2em; opacity: 0.9;">{risk_result['risk_description']}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col_status2:
        st.markdown(f"""
            <div class="score-card" style="text-align: center;">
                <div style="font-size: 0.9em; color: #6c757d; margin-bottom: 8px;">RISK SCORE</div>
                <div style="font-size: 3em; font-weight: bold; color: {risk_result['risk_color']};">
                    {risk_score:.1f}
                </div>
                <div style="font-size: 1.2em; color: #6c757d;">/ 100</div>
                <div style="font-size: 0.85em; margin-top: 10px; color: #6c757d;">
                    Base: {risk_result['total_score']:.1f} | 
                    Seasonal: ×{risk_result['seasonal_multiplier']}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Notifikasi perubahan status
    if tingkat_bahaya != st.session_state.last_status:
        st.session_state.last_status = tingkat_bahaya
        notif_time = datetime.now()
        
        st.session_state.notifications.append({
            'timestamp': notif_time,
            'old_status': st.session_state.last_status,
            'new_status': tingkat_bahaya,
            'score': risk_score
        })
        
        # Kirim Telegram alert
        if TELEGRAM_ENABLED:
            telegram_msg = format_telegram_alert(risk_result, weather_data)
            send_success = send_telegram_message(telegram_msg)
            
            if send_success:
                st.success(f"✅ Alert Telegram terkirim ke semua subscriber!")
    
    # Bagian Risk Scoring Detail
    st.subheader("📊 Analisis Risk Scoring Detail")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Skor Per Parameter")
        
        for param_name, param_data in risk_result['parameters'].items():
            # Map nama parameter ke label yang lebih friendly
            param_labels = {
                'rainfall_hourly': '🌧️ Curah Hujan/Jam',
                'cumulative_3day': '📊 Kumulatif 3 Hari',
                'cumulative_7day': '📈 Kumulatif 7 Hari',
                'humidity': '💧 Kelembaban',
                'wind_speed': '💨 Kecepatan Angin'
            }
            
            label = param_labels.get(param_name, param_name)
            value = param_data['value']
            raw_score = param_data['raw_score']
            weight = param_data['weight']
            weighted = param_data['weighted_score']
            
            # Determine color based on score
            if raw_score < 30:
                color = "#28a745"
            elif raw_score < 60:
                color = "#ffc107"
            else:
                color = "#dc3545"
            
            st.markdown(f"""
                <div class="parameter-detail">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: bold; font-size: 1.1em;">{label}</div>
                            <div style="color: #6c757d; font-size: 0.9em;">
                                Nilai: {value:.1f} | Bobot: {weight*100:.0f}%
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.5em; font-weight: bold; color: {color};">
                                {raw_score:.1f}
                            </div>
                            <div style="font-size: 0.85em; color: #6c757d;">
                                → {weighted:.1f}
                            </div>
                        </div>
                    </div>
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
    st.error(f"❌ Gagal mengambil data dari BMKG API")
    st.warning(f"**Detail Error:** {weather_data.get('message', 'Unknown error')}")

# Sidebar
with st.sidebar:
    st.title("⚙️ Sistem Info")
    
    st.markdown("### 🔬 Risk Scoring v2.0")
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
    
    Kode: {KODE_WILAYAH_ADM4}
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
st.caption("🔬 EWS Longsor v2.0 - Advanced Risk Scoring System")
st.caption("📊 Berdasarkan analisis data historis CHIRPS 2005-2025 (20.5 tahun)")
st.caption("📡 Data real-time dari BMKG API Publik | 🤖 Telegram Auto-notification")
st.caption(f"💾 Cache: 10 menit | 📝 Historical data: {len(st.session_state.historical_data)} points")
