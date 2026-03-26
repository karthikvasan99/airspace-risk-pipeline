import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 1. Load Environment Variables
# This reads the .env file and securely loads the DB_URI
load_dotenv()
DB_URI = os.getenv("SUPABASE_URI")

# Add a quick safety check so the script fails cleanly if it can't find the .env file
if not DB_URI:
    raise ValueError("No SUPABASE_URI found. Please check your .env file.")

def load_airports_data():
    print("Downloading latest OurAirports data...")
    # OurAirports provides a daily updated open-source CSV
    csv_url = "https://davidmegginson.github.io/ourairports-data/airports.csv"
    
    # Load raw data into a Pandas DataFrame
    df = pd.read_csv(csv_url)
    print(f"Total raw airports downloaded: {len(df)}")

    # 2. FDE Data Cleaning & Filtering
    # The raw dataset has over 70,000 entries, including closed dirt strips and helipads.
    # We only want to track commercial cargo flights, so we filter for medium and large airports.
    valid_types = ['large_airport', 'medium_airport']
    df_filtered = df[df['type'].isin(valid_types)].copy()
    
    # Select only the columns that match our PostgreSQL schema
    df_clean = df_filtered[['ident', 'name', 'latitude_deg', 'longitude_deg', 'iso_country', 'municipality']]
    
    # Drop any messy rows that are missing critical coordinates or IDs
    df_clean = df_clean.dropna(subset=['ident', 'latitude_deg', 'longitude_deg'])
    
    print(f"Filtered down to {len(df_clean)} viable destination airports.")

    # 3. Load into PostgreSQL (Supabase)
    print("Connecting to Supabase...")
    engine = create_engine(DB_URI)
    
    print("Inserting data into the 'airports' table. This might take a few seconds...")
    
    try:
        # if_exists='append' ensures we add to the table without overwriting the schema
        # index=False prevents Pandas from inserting its own row numbers
        df_clean.to_sql('airports', engine, if_exists='append', index=False, method='multi', chunksize=1000)
        print("Success! Static reference data is successfully loaded into Supabase.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    load_airports_data()