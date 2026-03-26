import time
import subprocess
import sys

def run_script(script_name):
    print(f"\n--- Running {script_name} ---")
    try:
        # Runs the script and waits for it to finish before moving on
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")

def orchestrate_pipeline():
    print("🚀 Starting FDE Control Tower Pipeline Orchestrator...")
    print("Press Ctrl+C to stop.")
    
    while True:
        print("\n" + "="*40)
        print(f"🕒 Pipeline Cycle Started at: {time.strftime('%X')}")
        print("="*40)
        
        # Step 1: Pull live planes
        run_script("track_flights.py")
        
        # Step 2: Map to nearest airports (for the UI)
        run_script("map_destinations.py")
        
        # Step 3: Check weather and assign risk scores
        run_script("risk_engine.py")
        
        print("\n✅ Pipeline Cycle Complete.")
        print("⏳ Sleeping for 5 minutes to respect API rate limits...")
        
        # Sleep for 5 minutes (300 seconds) before repeating
        time.sleep(300)

if __name__ == "__main__":
    try:
        orchestrate_pipeline()
    except KeyboardInterrupt:
        print("\n🛑 Pipeline stopped by user.")