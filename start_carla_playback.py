#!/usr/bin/env python3

import argparse
import sys
import os

try:
    import carla
except ImportError:
    print("ERROR: carla Python package not found.")
    print("  pip install carla==0.9.15")
    print("  or add the .egg to sys.path")
    sys.exit(1)

def start_playback(host: str, port: int, recording: str, start: float, duration: float, camera: int, time_factor: float):
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
    final_log_path = os.path.join(recordings_dir, recording)

    final_log_path = final_log_path.replace('\\', '/')

    # Safety Check: Does the file actually exist?
    if not os.path.isfile(final_log_path):
        print(f"ERROR: Could not find recording file at:\n{final_log_path}")
        sys.exit(1)

    print(f"Replaying CARLA recording: {final_log_path}")

    # Set time factor
    client.set_replayer_time_factor(time_factor)

    # Start replay
    result = client.replay_file(final_log_path, start, duration, camera)
    print(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replays a CARLA simulation recording")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument(
        "--recording",
        type=str,
        required=True,
        help="The log file name with .log extension to be replayed",
    )
    parser.add_argument(
        "--start",
        type=float,
        default=0.0,
        help="Recording time in seconds to start the simulation at. If positive, time will be considered from the beginning of the recording. If negative, it will be considered from the end.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="Seconds to playback. 0 is all the recording. By the end of the playback, vehicles will be set to autopilot and pedestrians will stop.",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="ID of the actor that the camera will focus on. Set it to 0 to let the spectator move freely.",
    )
    parser.add_argument(
        "--time_factor",
        type=float,
        default=1.0,
        help="Will determine the playback speed.",
    )
    args = parser.parse_args()

    start_playback(args.host, args.port, args.recording, args.start, args.duration, args.camera, args.time_factor)