#!/usr/bin/env python3
import sys
import time
import argparse
import carla

def spawn_vehicle(host, port, vehicle_filter, map_name):
    print(f"[SPAWN] Connecting to CARLA at {host}:{port}...")
    client = carla.Client(host, port)
    client.set_timeout(10.0)

    if map_name:
        print(f"[SPAWN] Loading map {map_name}...")
        client.load_world(map_name)

    world = client.get_world()
    blueprint_library = world.get_blueprint_library()

    # Spawn Ego Vehicle
    vehicle_bp = blueprint_library.filter(vehicle_filter)[0]
    vehicle_bp.set_attribute("role_name", "ego_vehicle") 

    # Clear old actors to avoid conflicts
    for actor in world.get_actors().filter('vehicle.*'):
        if actor.attributes.get("role_name") == "ego_vehicle":
            print(f"[SPAWN] Cleaning up old ego_vehicle (ID {actor.id})...")
            actor.destroy()

    spawn_point = world.get_map().get_spawn_points()[0]
    vehicle = world.spawn_actor(vehicle_bp, spawn_point)
    vehicle.set_autopilot(False)
    
    # FORCE BRAKES ON TO PREVENT "VEHICLE NOT STOPPED" ERROR IN AUTOWARE
    ctrl = carla.VehicleControl()
    ctrl.brake = 1.0
    vehicle.apply_control(ctrl)
    
    print(f"[SPAWN] Ego Vehicle spawned: {vehicle.id} at {spawn_point.location}")

    # Attach LiDAR (Required for Autoware 'align server')
    print("[SPAWN] Attaching LiDAR sensor...")
    lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')
    lidar_bp.set_attribute('range', '100')
    lidar_bp.set_attribute('rotation_frequency', '10')
    lidar_bp.set_attribute('channels', '64')
    lidar_bp.set_attribute('points_per_second', '600000')
    
    # Lock LiDAR generation to exactly 10 Hz
    lidar_bp.set_attribute('sensor_tick', '0.1')
    
    lidar_bp.set_attribute('role_name', 'lidar_sensor')

    lidar_transform = carla.Transform(carla.Location(x=0, z=2.4))
    lidar = world.spawn_actor(lidar_bp, lidar_transform, attach_to=vehicle)
    print(f"[SPAWN] LiDAR attached successfully (ID: {lidar.id})")

    print("-" * 50)
    print("SYSTEM READY: Keep this terminal open.")
    print("-" * 50)

    try:
        while True:
            loc = vehicle.get_location()
            v = vehicle.get_velocity()
            speed = (v.x**2 + v.y**2 + v.z**2)**0.5
            print(f"\r[SPAWN] Status: Speed={speed:.2f} m/s | Location: x={loc.x:.1f}, y={loc.y:.1f}   ", end="")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[SPAWN] Destroying actors...")
        lidar.destroy()
        vehicle.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--vehicle", default="vehicle.lincoln.mkz_2020")
    parser.add_argument("--map", default="Town01")
    args = parser.parse_args()
    spawn_vehicle(args.host, args.port, args.vehicle, args.map)