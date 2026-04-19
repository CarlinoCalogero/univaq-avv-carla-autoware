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

def export_recording_info(host: str, port: int, recording: str, show_all: bool):
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

    print(f"Extracting '{final_log_path}' data (Detailed mode: {show_all})...")

    # Extract data
    info_string = client.show_recorder_file_info(final_log_path, show_all)

    # Change the filename slightly so summaries and detailed dumps don't overwrite each other
    suffix = "_detailed.txt" if show_all else "_summary.txt"
    txt_filename = recording.replace(".log", suffix)
    txt_save_path = os.path.join(recordings_dir, txt_filename)

    with open(txt_save_path, 'w', encoding='utf-8') as file:
        file.write(info_string)

    print(f"SUCCESS! Information saved to:\n{txt_save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exports CARLA log info to a text file")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument(
        "--recording",
        type=str,
        required=True,
        help="The log file name with .log extension",
    )
    parser.add_argument(
        "--show_all",
        action='store_true',
        help="By default, it only retrieves those frames where an event was registered. Setting the parameter show_all would return all the information for every frame.",
    )
    args = parser.parse_args()

    export_recording_info(args.host, args.port, args.recording, args.show_all)