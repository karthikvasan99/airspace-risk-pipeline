import os
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
DB_URI = os.getenv("SUPABASE_URI")

def get_live_flights():
    print("Fetching live air traffic from OpenSky...")
    
    # Bounding box for the Northeast US (Roughly DC to Boston)
    # lamin, lomin, lamax, lomax
    url = "https://opensky-network.org/api/states/all?lamin=39.0&lomin=-75.0&lamax=43.0&lomax=-70.0"
    
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        print(f"API Error {response.status_code}: Could not fetch data.")
        return

    data = response.json()
    states = data.get('states')
    
    if not states:
        print("No flights currently found in this sector.")
        return

    # 2. Parse the messy JSON array
    # OpenSky returns an array of arrays. We have to map indices manually.
    flight_records = []
    for s in states:
        # Skip planes that aren't transmitting coordinates
        if s[5] is None or s[6] is None:
            continue
            
        callsign = str(s[1]).strip() if s[1] else None
        if not callsign:
            continue
            
        flight_records.append({
            'callsign': callsign,
            'origin_country': s[2],
            'longitude': s[5],
            'latitude': s[6],
            'velocity': s[9],     # meters per second
            'true_track': s[10]   # heading in degrees
        })

    df_flights = pd.DataFrame(flight_records)
    print(f"Parsed {len(df_flights)} active flights. Pushing to database...")

    # 3. Upsert into Supabase (Insert new, update existing)
    engine = create_engine(DB_URI)
    
    # Use engine.begin() instead of connect() so it automatically commits the transaction!
    with engine.begin() as conn:
        for idx, row in df_flights.iterrows():
            # Wrap the raw SQL string in the text() function
            stmt = text(f"""
                INSERT INTO active_flights (callsign, origin_country, longitude, latitude, velocity, true_track, last_updated)
                VALUES ('{row['callsign']}', '{row['origin_country'].replace("'", "''")}', {row['longitude']}, {row['latitude']}, {row['velocity'] if pd.notnull(row['velocity']) else 'NULL'}, {row['true_track'] if pd.notnull(row['true_track']) else 'NULL'}, CURRENT_TIMESTAMP)
                ON CONFLICT (callsign) 
                DO UPDATE SET 
                    longitude = EXCLUDED.longitude,
                    latitude = EXCLUDED.latitude,
                    velocity = EXCLUDED.velocity,
                    true_track = EXCLUDED.true_track,
                    last_updated = CURRENT_TIMESTAMP;
            """)
            conn.execute(stmt)

    print("Live flight data successfully synced to Supabase!")

if __name__ == "__main__":
    get_live_flights()