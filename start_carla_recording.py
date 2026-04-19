#!/usr/bin/env python3

import argparse
import sys
import os
from datetime import datetime
import time

try:
    import carla
except ImportError:
    print("ERROR: carla Python package not found.")
    print("  pip install carla==0.9.15")
    print("  or add the .egg to sys.path")
    sys.exit(1)

def start_recording(host: str, port: int, additional_data: bool):
    # Connect to CARLA
    try:
        client = carla.Client(host, port)
        client.set_timeout(10.0)
    except Exception as e:
        print(f"ERROR: Could not connect to CARLA server at {host}:{port}")
        sys.exit(1)

    # Get the absolute path where this Python script is located on Windows
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the target folder relative to the script
    recordings_dir = os.path.join(script_dir, "recordings", "carla")

    # Create the folder if it doesn't exist yet (CARLA will crash if the folder is missing)
    os.makedirs(recordings_dir, exist_ok=True)

    # Generate a formatted timestamp (e.g., "2026-04-19_20-52-45")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"my_snapshot_{timestamp}.log"
    # Construct the final file path
    final_save_path = os.path.join(recordings_dir, log_filename)
    final_save_path = final_save_path.replace('\\', '/')

    print(f"Saving CARLA recording to: {final_save_path}")

    # Start recording
    client.start_recorder(final_save_path, additional_data)
    print("Recording started. Press Ctrl+C to stop.")

    # Record the exact moment we started
    start_time = time.time()

    try:
        while True:
            # Calculate elapsed time in seconds
            elapsed = int(time.time() - start_time)
            
            # Format as MM:SS
            mins, secs = divmod(elapsed, 60)
            
            # Print with a carriage return '\r' and end='' so it overwrites the same line
            print(f"\rRecording time: {mins:02d}:{secs:02d}", end='', flush=True)
            
            # Sleep for 1 second so we don't consume 100% CPU on an empty loop
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopping...")
        client.stop_recorder()
        print(f"Recording saved: {final_save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts Carla Recording")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument(
        "--additional_data",
        action='store_true',
        help="Additional data includes: linear and angular velocity of vehicles and pedestrians, traffic light time settings, execution time, actors' trigger and bounding boxes, and physics controls for vehicles.",
    )
    args = parser.parse_args()

    start_recording(args.host, args.port, args.additional_data)