#!/usr/bin/env python3

import argparse
import sys
import os
import time
from datetime import datetime
import subprocess

# --- INITIALIZATION & SAFETY CHECKS ---
# Autoware tools require the ROS 2 environment to be sourced
if "ROS_DISTRO" not in os.environ:
    print("ERROR: ROS 2 environment is not sourced.")
    print("Please run: source /opt/ros/humble/setup.bash (or source your workspace)")
    sys.exit(1)

# Default ADAS topics to record if the user doesn't specify any
DEFAULT_TOPICS = [
    "/planning/scenario_planning/trajectory",
    "/control/command/control_cmd",
    "/perception/object_recognition/objects",
    "/localization/kinematic_state",
    "/tf",
    "/tf_static"
]


# --- SHARED HELPER FUNCTIONS ---
def get_recordings_dir() -> str:
    """Returns the absolute path to the recordings/autoware directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    recordings_dir = os.path.join(script_dir, "recordings")
    os.makedirs(recordings_dir, exist_ok=True)
    return recordings_dir

def get_valid_bag_path(bag_name: str) -> str:
    """Verifies the ROS 2 bag directory exists."""
    final_path = os.path.join(get_recordings_dir(), bag_name)
    if not os.path.exists(final_path):
        print(f"ERROR: Could not find ROS 2 bag at:\n{final_path}")
        sys.exit(1)
    return final_path


# --- COMMAND LOGIC ---
def command_record(args):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    bag_name = f"autoware_bag_{timestamp}"
    final_save_path = os.path.join(get_recordings_dir(), bag_name)

    # Build the ROS 2 bag command
    cmd = ["ros2", "bag", "record", "-o", final_save_path]
    if args.all:
        cmd.append("-a")
    else:
        cmd.extend(args.topics)

    print(f"Saving Autoware ROS 2 bag to: {final_save_path}")
    print(f"Recording {len(args.topics) if not args.all else 'ALL'} topics...")
    
    # Run the process in the background and hide its default console spam
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Recording started. Press Ctrl+C to stop.")

    start_time = time.time()
    try:
        while process.poll() is None:
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            print(f"\rRecording time: {mins:02d}:{secs:02d}", end='', flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping recording safely. Please wait for ROS 2 to index the bag...")
        process.terminate()
        process.wait() # Ensure the bag closes cleanly to avoid corruption
        print(f"Bag saved successfully: {final_save_path}")

def command_info(args):
    final_bag_path = get_valid_bag_path(args.bag)
    print(f"Extracting metadata from '{final_bag_path}'...")

    # Run the info command and capture the text output
    result = subprocess.run(["ros2", "bag", "info", final_bag_path], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("ERROR: Failed to read bag info. Is the bag corrupted?")
        sys.exit(1)

    txt_filename = f"{args.bag}_info.txt"
    txt_save_path = os.path.join(get_recordings_dir(), txt_filename)

    with open(txt_save_path, 'w', encoding='utf-8') as file:
        file.write(result.stdout)

    print(f"SUCCESS! Information saved to:\n{txt_save_path}")


# --- ARGUMENT PARSING ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified Autoware (ROS 2) Recording & Replay Tool")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Action to perform")

    # --- Record Parser ---
    record_parser = subparsers.add_parser("record", help="Start a new ROS 2 bag recording")
    record_parser.add_argument("--all", action='store_true', help="Record ALL topics (Warning: Massive file size!)")
    record_parser.add_argument("--topics", nargs='+', default=DEFAULT_TOPICS, help="Specific topics to record (space-separated)")
    record_parser.set_defaults(func=command_record)

    # --- Info Parser ---
    info_parser = subparsers.add_parser("info", help="Extract bag info to a text file")
    info_parser.add_argument("--bag", type=str, required=True, help="The bag folder name to parse")
    info_parser.set_defaults(func=command_info)

    # Parse and execute
    args = parser.parse_args()
    args.func(args)