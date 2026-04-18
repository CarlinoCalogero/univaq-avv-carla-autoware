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
    blueprint_library = world.get_blueprint_library()

    # 1. Spawn Ego Vehicle
    vehicle_bp = blueprint_library.filter(vehicle_filter)[0]
    vehicle_bp.set_attribute("role_name", "ego_vehicle") 

    # Clear old actors
    for actor in world.get_actors():
        if actor.attributes.get("role_name") in ["ego_vehicle", "lidar_sensor"]:
            actor.destroy()

    spawn_point = world.get_map().get_spawn_points()[0]
    vehicle = world.spawn_actor(vehicle_bp, spawn_point)
    vehicle.set_autopilot(False)

    # 2. Attach LiDAR Sensor (Required for Autoware Localization)
    lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')
    lidar_bp.set_attribute('range', '100')
    lidar_bp.set_attribute('rotation_frequency', '10')
    lidar_bp.set_attribute('channels', '64')
    lidar_bp.set_attribute('points_per_second', '600000')
    lidar_bp.set_attribute('role_name', 'lidar_sensor') # Tag for the bridge

    lidar_location = carla.Location(x=0, z=2.4) # On the roof
    lidar_rotation = carla.Rotation(pitch=0)
    lidar_transform = carla.Transform(lidar_location, lidar_rotation)
    
    lidar = world.spawn_actor(lidar_bp, lidar_transform, attach_to=vehicle)
    
    print("-" * 30)
    print(f"VEHICLE & LIDAR SPAWNED (ID: {vehicle.id})")
    print("-" * 30)

    try:
        while True:
            time.sleep(1.0)
            loc = vehicle.get_location()
            print(f"\r[SPAWN] Active at x={loc.x:.1f}, y={loc.y:.1f}", end="")
    except KeyboardInterrupt:
        lidar.destroy()
        vehicle.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--vehicle", default="vehicle.lincoln.mkz_2020")
    parser.add_argument("--map", default=None)
    args = parser.parse_args()
    spawn_vehicle(args.host, args.port, args.vehicle, args.map)