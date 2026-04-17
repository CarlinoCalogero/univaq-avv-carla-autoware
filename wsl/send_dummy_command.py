#!/usr/bin/env python3
"""
Dummy command sender + live verifier
====================================
1. Publishes a constant forward control command to /control/command/control_cmd
   (the same topic the bridge_node is subscribed to).
2. Connects directly to CARLA via Python API to read the ego_vehicle position
   and prints live distance / speed.
3. After --duration seconds it sends a stop command and prints a PASS/FAIL result.

You should VISUALLY see the car moving in the CARLA spectator window.

Usage (WSL terminal):
    # Make sure bridge_node.py is running in another terminal first!
    python3 send_dummy_command.py \
        --carla-host 172.x.x.x \
        --target-speed 5.0 \
        --duration 10

Environment variable alternative:
    CARLA_HOST=172.x.x.x python3 send_dummy_command.py
"""

import argparse
import math
import os
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Header

try:
    from autoware_auto_control_msgs.msg import AckermannControlCommand

    AUTOWARE_MSGS = True
except ImportError:
    try:
        from ackermann_msgs.msg import AckermannDrive

        AUTOWARE_MSGS = False
    except ImportError:
        raise ImportError(
            "Install autoware_auto_control_msgs or ackermann_msgs before running."
        )

try:
    import carla
except ImportError:
    raise ImportError(
        "carla Python package not found.\n"
        "pip install carla==<your-carla-version>"
    )


# ─────────────────────────────────────────────────────────────────────────────
class DummyCommandSender(Node):
    def __init__(self, carla_host: str, carla_port: int, target_speed: float, duration: float):
        super().__init__("dummy_command_sender")

        self.target_speed = target_speed
        self.duration = duration
        self.start_time = time.time()
        self.last_log_second = -1

        # ── ROS2 publisher ────────────────────────────────────────────────
        if AUTOWARE_MSGS:
            self.pub = self.create_publisher(
                AckermannControlCommand, "/control/command/control_cmd", 10
            )
            self.get_logger().info(
                "Publishing AckermannControlCommand -> /control/command/control_cmd"
            )
        else:
            self.pub = self.create_publisher(
                AckermannDrive, "/control/command/control_cmd", 10
            )
            self.get_logger().info(
                "Publishing AckermannDrive -> /control/command/control_cmd"
            )

        # ── Direct CARLA connection for monitoring ────────────────────────
        self.ego_vehicle = None
        self.initial_location = None
        try:
            self.get_logger().info(f"Connecting to CARLA at {carla_host}:{carla_port} for monitoring ...")
            carla_client = carla.Client(carla_host, carla_port)
            carla_client.set_timeout(5.0)
            world = carla_client.get_world()
            for actor in world.get_actors():
                if actor.attributes.get("role_name") == "ego_vehicle":
                    self.ego_vehicle = actor
                    self.initial_location = actor.get_location()
                    self.get_logger().info(
                        f"Monitoring ego_vehicle id={actor.id}  "
                        f"start=({self.initial_location.x:.2f}, {self.initial_location.y:.2f})"
                    )
                    break
            if self.ego_vehicle is None:
                self.get_logger().warn(
                    "Ego vehicle not found in CARLA – movement cannot be verified. "
                    "Run windows/spawn_vehicle.py first."
                )
        except Exception as exc:
            self.get_logger().warn(f"Could not connect to CARLA for monitoring: {exc}")

        self.get_logger().info(
            f"Sending target_speed={target_speed} m/s ({target_speed * 3.6:.1f} km/h) "
            f"for {duration} s – watch the CARLA window!"
        )
        self.get_logger().info("-" * 60)

        # 10 Hz command loop
        self.timer = self.create_timer(0.1, self._tick)

    # ── timer callback ────────────────────────────────────────────────────

    def _tick(self):
        elapsed = time.time() - self.start_time

        if elapsed >= self.duration:
            self._send_stop()
            self._report()
            self.timer.cancel()
            # Give the stop command a moment to propagate, then shutdown
            time.sleep(0.3)
            rclpy.shutdown()
            return

        self._send_drive(self.target_speed, accel=2.0, steer=0.0)
        self._log_progress(elapsed)

    def _send_drive(self, speed: float, accel: float, steer: float):
        if AUTOWARE_MSGS:
            msg = AckermannControlCommand()
            msg.stamp = self.get_clock().now().to_msg()
            msg.longitudinal.speed = float(speed)
            msg.longitudinal.acceleration = float(accel)
            msg.lateral.steering_tire_angle = float(steer)
        else:
            msg = AckermannDrive()
            msg.speed = float(speed)
            msg.acceleration = float(accel)
            msg.steering_angle = float(steer)
        self.pub.publish(msg)

    def _send_stop(self):
        self.get_logger().info("Duration reached – sending STOP command ...")
        self._send_drive(speed=0.0, accel=-5.0, steer=0.0)

    def _log_progress(self, elapsed: float):
        current_second = int(elapsed)
        if current_second == self.last_log_second:
            return
        self.last_log_second = current_second

        if self.ego_vehicle is None:
            return
        loc = self.ego_vehicle.get_location()
        vel = self.ego_vehicle.get_velocity()
        speed = math.sqrt(vel.x ** 2 + vel.y ** 2 + vel.z ** 2)
        dist = math.sqrt(
            (loc.x - self.initial_location.x) ** 2
            + (loc.y - self.initial_location.y) ** 2
        )
        self.get_logger().info(
            f"[{elapsed:4.1f}s]  "
            f"pos=({loc.x:.2f}, {loc.y:.2f})  "
            f"dist_moved={dist:.2f} m  "
            f"speed={speed:.2f} m/s ({speed * 3.6:.1f} km/h)"
        )

    def _report(self):
        print()
        print("=" * 60)
        print("TEST RESULT")
        print("=" * 60)
        if self.ego_vehicle is None or self.initial_location is None:
            print("UNKNOWN – could not connect to CARLA for position verification.")
            print("Check bridge_node.py is running and CARLA is reachable from WSL.")
        else:
            final = self.ego_vehicle.get_location()
            dist = math.sqrt(
                (final.x - self.initial_location.x) ** 2
                + (final.y - self.initial_location.y) ** 2
            )
            print(f"  Initial position : ({self.initial_location.x:.2f}, {self.initial_location.y:.2f})")
            print(f"  Final position   : ({final.x:.2f}, {final.y:.2f})")
            print(f"  Total distance   : {dist:.2f} m")
            print()
            if dist > 0.5:
                print("  ✓  PASS – vehicle moved in CARLA!")
            else:
                print("  ✗  FAIL – vehicle did not move.")
                print("     Check:")
                print("       1. bridge_node.py is running")
                print("       2. CARLA_HOST / carla_host parameter is correct")
                print("       3. spawn_vehicle.py is running on Windows")
        print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Send dummy Autoware control command and verify CARLA movement")
    parser.add_argument(
        "--carla-host",
        default=os.environ.get("CARLA_HOST", "172.28.0.1"),
        help="Windows host IP reachable from WSL2 (default: $CARLA_HOST or 172.28.0.1)",
    )
    parser.add_argument("--carla-port", type=int, default=2000, help="CARLA port (default: 2000)")
    parser.add_argument("--target-speed", type=float, default=5.0, help="Target speed in m/s (default: 5.0)")
    parser.add_argument("--duration", type=float, default=10.0, help="Test duration in seconds (default: 10)")
    args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)
    node = DummyCommandSender(
        carla_host=args.carla_host,
        carla_port=args.carla_port,
        target_speed=args.target_speed,
        duration=args.duration,
    )
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, Exception):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    main()
