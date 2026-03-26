import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DB_URI = os.getenv("SUPABASE_URI")

# The Haversine formula calculates the distance between two points on a sphere (the Earth)
def haversine_vectorized(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in kilometers
    
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    return R * c

def map_nearest_airports():
    print("Connecting to database...")
    engine = create_engine(DB_URI)
    
    with engine.connect() as conn:
        # Get flights that don't have a destination yet
        flights_df = pd.read_sql(text("SELECT callsign, latitude, longitude FROM active_flights WHERE destination_ident IS NULL"), conn)
        # Get all our valid airports
        airports_df = pd.read_sql(text("SELECT ident, latitude_deg, longitude_deg FROM airports"), conn)
        
    if flights_df.empty:
        print("All flights already have a mapped destination!")
        return

    print(f"Calculating nearest airports for {len(flights_df)} flights...")
    
    updates = []
    
    # For each flight, calculate the distance to ALL airports and pick the minimum
    for _, flight in flights_df.iterrows():
        f_lat, f_lon = flight['latitude'], flight['longitude']
        
        # Vectorized distance calculation against all airports at once
        distances = haversine_vectorized(f_lat, f_lon, airports_df['latitude_deg'].values, airports_df['longitude_deg'].values)
        
        # Find the index of the closest airport
        closest_idx = np.argmin(distances)
        closest_airport_ident = airports_df.iloc[closest_idx]['ident']
        
        updates.append({
            'callsign': flight['callsign'],
            'closest_ident': closest_airport_ident
        })

    # Push the updates back to the database
    print("Updating the database with nearest divert airports...")
    with engine.begin() as conn:
        for u in updates:
            stmt = text(f"""
                UPDATE active_flights 
                SET destination_ident = '{u['closest_ident']}' 
                WHERE callsign = '{u['callsign']}';
            """)
            conn.execute(stmt)
            
    print("Success! All active flights are now mapped to a local airport.")

if __name__ == "__main__":
    map_nearest_airports()