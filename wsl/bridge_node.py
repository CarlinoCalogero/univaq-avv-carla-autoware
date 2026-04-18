#!/usr/bin/env python3
"""
CARLA <-> Autoware Bridge Node (Modern Autoware Universe Version)
"""

import math
import os
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster

from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, NavSatFix, NavSatStatus
from std_msgs.msg import Header

# ── Modern Autoware message types ──────────────────────────────────────────
try:
    from autoware_control_msgs.msg import Control
    from autoware_vehicle_msgs.msg import SteeringReport, VelocityReport
    AUTOWARE_MSGS = True
except ImportError:
    try:
        from ackermann_msgs.msg import AckermannDrive
        AUTOWARE_MSGS = False
    except ImportError:
        raise ImportError("Neither autoware_control_msgs nor ackermann_msgs is installed.")

try:
    import carla
except ImportError:
    raise ImportError("carla Python package not found. pip install carla")

CARLA_MAX_STEER_RAD = math.radians(70.0)
MAP_ORIGIN_LAT = 48.9968 
MAP_ORIGIN_LON = 8.0000   
METERS_PER_DEG_LAT = 111320.0
METERS_PER_DEG_LON = 111320.0 * math.cos(math.radians(MAP_ORIGIN_LAT))

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

        self.client = carla.Client(self.carla_host, self.carla_port)
        self.client.set_timeout(10.0)
        self.world = self.client.get_world()

        self.ego_vehicle = None
        self._find_ego_vehicle()

        # TF Broadcaster to connect the tree
        self.tf_broadcaster = TransformBroadcaster(self)

        self.pub_gnss = self.create_publisher(NavSatFix, "/sensing/gnss/pose", 10)
        self.pub_imu = self.create_publisher(Imu, "/sensing/imu/imu_raw", 10)
        self.pub_odom = self.create_publisher(Odometry, "/localization/kinematic_state", 10)

        if AUTOWARE_MSGS:
            self.pub_vel = self.create_publisher(VelocityReport, "/vehicle/status/velocity_status", 10)
            self.pub_steer = self.create_publisher(SteeringReport, "/vehicle/status/steering_status", 10)
            self.create_subscription(Control, "/control/command/control_cmd", self._on_control_command, 10)
        else:
            self.create_subscription(AckermannDrive, "/control/command/control_cmd", self._on_ackermann_drive, 10)

        self.create_timer(1.0 / publish_rate, self._publish_vehicle_state)

    def _find_ego_vehicle(self):
        for actor in self.world.get_actors():
            if actor.attributes.get("role_name") == self.ego_role_name:
                self.ego_vehicle = actor
                return

    def _current_speed(self) -> float:
        vel = self.ego_vehicle.get_velocity()
        return math.sqrt(vel.x**2 + vel.y**2 + vel.z**2)

    def _make_header(self, frame_id: str) -> Header:
        h = Header()
        h.stamp = carla_to_ros_stamp(self)
        h.frame_id = frame_id
        return h

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
                ctrl.throttle = 0.02
        else:
            ctrl.reverse = True
            ctrl.throttle = min(abs(target_speed) * self.speed_kp, 1.0)
        ctrl.steer = max(-1.0, min(1.0, -steering_angle / CARLA_MAX_STEER_RAD))
        self.ego_vehicle.apply_control(ctrl)

    def _on_control_command(self, msg):
        if self.ego_vehicle:
            self._apply_control(msg.longitudinal.velocity, msg.longitudinal.acceleration, msg.lateral.steering_tire_angle)

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
        yaw = math.radians(-rot.yaw)

        # --- BROADCAST TF ---
        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = "map"
        t.child_frame_id = "base_link"
        t.transform.translation.x = loc.x
        t.transform.translation.y = -loc.y
        t.transform.translation.z = loc.z
        t.transform.rotation.z = math.sin(yaw / 2.0)
        t.transform.rotation.w = math.cos(yaw / 2.0)
        self.tf_broadcaster.sendTransform(t)

        # GNSS
        gnss = NavSatFix(header=self._make_header("gnss_link"))
        gnss.latitude = MAP_ORIGIN_LAT + loc.y / METERS_PER_DEG_LAT
        gnss.longitude = MAP_ORIGIN_LON + loc.x / METERS_PER_DEG_LON
        gnss.altitude = loc.z
        self.pub_gnss.publish(gnss)

        # IMU
        imu = Imu(header=self._make_header("imu_link"))
        imu.orientation.z = math.sin(yaw / 2.0)
        imu.orientation.w = math.cos(yaw / 2.0)
        self.pub_imu.publish(imu)

        # ODOMETRY
        odom = Odometry(header=self._make_header("map"))
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = loc.x
        odom.pose.pose.position.y = -loc.y
        odom.pose.pose.orientation.z = math.sin(yaw / 2.0)
        odom.pose.pose.orientation.w = math.cos(yaw / 2.0)
        self.pub_odom.publish(odom)

        if AUTOWARE_MSGS:
            v_rep = VelocityReport(header=self._make_header("base_link"))
            v_rep.longitudinal_velocity = float(self._current_speed())
            self.pub_vel.publish(v_rep)
            s_rep = SteeringReport(stamp=now)
            s_rep.steering_tire_angle = float(-self.ego_vehicle.get_control().steer * CARLA_MAX_STEER_RAD)
            self.pub_steer.publish(s_rep)

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