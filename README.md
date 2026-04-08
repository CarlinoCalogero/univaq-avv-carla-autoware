# Autoware & CARLA Integration Template (Multi-Agent & Auto-Logging)
This repository serves as a robust template for integrating the CARLA Simulator with Autoware.Universe. It is designed for repeated testing and scalability, featuring automated simulation snapshots (CARLA) and ADAS data logging (ROS 2 Bags), as well as parameterized launch files to support multi-agent scenarios.

## Architecture
CARLA is a physics and rendering engine built on Unreal Engine. It outputs raw sensor data (LiDAR, Cameras) via a proprietary Python/C++ API. Autoware.Universe is an autonomous driving software stack built on Linux using ROS 2 (Robot Operating System). **They do not speak the same language**.

To bridge this gap, we create a continuous loop:
1. **The Body (CARLA)**: Generates the virtual physical world, 3D laser points, and camera pixels.
2. **The Nervous System (ROS 2 Bridge)**: Catches CARLA's Python API data and translates it into standardized ROS 2 messages.
3. **The Translator (`autoware_carla_integration.launch.py`)**: Relays those general ROS 2 messages directly into Autoware's specific intake topics.
4. **The Brain (Autoware in Docker)**: Processes the data through Localization, Perception, Planning, and Control modules in a fraction of a second.
5. **The Muscle**: Autoware spits out an Ackermann steering command, which is sent back across the bridge to physically turn the wheels of the car in CARLA.

## Prerequisites (The Setup)
Before touching the code, ensure you have the following installed on your Windows machine:
1. **WSL2 (Ubuntu)**: Install via PowerShell (`wsl --install -d Ubuntu-22.04`).
2. **Docker Desktop**: Install and ensure the WSL2 integration is enabled in its settings.

### Enable WS2 integration
1. Open Docker Desktop.
2. Click the Gear icon (`Settings`) in the top right.
3.  Go to `Resources` > `WSL Integration`.
4. Make sure `Enable integration with my default WSL distro` is checked, AND explicitly flip the switch on for your specific `Ubuntu-22.04` distro in the list below it.
5. Click `Apply & restart`.

## Phase 1: First-Time Setup & Build
*If you have already built Autoware and the Bridge once, you can skip to Phase 2.*

### Step 1: Set up the CARLA ROS Bridge
The bridge translates CARLA's environment into ROS 2.
1. Open your Ubuntu terminal as root by writing on PowerShell
```bash
wsl -d Ubuntu-22.04 -u root
```
Once the black terminal window opens, if you aren't sure which version you are in, just run:
```bash
lsb_release -r
```
2. Navigate to your folder by typing this command (replace YourUsername with your actual Windows username and PathToFolder to your actual path to this folder):
```bash
cd /mnt/c/Users/YourUsername/PathToFolder
```
3. Before you run the script, we need to strip out those invisible Windows carriage returns so Linux can read it cleanly. Run this exact command in your Ubuntu terminal:
```bash
sed -i 's/\r$//' setup_bridge.sh
```
*(Note: This silently fixes the file. It won't output anything if it works successfully).*

4. Because your script contains source commands (which set up environment variables for your active terminal), you cannot just "run" it like a normal program. If you do, it will run in a temporary background shell and immediately forget the variables when it finishes.
To apply the source commands to your current open terminal, you must run it using the source command itself:
```bash
source setup_bridge.sh
```
*This installs ROS 2 Humble, the CARLA Python API, and builds the bridge workspace.*

### Step 2: Deploy & Compile Autoware
Now we deploy the autonomous brain.
1. Start the Docker engine and open a brand new Ubuntu WSL2 terminal
```bash
wsl -d Ubuntu-22.04 -u root
```
2. Navigate to your folder by typing this command (replace YourUsername with your actual Windows username and PathToFolder to your actual path to this folder):
```bash
cd /mnt/c/Users/YourUsername/PathToFolder
```
3. Before you run the script, we need to strip out those invisible Windows carriage returns so Linux can read it cleanly. Run this exact command in your Ubuntu terminal:
```bash
sed -i 's/\r$//' launch_autoware.sh
```
*(Note: This silently fixes the file. It won't output anything if it works successfully).*

4. Because your script contains source commands (which set up environment variables for your active terminal), you cannot just "run" it like a normal program. If you do, it will run in a temporary background shell and immediately forget the variables when it finishes.
To apply the source commands to your current open terminal, you must run it using the source command itself:
```bash
source launch_autoware.sh
```

*(Note: You are now inside the Docker container. The following steps must be run in this container terminal).*

5. Navigate to the Shared Folder

First, let's make sure you are in the workspace folder that is magically linked to your Windows computer.

```bash
cd /workspace
```

6. Download the Universe Code

Autoware is massive, so it's split across hundreds of repositories. We will use a tool called vcs (Version Control System) to read the `autoware.repos` blueprint file and download all the actual code into a new src folder.

```bash
mkdir -p src
```

Import and FORCE sync all repositories to the correct versions

```bash
vcs import src --recursive --force < repositories/autoware.repos
```

7. Install Hidden Dependencies

Even though the Docker container comes with a lot of tools pre-installed, those hundreds of packages you just downloaded might need a few extra specific libraries to compile properly.

```bash
sudo apt update
```

8. Fix potential permission issues with rosdep in Docker

```bash
sudo rosdep fix-permissions
```

9. Update the package

```bash
rosdep update
```

10. Install all missing libraries for the packages in /src

```bash
rosdep install -y --from-paths src --ignore-src --rosdistro $ROS_DISTRO
```

11. Build the entire autonomous driving stack.

Building the whole stack takes a long time. To make this "reboot-friendly," we use `--continue-on-error`. If the build fails halfway through, you can run it again and it will pick up exactly where it left off instead of starting from zero.

```bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --continue-on-error
```

## Phase 2: Running the Simulation (Everyday Workflow)
### CRITICAL ORDER OF OPERATIONS: The Body Before The Brain
You must **always** spawn the physical vehicle in CARLA (Step 3) before you launch the Autoware integration (Step 4). If you launch Autoware first, it will fail to find the car's sensor topics and the integration will crash.

**The Golden Rule:** Start the World ➔ Start the Bridge ➔ Spawn the Car ➔ Boot the Brain.

### Step1: Launch the World & Recorder (Windows)
1. Open PowerShell, navigate to your CARLA installation folder, and launch the engine. It's best to force it to use a low-quality rendering mode if your GPU is going to be strained by running Autoware simultaneously:
```bash
.\CarlaUE4.exe -quality-level=Low -carla-rpc-port=2000 -dx11 -windowed -ResX=800 -ResY=600
```
2. Open a second PowerShell window, navigate to your integration folder, and start the automated recorder. This saves the physics snapshot so you can replay the exact scenario later:
```python
python3 start_simulation.py --host 127.0.0.1 --port 2000 --log_name run_001.log
```
(*Note: Press `Ctrl+C` in this window when you are done to safely save the log*).

### Step 2: Launch the Bridge (WSL Terminal 1)
1. Check your ip with `ipconfig` command in windows
2. Open a WSL terminal
```bash
wsl -d Ubuntu-22.04 -u root
```
3. Source your bridge
```bash
source /opt/ros/humble/setup.bash
```
```bash
source $HOME/carla_ws/install/setup.bash
```
4. Connect to CARLA (Update the host IP to your Windows IPv4 address):
```bash
ros2 launch carla_ros_bridge carla_ros_bridge.launch.py host:=192.168.1.12 port:=2000 timeout:=60
```

### Step 3: Spawn the Vehicle (WSL Terminal 2)
The bridge is running, but the world is empty. You must spawn a car and its sensors:
1. Check your ip with `ipconfig` command in windows
2. Open a WSL terminal
```bash
wsl -d Ubuntu-22.04 -u root
```
3. Source your bridge
```bash
source /opt/ros/humble/setup.bash
```
```bash
source $HOME/carla_ws/install/setup.bash
```
4. Spawn a car and its sensors
```bash
ros2 launch carla_spawn_objects carla_example_ego_vehicle.launch.py role_name:=ego_vehicle
```

### Step 4: Boot the Brain & Integrate (WSL Terminal 3 -> Docker)
Run your `launch_autoware.sh` script to enter the Docker container. Once inside, launch your integration:
1. Open a WSL terminal
```bash
wsl -d Ubuntu-22.04 -u root
```
2. Navigate to your folder by typing this command (replace YourUsername with your actual Windows username and PathToFolder to your actual path to this folder):
```bash
cd /mnt/c/Users/YourUsername/PathToFolder
```
3. Boot the Docker container
```bash
source launch_autoware.sh
```
4. Once inside the Docker container, source the built workspace
```bash
source install/setup.bash
```
5. Launch the integration
```bash
ros2 launch autoware_carla_integration.launch.py vehicle_name:=ego_vehicle
```
*Note: This script automatically starts a rosbag2 recorder to log your ADAS data.*

### Step 5: Command the Vehicle (RViz)
Autoware's 3D interface (RViz) will now open. To make the car drive:
1. **Localize**: Click "**2D Pose Estimate**" in the top toolbar and drag on the map where the car is currently sitting to align the LiDAR points.
2. **Route**: Click "**2D Goal Pose**" and click a destination on the road. Autoware will draw a trajectory line.
3. **Drive**: In the Autoware State panel, click "**Engage**" (or Autonomous mode). The car will begin driving in CARLA!

# Advanced: Multi-Agent Workflow
To run multiple autonomous vehicles interacting with each other, follow the golden rule: **One Docker Container = One Vehicle Brain**.
1. **Start the World & Bridge** (Follow Steps 1 & 2 above).
2. **Spawn Multiple Vehicles**: In your spawn terminal, drop two cars at different coordinates with unique names:
```bash
ros2 launch carla_spawn_objects carla_example_ego_vehicle.launch.py role_name:=ego_vehicle_1 spawn_point:="100,200,2,0,0,0"
```
```bash
ros2 launch carla_spawn_objects carla_example_ego_vehicle.launch.py role_name:=ego_vehicle_2 spawn_point:="110,200,2,0,0,0"
```
3. **Boot Agent 1**: Open a Docker terminal, source, and launch integration for Car 1:
```bash
ros2 launch autoware_carla_integration.launch.py vehicle_name:=ego_vehicle_1
```
4. **Boot Agent 2**: Open a completely new WSL terminal, run `launch_autoware.sh` to start a second Docker container, and launch for Car 2:
```bash
ros2 launch autoware_carla_integration.launch.py vehicle_name:=ego_vehicle_2
```

# Where are my logs?
This template generates two types of logs automatically:
* **CARLA Simulation Snapshots**: These `.log` files contain the physical state of the world (positions of all cars, pedestrians, traffic lights). They are saved on your Windows machine in your CARLA installation folder under `CarlaUE4/Saved/`. Use `client.replay_file("run_001.log")` to watch them in the simulator.
* **Autoware ADAS Bags**: These are raw ROS 2 data logs containing the LiDAR point clouds, camera feeds, and control commands generated by Autoware. They are saved directly to your shared `/workspace` folder as a directory (e.g., `/workspace/log_ego_vehicle_1`).