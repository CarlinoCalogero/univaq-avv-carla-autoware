# Autoware & CARLA Integration Template (Multi-Agent & Auto-Logging)
This repository serves as a robust template for integrating the CARLA Simulator with Autoware.Universe. It is designed for repeated testing and scalability, featuring automated simulation snapshots (CARLA) and ADAS data logging (ROS 2 Bags), as well as parameterized launch files to support multi-agent scenarios.

# Prerequisites (The Setup)
Before touching the code, ensure you have the following installed on your Windows machine:
1. **WSL2 (Ubuntu)**: Install this via PowerShell (`wsl --install -d Ubuntu-22.04`).
2. **Docker Desktop**: Install and ensure the WSL2 integration is enabled in its settings.

# Step 1: Launch the CARLA Simulation Environment & Recorder
You need CARLA running in server mode so Autoware can talk to it. We use a custom starter script to automatically begin recording the simulation snapshot.
1. Open your Windows command prompt or PowerShell.
2. Navigate to your CARLA installation folder and launch CARLA. It's best to force it to use a low-quality rendering mode if your GPU is going to be strained by running Autoware simultaneously:
```bash
.\CarlaUE4.exe -quality-level=Low -carla-rpc-port=2000 -dx11 -windowed -ResX=800 -ResY=600
```
3. Open a second PowerShell window, navigate to your integration folder, and start the automated recorder. This saves the physics snapshot so you can replay the exact scenario later:
```python
python3 start_simulation.py --host 127.0.0.1 --port 2000 --log_name run_001.log
```
(*Note: Press `Ctrl+C` in this window when you are done to safely save the log*).

# Step 2: Set up the CARLA ROS Bridge
The CARLA ROS Bridge is the translator between CARLA's Python API and Autoware's ROS2 middleware. It converts things like CARLA camera data into ROS2 Image messages.
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
5. Check your ip with `ipconfig` command in windows
6. Now, launch the bridge to connect to your Windows CARLA instance (WSL2 can communicate with Windows localhost). Replace with your ip:
```bash
ros2 launch carla_ros_bridge carla_ros_bridge.launch.py host:=192.168.1.12 port:=2000 timeout:=60
```
At this point, CARLA sensor topics are officially bridged to ROS2.

# Step 3: Deploy Autoware.Universe via Docker
Now we deploy the autonomous brain. The launch script is optimized to only download the massive Autoware repository once, saving time on future reboots.
1. Open Docker Desktop.
2. Click the Gear icon (Settings) in the top right.
3.  Go to Resources > WSL Integration.
4. Make sure "Enable integration with my default WSL distro" is checked, AND explicitly flip the switch on for your specific Ubuntu-22.04 distro in the list below it.
5. Click Apply & restart.
6. Now that Windows is hosting the Docker engine and sharing it with Ubuntu, open a brand new Ubuntu WSL2 terminal
7. Navigate to your folder by typing this command (replace YourUsername with your actual Windows username and PathToFolder to your actual path to this folder):
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
# Step 4: Download & Compile the Brain (First Run Only)
*If you have already built Autoware once, you can skip to Step 5.*

Inside your Docker container (`/workspace`), execute the following commands to download and force-sync the codebase, install dependencies, and compile.

1. Navigate to the Shared Folder

First, let's make sure you are in the workspace folder that is magically linked to your Windows computer.

```bash
cd /workspace
```

2. Download the Universe Code

Autoware is massive, so it's split across hundreds of repositories. We will use a tool called vcs (Version Control System) to read the `autoware.repos` blueprint file and download all the actual code into a new src folder.

```bash
mkdir -p src
```

Import and FORCE sync all repositories to the correct versions

```bash
vcs import src --recursive --force < repositories/autoware.repos
```

3. Install Hidden Dependencies

Even though the Docker container comes with a lot of tools pre-installed, those hundreds of packages you just downloaded might need a few extra specific libraries to compile properly.

```bash
sudo apt update
```

Fix potential permission issues with rosdep in Docker

```bash
sudo rosdep fix-permissions
```

```bash
rosdep update
```

Install all missing libraries for the packages in /src

```bash
rosdep install -y --from-paths src --ignore-src --rosdistro $ROS_DISTRO
```

4. Compile the Brain (The Big One)

Now, we build the entire autonomous driving stack.

Building the whole stack takes a long time. To make this "reboot-friendly," we use `--continue-on-error`. If the build fails halfway through, you can run it again and it will pick up exactly where it left off instead of starting from zero.

```bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --continue-on-error
```

# Step 5: Launch the Integration (Multi-Agent Support)
This is the core of "Injecting Autoware into CARLA." The launch file automatically maps sensors, relays control commands, and spins up a rosbag2 recorder for ADAS analysis.

Because this is a template, you must define the vehicle_name when launching. One Docker container = One Vehicle Brain.
1. Source your newly built workspace:
```bash
source install/setup.bash
```
Launch the integration for your specific agent:
```bash
ros2 launch autoware_carla_integration.launch.py vehicle_name:=ego_vehicle_1
```

# Running Multiple Agents?
If you spawn a second autonomous vehicle in CARLA, simply open a new WSL terminal, run Step 3 to open a second Docker container, and launch the integration with the new name:
```bash
ros2 launch autoware_carla_integration.launch.py vehicle_name:=ego_vehicle_2
```

# Where are my logs?
This template generates two types of logs automatically:
* CARLA Simulation Snapshots: These `.log` files contain the physical state of the world (positions of all cars, pedestrians, traffic lights). They are saved on your Windows machine in your CARLA installation folder under `CarlaUE4/Saved/`. Use `client.replay_file("run_001.log")` to watch them in the simulator.
* Autoware ADAS Bags: These are raw ROS 2 data logs containing the LiDAR point clouds, camera feeds, and control commands generated by Autoware. They are saved directly to your shared `/workspace` folder as a directory (e.g., `/workspace/log_ego_vehicle_1`).