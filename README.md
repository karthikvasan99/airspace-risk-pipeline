# ✈️ Live Airspace Risk Control Tower

*An end-to-end data pipeline and real-time dashboard for proactive logistics risk management.*

---

## 📖 Overview
In modern logistics and aviation, operations teams often react to severe weather delays after they happen. This project serves as a Forward Deployed Engineering (FDE) proof-of-concept to solve that operational blind spot. 

This Control Tower continuously ingests live, messy ADS-B flight telemetry, cross-references it with live meteorological data, applies a custom business logic engine to flag flights at risk of mid-air weather emergencies, and dynamically calculates the nearest safe divert airport.

## 🏗️ Architecture & Tech Stack
- **Data Ingestion:** Python (`requests`, `pandas`) pulling live data from the **OpenSky Network API** and **Open-Meteo API**.
- **Database & Data Warehouse:** Cloud-hosted **PostgreSQL (Supabase)**.
- **Geospatial Processing:** **NumPy** for high-speed, vectorized distance calculations (Haversine formula).
- **Front-End Dashboard:** **Streamlit** for real-time data visualization and operational alerting.

## 🧠 Key Technical Challenges Overcome
As an FDE project, the primary focus was handling the realities of chaotic, real-world data:

1. **The "Missing Destination" Problem (Geospatial Heuristics):** Live ADS-B telemetry frequently drops the destination airport code. To provide actionable intelligence to the operations team, I built a vectorized Python engine that calculates the distance between a mid-air flight and a static database of thousands of global airports, instantly mapping the flight to its nearest viable "Divert Airport" in case of an emergency.
2. **API Rate Limiting & Orchestration:** Free-tier weather and flight APIs aggressively rate-limit requests. I designed a decoupled architecture where an independent orchestrator script batches requests, throttles payload sizes, and updates the PostgreSQL database asynchronously. This allows the front-end to query the database instantly without waiting on external APIs.
3. **Dependency & Environment Management:** Navigated dependency cascades between C-compiled Protobuf libraries, Altair graphing engines, and PyArrow serialization by enforcing strict pure-Python execution flags and rolling back to stable caching decorators to ensure maximum uptime.

## 🚀 How to Run the Application

### 1. Environment Setup
Clone the repository and install the required dependencies (Python 3.11 recommended):

```bash
pip install pandas psycopg2-binary sqlalchemy requests python-dotenv streamlit numpy "protobuf<4" "altair<5"
```

### 2. Configure Database Credentials
Create a `.env` file in the root directory and add your Supabase PostgreSQL connection string:

```text
SUPABASE_URI=postgresql://[user]:[password]@[host]:6543/postgres
```

### 3. Start the Pipeline Orchestrator
In your first terminal, start the backend data ingestion engine. This will fetch live planes, calculate risks, and map destinations every 5 minutes:

```bash
python run_pipeline.py
```

### 4. Launch the Control Tower Dashboard
In a second terminal, launch the Streamlit UI:

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python streamlit run app.py
```
Navigate to `http://localhost:8501` to view the live radar.

## 👨‍💻 About the Author
**Karthik Srinivasan**
*PhD Candidate in Biomedical Engineering | Former Scale AI Intern*
- [Personal Website](https://your-website.com)
- [LinkedIn](https://linkedin.com/in/your-profile)