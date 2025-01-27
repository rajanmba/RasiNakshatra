from fastapi import FastAPI
from pydantic import BaseModel
import swisseph as swe
from datetime import datetime, timedelta

# Define input data structure for FastAPI
class BirthData(BaseModel):
    dob: str  # Date of birth (e.g., '1990-01-01')
    tob: str  # Time of birth (e.g., '10:30:00')
    latitude: float
    longitude: float
    house_system: str = 'P'  # Optional: Default to Placidus

app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "Welcome to the API!"}

def get_rasi_nakshatra_planets(birthdate, birthtime, latitude, longitude, house_system='P'):
    # The existing code from your function goes here
    
    # Planet names and ephemeris codes
    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE
    }

    # Set the Ayanamsa (precession of the equinoxes)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)  # Use Lahiri Ayanamsa
    
    # Convert birthdate and time to Julian Day
    birth_datetime = datetime.strptime(f"{birthdate} {birthtime}", "%Y-%m-%d %H:%M:%S")
    utc_offset = timedelta(hours=5, minutes=30)
    birth_datetime_utc = birth_datetime - utc_offset

    jd = swe.julday(birth_datetime_utc.year, birth_datetime_utc.month, birth_datetime_utc.day,
                    birth_datetime_utc.hour + birth_datetime_utc.minute / 60.0 + birth_datetime_utc.second / 3600.0)
    
    flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    moon_long, _ = swe.calc_ut(jd, swe.MOON, flag)
    sun_long, _ = swe.calc_ut(jd, swe.SUN, flag)
    # Check if moon_long is a tuple, if so, extract the first element (longitude)

    # Rasi and Nakshatra calculation logic
    rasi_names = ["Mesha", "Vrisha", "Mithuna", "Kataka", "Simha", "Kanya",
                  "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
    if isinstance(moon_long, tuple):
        moon_long = moon_long[0]  # Explicitly use the first element

    rasi_index = int(moon_long // 30) % 12
    rasi = rasi_names[rasi_index]

    nakshatra_deg = moon_long / 13.3333
    nakshatra_index = int(nakshatra_deg)

    nakshatra_names = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purvaphalguni", "Uttaphalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purvashadha", "Uttarasadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purvabhadrapada", "Uttabhadrapada", "Revati"
    ]
    
    nakshatra = nakshatra_names[nakshatra_index]
    pada = int((moon_long % 13.3333) / 3.3333) + 1  # Calculate the Pada number (1 to 4)
    
    # Calculate Ascendant
    ascendant = swe.houses_ex(jd, latitude, longitude, b'P', swe.FLG_SIDEREAL)[0][0]

    planet_degrees = {}
    for planet_name, planet_code in planets.items():
        planet_long, _ = swe.calc_ut(jd, planet_code, flag)
        planet_degrees[planet_name] = planet_long

    return {"rasi": rasi, "nakshatra": nakshatra, "pada": pada, "ascendant": ascendant, "planets": planet_degrees}

@app.post("/get_rasi_nakshatra_planets/")
async def calculate_rasi_nakshatra(data: BirthData):
    results = get_rasi_nakshatra_planets(
        data.dob, data.tob, data.latitude, data.longitude, data.house_system
    )
    return results
