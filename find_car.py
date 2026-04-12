import carla
import argparse

def main():
    parser = argparse.ArgumentParser(description="Teleport spectator camera to the car.")
    parser.add_argument('--host', default='127.0.0.1', help='CARLA Server IP address')
    parser.add_argument('--port', default=2000, type=int, help='CARLA Server Port')
    args = parser.parse_args()

    print(f"Connecting to CARLA at {args.host}:{args.port}...")
    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)
    world = client.get_world()

    # Get every vehicle in the simulation
    vehicles = world.get_actors().filter('vehicle.*')

    if not vehicles:
        print("ERROR: There are absolutely zero vehicles in the simulation right now.")
        print("Make sure your ROS 2 spawn command actually finished running!")
        return

    print(f"Found {len(vehicles)} vehicle(s) in the world.")

    target_vehicle = None
    
    # Check all cars to see what names they actually have
    for v in vehicles:
        role = v.attributes.get('role_name', 'NO_NAME_TAG')
        print(f" -> Spotted a {v.type_id} (Role: {role})")
        if role == 'ego_vehicle':
            target_vehicle = v

    # If it didn't find the exact name, just grab the first car!
    if not target_vehicle:
        print("\nCould not find 'ego_vehicle'. Teleporting to the first available car instead...")
        target_vehicle = vehicles[0]

    # Teleport the camera
    transform = target_vehicle.get_transform()
    transform.location.x -= 8.0
    transform.location.z += 3.0
    
    world.get_spectator().set_transform(transform)
    print("Teleported! Check your Windows CARLA screen.")

if __name__ == '__main__':
    main()