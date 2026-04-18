#!/usr/bin/env python3
import sys
import time
import argparse

try:
    import carla
except ImportError:
    print("ERROR: carla Python package not found.")
    sys.exit(1)

def spawn_vehicle(host: str, port: int, vehicle_filter: str, map_name: str) -> None:
    print(f"[SPAWN] Connecting to CARLA at {host}:{port}...")
    client = carla.Client(host, port)
    client.set_timeout(10.0)

    if map_name:
        print(f"[SPAWN] Changing map to {map_name}...")
        client.load_world(map_name)

    world = client.get_world()
    print(f"[SPAWN] Current map: {world.get_map().name}")

    blueprint_library = world.get_blueprint_library()
    vehicle_bp = blueprint_library.filter(vehicle_filter)[0]
    vehicle_bp.set_attribute("role_name", "ego_vehicle") # CRITICAL FOR BRIDGE

    # Clear old actors
    for actor in world.get_actors():
        if actor.attributes.get("role_name") == "ego_vehicle":
            print(f"[SPAWN] Destroying old ego_vehicle (ID {actor.id})...")
            actor.destroy()

    spawn_point = world.get_map().get_spawn_points()[0]
    print(f"[SPAWN] Spawning vehicle at {spawn_point.location}...")
    vehicle = world.spawn_actor(vehicle_bp, spawn_point)
    vehicle.set_autopilot(False)
    
    print("-" * 30)
    print(f"VEHICLE SPAWNED: {vehicle.id}")
    print(f"ROLE NAME: {vehicle_bp.get_attribute('role_name')}")
    print("-" * 30)

    try:
        while True:
            time.sleep(0.5)
            v = vehicle.get_velocity()
            speed = (v.x**2 + v.y**2 + v.z**2)**0.5 * 3.6
            print(f"\r[SPAWN] Active: Speed={speed:.1f}km/h | Location: {vehicle.get_location()}", end="")
    except KeyboardInterrupt:
        vehicle.destroy()
        print("\n[SPAWN] Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--vehicle", default="vehicle.lincoln.mkz_2020")
    parser.add_argument("--map", default=None)
    args = parser.parse_args()
    spawn_vehicle(args.host, args.port, args.vehicle, args.map)