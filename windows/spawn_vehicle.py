#!/usr/bin/env python3
"""
Spawn a base ego vehicle in CARLA.
Run this script on Windows where CARLA server is running.

Usage:
    python spawn_vehicle.py
    python spawn_vehicle.py --map Town01
    python spawn_vehicle.py --host localhost --port 2000 --vehicle vehicle.lincoln.mkz_2020 --map Town03
"""

import sys
import time
import argparse

try:
    import carla
except ImportError:
    print("ERROR: carla Python package not found.")
    print("")
    print("Fix options:")
    print("  1) Add the CARLA egg to sys.path in this script:")
    print("     sys.path.append('C:/CARLA/PythonAPI/carla/dist/carla-0.9.15-py3.8-win-amd64.egg')")
    print("  2) Or install via pip: pip install carla==0.9.15")
    sys.exit(1)


def spawn_vehicle(host: str, port: int, vehicle_filter: str, map_name: str) -> None:
    print(f"Connecting to CARLA at {host}:{port} ...")
    client = carla.Client(host, port)
    client.set_timeout(10.0)

    # --- NEW: Load the requested map if provided ---
    if map_name:
        print(f"Requesting map change to '{map_name}'... (this may take a few seconds)")
        client.load_world(map_name)

    world = client.get_world()
    print(f"Connected. Map: {world.get_map().name}")

    blueprint_library = world.get_blueprint_library()
    vehicles = blueprint_library.filter(vehicle_filter)

    if not vehicles:
        print(f"\nERROR: No vehicle matching '{vehicle_filter}' found.")
        print("Available vehicles:")
        for bp in sorted(blueprint_library.filter("vehicle.*"), key=lambda b: b.id):
            print(f"  {bp.id}")
        return

    vehicle_bp = vehicles[0]
    vehicle_bp.set_attribute("role_name", "ego_vehicle")

    # Destroy any previous ego_vehicle so we don't stack duplicates
    for actor in world.get_actors():
        if actor.attributes.get("role_name") == "ego_vehicle":
            print(f"Removing existing ego_vehicle (ID {actor.id}) ...")
            actor.destroy()
            time.sleep(0.5)

    spawn_points = world.get_map().get_spawn_points()
    if not spawn_points:
        print("ERROR: No spawn points in this map.")
        return

    spawn_point = spawn_points[0]
    print(f"Spawning '{vehicle_bp.id}' at spawn point 0 ...")
    vehicle = world.spawn_actor(vehicle_bp, spawn_point)
    vehicle.set_autopilot(False)

    loc = spawn_point.location
    print(f"Vehicle spawned  id={vehicle.id}")
    print(f"Position         x={loc.x:.2f}  y={loc.y:.2f}  z={loc.z:.2f}")
    print("")
    print("Keep this window open.  Ctrl+C to destroy vehicle and exit.")
    print("-" * 60)

    try:
        while True:
            time.sleep(1.0)
            loc = vehicle.get_location()
            vel = vehicle.get_velocity()
            speed_kmh = (vel.x ** 2 + vel.y ** 2 + vel.z ** 2) ** 0.5 * 3.6
            ctrl = vehicle.get_control()
            print(
                f"\r  x={loc.x:8.2f}  y={loc.y:8.2f}  z={loc.z:5.2f}"
                f"  speed={speed_kmh:5.1f} km/h"
                f"  throttle={ctrl.throttle:.2f}  steer={ctrl.steer:+.2f}  brake={ctrl.brake:.2f}",
                end="",
                flush=True,
            )
    except KeyboardInterrupt:
        print("\n\nDestroying vehicle ...")
        vehicle.destroy()
        print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spawn ego vehicle in CARLA")
    parser.add_argument("--host", default="localhost", help="CARLA server host (default: localhost)")
    parser.add_argument("--port", type=int, default=2000, help="CARLA server port (default: 2000)")
    parser.add_argument(
        "--vehicle",
        default="vehicle.lincoln.mkz_2020",
        help="Vehicle blueprint filter (default: vehicle.lincoln.mkz_2020)",
    )
    # --- NEW: Map argument ---
    parser.add_argument(
        "--map",
        default=None,
        type=str,
        help="Load a specific CARLA map before spawning (e.g., Town01, Town03)",
    )
    args = parser.parse_args()
    
    # Pass the new map argument to the function
    spawn_vehicle(args.host, args.port, args.vehicle, args.map)