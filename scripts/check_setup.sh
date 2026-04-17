#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# check_setup.sh
# Verifies that all prerequisites are present in WSL before running the bridge.
# ─────────────────────────────────────────────────────────────────────────────

OK="\e[32m[OK]\e[0m"
WARN="\e[33m[WARN]\e[0m"
FAIL="\e[31m[FAIL]\e[0m"

echo "========================================================"
echo " CARLA-Autoware Bridge – Setup Check"
echo "========================================================"
echo ""

# ── ROS2 ──────────────────────────────────────────────────────────────────
if command -v ros2 &>/dev/null; then
    ROS_VER=$(ros2 --version 2>&1 | head -1)
    echo -e "$OK  ROS2 found: $ROS_VER"
else
    echo -e "$FAIL ROS2 not found."
    echo "    Install: https://docs.ros.org/en/humble/Installation.html"
fi

# ── rclpy ─────────────────────────────────────────────────────────────────
python3 -c "import rclpy" 2>/dev/null \
    && echo -e "$OK  rclpy importable" \
    || echo -e "$FAIL rclpy not importable (source /opt/ros/<distro>/setup.bash)"

# ── CARLA Python API ──────────────────────────────────────────────────────
CARLA_VER=$(python3 -c "import carla; print(carla.__version__)" 2>/dev/null)
if [[ -n "$CARLA_VER" ]]; then
    echo -e "$OK  carla Python package: $CARLA_VER"
else
    echo -e "$FAIL carla Python package not found."
    echo "    pip install carla==<your-carla-version>"
fi

# ── Autoware control msgs ─────────────────────────────────────────────────
python3 -c "from autoware_auto_control_msgs.msg import AckermannControlCommand" 2>/dev/null \
    && echo -e "$OK  autoware_auto_control_msgs available" \
    || echo -e "$WARN autoware_auto_control_msgs not found – bridge will use ackermann_msgs fallback"

python3 -c "from autoware_auto_vehicle_msgs.msg import VelocityReport" 2>/dev/null \
    && echo -e "$OK  autoware_auto_vehicle_msgs available" \
    || echo -e "$WARN autoware_auto_vehicle_msgs not found – VelocityReport / SteeringReport won't be published"

python3 -c "from ackermann_msgs.msg import AckermannDrive" 2>/dev/null \
    && echo -e "$OK  ackermann_msgs available (fallback)" \
    || echo -e "$WARN ackermann_msgs not available"

# ── Windows host IP ───────────────────────────────────────────────────────
echo ""
HOST_IP=$(ip route show | grep -i default | awk '{ print $3 }' | head -1)
echo "  Windows host IP (CARLA_HOST): $HOST_IP"

if [[ -n "$HOST_IP" ]]; then
    echo -n "  Testing CARLA port 2000 ... "
    if timeout 2 bash -c "echo >/dev/tcp/$HOST_IP/2000" 2>/dev/null; then
        echo -e "$OK reachable"
    else
        echo -e "$FAIL not reachable (is CARLA running on Windows?)"
    fi
fi

echo ""
echo "========================================================"
