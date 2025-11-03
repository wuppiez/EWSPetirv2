"""
Risk Scoring Module for Landslide Early Warning System
Desa Petir, Dramaga, Bogor

Berdasarkan analisis data historis CHIRPS 2005-2025 (20.5 tahun)
Parameter: Curah hujan, kelembaban, kecepatan angin, akumulasi hujan
"""

import json
from datetime import datetime
from typing import Dict, Tuple, List

class LandslideRiskScorer:
    """
    Kelas untuk menghitung skor risiko longsor berdasarkan multiple parameters
    dengan weighted scoring system dan data historis 20 tahun
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize risk scorer dengan konfigurasi
        
        Args:
            config_path: Path ke file konfigurasi JSON (opsional)
        """
        if config_path:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default configuration berdasarkan data historis
            self.config = self._get_default_config()
        
        self.thresholds = self.config['thresholds']
        self.weights = self.config['weights']
        self.risk_levels = self.config['risk_levels']
        
    def _get_default_config(self) -> Dict:
        """Konfigurasi default berdasarkan analisis data CHIRPS 2005-2025"""
        return {
            "version": "2.0",
            "data_source": "CHIRPS 2005-2025 (20.5 years)",
            "location": "Desa Petir, Dramaga, Bogor",
            
            "thresholds": {
                "rainfall_hourly": {
                    "description": "Curah hujan per jam (mm/jam)",
                    "aman": {"max": 5, "score_range": [0, 30]},
                    "waspada": {"min": 5, "max": 15, "score_range": [31, 60]},
                    "bahaya": {"min": 15, "max": 999, "score_range": [61, 100]}
                },
                
                "cumulative_3day": {
                    "description": "Akumulasi hujan 3 hari (mm)",
                    "aman": {"max": 60, "score_range": [0, 25]},
                    "waspada": {"min": 60, "max": 100, "score_range": [26, 50]},
                    "bahaya": {"min": 100, "max": 999, "score_range": [51, 100]}
                },
                
                "cumulative_7day": {
                    "description": "Akumulasi hujan 7 hari (mm)",
                    "aman": {"max": 150, "score_range": [0, 25]},
                    "waspada": {"min": 150, "max": 200, "score_range": [26, 50]},
                    "bahaya": {"min": 200, "max": 999, "score_range": [51, 100]}
                },
                
                "humidity": {
                    "description": "Kelembaban udara (%)",
                    "aman": {"max": 70, "score_range": [0, 20]},
                    "waspada": {"min": 70, "max": 85, "score_range": [21, 50]},
                    "bahaya": {"min": 85, "max": 100, "score_range": [51, 100]}
                },
                
                "wind_speed": {
                    "description": "Kecepatan angin (km/jam)",
                    "aman": {"max": 20, "score_range": [0, 10]},
                    "waspada": {"min": 20, "max": 40, "score_range": [11, 30]},
                    "bahaya": {"min": 40, "max": 999, "score_range": [31, 50]}
                }
            },
            
            "weights": {
                "rainfall_hourly": 0.30,
                "cumulative_3day": 0.25,
                "cumulative_7day": 0.15,
                "humidity": 0.20,
                "wind_speed": 0.10
            },
            
            "risk_levels": {
                "AMAN": {
                    "score_range": [0, 40],
                    "color": "green",
                    "emoji": "🟢",
                    "description": "Kondisi normal, risiko longsor rendah"
                },
                "WASPADA": {
                    "score_range": [41, 70],
                    "color": "yellow",
                    "emoji": "🟡",
                    "description": "Peningkatan risiko, perlu kewaspadaan"
                },
                "BAHAYA": {
                    "score_range": [71, 100],
                    "color": "red",
                    "emoji": "🔴",
                    "description": "Risiko tinggi, evakuasi segera"
                }
            },
            
            "seasonal_factors": {
                "high_risk_months": [11, 12, 1, 2, 3, 4],  # Nov-Apr
                "moderate_risk_months": [5, 10],  # Mei, Okt
                "low_risk_months": [6, 7, 8, 9],  # Jun-Sep
                "multipliers": {
                    "high": 1.2,
                    "moderate": 1.0,
                    "low": 0.8
                }
            }
        }
    
    def calculate_parameter_score(self, value: float, parameter_name: str) -> float:
        """
        Hitung skor untuk satu parameter dengan linear interpolation
        
        Args:
            value: Nilai parameter
            parameter_name: Nama parameter (rainfall_hourly, humidity, dll)
        
        Returns:
            Skor (0-100)
        """
        if parameter_name not in self.thresholds:
            return 0.0
        
        thresholds = self.thresholds[parameter_name]
        
        # Check AMAN range
        if value <= thresholds['aman']['max']:
            ratio = value / thresholds['aman']['max'] if thresholds['aman']['max'] > 0 else 0
            return ratio * thresholds['aman']['score_range'][1]
        
        # Check WASPADA range
        if value <= thresholds['waspada']['max']:
            range_min = thresholds['waspada']['min']
            range_max = thresholds['waspada']['max']
            score_min = thresholds['waspada']['score_range'][0]
            score_max = thresholds['waspada']['score_range'][1]
            
            if range_max - range_min > 0:
                ratio = (value - range_min) / (range_max - range_min)
                return score_min + ratio * (score_max - score_min)
            return score_min
        
        # BAHAYA range
        range_min = thresholds['bahaya']['min']
        range_max = thresholds['bahaya']['max']
        score_min = thresholds['bahaya']['score_range'][0]
        score_max = thresholds['bahaya']['score_range'][1]
        
        if range_max == 999:  # Unlimited upper bound
            # Progressive increase but capped at 100
            return min(100, score_min + (value - range_min) / 10)
        
        if value <= range_max:
            if range_max - range_min > 0:
                ratio = (value - range_min) / (range_max - range_min)
                return min(100, score_min + ratio * (score_max - score_min))
        
        return min(100, score_max)
    
    def calculate_risk_score(self, 
                            rainfall_hourly: float = 0,
                            cumulative_3day: float = 0,
                            cumulative_7day: float = 0,
                            humidity: float = 0,
                            wind_speed: float = 0,
                            current_month: int = None) -> Dict:
        """
        Hitung total skor risiko dengan weighted scoring
        
        Args:
            rainfall_hourly: Curah hujan per jam (mm/jam)
            cumulative_3day: Akumulasi hujan 3 hari (mm)
            cumulative_7day: Akumulasi hujan 7 hari (mm)
            humidity: Kelembaban udara (%)
            wind_speed: Kecepatan angin (km/jam)
            current_month: Bulan saat ini (1-12) untuk faktor musiman
        
        Returns:
            Dictionary berisi skor detail dan tingkat risiko
        """
        
        # Hitung skor untuk setiap parameter
        parameters = {
            'rainfall_hourly': rainfall_hourly,
            'cumulative_3day': cumulative_3day,
            'cumulative_7day': cumulative_7day,
            'humidity': humidity,
            'wind_speed': wind_speed
        }
        
        scores = {}
        weighted_scores = {}
        
        for param, value in parameters.items():
            score = self.calculate_parameter_score(value, param)
            weight = self.weights.get(param, 0)
            weighted_score = score * weight
            
            scores[param] = {
                'value': value,
                'raw_score': round(score, 2),
                'weight': weight,
                'weighted_score': round(weighted_score, 2)
            }
            weighted_scores[param] = weighted_score
        
        # Total skor
        total_score = sum(weighted_scores.values())
        
        # Apply seasonal factor jika ada
        seasonal_multiplier = 1.0
        if current_month:
            if current_month in self.config['seasonal_factors']['high_risk_months']:
                seasonal_multiplier = self.config['seasonal_factors']['multipliers']['high']
            elif current_month in self.config['seasonal_factors']['moderate_risk_months']:
                seasonal_multiplier = self.config['seasonal_factors']['multipliers']['moderate']
            else:
                seasonal_multiplier = self.config['seasonal_factors']['multipliers']['low']
        
        adjusted_score = min(100, total_score * seasonal_multiplier)
        
        # Tentukan tingkat risiko
        risk_level = self._determine_risk_level(adjusted_score)
        
        return {
            'parameters': scores,
            'total_score': round(total_score, 2),
            'seasonal_multiplier': seasonal_multiplier,
            'adjusted_score': round(adjusted_score, 2),
            'risk_level': risk_level['level'],
            'risk_emoji': risk_level['emoji'],
            'risk_description': risk_level['description'],
            'risk_color': risk_level['color'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _determine_risk_level(self, score: float) -> Dict:
        """Tentukan tingkat risiko berdasarkan skor"""
        for level, config in self.risk_levels.items():
            if config['score_range'][0] <= score <= config['score_range'][1]:
                return {
                    'level': level,
                    'emoji': config['emoji'],
                    'description': config['description'],
                    'color': config['color']
                }
        
        # Default ke BAHAYA jika di luar range
        return {
            'level': 'BAHAYA',
            'emoji': '🔴',
            'description': 'Risiko tinggi, evakuasi segera',
            'color': 'red'
        }
    
    def get_recommendations(self, risk_level: str) -> List[str]:
        """
        Dapatkan rekomendasi tindakan berdasarkan tingkat risiko
        
        Args:
            risk_level: AMAN, WASPADA, atau BAHAYA
        
        Returns:
            List rekomendasi tindakan
        """
        recommendations = {
            'AMAN': [
                '☁️ Kondisi cuaca dalam batas normal',
                '👁️ Tetap waspada terhadap perubahan cuaca',
                '🔧 Lakukan pemeriksaan rutin drainase',
                '🧹 Jaga kebersihan saluran air',
                '📚 Edukasi masyarakat tentang mitigasi bencana'
            ],
            'WASPADA': [
                '📡 Pantau perkembangan cuaca secara berkala',
                '🎒 Siapkan rencana evakuasi dan tas darurat',
                '👀 Perhatikan tanda-tanda longsor (retakan tanah, air keruh)',
                '⛰️ Hindari aktivitas di dekat lereng',
                '💬 Tetap berkomunikasi dengan warga sekitar',
                '🔦 Siapkan penerangan dan alat komunikasi darurat'
            ],
            'BAHAYA': [
                '🚨 Segera evakuasi ke tempat aman yang lebih tinggi',
                '📞 Hubungi pihak berwenang dan tim SAR',
                '🏔️ Jauhi lereng dan tebing',
                '🎒 Bawa tas darurat dan dokumen penting',
                '📻 Pantau informasi dari petugas setempat',
                '👥 Bantu warga yang memerlukan bantuan evakuasi'
            ]
        }
        
        return recommendations.get(risk_level, recommendations['AMAN'])
    
    def export_config(self, filepath: str):
        """Export konfigurasi ke file JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_threshold_info(self, parameter_name: str) -> Dict:
        """Dapatkan informasi threshold untuk parameter tertentu"""
        if parameter_name in self.thresholds:
            return self.thresholds[parameter_name]
        return {}


# Fungsi helper untuk penggunaan cepat
def quick_risk_assessment(rainfall_mm_per_hour: float, 
                          humidity_percent: float,
                          wind_speed_kmh: float = 0,
                          cumulative_3day: float = 0,
                          cumulative_7day: float = 0) -> str:
    """
    Fungsi cepat untuk mendapatkan tingkat risiko
    
    Args:
        rainfall_mm_per_hour: Curah hujan dalam mm/jam
        humidity_percent: Kelembaban dalam persen
        wind_speed_kmh: Kecepatan angin dalam km/jam (opsional)
        cumulative_3day: Akumulasi 3 hari dalam mm (opsional)
        cumulative_7day: Akumulasi 7 hari dalam mm (opsional)
    
    Returns:
        String tingkat risiko: AMAN, WASPADA, atau BAHAYA
    """
    scorer = LandslideRiskScorer()
    result = scorer.calculate_risk_score(
        rainfall_hourly=rainfall_mm_per_hour,
        humidity=humidity_percent,
        wind_speed=wind_speed_kmh,
        cumulative_3day=cumulative_3day,
        cumulative_7day=cumulative_7day,
        current_month=datetime.now().month
    )
    return result['risk_level']


# Demo dan testing
if __name__ == "__main__":
    print("="*80)
    print("LANDSLIDE RISK SCORING SYSTEM")
    print("Desa Petir, Dramaga, Bogor")
    print("="*80)
    
    # Initialize scorer
    scorer = LandslideRiskScorer()
    
    # Test case 1: Kondisi Normal
    print("\n📊 TEST CASE 1: Kondisi Normal")
    print("-" * 60)
    result1 = scorer.calculate_risk_score(
        rainfall_hourly=3,
        cumulative_3day=15,
        cumulative_7day=45,
        humidity=65,
        wind_speed=10,
        current_month=7  # Juli (musim kering)
    )
    
    print(f"Tingkat Risiko: {result1['risk_emoji']} {result1['risk_level']}")
    print(f"Skor Total: {result1['total_score']:.1f}")
    print(f"Skor Adjusted: {result1['adjusted_score']:.1f}")
    print(f"Deskripsi: {result1['risk_description']}")
    
    # Test case 2: Kondisi Waspada
    print("\n\n📊 TEST CASE 2: Kondisi Waspada")
    print("-" * 60)
    result2 = scorer.calculate_risk_score(
        rainfall_hourly=12,
        cumulative_3day=80,
        cumulative_7day=180,
        humidity=82,
        wind_speed=25,
        current_month=11  # November (musim hujan)
    )
    
    print(f"Tingkat Risiko: {result2['risk_emoji']} {result2['risk_level']}")
    print(f"Skor Total: {result2['total_score']:.1f}")
    print(f"Skor Adjusted: {result2['adjusted_score']:.1f}")
    print(f"Deskripsi: {result2['risk_description']}")
    
    # Test case 3: Kondisi Bahaya
    print("\n\n📊 TEST CASE 3: Kondisi Bahaya")
    print("-" * 60)
    result3 = scorer.calculate_risk_score(
        rainfall_hourly=28,
        cumulative_3day=150,
        cumulative_7day=280,
        humidity=93,
        wind_speed=45,
        current_month=12  # Desember (musim hujan)
    )
    
    print(f"Tingkat Risiko: {result3['risk_emoji']} {result3['risk_level']}")
    print(f"Skor Total: {result3['total_score']:.1f}")
    print(f"Skor Adjusted: {result3['adjusted_score']:.1f}")
    print(f"Deskripsi: {result3['risk_description']}")
    
    print("\n" + "="*80)
    print("Rekomendasi Tindakan:")
    print("-" * 60)
    for rec in scorer.get_recommendations(result3['risk_level']):
        print(f"  {rec}")
    
    print("\n" + "="*80)
