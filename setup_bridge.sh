#!/bin/bash

# ==========================================
# Install ROS2 Humble Desktop & Tools
# ==========================================
if [ ! -f "/opt/ros/humble/setup.bash" ]; then
    echo "ROS2 Humble not found. Installing..."
    sudo apt update && sudo apt install locales -y
    sudo locale-gen en_US en_US.UTF-8
    sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
    export LANG=en_US.UTF-8

    sudo apt install software-properties-common curl git -y
    sudo add-apt-repository universe -y
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

    sudo apt update
    sudo apt install ros-humble-desktop python3-colcon-common-extensions build-essential python3-rosdep ros-humble-tf2-eigen ros-humble-pcl-ros ros-humble-pcl-conversions python3-pip -y
else
    echo "ROS2 Humble is installed. Ensuring dependencies are met..."
    sudo apt update
    sudo apt install ros-humble-desktop python3-colcon-common-extensions build-essential python3-rosdep ros-humble-tf2-eigen ros-humble-pcl-ros ros-humble-pcl-conversions python3-pip -y
fi

sudo rosdep init || true
rosdep update

# ==========================================
# Install CARLA Python API
# ==========================================
echo "Installing CARLA Python API (0.9.16)..."
pip3 install carla==0.9.16

# ==========================================
# Setup CARLA ROS Bridge
# ==========================================

source /opt/ros/humble/setup.bash

echo "Cleaning up old workspace to ensure a fresh start..."
rm -rf $HOME/carla_ws/src/ros-bridge
rm -rf $HOME/carla_ws/build
rm -rf $HOME/carla_ws/install
rm -rf $HOME/carla_ws/log

mkdir -p $HOME/carla_ws/src
cd $HOME/carla_ws/src

echo "Cloning CARLA ROS Bridge..."
git clone --recurse-submodules https://github.com/carla-simulator/ros-bridge.git

echo "Applying Humble compatibility fixes safely..."
grep -rl "tf2_eigen/tf2_eigen.h" $HOME/carla_ws/src/ros-bridge/ | xargs -r sed -i 's/tf2_eigen\.h>/tf2_eigen\.hpp>/g'
grep -rl "tf2_geometry_msgs/tf2_geometry_msgs.h" $HOME/carla_ws/src/ros-bridge/ | xargs -r sed -i 's/tf2_geometry_msgs\.h>/tf2_geometry_msgs\.hpp>/g'

echo "Patching CARLA ROS Bridge hardcoded version check (0.9.13 -> 0.9.16)..."
grep -rl "0.9.13" $HOME/carla_ws/src/ros-bridge/ | xargs -r sed -i 's/0.9.13/0.9.16/g'

echo "Disabling non-essential pcl_recorder package..."
touch $HOME/carla_ws/src/ros-bridge/pcl_recorder/COLCON_IGNORE

cd $HOME/carla_ws
echo "Scanning for missing ROS dependencies..."
rosdep install --from-paths src --ignore-src -r -y

echo "Building the workspace..."
colcon build --symlink-install --continue-on-error

source install/setup.bash

# Force CycloneDDS so the bridge uses the same DDS implementation as the
# Autoware Docker container. Without this, FastDDS (ROS 2 default) and
# CycloneDDS (Autoware default) cannot discover each other's topics.
echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc

echo "CARLA ROS Bridge setup complete! Ready to launch."