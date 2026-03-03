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

# Astrology Calculation using jyotishyamitra
def calculate_chart(birth_details: BirthDetailsInput, lat: float, lon: float, tz: str) -> Dict[str, Any]:
    """Calculate Vedic astrology chart using jyotishyamitra"""
    import jyotishyamitra as jsm
    
    try:
        # Clear any previous data
        jsm.clear_birthdata()
        
        # Parse date and time
        dob_parts = birth_details.date_of_birth.split("-")
        year = int(dob_parts[0])
        month = int(dob_parts[1])
        day = int(dob_parts[2])
        
        time_parts = birth_details.time_of_birth.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0
        
        # Input birth data
        jsm.input_birthdata(name=birth_details.name)
        jsm.input_birthdata(gender=birth_details.gender or "unknown")
        jsm.input_birthdata(year=year, month=month, day=day)
        jsm.input_birthdata(hour=hour, minute=minute, second=second)
        jsm.input_birthdata(latitude=lat, longitude=lon)
        jsm.input_birthdata(timezone=tz)
        
        # Get birthdata
        birthdata = jsm.get_birthdata()
        
        # Create temp output file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = tmpdir
            output_filename = "astro_output"
            
            status = jsm.set_output(path=output_path, filename=output_filename)
            if status != "SUCCESS":
                logger.error(f"Failed to set output path: {status}")
                raise Exception(f"Output path error: {status}")
            
            # Generate astrological data
            jsm.generate_astrologicalData(birthdata)
            
            # Read the output JSON
            output_file = os.path.join(output_path, f"{output_filename}.json")
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    chart_data = json.load(f)
                return chart_data
            else:
                logger.error("Output file not generated")
                raise Exception("Failed to generate chart data")
                
    except Exception as e:
        logger.error(f"Chart calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Chart calculation failed: {str(e)}")

def process_chart_data(raw_chart: Dict[str, Any]) -> Dict[str, Any]:
    """Process raw jyotishyamitra output into structured format"""
    processed = {
        "birth_info": {},
        "ascendant": {},
        "planets": [],
        "houses": [],
        "dasha": {},
        "nakshatra": {},
        "yogas": [],
        "chart_layout": {}
    }
    
    try:
        # Extract birth info
        if "Birthdata" in raw_chart:
            bd = raw_chart["Birthdata"]
            processed["birth_info"] = {
                "name": bd.get("Name", ""),
                "gender": bd.get("Gender", ""),
                "date": f"{bd.get('Year', '')}-{bd.get('Month', ''):02d}-{bd.get('Day', ''):02d}" if bd.get('Year') else "",
                "time": f"{bd.get('Hour', 0):02d}:{bd.get('Minute', 0):02d}:{bd.get('Second', 0):02d}",
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
                nakshatra = planet_info.get("Nakshatra", "")
                pada = planet_info.get("Pada", 1)
                retro = planet_info.get("Retrograde", False)
                
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
            processed["ascendant"] = {
                "sign": asc_info.get("Sign", ""),
                "degree": round(asc_info.get("Degree", 0), 2),
                "nakshatra": asc_info.get("Nakshatra", ""),
                "pada": asc_info.get("Pada", 1)
            }
        
        # Extract Moon sign (Rasi)
        moon_info = planets_data.get("Moon", {})
        if moon_info:
            processed["nakshatra"] = {
                "moon_sign": moon_info.get("Sign", ""),
                "nakshatra": moon_info.get("Nakshatra", ""),
                "pada": moon_info.get("Pada", 1)
            }
        
        # Extract Dasha information
        dasha_info = raw_chart.get("Dasha", {})
        if dasha_info:
            processed["dasha"] = {
                "maha_dasha": dasha_info.get("MahaDasha", {}),
                "antar_dasha": dasha_info.get("AntarDasha", {}),
                "current_dasha": dasha_info.get("CurrentDasha", ""),
                "dasha_balance": dasha_info.get("DashaBalance", "")
            }
        
        # Build chart layout for South Indian style
        asc_sign = processed["ascendant"].get("sign", "Aries")
        asc_index = SIGN_ORDER.index(asc_sign) if asc_sign in SIGN_ORDER else 0
        
        chart_layout = {}
        for i in range(12):
            sign = SIGN_ORDER[(asc_index + i) % 12]
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
        
        # Extract houses
        houses_data = raw_chart.get("D1", {}).get("Houses", {})
        for i in range(1, 13):
            house_key = f"House{i}"
            house_info = houses_data.get(house_key, {})
            processed["houses"].append({
                "number": i,
                "sign": house_info.get("Sign", ""),
                "degree": house_info.get("Degree", 0),
                "planets": [p["name"] for p in house_planets.get(i, [])]
            })
        
        # Extract yogas if available
        yogas_data = raw_chart.get("Yogas", [])
        if yogas_data:
            processed["yogas"] = yogas_data
            
    except Exception as e:
        logger.error(f"Error processing chart data: {e}")
    
    return processed

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
