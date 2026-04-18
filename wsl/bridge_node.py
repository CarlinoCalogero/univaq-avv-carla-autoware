#!/usr/bin/env python3
"""
CARLA <-> Autoware Bridge Node (Automated Initialization & Extensive Debug Version)
"""

import math
import os
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster

from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, NavSatFix
from std_msgs.msg import Header
from autoware_adapi_v1_msgs.srv import InitializeLocalization

# ── Modern Autoware message types ──────────────────────────────────────────
try:
    from autoware_control_msgs.msg import Control
    from autoware_vehicle_msgs.msg import SteeringReport, VelocityReport
    AUTOWARE_MSGS = True
    print("[BRIDGE] Success: Found Autoware message types.")
except ImportError:
    AUTOWARE_MSGS = False
    print("[BRIDGE] Warning: Autoware messages not found, using fallback logic.")

try:
    import carla
    print(f"[BRIDGE] Success: CARLA Python API loaded.")
except ImportError:
    raise ImportError("carla Python package not found.")

CARLA_MAX_STEER_RAD = math.radians(70.0)

class CarlaAutowareBridge(Node):
    def __init__(self):
        super().__init__("carla_autoware_bridge")

        self.declare_parameter("carla_host", "host.docker.internal")
        self.declare_parameter("carla_port", 2000)
        self.declare_parameter("ego_role_name", "ego_vehicle")

        self.carla_host = self.get_parameter("carla_host").value
        self.carla_port = self.get_parameter("carla_port").value
        self.role_name = self.get_parameter("ego_role_name").value

        # CARLA Connection
        print(f"[BRIDGE] Attempting to connect to CARLA at {self.carla_host}:{self.carla_port}...")
        try:
            self.client = carla.Client(self.carla_host, self.carla_port)
            self.client.set_timeout(5.0)
            self.world = self.client.get_world()
            print(f"[BRIDGE] Connected to CARLA world: {self.world.get_map().name}")
        except Exception as e:
            print(f"[BRIDGE] FATAL: Could not connect to CARLA: {e}")
            return

        self.ego_vehicle = None
        self.localization_initialized = False
        
        # Publishers
        self.tf_broadcaster = TransformBroadcaster(self)
        self.pub_gnss_pose = self.create_publisher(PoseWithCovarianceStamped, "/sensing/gnss/pose", 10)
        self.pub_imu = self.create_publisher(Imu, "/sensing/imu/imu_raw", 10)
        self.pub_odom = self.create_publisher(Odometry, "/localization/kinematic_state", 10)
        self.pub_vel = self.create_publisher(VelocityReport, "/vehicle/status/velocity_status", 10)
        self.pub_steer = self.create_publisher(SteeringReport, "/vehicle/status/steering_status", 10)

        # Autoware Initialization Service Client
        self.init_cli = self.create_client(InitializeLocalization, "/api/localization/initialize")
        print("[BRIDGE] Waiting for Autoware '/api/localization/initialize' service...")

        # Subscriptions
        self.create_subscription(Control, "/control/command/control_cmd", self._on_control_command, 10)
        
        # Timers
        self.create_timer(0.05, self._publish_vehicle_state)  # 20Hz Update
        self.create_timer(2.0, self._attempt_autoware_initialization) # 0.5Hz Init Loop
        
        print("[BRIDGE] Node fully initialized. Searching for ego_vehicle in CARLA...")

    def _find_ego_vehicle(self):
        actors = self.world.get_actors()
        for actor in actors:
            if actor.attributes.get("role_name") == self.role_name:
                self.ego_vehicle = actor
                print(f"[BRIDGE] Found vehicle with role '{self.role_name}' (ID: {actor.id})")
                return True
        return False

    def _attempt_autoware_initialization(self):
        """Service loop to force Autoware localization to turn on."""
        if self.localization_initialized:
            return

        if not self.ego_vehicle:
            print("[BRIDGE] Initialization waiting: Vehicle not yet found.")
            return

        if not self.init_cli.service_is_ready():
            print("[BRIDGE] Initialization waiting: Autoware service not ready.")
            return

        # Get current CARLA pose for the request
        transform = self.ego_vehicle.get_transform()
        loc = transform.location
        rot = transform.rotation
        yaw = math.radians(-rot.yaw)

        req = InitializeLocalization.Request()
        p = PoseWithCovarianceStamped()
        p.header.stamp = self.get_clock().now().to_msg()
        p.header.frame_id = "map"
        p.pose.pose.position.x = loc.x
        p.pose.pose.position.y = -loc.y
        p.pose.pose.orientation.z = math.sin(yaw / 2.0)
        p.pose.pose.orientation.w = math.cos(yaw / 2.0)
        
        req.pose = [p] # The ADAPI Initializer expects a list of poses

        print(f"[BRIDGE] ---> Sending Initialization Request to Autoware at ({loc.x:.2f}, {-loc.y:.2f})")
        future = self.init_cli.call_async(req)
        future.add_done_callback(self._init_callback)

    def _init_callback(self, future):
        try:
            response = future.result()
            if response.status.success:
                print("[BRIDGE] SUCCESS: Autoware EKF Localizer is now ACTIVATED.")
                self.localization_initialized = True
            else:
                print(f"[BRIDGE] Autoware Rejected Pose: {response.status.message}")
        except Exception as e:
            print(f"[BRIDGE] Initialization call failed: {e}")

    def _on_control_command(self, msg):
        if self.ego_vehicle:
            # Throttle and steering conversion
            ctrl = carla.VehicleControl()
            ctrl.throttle = min(msg.longitudinal.velocity * 0.1, 1.0)
            ctrl.steer = -msg.lateral.steering_tire_angle / CARLA_MAX_STEER_RAD
            self.ego_vehicle.apply_control(ctrl)
            # Print command every few seconds to verify Autoware is "driving"
            if self.get_clock().now().nanoseconds % 5000000000 < 50000000:
                print(f"[BRIDGE] Receiving control: Speed={msg.longitudinal.velocity:.2f}, Steer={ctrl.steer:.2f}")

    def _publish_vehicle_state(self):
        if not self.ego_vehicle:
            if not self._find_ego_vehicle():
                return

        now = self.get_clock().now().to_msg()
        transform = self.ego_vehicle.get_transform()
        velocity = self.ego_vehicle.get_velocity()
        loc = transform.location
        rot = transform.rotation
        yaw = math.radians(-rot.yaw)

        # Force speed to 0 if car is jittering (prevents 'vehicle not stopped' errors)
        real_speed = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
        reported_speed = 0.0 if real_speed < 0.2 else real_speed

        # TF map -> base_link
        t = TransformStamped()
        t.header.stamp, t.header.frame_id, t.child_frame_id = now, "map", "base_link"
        t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = loc.x, -loc.y, loc.z
        t.transform.rotation.z, t.transform.rotation.w = math.sin(yaw/2), math.cos(yaw/2)
        self.tf_broadcaster.sendTransform(t)

        # GNSS Pose (Initial guess for Autoware)
        gnss_pose = PoseWithCovarianceStamped()
        gnss_pose.header.stamp, gnss_pose.header.frame_id = now, "map"
        gnss_pose.pose.pose.position.x, gnss_pose.pose.pose.position.y = loc.x, -loc.y
        gnss_pose.pose.pose.orientation = t.transform.rotation
        self.pub_gnss_pose.publish(gnss_pose)

        # Velocity and IMU
        v_rep = VelocityReport()
        v_rep.header.stamp, v_rep.header.frame_id = now, "base_link"
        v_rep.longitudinal_velocity = float(reported_speed)
        self.pub_vel.publish(v_rep)

        imu = Imu()
        imu.header.stamp, imu.header.frame_id = now, "base_link"
        imu.orientation = t.transform.rotation
        self.pub_imu.publish(imu)

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