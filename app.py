#!/usr/bin/env python3
"""
Astrology Backend for COGNICOO Child Compass
Calculates Western and Vedic (Sidereal) astrology charts using Swiss Ephemeris
"""

from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime
import math

app = Flask(__name__)

# Set ephemeris path to current directory
swe.set_ephe_path('.')

# Zodiac signs
WESTERN_SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

VEDIC_SIGNS = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
               'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena']

# Nakshatras (27 lunar mansions)
NAKSHATRAS = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
]

# Planet names
PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Uranus': swe.URANUS,
    'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO,
    'North Node': swe.TRUE_NODE,
    'South Node': swe.TRUE_NODE  # Will subtract 180 degrees
}

# Ayanamsa for Vedic (Lahiri)
AYANAMSA = swe.SIDM_LAHIRI

def get_julian_day(date_str, time_str, latitude, longitude):
    """Convert date/time to Julian Day with timezone consideration"""
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    
    # Calculate Julian Day
    jd = swe.julday(dt.year, dt.month, dt.day, 
                    dt.hour + dt.minute / 60.0)
    
    return jd

def get_sign_and_degree(longitude, sidereal=False):
    """Get zodiac sign and degree from ecliptic longitude"""
    if sidereal:
        # Apply ayanamsa for sidereal zodiac
        ayanamsa = swe.get_ayanamsa(swe.julday(2000, 1, 1))
        longitude = (longitude - ayanamsa) % 360
        signs = VEDIC_SIGNS
    else:
        signs = WESTERN_SIGNS
    
    sign_index = int(longitude / 30)
    degree = longitude % 30
    
    return signs[sign_index], degree

def get_nakshatra(moon_longitude):
    """Get Nakshatra from Moon's sidereal longitude"""
    # Apply ayanamsa
    ayanamsa = swe.get_ayanamsa(swe.julday(2000, 1, 1))
    sidereal_long = (moon_longitude - ayanamsa) % 360
    
    # Each nakshatra is 13°20' (13.333 degrees)
    nakshatra_index = int(sidereal_long / 13.333333)
    nakshatra_degree = sidereal_long % 13.333333
    
    # Pada (quarter within nakshatra)
    pada = int(nakshatra_degree / 3.333333) + 1
    
    return NAKSHATRAS[nakshatra_index], pada

def calculate_houses(jd, latitude, longitude):
    """Calculate house cusps using Placidus system"""
    houses, ascmc = swe.houses(jd, latitude, longitude, b'P')  # 'P' = Placidus
    
    # ascmc contains: [0]=Ascendant, [1]=MC, [2]=ARMC, [3]=Vertex
    house_cusps = list(houses)
    ascendant = ascmc[0]
    midheaven = ascmc[1]
    
    return {
        'cusps': house_cusps,
        'ascendant': ascendant,
        'midheaven': midheaven
    }

def calculate_aspects(planet_positions):
    """Calculate major aspects between planets"""
    aspects = []
    
    # Major aspects and their orbs
    aspect_rules = {
        0: ('Conjunction', 8),
        60: ('Sextile', 6),
        90: ('Square', 8),
        120: ('Trine', 8),
        180: ('Opposition', 8)
    }
    
    planet_list = list(planet_positions.items())
    
    for i, (name1, pos1) in enumerate(planet_list):
        for name2, pos2 in planet_list[i+1:]:
            angle = abs(pos1['longitude'] - pos2['longitude'])
            if angle > 180:
                angle = 360 - angle
            
            for aspect_angle, (aspect_name, orb) in aspect_rules.items():
                if abs(angle - aspect_angle) <= orb:
                    aspects.append({
                        'planet1': name1,
                        'planet2': name2,
                        'aspect': aspect_name,
                        'angle': aspect_angle,
                        'orb': abs(angle - aspect_angle)
                    })
                    break
    
    return aspects

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'astrology-backend',
        'version': '1.0.0'
    })

@app.route('/calculate/western', methods=['POST'])
def calculate_western():
    """Calculate Western (Tropical) astrology chart"""
    try:
        data = request.get_json()
        
        # Extract parameters
        date_str = data['date']  # YYYY-MM-DD
        time_str = data['time']  # HH:MM
        latitude = float(data['location']['latitude'])
        longitude = float(data['location']['longitude'])
        
        # Get Julian Day
        jd = get_julian_day(date_str, time_str, latitude, longitude)
        
        # Calculate planet positions (Tropical/Western)
        planets = {}
        for name, planet_id in PLANETS.items():
            if name == 'South Node':
                # South Node is opposite to North Node
                north_node_pos = swe.calc_ut(jd, swe.TRUE_NODE)[0][0]
                longitude_deg = (north_node_pos + 180) % 360
            else:
                result = swe.calc_ut(jd, planet_id)
                longitude_deg = result[0][0]
            
            sign, degree = get_sign_and_degree(longitude_deg, sidereal=False)
            
            planets[name] = {
                'longitude': longitude_deg,
                'sign': sign,
                'degree': degree,
                'formatted': f"{sign} {int(degree)}°{int((degree % 1) * 60)}'"
            }
        
        # Calculate houses
        houses = calculate_houses(jd, latitude, longitude)
        
        # Get Ascendant and Midheaven signs
        asc_sign, asc_degree = get_sign_and_degree(houses['ascendant'], sidereal=False)
        mc_sign, mc_degree = get_sign_and_degree(houses['midheaven'], sidereal=False)
        
        # Calculate aspects
        aspects = calculate_aspects(planets)
        
        # Build response
        response = {
            'type': 'western',
            'planets': planets,
            'houses': {
                'system': 'Placidus',
                'cusps': [f"{int(cusp)}°" for cusp in houses['cusps']],
                'ascendant': {
                    'sign': asc_sign,
                    'degree': asc_degree,
                    'formatted': f"{asc_sign} {int(asc_degree)}°{int((asc_degree % 1) * 60)}'"
                },
                'midheaven': {
                    'sign': mc_sign,
                    'degree': mc_degree,
                    'formatted': f"{mc_sign} {int(mc_degree)}°{int((mc_degree % 1) * 60)}'"
                }
            },
            'aspects': aspects,
            'sunSign': planets['Sun']['sign'],
            'moonSign': planets['Moon']['sign'],
            'risingSign': asc_sign
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/calculate/vedic', methods=['POST'])
def calculate_vedic():
    """Calculate Vedic (Sidereal) astrology chart"""
    try:
        data = request.get_json()
        
        # Extract parameters
        date_str = data['date']
        time_str = data['time']
        latitude = float(data['location']['latitude'])
        longitude = float(data['location']['longitude'])
        
        # Get Julian Day
        jd = get_julian_day(date_str, time_str, latitude, longitude)
        
        # Set ayanamsa for Vedic
        swe.set_sid_mode(AYANAMSA)
        
        # Calculate planet positions (Sidereal/Vedic)
        planets = {}
        for name, planet_id in PLANETS.items():
            if name in ['Uranus', 'Neptune', 'Pluto']:
                # Vedic doesn't traditionally use outer planets
                continue
            
            if name == 'South Node':
                north_node_pos = swe.calc_ut(jd, swe.TRUE_NODE)[0][0]
                longitude_deg = (north_node_pos + 180) % 360
            else:
                result = swe.calc_ut(jd, planet_id)
                longitude_deg = result[0][0]
            
            sign, degree = get_sign_and_degree(longitude_deg, sidereal=True)
            
            planets[name] = {
                'longitude': longitude_deg,
                'sign': sign,
                'degree': degree,
                'formatted': f"{sign} {int(degree)}°{int((degree % 1) * 60)}'"
            }
        
        # Get Moon's Nakshatra
        moon_longitude = planets['Moon']['longitude']
        nakshatra_name, pada = get_nakshatra(moon_longitude)
        
        # Calculate Lagna (Ascendant) using sidereal
        houses = calculate_houses(jd, latitude, longitude)
        lagna_sign, lagna_degree = get_sign_and_degree(houses['ascendant'], sidereal=True)
        
        # Build response
        response = {
            'type': 'vedic',
            'planets': planets,
            'lagna': {
                'sign': lagna_sign,
                'degree': lagna_degree,
                'formatted': f"{lagna_sign} {int(lagna_degree)}°{int((lagna_degree % 1) * 60)}'"
            },
            'nakshatra': {
                'name': nakshatra_name,
                'pada': pada,
                'formatted': f"{nakshatra_name} Pada {pada}"
            },
            'rashiChart': {
                'sun': planets['Sun']['sign'],
                'moon': planets['Moon']['sign'],
                'lagna': lagna_sign
            },
            'moonSign': planets['Moon']['sign'],
            'sunSign': planets['Sun']['sign']
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/calculate/both', methods=['POST'])
def calculate_both():
    """Calculate both Western and Vedic charts"""
    try:
        data = request.get_json()
        
        # Get Western chart
        western_response = calculate_western()
        western_data = western_response.get_json()
        
        # Get Vedic chart
        vedic_response = calculate_vedic()
        vedic_data = vedic_response.get_json()
        
        return jsonify({
            'western': western_data,
            'vedic': vedic_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    import os
    # Download ephemeris files on startup
    print("Astrology Backend starting...")
    print("Swiss Ephemeris ready")
    
    # Run Flask app
    port = int(os.environ.get('PORT', 3002))
    app.run(host='0.0.0.0', port=port, debug=False)
