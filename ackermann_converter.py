#!/usr/bin/env python3
"""
Ackermann type converter: bridges the type gap between Autoware and CARLA.

Autoware publishes:  /control/command/control_cmd
                     (autoware_auto_control_msgs/msg/AckermannControlCommand)

CARLA bridge expects: /carla/{vehicle_name}/ackermann_cmd
                      (ackermann_msgs/msg/AckermannDrive)

Run inside the Autoware Docker container:
  python3 /workspace/ackermann_converter.py [vehicle_name]
"""

import sys
import rclpy
from rclpy.node import Node
from autoware_auto_control_msgs.msg import AckermannControlCommand
from ackermann_msgs.msg import AckermannDrive


class AckermannConverter(Node):
    def __init__(self, vehicle_name: str):
        super().__init__('ackermann_converter')

        self._sub = self.create_subscription(
            AckermannControlCommand,
            '/control/command/control_cmd',
            self._callback,
            10
        )

        self._pub = self.create_publisher(
            AckermannDrive,
            f'/carla/{vehicle_name}/ackermann_cmd',
            10
        )

        self.get_logger().info(
            f'AckermannConverter ready: '
            f'/control/command/control_cmd -> /carla/{vehicle_name}/ackermann_cmd'
        )

    def _callback(self, msg: AckermannControlCommand):
        out = AckermannDrive()
        out.steering_angle          = msg.lateral.steering_tire_angle
        out.steering_angle_velocity = msg.lateral.steering_tire_rotation_rate
        out.speed                   = msg.longitudinal.speed
        out.acceleration            = msg.longitudinal.acceleration
        out.jerk                    = msg.longitudinal.jerk
        self._pub.publish(out)


def main():
    vehicle_name = sys.argv[1] if len(sys.argv) > 1 else 'ego_vehicle'
    rclpy.init()
    node = AckermannConverter(vehicle_name)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
