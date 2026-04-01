#!/bin/bash

# 1. Ensure graphical utilities (xhost) are installed
if ! command -v xhost &> /dev/null; then
    echo "xhost not found. Installing graphical server utilities..."
    sudo apt update && sudo apt install x11-xserver-utils -y
fi

# 2. Navigate to your workspace and clean the old failed attempt
cd /mnt/d/carla-autoware
rm -rf autoware

# 3. Clone a fresh copy of Autoware
echo "Cloning Autoware..."
git clone https://github.com/autowarefoundation/autoware.git
cd autoware

# 4. Launch the Docker container using the official script
echo "Launching Autoware Docker Container..."
bash docker/run.sh --devel