import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

st.set_page_config(page_title="FDE Control Tower", layout="wide")
st.title("✈️ Live Airspace Risk Control Tower")

# 1. Use the legacy caching decorator
@st.cache(allow_output_mutation=True)
def init_connection():
    load_dotenv()
    return create_engine(os.getenv("SUPABASE_URI"))

engine = init_connection()

# 2. Use the legacy data caching decorator
@st.cache(ttl=60, allow_output_mutation=True)
def get_flight_data():
    query = """
        SELECT 
            f.callsign, 
            f.latitude, 
            f.longitude, 
            f.velocity, 
            f.risk_score, 
            a.name AS nearest_airport,
            a.ident AS airport_code
        FROM active_flights f
        LEFT JOIN airports a ON f.destination_ident = a.ident
        WHERE f.latitude IS NOT NULL AND f.longitude IS NOT NULL
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df

with st.spinner("Fetching live radar and risk data from Supabase..."):
    df = get_flight_data()

if not df.empty:
    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("🚨 Active Alerts")
        high_risk_df = df[df['risk_score'] == 'High Risk']
        
        if high_risk_df.empty:
            st.success("No high-risk flights currently detected.")
        else:
            st.error(f"{len(high_risk_df)} Flights require immediate attention!")
            
            for _, row in high_risk_df.iterrows():
                with st.container():
                    st.markdown(f"**Callsign:** `{row['callsign']}`")
                    st.markdown(f"**Status:** 🔴 Severe Mid-Air Weather")
                    st.markdown(f"**Nearest Safe Divert:** {row['nearest_airport']} ({row['airport_code']})")
                    st.markdown("---") # Added divider for cleaner UI in older versions

    with col2:
        st.subheader("Radar Map")
        # Legacy st.map automatically reads the latitude/longitude columns directly
        st.map(df)

else:
    st.warning("No flight data found. Make sure your ingestion scripts are running!")

if st.button("🔄 Refresh Radar"):
    # The ttl=60 in our cache decorator automatically handles the data refresh!
    # We just need to force the UI to redraw.
    st.experimental_rerun()