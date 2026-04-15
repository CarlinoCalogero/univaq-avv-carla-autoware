import carla
import math
import argparse
import subprocess
import time


def get_vehicle_pose(host, port):
    client = carla.Client(host, port)
    client.set_timeout(10.0)
    world = client.get_world()

    vehicles = world.get_actors().filter('vehicle.*')
    if not vehicles:
        print("No vehicles found in CARLA!")
        return None

    t = vehicles[0].get_transform()

    # Coordinate system conversion: CARLA (left-handed) -> ROS 2 (right-handed)
    ros_x = t.location.x
    ros_y = -t.location.y
    ros_z = t.location.z
    ros_yaw = math.radians(-t.rotation.yaw)

    # Euler yaw -> quaternion
    qz = math.sin(ros_yaw / 2.0)
    qw = math.cos(ros_yaw / 2.0)

    return ros_x, ros_y, ros_z, qz, qw


def _build_msg_str(x, y, z, qz, qw, sec, nanosec):
    cov = ("[0.25, 0.0, 0.0, 0.0, 0.0, 0.0, "
           "0.0, 0.25, 0.0, 0.0, 0.0, 0.0, "
           "0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "
           "0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "
           "0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "
           "0.0, 0.0, 0.0, 0.0, 0.0, 0.068]")
    return (
        f"{{header: {{stamp: {{sec: {sec}, nanosec: {nanosec}}}, frame_id: 'map'}}, "
        f"pose: {{pose: {{position: {{x: {x}, y: {y}, z: {z}}}, "
        f"orientation: {{x: 0.0, y: 0.0, z: {qz}, w: {qw}}}}}, "
        f"covariance: {cov} }}}}"
    )


def publish_via_subprocess(x, y, z, qz, qw):
    """
    Publish /initialpose by calling ros2 topic pub in a bash subprocess.

    This works regardless of the Python version used to run this script —
    the subprocess sources ROS 2 Humble directly so it always uses the
    correct Python 3.10 environment where rclpy lives.
    """
    t = time.time()
    sec     = int(t)
    nanosec = int((t - sec) * 1e9)

    msg = _build_msg_str(x, y, z, qz, qw, sec, nanosec)

    cmd = (
        "source /opt/ros/humble/setup.bash && "
        "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && "
        f"ros2 topic pub /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "
        f'"{msg}" --once'
    )

    print("Publishing /initialpose via ros2 CLI...")
    result = subprocess.run(
        ['bash', '-c', cmd],
        text=True,
        timeout=60
    )

    if result.returncode == 0:
        print(f"Published successfully with timestamp {sec}.{nanosec:09d}")
    else:
        print("ros2 topic pub failed — falling back to print mode.")
        print_command(x, y, z, qz, qw)


def print_command(x, y, z, qz, qw):
    """
    Last-resort fallback: print the command so the user can paste it manually.
    The timestamp is baked in so it is never zero.
    """
    t = time.time()
    sec     = int(t)
    nanosec = int((t - sec) * 1e9)

    msg = _build_msg_str(x, y, z, qz, qw, sec, nanosec)

    print("\n--- COPY AND PASTE THIS COMMAND INTO YOUR DOCKER TERMINAL (run immediately) ---\n")
    print(
        f"ros2 topic pub /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "
        f'"{msg}" --once'
    )
    print("\n--------------------------------------------------------------------------------")
    print(f"NOTE: The timestamp ({sec}.{nanosec}) is baked in — run the command immediately.")
    print("      Make sure Autoware's localization stack is already running first.\n")


def main():
    parser = argparse.ArgumentParser(
        description='Read ego vehicle pose from CARLA and publish /initialpose to Autoware.'
    )
    parser.add_argument('--host', default='10.48.106.7', help='CARLA server IP')
    parser.add_argument('--port', default=2000, type=int,  help='CARLA server port')
    parser.add_argument(
        '--no-publish', dest='publish', action='store_false',
        help='Print the ros2 topic pub command instead of publishing automatically'
    )
    parser.set_defaults(publish=True)
    args = parser.parse_args()

    pose = get_vehicle_pose(args.host, args.port)
    if pose is None:
        return

    x, y, z, qz, qw = pose

    if args.publish:
        publish_via_subprocess(x, y, z, qz, qw)
    else:
        print_command(x, y, z, qz, qw)


if __name__ == '__main__':
    main()
