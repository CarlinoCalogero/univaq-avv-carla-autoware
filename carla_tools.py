#!/usr/bin/env python3

import argparse
import sys
import os
import time
from datetime import datetime

# --- INITIALIZATION & IMPORTS ---
try:
    import carla
except ImportError:
    print("ERROR: carla Python package not found.")
    print("  pip install carla==0.9.15")
    print("  or add the .egg to sys.path")
    sys.exit(1)


# --- SHARED HELPER FUNCTIONS ---
def get_recordings_dir() -> str:
    """Returns the absolute path to the recordings/carla directory, creating it if needed."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    recordings_dir = os.path.join(script_dir, "recordings")
    os.makedirs(recordings_dir, exist_ok=True)
    return recordings_dir

def connect_to_carla(host: str, port: int):
    """Connects to the CARLA server and returns the client."""
    try:
        client = carla.Client(host, port)
        client.set_timeout(10.0)
        return client
    except Exception as e:
        print(f"ERROR: Could not connect to CARLA server at {host}:{port}")
        sys.exit(1)

def get_valid_log_path(recording_name: str) -> str:
    """Combines the folder and filename, ensures forward slashes, and verifies existence."""
    final_path = os.path.join(get_recordings_dir(), recording_name).replace('\\', '/')
    if not os.path.isfile(final_path):
        print(f"ERROR: Could not find recording file at:\n{final_path}")
        sys.exit(1)
    return final_path


# --- COMMAND LOGIC ---
def command_record(args):
    client = connect_to_carla(args.host, args.port)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"carla_snapshot_{timestamp}.log"
    final_save_path = os.path.join(get_recordings_dir(), log_filename).replace('\\', '/')

    print(f"Saving CARLA recording to: {final_save_path}")
    client.start_recorder(final_save_path, args.additional_data)
    print("Recording started. Press Ctrl+C to stop.")

    start_time = time.time()
    try:
        while True:
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            print(f"\rRecording time: {mins:02d}:{secs:02d}", end='', flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        client.stop_recorder()
        print(f"Recording saved: {final_save_path}")

def command_replay(args):
    final_bag_path = get_valid_bag_path(args.bag)
    print(f"Replaying Autoware bag: {final_bag_path}")

    # ADDED: "--clock" is strictly required for Autoware to accept historical data!
    cmd = ["ros2", "bag", "play", final_bag_path, "-r", str(args.rate), "--clock"]
    
    # CHANGED: We removed stderr=subprocess.DEVNULL. 
    # Now, if ROS 2 fails to play the bag, it will actually print the error to your screen!
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
    print("Playback started. Press Ctrl+C to stop the replay.")

    start_time = time.time()
    try:
        while process.poll() is None:
            real_elapsed = time.time() - start_time
            sim_elapsed = int(real_elapsed * args.rate)
            mins, secs = divmod(sim_elapsed, 60)
            print(f"\rReplay time: {mins:02d}:{secs:02d} (Speed: {args.rate}x)", end='', flush=True)
            time.sleep(1)
        print("\nPlayback finished naturally.")
    except KeyboardInterrupt:
        print("\nStopping playback...")
        process.terminate()
        process.wait()
        print("Playback stopped successfully.")

def command_info(args):
    final_log_path = get_valid_log_path(args.recording)
    print(f"Extracting '{final_log_path}' data (Detailed mode: {args.show_all})...")

    client = connect_to_carla(args.host, args.port)
    info_string = client.show_recorder_file_info(final_log_path, args.show_all)

    suffix = "_detailed.txt" if args.show_all else "_summary.txt"
    txt_filename = args.recording.replace(".log", suffix)
    txt_save_path = os.path.join(get_recordings_dir(), txt_filename)

    with open(txt_save_path, 'w', encoding='utf-8') as file:
        file.write(info_string)

    print(f"SUCCESS! Information saved to:\n{txt_save_path}")


# --- ARGUMENT PARSING ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified CARLA Recording & Replay Tool")
    
    # Global arguments (apply to all subcommands)
    parser.add_argument("--host", default="localhost", help="CARLA server host IP")
    parser.add_argument("--port", type=int, default=2000, help="CARLA server port")

    # Create subparsers for the different tools
    subparsers = parser.add_subparsers(dest="command", required=True, help="Action to perform")

    # --- Record Parser ---
    record_parser = subparsers.add_parser("record", help="Start a new recording")
    record_parser.add_argument("--additional_data", action='store_true', help="Additional data includes: linear and angular velocity of vehicles and pedestrians, traffic light time settings, execution time, actors' trigger and bounding boxes, and physics controls for vehicles")
    record_parser.set_defaults(func=command_record)

    # --- Replay Parser ---
    replay_parser = subparsers.add_parser("replay", help="Replay an existing recording")
    replay_parser.add_argument("--recording", type=str, required=True, help="The .log file to replay")
    replay_parser.add_argument("--start", type=float, default=0.0, help="Recording time in seconds to start the simulation at. If positive, time will be considered from the beginning of the recording. If negative, it will be considered from the end")
    replay_parser.add_argument("--duration", type=float, default=0.0, help="Seconds to playback. 0 is all the recording. By the end of the playback, vehicles will be set to autopilot and pedestrians will stop")
    replay_parser.add_argument("--camera", type=int, default=0, help="ID of the actor that the camera will focus on. Set it to 0 to let the spectator move freely")
    replay_parser.add_argument("--time_factor", type=float, default=1.0, help="Will determine the playback speed")
    replay_parser.set_defaults(func=command_replay)

    # --- Info Parser ---
    info_parser = subparsers.add_parser("info", help="Extract information from a recording to a text file")
    info_parser.add_argument("--recording", type=str, required=True, help="The .log file to parse")
    info_parser.add_argument("--show_all", action='store_true', help="By default, it only retrieves those frames where an event was registered. Setting the parameter show_all would return all the information for every frame")
    info_parser.set_defaults(func=command_info)

    # Parse and execute
    args = parser.parse_args()
    args.func(args)