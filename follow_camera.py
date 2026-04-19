#!/usr/bin/env python3
"""
follow_camera.py
Continuously moves the CARLA spectator camera to follow the ego vehicle.
Run this on Windows alongside spawn_vehicle.py.

Usage:
    python follow_camera.py
    python follow_camera.py --mode behind       # chase cam (default)
    python follow_camera.py --mode top          # bird's-eye view
    python follow_camera.py --mode front        # front-facing cam
    python follow_camera.py --offset-z 10 --offset-back 15
"""

import argparse
import math
import sys
import time

try:
    import carla
except ImportError:
    print("ERROR: carla Python package not found.")
    print("  pip install carla==0.9.15")
    print("  or add the .egg to sys.path")
    sys.exit(1)


def build_camera_transform(
    vehicle_transform: carla.Transform,
    mode: str,
    offset_back: float,
    offset_z: float,
) -> carla.Transform:
    """Return a spectator Transform relative to the vehicle."""

    yaw_rad = math.radians(vehicle_transform.rotation.yaw)
    loc = vehicle_transform.location

    if mode == "behind":
        # Behind and above the vehicle, looking forward
        cam_x = loc.x - offset_back * math.cos(yaw_rad)
        cam_y = loc.y - offset_back * math.sin(yaw_rad)
        cam_z = loc.z + offset_z
        pitch = -15.0   # look slightly downward
        yaw   = vehicle_transform.rotation.yaw

    elif mode == "top":
        # Directly above, looking straight down
        cam_x = loc.x
        cam_y = loc.y
        cam_z = loc.z + offset_z * 3.0
        pitch = -90.0
        yaw   = vehicle_transform.rotation.yaw

    elif mode == "front":
        # In front of the vehicle, looking back at it
        cam_x = loc.x + offset_back * math.cos(yaw_rad)
        cam_y = loc.y + offset_back * math.sin(yaw_rad)
        cam_z = loc.z + offset_z
        pitch = -10.0
        yaw   = vehicle_transform.rotation.yaw + 180.0

    else:
        raise ValueError(f"Unknown mode '{mode}'. Choose: behind, top, front")

    return carla.Transform(
        carla.Location(x=cam_x, y=cam_y, z=cam_z),
        carla.Rotation(pitch=pitch, yaw=yaw, roll=0.0),
    )


def follow_camera(host: str, port: int, mode: str, offset_back: float, offset_z: float, rate: float):
    client = carla.Client(host, port)
    client.set_timeout(10.0)
    world = client.get_world()
    spectator = world.get_spectator()

    print(f"Connected to CARLA. Map: {world.get_map().name}")
    print(f"Camera mode : {mode}")
    print(f"Looking for ego_vehicle ... (run spawn_vehicle.py if not spawned yet)")
    print("Press Ctrl+C to stop.\n")

    ego = None
    interval = 1.0 / rate

    try:
        while True:
            # Re-scan for ego_vehicle if not found yet
            if ego is None or not ego.is_alive:
                ego = None
                for actor in world.get_actors():
                    if actor.attributes.get("role_name") == "ego_vehicle":
                        ego = actor
                        print(f"Tracking ego_vehicle id={ego.id}  ({ego.type_id})")
                        break
                if ego is None:
                    print("\rWaiting for ego_vehicle ...", end="", flush=True)
                    time.sleep(1.0)
                    continue

            cam_transform = build_camera_transform(
                ego.get_transform(), mode, offset_back, offset_z
            )
            spectator.set_transform(cam_transform)

            loc = ego.get_location()
            vel = ego.get_velocity()
            speed_kmh = math.sqrt(vel.x**2 + vel.y**2 + vel.z**2) * 3.6
            print(
                f"\r  x={loc.x:8.2f}  y={loc.y:8.2f}  z={loc.z:5.2f}"
                f"  speed={speed_kmh:5.1f} km/h  mode={mode}   ",
                end="",
                flush=True,
            )

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Follow ego vehicle with CARLA spectator camera")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument(
        "--mode",
        default="behind",
        choices=["behind", "top", "front"],
        help="Camera position mode (default: behind)",
    )
    parser.add_argument("--offset-back", type=float, default=8.0, help="Distance behind vehicle in metres (default: 8)")
    parser.add_argument("--offset-z", type=float, default=4.0, help="Height above vehicle in metres (default: 4)")
    parser.add_argument("--rate", type=float, default=30.0, help="Camera update rate in Hz (default: 30)")
    args = parser.parse_args()

    follow_camera(args.host, args.port, args.mode, args.offset_back, args.offset_z, args.rate)
