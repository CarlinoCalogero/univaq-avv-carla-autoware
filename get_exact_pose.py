import carla
import math
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='192.168.1.12', help='CARLA Server IP') # Using the IP from your previous steps
    parser.add_argument('--port', default=2000, type=int)
    args = parser.parse_args()

    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)
    world = client.get_world()
    
    # Grab the first vehicle
    vehicles = world.get_actors().filter('vehicle.*')
    if not vehicles:
        print("No vehicles found in CARLA!")
        return

    t = vehicles[0].get_transform()
    
    # 1. Coordinate System Conversion (CARLA Left-Handed -> ROS 2 Right-Handed)
    ros_x = t.location.x
    ros_y = -t.location.y
    ros_z = t.location.z
    ros_yaw = math.radians(-t.rotation.yaw)
    
    # 2. Convert Euler Yaw to Quaternion (Required by Autoware)
    qz = math.sin(ros_yaw / 2.0)
    qw = math.cos(ros_yaw / 2.0)
    
    # Standard RViz covariance matrix to keep Autoware happy
    cov = "[0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.068]"
    
    print("\n--- COPY AND PASTE THIS ENTIRE COMMAND INTO YOUR DOCKER TERMINAL ---\n")
    print(f"ros2 topic pub /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \"{{header: {{frame_id: 'map'}}, pose: {{pose: {{position: {{x: {ros_x}, y: {ros_y}, z: {ros_z}}}, orientation: {{x: 0.0, y: 0.0, z: {qz}, w: {qw}}}}}, covariance: {cov} }}}}\" --once")
    print("\n--------------------------------------------------------------------\n")

if __name__ == '__main__':
    main()