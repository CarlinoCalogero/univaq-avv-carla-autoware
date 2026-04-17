#!/usr/bin/env python3
"""
CARLA <-> Autoware Bridge Node (Modern Autoware Universe Version)
"""

import math
import os
import time

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, NavSatFix, NavSatStatus
from std_msgs.msg import Header

# ── Modern Autoware message types (with ackermann_msgs fallback) ───────────
try:
    # Changed from autoware_auto_* to standard autoware_*
    from autoware_control_msgs.msg import Control
    from autoware_vehicle_msgs.msg import SteeringReport, VelocityReport

    AUTOWARE_MSGS = True
except ImportError:
    try:
        from ackermann_msgs.msg import AckermannDrive

        AUTOWARE_MSGS = False
        print(
            "[bridge_node] autoware_control_msgs not found – "
            "falling back to ackermann_msgs/AckermannDrive"
        )
    except ImportError:
        raise ImportError(
            "Neither autoware_control_msgs nor ackermann_msgs is installed."
        )

# ── CARLA Python API ───────────────────────────────────────────────────────
try:
    import carla
except ImportError:
    raise ImportError(
        "carla Python package not found in WSL.\n"
        "pip install carla==<your-carla-version>\n"
    )

CARLA_MAX_STEER_RAD = math.radians(70.0)

MAP_ORIGIN_LAT = 48.9968 
MAP_ORIGIN_LON = 8.0000   
METERS_PER_DEG_LAT = 111_320.0
METERS_PER_DEG_LON = 111_320.0 * math.cos(math.radians(MAP_ORIGIN_LAT))

def carla_to_ros_stamp(node: Node):
    return node.get_clock().now().to_msg()


class CarlaAutowareBridge(Node):
    def __init__(self):
        super().__init__("carla_autoware_bridge")

        self.declare_parameter("carla_host", os.environ.get("CARLA_HOST", "172.28.0.1"))
        self.declare_parameter("carla_port", 2000)
        self.declare_parameter("ego_role_name", "ego_vehicle")
        self.declare_parameter("publish_rate", 20.0)   
        self.declare_parameter("speed_kp", 0.4)        
        self.declare_parameter("brake_kp", 0.6)        

        self.carla_host = self.get_parameter("carla_host").value
        self.carla_port = self.get_parameter("carla_port").value
        self.ego_role_name = self.get_parameter("ego_role_name").value
        publish_rate = self.get_parameter("publish_rate").value
        self.speed_kp = self.get_parameter("speed_kp").value
        self.brake_kp = self.get_parameter("brake_kp").value

        self.get_logger().info(f"Connecting to CARLA at {self.carla_host}:{self.carla_port} ...")
        self.client = carla.Client(self.carla_host, self.carla_port)
        self.client.set_timeout(10.0)
        self.world = self.client.get_world()
        self.get_logger().info(f"Connected. Map: {self.world.get_map().name}")

        self.ego_vehicle = None
        self._find_ego_vehicle()

        self.pub_gnss = self.create_publisher(NavSatFix, "/sensing/gnss/pose", 10)
        self.pub_imu = self.create_publisher(Imu, "/sensing/imu/imu_raw", 10)
        self.pub_odom = self.create_publisher(Odometry, "/localization/kinematic_state", 10)

        if AUTOWARE_MSGS:
            self.pub_vel = self.create_publisher(VelocityReport, "/vehicle/status/velocity_status", 10)
            self.pub_steer = self.create_publisher(SteeringReport, "/vehicle/status/steering_status", 10)
        else:
            self.pub_vel = None
            self.pub_steer = None

        if AUTOWARE_MSGS:
            self.create_subscription(
                Control,  # Changed from AckermannControlCommand
                "/control/command/control_cmd",
                self._on_control_command,
                10,
            )
        else:
            self.create_subscription(AckermannDrive, "/control/command/control_cmd", self._on_ackermann_drive, 10)

        self.get_logger().info("Bridge ready.")
        self.create_timer(1.0 / publish_rate, self._publish_vehicle_state)

    def _find_ego_vehicle(self):
        for actor in self.world.get_actors():
            if actor.attributes.get("role_name") == self.ego_role_name:
                self.ego_vehicle = actor
                self.get_logger().info(f"Found ego_vehicle: {actor.type_id}  id={actor.id}")
                return
        self.get_logger().warn(f"Ego vehicle not found. Run windows/spawn_vehicle.py first.")

    def _current_speed(self) -> float:
        vel = self.ego_vehicle.get_velocity()
        return math.sqrt(vel.x ** 2 + vel.y ** 2 + vel.z ** 2)

    def _make_header(self, frame_id: str) -> Header:
        h = Header()
        h.stamp = carla_to_ros_stamp(self)
        h.frame_id = frame_id
        return h

    def _on_control_command(self, msg):
        if self.ego_vehicle is None:
            self._find_ego_vehicle()
            return
        self._apply_control(
            target_speed=msg.longitudinal.velocity, # Changed from .speed to .velocity
            target_accel=msg.longitudinal.acceleration,
            steering_angle=msg.lateral.steering_tire_angle,
        )

    def _on_ackermann_drive(self, msg):
        if self.ego_vehicle is None:
            self._find_ego_vehicle()
            return
        self._apply_control(target_speed=msg.speed, target_accel=msg.acceleration, steering_angle=msg.steering_angle)

    def _apply_control(self, target_speed: float, target_accel: float, steering_angle: float):
        current_speed = self._current_speed()
        speed_error = target_speed - current_speed

        ctrl = carla.VehicleControl()

        if target_speed >= 0.0:
            ctrl.reverse = False
            if speed_error > 0.05:
                ctrl.throttle = min(speed_error * self.speed_kp, 1.0)
                ctrl.brake = 0.0
            elif speed_error < -0.05:
                ctrl.throttle = 0.0
                ctrl.brake = min(abs(speed_error) * self.brake_kp, 1.0)
            else:
                ctrl.throttle = 0.03  
                ctrl.brake = 0.0
        else:
            ctrl.reverse = True
            ctrl.throttle = min(abs(target_speed) * self.speed_kp, 1.0)
            ctrl.brake = 0.0

        ctrl.steer = max(-1.0, min(1.0, -steering_angle / CARLA_MAX_STEER_RAD))
        self.ego_vehicle.apply_control(ctrl)

    def _publish_vehicle_state(self):
        if self.ego_vehicle is None:
            self._find_ego_vehicle()
            return

        now = carla_to_ros_stamp(self)
        transform = self.ego_vehicle.get_transform()
        velocity = self.ego_vehicle.get_velocity()
        accel = self.ego_vehicle.get_acceleration()
        ang_vel = self.ego_vehicle.get_angular_velocity()

        loc = transform.location
        rot = transform.rotation

        gnss = NavSatFix()
        gnss.header = self._make_header("gnss_link")
        gnss.status.status = NavSatStatus.STATUS_FIX
        gnss.status.service = NavSatStatus.SERVICE_GPS
        gnss.latitude = MAP_ORIGIN_LAT + loc.y / METERS_PER_DEG_LAT
        gnss.longitude = MAP_ORIGIN_LON + loc.x / METERS_PER_DEG_LON
        gnss.altitude = loc.z
        gnss.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
        self.pub_gnss.publish(gnss)

        imu = Imu()
        imu.header = self._make_header("imu_link")
        imu.linear_acceleration.x = accel.x
        imu.linear_acceleration.y = -accel.y   
        imu.linear_acceleration.z = accel.z
        imu.angular_velocity.x = math.radians(ang_vel.x)
        imu.angular_velocity.y = -math.radians(ang_vel.y)
        imu.angular_velocity.z = -math.radians(ang_vel.z)
        yaw = math.radians(-rot.yaw)
        imu.orientation.z = math.sin(yaw / 2.0)
        imu.orientation.w = math.cos(yaw / 2.0)
        self.pub_imu.publish(imu)

        odom = Odometry()
        odom.header = self._make_header("map")
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = loc.x
        odom.pose.pose.position.y = -loc.y   
        odom.pose.pose.position.z = loc.z
        odom.pose.pose.orientation.z = math.sin(yaw / 2.0)
        odom.pose.pose.orientation.w = math.cos(yaw / 2.0)
        odom.twist.twist.linear.x = velocity.x
        odom.twist.twist.linear.y = -velocity.y
        odom.twist.twist.angular.z = -math.radians(ang_vel.z)
        self.pub_odom.publish(odom)

        if AUTOWARE_MSGS:
            speed = math.sqrt(velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2)
            vel_report = VelocityReport()
            vel_report.header = self._make_header("base_link")
            vel_report.longitudinal_velocity = float(speed)
            vel_report.lateral_velocity = 0.0
            vel_report.heading_rate = float(-math.radians(ang_vel.z))
            self.pub_vel.publish(vel_report)

            steer_report = SteeringReport()
            steer_report.stamp = now
            ctrl_state = self.ego_vehicle.get_control()
            steer_report.steering_tire_angle = float(-ctrl_state.steer * CARLA_MAX_STEER_RAD)
            self.pub_steer.publish(steer_report)

def main(args=None):
    rclpy.init(args=args)
    node = CarlaAutowareBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()