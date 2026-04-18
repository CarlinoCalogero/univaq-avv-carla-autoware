import carla
import time
import math

def main():
    # Connect to CARLA
    try:
        client = carla.Client('localhost', 2000)
        client.set_timeout(5.0)
        world = client.get_world()
        print(f"[CONNECTED] Map: {world.get_map().name}")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return

    # Find Ego Vehicle
    ego_vehicle = None
    for actor in world.get_actors():
        if actor.attributes.get('role_name') == 'ego_vehicle':
            ego_vehicle = actor
            break

    if not ego_vehicle:
        print("[ERROR] Could not find 'ego_vehicle'. Ensure your spawn script or bridge is running!")
        return

    print(f"[MONITORING] Vehicle ID: {ego_vehicle.id}")

    # Sensor Callbacks (Define how to print each type)
    def on_lidar(data):
        print(f"[LIDAR]  Points: {len(data):<6} | TS: {data.timestamp:.3f}")

    def on_gnss(data):
        print(f"[GNSS ]  Lat: {data.latitude:10.6f} | Lon: {data.longitude:10.6f}")

    def on_imu(data):
        accel = data.linear_acceleration
        print(f"[IMU  ]  Accel: x={accel.x:5.2f} y={accel.y:5.2f} z={accel.z:5.2f}")

    def on_camera(data, name):
        print(f"[CAM  ]  {name:15} | Res: {data.width}x{data.height} | TS: {data.timestamp:.3f}")

    def on_radar(data):
        print(f"[RADAR]  Detections: {len(data):<3} | TS: {data.timestamp:.3f}")

    # Attach Listeners to ALL sensors belonging to the ego_vehicle
    attached_sensors = []
    all_actors = world.get_actors()
    sensors = all_actors.filter('sensor.*')

    for s in sensors:
        # Check if the sensor is bolted to our car
        if s.parent and s.parent.id == ego_vehicle.id:
            s_type = s.type_id
            
            if 'lidar' in s_type:
                s.listen(on_lidar)
            elif 'gnss' in s_type:
                s.listen(on_gnss)
            elif 'imu' in s_type:
                s.listen(on_imu)
            elif 'radar' in s_type:
                s.listen(on_radar)
            elif 'camera' in s_type:
                # Cameras need an extra argument to show which one is which
                cam_name = s.attributes.get('role_name', s_type.split('.')[-1])
                s.listen(lambda data, name=cam_name: on_camera(data, name))
            else:
                # Fallback for any other sensor types
                s.listen(lambda data: print(f"[OTHER]  {s.type_id} data received"))
            
            attached_sensors.append(s)
            print(f"[ATTACHED] {s.type_id} (ID: {s.id})")

    if not attached_sensors:
        print("[WARN] No sensors found attached to the ego_vehicle!")
    else:
        print(f"[INFO] Successfully listening to {len(attached_sensors)} sensors.\n")

    try:
        while True:
            # Continuous Ground Truth Physics Print
            v = ego_vehicle.get_velocity()
            speed = math.sqrt(v.x**2 + v.y**2 + v.z**2)
            c = ego_vehicle.get_control()
            
            print(f"[PHYS ]  Speed: {speed:6.4f} m/s | Throttle: {c.throttle:.2f} | Brake: {c.brake:.2f}")
            time.sleep(1.0) # Slowed down to 1s so the sensor prints are readable
    except KeyboardInterrupt:
        print("\n[STOPPING] Cleaning up...")
        for s in attached_sensors:
            s.stop()
        print("[DONE]")

if __name__ == '__main__':
    main()