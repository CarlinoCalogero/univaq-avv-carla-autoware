#!/bin/bash

# Ensure graphical utilities (xhost) are installed
if ! command -v xhost &> /dev/null; then
    echo "xhost not found. Installing graphical server utilities..."
    sudo apt update && sudo apt install x11-xserver-utils -y
fi

# Grant Docker permission to draw on the X display (WSLg / X11).
# Without this call, RViz launches inside the container but its window
# is silently rejected by the display server and never appears.
if [ -n "$DISPLAY" ]; then
    xhost +local:root > /dev/null 2>&1
    echo "X display access granted (DISPLAY=$DISPLAY)"
else
    echo "WARNING: \$DISPLAY is not set — RViz will not open."
    echo "  Verify WSLg is active: 'echo \$DISPLAY' should print ':0'."
    echo "  On Windows 10 you need a separate X server (e.g. VcXsrv)."
fi

# Clone Autoware ONLY if the folder does not exist
if [ ! -d "autoware" ]; then
    echo "Cloning Autoware..."
    git clone https://github.com/autowarefoundation/autoware.git
else
    echo "Autoware directory already exists. Skipping clone..."
fi

# Navigate into the autoware folder
cd autoware

# Copy files into the workspace so Docker mounts them at /workspace/
echo "Copying CARLA integration launch file..."
cp ../autoware_carla_integration.launch.py .

echo "Copying Ackermann type converter..."
cp ../ackermann_converter.py .

# Launch the Docker container using the official script
echo "Launching Autoware Docker Container..."
echo ""
echo "================================================================"
echo " NEXT STEPS — run these commands inside the Docker container:   "
echo "================================================================"
echo ""
echo "  1. Source the workspace:"
echo "     cd /workspace && source boot.sh"
echo ""
echo "  2. Launch the full stack (uses e2e_simulator internally, RViz will open):"
echo ""
echo "     ros2 launch autoware_carla_integration.launch.py \\"
echo "       vehicle_name:=ego_vehicle \\"
echo "       map_path:=/workspace/Town01_map"
echo ""
echo "  3. Once Autoware is up and showing 'Waiting for initial pose',"
echo "     open a NEW WSL terminal and run:"
echo ""
echo "     cd ~/projects/univaq-avv-carla-autoware"
echo "     source .venv/bin/activate"
echo "     python3 get_exact_pose.py"
echo ""
echo "     The script sources ROS 2 internally and publishes"
echo "     /initialpose with a valid timestamp automatically."
echo "================================================================"
echo ""

bash docker/run.sh --devel
