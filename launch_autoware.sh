#!/bin/bash

# 1. Ensure graphical utilities (xhost) are installed
if ! command -v xhost &> /dev/null; then
    echo "xhost not found. Installing graphical server utilities..."
    sudo apt update && sudo apt install x11-xserver-utils -y
fi

# 2. Navigate to your workspace
cd /mnt/c/Users/calog/Desktop/univaq-avv-carla-autoware/

# 3. Clone Autoware ONLY if the folder does not exist
if [ ! -d "autoware" ]; then
    echo "Cloning Autoware..."
    git clone https://github.com/autowarefoundation/autoware.git
else
    echo "Autoware directory already exists. Skipping clone..."
fi

# Navigate into the autoware folder
cd autoware

# Copy the launch file into the workspace so Docker mounts it
echo "Copying CARLA integration launch file..."
cp ../autoware_carla_integration.launch.py .

# 4. Launch the Docker container using the official script
echo "Launching Autoware Docker Container..."
bash docker/run.sh --devel