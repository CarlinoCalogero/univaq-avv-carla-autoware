#!/usr/bin/env python3
"""
CARLA <-> Autoware Bridge Node (Automated Initialization & Point Cloud)
"""

import math
import os
import rclpy
import numpy as np
from rclpy.node import Node
from tf2_ros import TransformBroadcaster

from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, NavSatFix, PointCloud2, PointField
from std_msgs.msg import Header
from autoware_adapi_v1_msgs.srv import InitializeLocalization

try:
    from autoware_control_msgs.msg import Control
    from autoware_vehicle_msgs.msg import SteeringReport, VelocityReport
    AUTOWARE_MSGS = True
    print("[BRIDGE] Success: Found Autoware message types.")
except ImportError:
    AUTOWARE_MSGS = False
    print("[BRIDGE] Warning: Autoware messages not found, using fallback logic.")

try:
    from autoware_perception_msgs.msg import PredictedObjects
    PERCEPTION_MSGS = True
    print("[BRIDGE] Success: Found autoware_perception_msgs.")
except ImportError:
    try:
        from autoware_auto_perception_msgs.msg import PredictedObjects
        PERCEPTION_MSGS = True
        print("[BRIDGE] Success: Found autoware_auto_perception_msgs.")
    except ImportError:
        PERCEPTION_MSGS = False
        print("[BRIDGE] Warning: PredictedObjects not found — dynamic_object stub disabled.")

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
        self.lidar_sensor = None
        self.localization_initialized = False
        self.init_sent = False
        self.last_control_time = 0 
        
        self.tf_broadcaster = TransformBroadcaster(self)
        self.pub_gnss_pose = self.create_publisher(PoseWithCovarianceStamped, "/sensing/gnss/pose", 10)
        self.pub_gnss_cov = self.create_publisher(PoseWithCovarianceStamped, "/sensing/gnss/pose_with_covariance", 10)
        
        self.pub_imu = self.create_publisher(Imu, "/sensing/imu/imu_raw", 10)
        # Publish directly to imu_corrector output: the imu_corrector node receives
        # nothing (wrong input topic in the sensor kit), so its output is dead.
        # This bypasses it and ensures gyro_odometer gets angular velocity data.
        self.pub_imu_corrected = self.create_publisher(Imu, "/sensing/imu/imu_corrector/imu", 10)
        self.pub_vel = self.create_publisher(VelocityReport, "/vehicle/status/velocity_status", 10)
        self.pub_steer = self.create_publisher(SteeringReport, "/vehicle/status/steering_status", 10)
        
        self.pub_lidar = self.create_publisher(PointCloud2, "/sensing/lidar/concatenated/pointcloud", 10)

        if PERCEPTION_MSGS:
            self.pub_objects = self.create_publisher(
                PredictedObjects, "/perception/object_recognition/objects", 10)
        else:
            self.pub_objects = None

        self.init_cli = self.create_client(InitializeLocalization, "/api/localization/initialize")

        self.create_subscription(Control, "/control/command/control_cmd", self._on_control_command, 10)
        
        self.create_timer(0.05, self._publish_vehicle_state) 
        self.create_timer(2.0, self._attempt_autoware_initialization) 
        
        print("[BRIDGE] Node fully initialized. Searching for ego_vehicle in CARLA...")

    def _find_actors(self):
        actors = self.world.get_actors()
        found_ego = False
        for actor in actors:
            if actor.attributes.get("role_name") == self.role_name:
                if not self.ego_vehicle:
                    self.ego_vehicle = actor
                    print(f"[BRIDGE] Found vehicle with role '{self.role_name}' (ID: {actor.id})")
                found_ego = True
            elif actor.attributes.get("role_name") == "lidar_sensor":
                if not self.lidar_sensor:
                    self.lidar_sensor = actor
                    self.lidar_sensor.listen(self._on_lidar_data)
                    print(f"[BRIDGE] Found lidar_sensor (ID: {actor.id}). Started publishing PointCloud2.")
        return found_ego

    def _on_lidar_data(self, carla_lidar_measurement):
        raw_data = np.frombuffer(carla_lidar_measurement.raw_data, dtype=np.float32)
        points = np.reshape(raw_data, (-1, 4))
        num_points = points.shape[0]

        dt = np.dtype({
            'names': ['x', 'y', 'z', 'intensity', 'return_type', 'channel', 'time_stamp'],
            'formats': ['<f4', '<f4', '<f4', 'u1', 'u1', '<u2', '<u4'],
            'offsets': [0, 4, 8, 12, 13, 14, 16],
            'itemsize': 32
        })
        
        structured_points = np.zeros(num_points, dtype=dt)
        structured_points['x'] = points[:, 0]
        structured_points['y'] = -points[:, 1]
        structured_points['z'] = points[:, 2]
        structured_points['intensity'] = (points[:, 3] * 255.0).astype(np.uint8)

        msg = PointCloud2()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "velodyne_top"
        msg.height = 1
        msg.width = num_points
        msg.is_dense = True
        msg.is_bigendian = False
        msg.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name='intensity', offset=12, datatype=PointField.UINT8, count=1),
            PointField(name='return_type', offset=13, datatype=PointField.UINT8, count=1),
            PointField(name='channel', offset=14, datatype=PointField.UINT16, count=1),
            PointField(name='time_stamp', offset=16, datatype=PointField.UINT32, count=1),
        ]
        msg.point_step = 32
        msg.row_step = msg.point_step * num_points
        msg.data = structured_points.tobytes()
        
        self.pub_lidar.publish(msg)

    def _attempt_autoware_initialization(self):
        if self.localization_initialized or self.init_sent or not self.ego_vehicle:
            return

        if not self.init_cli.service_is_ready():
            return

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
        p.pose.pose.position.z = loc.z  
        p.pose.pose.orientation.z = math.sin(yaw / 2.0)
        p.pose.pose.orientation.w = math.cos(yaw / 2.0)
        
        req.pose = [p] 

        self.init_sent = True
        print(f"[BRIDGE] ---> Sending Init Request to Autoware at (X:{loc.x:.1f}, Y:{-loc.y:.1f}, Z:{loc.z:.1f})")
        future = self.init_cli.call_async(req)
        future.add_done_callback(self._init_callback)

    def _init_callback(self, future):
        try:
            response = future.result()
            if response.status.success:
                print("\n[BRIDGE] SUCCESS: Autoware EKF Localizer is now ACTIVATED.\n")
                self.localization_initialized = True
            else:
                print(f"[BRIDGE] Autoware Rejected Pose: {response.status.message}")
                self.init_sent = False
        except Exception as e:
            print(f"[BRIDGE] Initialization call failed: {e}")
            self.init_sent = False

    def _on_control_command(self, msg):
        self.last_control_time = self.get_clock().now().nanoseconds
        
        if self.ego_vehicle:
            ctrl = carla.VehicleControl()
            target_vel = msg.longitudinal.velocity
            
            print(f"\r[CONTROL] Autoware Target Vel: {target_vel:>5.2f} m/s  |  ", end="")
            
            if target_vel > 0.1:
                ctrl.throttle = min(target_vel * 0.1, 1.0)
                ctrl.brake = 0.0
                ctrl.hand_brake = False
                ctrl.reverse = False
                print(f"ACTION: Throttle ({ctrl.throttle:.2f})", end="")
            elif target_vel < -0.1:
                ctrl.throttle = min(abs(target_vel) * 0.1, 1.0)
                ctrl.brake = 0.0
                ctrl.hand_brake = False
                ctrl.reverse = True
                print(f"ACTION: Reverse  ({ctrl.throttle:.2f})", end="")
            else:
                ctrl.throttle = 0.0
                ctrl.brake = 1.0 
                ctrl.hand_brake = True
                print("ACTION: HARD BRAKE LOCKED", end="")
                
            ctrl.steer = -msg.lateral.steering_tire_angle / CARLA_MAX_STEER_RAD
            self.ego_vehicle.apply_control(ctrl)

    def _publish_vehicle_state(self):
        if not self._find_actors():
            return

        now = self.get_clock().now().to_msg()
        current_time_ns = self.get_clock().now().nanoseconds
        
        if (current_time_ns - self.last_control_time) > 500_000_000:
            ctrl = carla.VehicleControl()
            ctrl.throttle = 0.0
            ctrl.steer = 0.0
            ctrl.brake = 1.0           
            ctrl.hand_brake = True     
            ctrl.manual_gear_shift = True
            ctrl.gear = 0
            self.ego_vehicle.apply_control(ctrl)

        transform = self.ego_vehicle.get_transform()
        velocity = self.ego_vehicle.get_velocity()
        loc = transform.location
        rot = transform.rotation

        real_speed = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
        reported_speed = 0.0 if real_speed < 0.2 else real_speed

        t_lidar = TransformStamped()
        t_lidar.header.stamp, t_lidar.header.frame_id, t_lidar.child_frame_id = now, "base_link", "velodyne_top"
        t_lidar.transform.translation.z = 2.4
        t_lidar.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t_lidar)

        # ---> CRITICAL FIX 1: Stop publishing GNSS after NDT wakes up to prevent EKF panic
        if not self.localization_initialized:
            gnss_pose = PoseWithCovarianceStamped()
            gnss_pose.header.stamp, gnss_pose.header.frame_id = now, "map"
            gnss_pose.pose.pose.position.x = loc.x
            gnss_pose.pose.pose.position.y = -loc.y
            gnss_pose.pose.pose.position.z = loc.z 
            yaw_rad = math.radians(-rot.yaw)
            gnss_pose.pose.pose.orientation.z = math.sin(yaw_rad/2)
            gnss_pose.pose.pose.orientation.w = math.cos(yaw_rad/2)
            
            gnss_pose.pose.covariance = [
                1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.01, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.01, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.05
            ]
            self.pub_gnss_pose.publish(gnss_pose)
            self.pub_gnss_cov.publish(gnss_pose) 

        v_rep = VelocityReport()
        v_rep.header.stamp, v_rep.header.frame_id = now, "base_link"
        v_rep.longitudinal_velocity = float(reported_speed)
        v_rep.heading_rate = 0.0
        self.pub_vel.publish(v_rep)

        steer = SteeringReport()
        steer.stamp = now
        steer.steering_tire_angle = float(self.ego_vehicle.get_control().steer * CARLA_MAX_STEER_RAD)
        self.pub_steer.publish(steer)

        # ---> CRITICAL FIX 2: Full 3D Orientation math for IMU so the car doesn't slide on hills
        imu = Imu()
        imu.header.stamp, imu.header.frame_id = now, "base_link"
        cr = math.cos(math.radians(-rot.roll) * 0.5)
        sr = math.sin(math.radians(-rot.roll) * 0.5)
        cp = math.cos(math.radians(-rot.pitch) * 0.5)
        sp = math.sin(math.radians(-rot.pitch) * 0.5)
        cy = math.cos(math.radians(-rot.yaw) * 0.5)
        sy = math.sin(math.radians(-rot.yaw) * 0.5)
        
        imu.orientation.w = cr * cp * cy + sr * sp * sy
        imu.orientation.x = sr * cp * cy - cr * sp * sy
        imu.orientation.y = cr * sp * cy + sr * cp * sy
        imu.orientation.z = cr * cp * sy - sr * sp * cy
        
        cov = [0.0] * 9
        cov[0], cov[4], cov[8] = 0.01, 0.01, 0.01
        imu.orientation_covariance = cov
        imu.angular_velocity_covariance = cov
        imu.linear_acceleration_covariance = cov
        
        imu.linear_acceleration.z = 9.81

        # Angular velocity from CARLA physics (convert left-handed → ROS right-handed: negate y and z)
        av = self.ego_vehicle.get_angular_velocity()  # degrees/s in CARLA world frame
        imu.angular_velocity.x =  math.radians( av.x)
        imu.angular_velocity.y =  math.radians(-av.y)
        imu.angular_velocity.z =  math.radians(-av.z)

        self.pub_imu.publish(imu)
        self.pub_imu_corrected.publish(imu)

        if self.pub_objects:
            empty_objects = PredictedObjects()
            empty_objects.header.stamp = now
            empty_objects.header.frame_id = "map"
            self.pub_objects.publish(empty_objects)

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