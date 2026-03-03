from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import tempfile
import requests
from timezonefinder import TimezoneFinder

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# API Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
PROKERALA_CLIENT_ID = os.environ.get('PROKERALA_CLIENT_ID')
PROKERALA_CLIENT_SECRET = os.environ.get('PROKERALA_CLIENT_SECRET')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Timezone finder
tf = TimezoneFinder()

# Pydantic Models
class BirthDetailsInput(BaseModel):
    name: str
    date_of_birth: str  # YYYY-MM-DD
    time_of_birth: str  # HH:MM or HH:MM:SS
    place_of_birth: str
    gender: Optional[str] = "unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone_str: Optional[str] = None

class PlaceSearchResult(BaseModel):
    place_name: str
    latitude: float
    longitude: float
    timezone: str
    formatted_address: str

class ChartSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    birth_details: Dict[str, Any]
    chart_data: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # user or assistant
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatInput(BaseModel):
    session_id: str
    message: str

# South Indian Chart Sign Positions (Fixed layout)
# The South Indian chart has fixed positions for each sign
SOUTH_INDIAN_POSITIONS = {
    "Pisces": (0, 0), "Aries": (0, 1), "Taurus": (0, 2), "Gemini": (0, 3),
    "Aquarius": (1, 0), "Cancer": (1, 3),
    "Capricorn": (2, 0), "Leo": (2, 3),
    "Sagittarius": (3, 0), "Scorpio": (3, 1), "Libra": (3, 2), "Virgo": (3, 3)
}

SIGN_ORDER = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

SIGN_NUMBERS = {sign: i+1 for i, sign in enumerate(SIGN_ORDER)}

# Planet abbreviations for chart display
PLANET_ABBREV = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
    "Rahu": "Ra", "Ketu": "Ke", "Ascendant": "As"
}

# Geocoding with OpenStreetMap Nominatim (free, no API key required)
async def geocode_place(place_name: str) -> List[PlaceSearchResult]:
    """Convert place name to coordinates using OpenStreetMap Nominatim API"""
    
    # Use OpenStreetMap Nominatim (free, no API key needed)
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "limit": 5,
        "addressdetails": 1
    }
    headers = {
        "User-Agent": "ParasaraAstroAI/1.0"  # Required by Nominatim
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if not data:
            logger.info(f"No results found for: {place_name}")
            return []
        
        results = []
        for result in data[:5]:
            lat = float(result.get("lat", 0))
            lon = float(result.get("lon", 0))
            tz = tf.timezone_at(lat=lat, lng=lon) or "UTC"
            
            # Build formatted address
            display_name = result.get("display_name", place_name)
            
            results.append(PlaceSearchResult(
                place_name=display_name,
                latitude=lat,
                longitude=lon,
                timezone=tz,
                formatted_address=display_name
            ))
        return results
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        # Return empty list instead of raising exception for better UX
        return []

# Astrology Calculation using Prokerala API
def calculate_chart(birth_details: BirthDetailsInput, lat: float, lon: float, tz: str) -> Dict[str, Any]:
    """Calculate Vedic astrology chart using Prokerala API with Lahiri ayanamsha"""
    from prokerala_api import ApiClient
    from datetime import datetime as dt
    import pytz
    
    try:
        # Initialize Prokerala API client
        prokerala_client = ApiClient(PROKERALA_CLIENT_ID, PROKERALA_CLIENT_SECRET)
        
        # Parse date and time
        dob_parts = birth_details.date_of_birth.split("-")
        year = int(dob_parts[0])
        month = int(dob_parts[1])
        day = int(dob_parts[2])
        
        time_parts = birth_details.time_of_birth.split(":")
        hour = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(time_parts[2]) if len(time_parts) > 2 else 0
        
        # Get timezone offset
        try:
            tz_obj = pytz.timezone(tz)
            birth_dt = dt(year, month, day, hour, minutes, seconds)
            localized_dt = tz_obj.localize(birth_dt)
            tz_offset = localized_dt.strftime('%z')
            tz_offset_formatted = f"{tz_offset[:3]}:{tz_offset[3:]}"
        except:
            tz_offset_formatted = "+05:30"  # Default to IST
        
        # Format datetime for Prokerala API
        datetime_str = f"{year}-{month:02d}-{day:02d}T{hour:02d}:{minutes:02d}:{seconds:02d}{tz_offset_formatted}"
        coordinates = f"{lat},{lon}"
        
        # API parameters
        params = {
            'ayanamsa': 1,  # Lahiri ayanamsha
            'coordinates': coordinates,
            'datetime': datetime_str
        }
        
        # Get planet positions
        planet_result = prokerala_client.get('v2/astrology/planet-position', params)
        planet_data = planet_result.get('data', {}).get('planet_position', [])
        
        # Get advanced kundli data (nakshatra, dasha, yogas)
        kundli_result = prokerala_client.get('v2/astrology/kundli/advanced', params)
        kundli_data = kundli_result.get('data', {})
        
        # Build chart data structure
        chart_data = {
            "Birthdata": {
                "Name": birth_details.name,
                "Gender": birth_details.gender or "unknown",
                "Year": year,
                "Month": month,
                "Day": day,
                "Hour": hour,
                "Minute": minutes,
                "Place": birth_details.place_of_birth,
                "Latitude": lat,
                "Longitude": lon,
                "Timezone": tz
            },
            "D1": {
                "Planets": {},
                "Houses": {}
            },
            "Dasha": {},
            "Yogas": [],
            "MangalDosha": {},
            "NakshatraDetails": {}
        }
        
        # Map Prokerala sign names to standard abbreviations
        sign_map = {
            "Mesha": "Aries", "Vrishabha": "Taurus", "Mithuna": "Gemini", 
            "Karka": "Cancer", "Simha": "Leo", "Kanya": "Virgo",
            "Tula": "Libra", "Vrischika": "Scorpio", "Dhanu": "Sagittarius",
            "Makara": "Capricorn", "Kumbha": "Aquarius", "Meena": "Pisces"
        }
        
        # Process planet positions
        ascendant_sign = None
        for planet in planet_data:
            name = planet.get('name')
            rasi = planet.get('rasi', {})
            sign_name = rasi.get('name', '')
            
            # Map to English sign name
            english_sign = sign_map.get(sign_name, sign_name)
            
            planet_info = {
                "Sign": english_sign,
                "Degree": round(planet.get('degree', 0), 2),
                "House": planet.get('position', 1),
                "Retrograde": planet.get('is_retrograde', False),
                "Longitude": round(planet.get('longitude', 0), 2)
            }
            
            chart_data["D1"]["Planets"][name] = planet_info
            
            if name == "Ascendant":
                ascendant_sign = english_sign
        
        # Build houses based on ascendant position
        if ascendant_sign:
            sign_order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            asc_idx = sign_order.index(ascendant_sign) if ascendant_sign in sign_order else 0
            
            for i in range(12):
                house_sign = sign_order[(asc_idx + i) % 12]
                chart_data["D1"]["Houses"][f"House{i+1}"] = {
                    "Sign": house_sign,
                    "Number": i + 1
                }
        
        # Process nakshatra details
        nakshatra_details = kundli_data.get('nakshatra_details', {})
        if nakshatra_details:
            nakshatra = nakshatra_details.get('nakshatra', {})
            chandra_rasi = nakshatra_details.get('chandra_rasi', {})
            soorya_rasi = nakshatra_details.get('soorya_rasi', {})
            
            chart_data["NakshatraDetails"] = {
                "nakshatra": nakshatra.get('name', ''),
                "pada": nakshatra.get('pada', 1),
                "lord": nakshatra.get('lord', {}).get('name', ''),
                "moon_sign": sign_map.get(chandra_rasi.get('name', ''), chandra_rasi.get('name', '')),
                "sun_sign": sign_map.get(soorya_rasi.get('name', ''), soorya_rasi.get('name', '')),
                "additional_info": nakshatra_details.get('additional_info', {})
            }
        
        # Process dasha periods
        dasha_periods = kundli_data.get('dasha_periods', [])
        dasha_balance = kundli_data.get('dasha_balance', {})
        
        if dasha_periods:
            maha_dasha = {}
            current_dasha = ""
            current_time = dt.now(pytz.UTC)
            
            for dasha in dasha_periods:
                lord_name = dasha.get('name', '')
                start_str = dasha.get('start', '')
                end_str = dasha.get('end', '')
                
                maha_dasha[lord_name] = {
                    "start": start_str,
                    "end": end_str,
                    "antardasha": dasha.get('antardasha', [])
                }
                
                # Check if this is current dasha
                try:
                    start_dt = dt.fromisoformat(start_str.replace('+05:30', '+0530'))
                    end_dt = dt.fromisoformat(end_str.replace('+05:30', '+0530'))
                    if start_dt <= current_time <= end_dt:
                        current_dasha = lord_name
                except:
                    pass
            
            chart_data["Dasha"] = {
                "MahaDasha": maha_dasha,
                "CurrentDasha": current_dasha,
                "DashaBalance": dasha_balance
            }
        
        # Process yogas
        yoga_details = kundli_data.get('yoga_details', [])
        present_yogas = []
        for yoga_group in yoga_details:
            for yoga in yoga_group.get('yoga_list', []):
                if yoga.get('has_yoga', False):
                    present_yogas.append({
                        "name": yoga.get('name', ''),
                        "description": yoga.get('description', '')
                    })
        chart_data["Yogas"] = present_yogas
        
        # Process Mangal Dosha
        mangal_dosha = kundli_data.get('mangal_dosha', {})
        chart_data["MangalDosha"] = {
            "has_dosha": mangal_dosha.get('has_dosha', False),
            "description": mangal_dosha.get('description', ''),
            "exceptions": mangal_dosha.get('exceptions', []),
            "remedies": mangal_dosha.get('remedies', [])
        }
        
        return chart_data
                
    except Exception as e:
        logger.error(f"Chart calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Chart calculation failed: {str(e)}")

def get_house_from_position(pos: float, subject) -> int:
    """Get house number from absolute position"""
    asc_pos = subject.first_house.position if hasattr(subject.first_house, 'position') else 0
    relative_pos = (pos - asc_pos) % 360
    return int(relative_pos / 30) + 1

def get_nakshatra(degree: float) -> str:
    """Get nakshatra name from degree position within a sign"""
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    # Each nakshatra spans 13°20' (13.333...)
    nakshatra_span = 360 / 27
    nakshatra_idx = int(degree / nakshatra_span) % 27
    return nakshatras[nakshatra_idx]

def get_pada(degree: float) -> int:
    """Get pada (quarter) of nakshatra"""
    nakshatra_span = 360 / 27
    pada_span = nakshatra_span / 4
    pos_in_nakshatra = degree % nakshatra_span
    return int(pos_in_nakshatra / pada_span) + 1

def calculate_vimshottari_dasha(moon_degree: float, birth_year: int, birth_month: int, birth_day: int) -> Dict:
    """Calculate Vimshottari Dasha periods based on Moon's nakshatra"""
    from datetime import datetime, timedelta
    
    # Dasha lords and their periods in years
    dasha_lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    dasha_years = [7, 20, 6, 10, 7, 18, 16, 19, 17]  # Total = 120 years
    
    # Get nakshatra index (0-26)
    nakshatra_span = 360 / 27
    nakshatra_idx = int(moon_degree / nakshatra_span) % 27
    
    # Each nakshatra is ruled by a planet in sequence
    nakshatra_lords = [
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
    ]
    
    birth_lord = nakshatra_lords[nakshatra_idx]
    birth_lord_idx = dasha_lords.index(birth_lord)
    
    # Calculate balance of dasha at birth
    pos_in_nakshatra = moon_degree % nakshatra_span
    balance_fraction = 1 - (pos_in_nakshatra / nakshatra_span)
    
    birth_date = datetime(birth_year, birth_month, birth_day)
    current_date = datetime.now()
    
    # Build Maha Dasha periods
    maha_dasha = {}
    dasha_start = birth_date
    
    # Start with birth dasha (with balance)
    first_dasha_years = dasha_years[birth_lord_idx] * balance_fraction
    dasha_end = dasha_start + timedelta(days=first_dasha_years * 365.25)
    maha_dasha[birth_lord] = {
        "start": dasha_start.strftime("%Y-%m-%d"),
        "end": dasha_end.strftime("%Y-%m-%d"),
        "years": round(first_dasha_years, 2)
    }
    dasha_start = dasha_end
    
    # Add remaining dashas
    for i in range(1, 9):
        lord_idx = (birth_lord_idx + i) % 9
        lord = dasha_lords[lord_idx]
        years = dasha_years[lord_idx]
        dasha_end = dasha_start + timedelta(days=years * 365.25)
        maha_dasha[lord] = {
            "start": dasha_start.strftime("%Y-%m-%d"),
            "end": dasha_end.strftime("%Y-%m-%d"),
            "years": years
        }
        dasha_start = dasha_end
    
    # Find current dasha
    current_dasha = ""
    for lord, period in maha_dasha.items():
        start = datetime.strptime(period["start"], "%Y-%m-%d")
        end = datetime.strptime(period["end"], "%Y-%m-%d")
        if start <= current_date <= end:
            current_dasha = lord
            break
    
    return {
        "MahaDasha": maha_dasha,
        "CurrentDasha": current_dasha,
        "DashaBalance": f"{round(first_dasha_years, 2)} years of {birth_lord}"
    }

def process_chart_data(raw_chart: Dict[str, Any]) -> Dict[str, Any]:
    """Process Prokerala API output into structured format for frontend"""
    processed = {
        "birth_info": {},
        "ascendant": {},
        "planets": [],
        "houses": [],
        "dasha": {},
        "nakshatra": {},
        "yogas": [],
        "chart_layout": {},
        "mangal_dosha": {}
    }
    
    try:
        # Extract birth info
        if "Birthdata" in raw_chart:
            bd = raw_chart["Birthdata"]
            processed["birth_info"] = {
                "name": bd.get("Name", ""),
                "gender": bd.get("Gender", ""),
                "date": f"{bd.get('Year', '')}-{bd.get('Month', ''):02d}-{bd.get('Day', ''):02d}" if bd.get('Year') else "",
                "time": f"{bd.get('Hour', 0):02d}:{bd.get('Minute', 0):02d}:00",
                "place": bd.get("Place", ""),
                "latitude": bd.get("Latitude", 0),
                "longitude": bd.get("Longitude", 0),
                "timezone": bd.get("Timezone", "")
            }
        
        # Extract planetary positions
        planets_data = raw_chart.get("D1", {}).get("Planets", {})
        house_planets = {i: [] for i in range(1, 13)}
        
        for planet_name, planet_info in planets_data.items():
            if isinstance(planet_info, dict):
                sign = planet_info.get("Sign", "")
                house = planet_info.get("House", 1)
                degree = planet_info.get("Degree", 0)
                retro = planet_info.get("Retrograde", False)
                longitude = planet_info.get("Longitude", 0)
                
                # Calculate nakshatra from longitude
                nakshatra = get_nakshatra_from_longitude(longitude)
                pada = get_pada_from_longitude(longitude)
                
                planet_entry = {
                    "name": planet_name,
                    "sign": sign,
                    "house": house,
                    "degree": round(degree, 2) if degree else 0,
                    "nakshatra": nakshatra,
                    "pada": pada,
                    "retrograde": retro,
                    "abbrev": PLANET_ABBREV.get(planet_name, planet_name[:2])
                }
                processed["planets"].append(planet_entry)
                
                if house and 1 <= house <= 12:
                    house_planets[house].append(planet_entry)
        
        # Extract Ascendant
        asc_info = planets_data.get("Ascendant", {})
        if asc_info:
            asc_longitude = asc_info.get("Longitude", 0)
            processed["ascendant"] = {
                "sign": asc_info.get("Sign", ""),
                "degree": round(asc_info.get("Degree", 0), 2),
                "nakshatra": get_nakshatra_from_longitude(asc_longitude),
                "pada": get_pada_from_longitude(asc_longitude)
            }
        
        # Extract nakshatra details from Prokerala
        nakshatra_details = raw_chart.get("NakshatraDetails", {})
        if nakshatra_details:
            processed["nakshatra"] = {
                "moon_sign": nakshatra_details.get("moon_sign", ""),
                "nakshatra": nakshatra_details.get("nakshatra", ""),
                "pada": nakshatra_details.get("pada", 1),
                "lord": nakshatra_details.get("lord", ""),
                "sun_sign": nakshatra_details.get("sun_sign", ""),
                "additional_info": nakshatra_details.get("additional_info", {})
            }
        
        # Extract Dasha information
        dasha_info = raw_chart.get("Dasha", {})
        if dasha_info:
            processed["dasha"] = {
                "maha_dasha": dasha_info.get("MahaDasha", {}),
                "current_dasha": dasha_info.get("CurrentDasha", ""),
                "dasha_balance": dasha_info.get("DashaBalance", {})
            }
        
        # Extract Yogas
        yogas = raw_chart.get("Yogas", [])
        processed["yogas"] = yogas
        
        # Extract Mangal Dosha
        mangal_dosha = raw_chart.get("MangalDosha", {})
        processed["mangal_dosha"] = mangal_dosha
        
        # Build chart layout for South Indian style
        asc_sign = processed["ascendant"].get("sign", "Aries")
        
        # Standard sign order
        sign_order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        asc_index = sign_order.index(asc_sign) if asc_sign in sign_order else 0
        
        chart_layout = {}
        for i in range(12):
            sign = sign_order[(asc_index + i) % 12]
            house_num = i + 1
            position = SOUTH_INDIAN_POSITIONS.get(sign, (0, 0))
            
            planets_in_house = []
            for p in processed["planets"]:
                if p.get("sign") == sign:
                    planets_in_house.append(p["abbrev"])
            
            chart_layout[sign] = {
                "house": house_num,
                "position": position,
                "planets": planets_in_house,
                "sign_number": SIGN_NUMBERS.get(sign, 1)
            }
        
        processed["chart_layout"] = chart_layout
        
        # Build houses list
        houses_data = raw_chart.get("D1", {}).get("Houses", {})
        for i in range(1, 13):
            house_key = f"House{i}"
            house_info = houses_data.get(house_key, {})
            processed["houses"].append({
                "number": i,
                "sign": house_info.get("Sign", ""),
                "planets": [p["name"] for p in house_planets.get(i, [])]
            })
            
    except Exception as e:
        logger.error(f"Error processing chart data: {e}")
    
    return processed

def get_nakshatra_from_longitude(longitude: float) -> str:
    """Get nakshatra name from absolute longitude"""
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    nakshatra_span = 360 / 27  # 13.333... degrees
    nakshatra_idx = int(longitude / nakshatra_span) % 27
    return nakshatras[nakshatra_idx]

def get_pada_from_longitude(longitude: float) -> int:
    """Get pada from absolute longitude"""
    nakshatra_span = 360 / 27
    pada_span = nakshatra_span / 4
    pos_in_nakshatra = longitude % nakshatra_span
    return int(pos_in_nakshatra / pada_span) + 1

# OpenAI Integration for Interpretation
async def generate_prediction(chart_data: Dict[str, Any], birth_name: str) -> str:
    """Generate astrological prediction using OpenAI GPT-5.2"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    system_prompt = """You are Parasara Astro AI, an expert Vedic astrologer providing insightful and personalized readings.

IMPORTANT RULES:
1. ONLY use the chart data provided - never invent or calculate positions
2. If data is missing, acknowledge it gracefully
3. Be insightful but not overly mystical
4. Provide practical, actionable insights
5. Always refer to specific placements from the provided data
6. Use proper Vedic astrology terminology
7. Keep predictions balanced - mention both opportunities and challenges

Structure your prediction with these sections:
- Personality & Core Nature (based on Ascendant and Moon)
- Career & Professional Life
- Relationships & Family
- Finances & Material Life
- Current Period Analysis (based on Dasha)
- Key Life Themes & Advice"""

    chart_summary = json.dumps(chart_data, indent=2)
    
    user_prompt = f"""Please provide a comprehensive Vedic astrology reading for {birth_name}.

Here is the complete chart data computed from their birth details:

{chart_summary}

Provide a personalized prediction covering all major life areas based ONLY on this computed data."""

    try:
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=f"prediction_{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=user_prompt))
        return response
    except Exception as e:
        logger.error(f"OpenAI prediction error: {e}")
        return f"Unable to generate detailed prediction at this time. Please review your chart data directly. Error: {str(e)}"

async def chat_with_astrologer(session_id: str, message: str, chart_data: Dict[str, Any]) -> str:
    """Chat with AI astrologer about the chart"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    # Get chat history from database
    history = await db.chat_messages.find(
        {"session_id": session_id}, 
        {"_id": 0}
    ).sort("timestamp", 1).to_list(50)
    
    system_prompt = f"""You are Parasara Astro AI, a knowledgeable Vedic astrology assistant.

The user has generated their birth chart with the following data:
{json.dumps(chart_data, indent=2)}

CRITICAL RULES:
1. ONLY answer questions using the chart data above
2. NEVER calculate or invent planetary positions, dashas, or any astrological data
3. If asked about something not in the data, say "This information is not available in your chart data"
4. Always reference specific placements from the provided data
5. Be helpful, insightful, and conversational
6. Use proper Vedic astrology terminology
7. Explain concepts clearly when asked"""

    # Build conversation context
    conversation_context = ""
    for msg in history[-10:]:  # Last 10 messages for context
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation_context += f"{role}: {msg['content']}\n\n"
    
    full_prompt = f"""Previous conversation:
{conversation_context}

User's new question: {message}

Please respond helpfully based only on the chart data provided."""

    try:
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=f"chat_{session_id}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=full_prompt))
        return response
    except Exception as e:
        logger.error(f"OpenAI chat error: {e}")
        return f"I apologize, but I'm having trouble responding right now. Please try again. Error: {str(e)}"

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Parasara Astro AI API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.post("/geocode")
async def search_place(place_name: str):
    """Search for a place and return coordinates"""
    results = await geocode_place(place_name)
    return {"results": [r.model_dump() for r in results]}

@api_router.post("/chart/generate")
async def generate_chart(birth_details: BirthDetailsInput):
    """Generate Vedic astrology chart from birth details"""
    
    # Get coordinates if not provided
    lat = birth_details.latitude
    lon = birth_details.longitude
    tz = birth_details.timezone_str
    
    if lat is None or lon is None:
        # Geocode the place
        places = await geocode_place(birth_details.place_of_birth)
        if not places:
            raise HTTPException(status_code=400, detail="Could not find the specified place. Please provide latitude and longitude manually.")
        
        place = places[0]
        lat = place.latitude
        lon = place.longitude
        tz = place.timezone
        birth_details.place_of_birth = place.formatted_address
    
    if not tz:
        tz = tf.timezone_at(lat=lat, lng=lon) or "UTC"
    
    # Calculate chart using jyotishyamitra
    raw_chart = calculate_chart(birth_details, lat, lon, tz)
    
    # Process into structured format
    processed_chart = process_chart_data(raw_chart)
    processed_chart["birth_info"]["place"] = birth_details.place_of_birth
    processed_chart["birth_info"]["latitude"] = lat
    processed_chart["birth_info"]["longitude"] = lon
    processed_chart["birth_info"]["timezone"] = tz
    processed_chart["raw_data"] = raw_chart
    
    # Generate prediction
    prediction = await generate_prediction(processed_chart, birth_details.name)
    
    # Create session
    session = ChartSession(
        name=birth_details.name,
        birth_details={
            "name": birth_details.name,
            "date_of_birth": birth_details.date_of_birth,
            "time_of_birth": birth_details.time_of_birth,
            "place_of_birth": birth_details.place_of_birth,
            "gender": birth_details.gender,
            "latitude": lat,
            "longitude": lon,
            "timezone": tz
        },
        chart_data=processed_chart
    )
    
    # Save to database
    session_doc = session.model_dump()
    await db.chart_sessions.insert_one(session_doc)
    
    return {
        "session_id": session.id,
        "chart_data": processed_chart,
        "prediction": prediction,
        "birth_details": session.birth_details,
        "created_at": session.created_at
    }

@api_router.get("/chart/sessions")
async def get_sessions():
    """Get all chart sessions"""
    sessions = await db.chart_sessions.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"sessions": sessions}

@api_router.get("/chart/session/{session_id}")
async def get_session(session_id: str):
    """Get a specific chart session"""
    session = await db.chart_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get chat history for this session
    messages = await db.chat_messages.find(
        {"session_id": session_id}, 
        {"_id": 0}
    ).sort("timestamp", 1).to_list(100)
    
    return {"session": session, "messages": messages}

@api_router.post("/chat")
async def chat_endpoint(chat_input: ChatInput):
    """Chat with astrologer about a chart"""
    
    # Get the session
    session = await db.chart_sessions.find_one({"id": chat_input.session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user message
    user_msg = ChatMessage(
        session_id=chat_input.session_id,
        role="user",
        content=chat_input.message
    )
    await db.chat_messages.insert_one(user_msg.model_dump())
    
    # Get AI response
    response = await chat_with_astrologer(
        chat_input.session_id,
        chat_input.message,
        session["chart_data"]
    )
    
    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=chat_input.session_id,
        role="assistant",
        content=response
    )
    await db.chat_messages.insert_one(assistant_msg.model_dump())
    
    return {
        "response": response,
        "message_id": assistant_msg.id,
        "timestamp": assistant_msg.timestamp
    }

@api_router.delete("/chart/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chart session and its messages"""
    await db.chart_sessions.delete_one({"id": session_id})
    await db.chat_messages.delete_many({"session_id": session_id})
    return {"status": "deleted", "session_id": session_id}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
