import os
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import time

# 1. Load Environment Variables
load_dotenv()
DB_URI = os.getenv("SUPABASE_URI")

def run_risk_engine():
    print("Starting the FDE Risk Engine...")
    engine = create_engine(DB_URI)
    
    # 2. Fetch active flights from your database
    # We limit to 50 here so we don't accidentally spam the free weather API
    with engine.connect() as conn:
        flights_df = pd.read_sql(text("SELECT callsign, latitude, longitude FROM active_flights LIMIT 50"), conn)
        
    if flights_df.empty:
        print("No active flights found. Run track_flights.py first!")
        return
        
    print(f"Scoring {len(flights_df)} flights for mid-air weather risk...")

    updates = []
    
    # 3. Iterate through flights and check the weather at their exact coordinates
    for index, row in flights_df.iterrows():
        lat, lon = row['latitude'], row['longitude']
        callsign = row['callsign']
        
        # Open-Meteo API (Free, no key required)
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=wind_speed_10m,precipitation"
        
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                weather = resp.json().get('current', {})
                wind_kmh = weather.get('wind_speed_10m', 0)
                precip_mm = weather.get('precipitation', 0)
                
                # 4. The FDE Business Logic: Calculate Risk Score
                risk_score = 'Low Risk'
                # If winds exceed 40 km/h or heavy rain
                if wind_kmh > 40 or precip_mm > 5.0:
                    risk_score = 'High Risk'
                # If moderate winds or light rain
                elif wind_kmh > 20 or precip_mm > 1.0:
                    risk_score = 'Medium Risk'
                    
                updates.append({
                    'callsign': callsign,
                    'risk_score': risk_score
                })
            # Be polite to the free API by adding a tiny delay
            time.sleep(0.1) 
        except Exception as e:
            print(f"Skipping {callsign} due to API error: {e}")

    # 5. Push the calculated scores back into Supabase
    if updates:
        print("Pushing Risk Scores to the database...")
        with engine.begin() as conn:
            for u in updates:
                stmt = text(f"""
                    UPDATE active_flights 
                    SET risk_score = '{u['risk_score']}' 
                    WHERE callsign = '{u['callsign']}';
                """)
                conn.execute(stmt)
                
        print("Risk Engine complete! Flights have been scored.")

if __name__ == "__main__":
    run_risk_engine()