# Autoware & CARLA Integration Template (Multi-Agent & Auto-Logging)
This repository serves as a robust template for integrating the CARLA Simulator with Autoware.Universe. It is designed for repeated testing and scalability, featuring automated simulation snapshots (CARLA) and ADAS data logging (ROS 2 Bags), as well as parameterized launch files to support multi-agent scenarios.

## Architecture
CARLA is a physics and rendering engine built on Unreal Engine. It outputs raw sensor data (LiDAR, Cameras) via a proprietary Python/C++ API. Autoware.Universe is an autonomous driving software stack built on Linux using ROS 2 (Robot Operating System). **They do not speak the same language**.

To bridge this gap, we create a continuous loop:
1. **The Body (CARLA)**: Generates the virtual physical world, 3D laser points, and camera pixels.
2. **The Nervous System (ROS 2 Bridge)**: Catches CARLA's Python API data and translates it into standardized ROS 2 messages.
3. **The Translator (`autoware_carla_integration.launch.py`)**: Launches the nodes that remap and relay those general ROS 2 messages into Autoware's specific intake topics.
4. **The Brain (Autoware in Docker)**: Processes the data through Localization, Perception, Planning, and Control modules.
5. **The Muscle (`ackermann_converter.py`)**: Autoware outputs a control command of type `AckermannControlCommand`. The CARLA bridge however expects a different type (`AckermannDrive`). This converter node runs alongside Autoware, subscribes to Autoware's control output, translates the message type, and republishes it to the CARLA bridge so it can physically turn the wheels of the car in CARLA.

## Prerequisites (The Setup)
Before touching the code, ensure you have the following installed on your Windows machine.

**Software:**
1. **WSL2 (Ubuntu 22.04)**: Install via PowerShell (`wsl --install -d Ubuntu-22.04`).
2. **Docker Desktop**: Install and ensure the WSL2 integration is enabled in its settings.
3. **CARLA Simulator 0.9.16**: Download from the [official CARLA releases page](https://github.com/carla-simulator/carla/releases/tag/0.9.16) and install it on your Windows machine.

**Hardware (Minimum Recommended):**
- **GPU**: A dedicated NVIDIA GPU is required for CARLA's Unreal Engine renderer. CUDA support is recommended for Autoware's perception modules.
- **RAM**: 32 GB recommended (16 GB minimum; the Autoware build alone peaks near 16 GB, and running CARLA simultaneously requires headroom).
- **Disk**: 100 GB of free space on the Linux filesystem. The Autoware build, Docker image, and downloaded source packages consume 50–100 GB combined.
- **OS**: Windows 11 (Build 22000 or later), required for WSLg GUI support (see below).

### Enable WSL2 Integration
1. Open Docker Desktop.
2. Click the Gear icon (`Settings`) in the top right.
3. Go to `Resources` > `WSL Integration`.
4. Make sure `Enable integration with my default WSL distro` is checked, AND explicitly flip the switch on for your specific `Ubuntu-22.04` distro in the list below it.
5. Click `Apply & restart`.

### Enable GUI Display (Required for RViz)
Autoware's 3D interface (RViz) runs inside a Docker container and must draw its window on your Windows desktop. This is handled through **WSLg**, which is built into Windows 11 and provides a display server automatically. The `launch_autoware.sh` script takes care of the Docker side — you only need to confirm WSLg is active in WSL2.

**Verify WSLg is working:**
1. Open your Ubuntu terminal.
```bash
wsl -d Ubuntu-22.04 -u root
```

2. run:
```bash
echo $DISPLAY
```
You should see `:0` or similar. If the output is empty, WSLg is not active — ensure your Windows 11 is fully up to date.

3. Test with a sample GUI app:
```bash
sudo apt install -y x11-apps && xclock
```
A clock window should appear on your Windows desktop. If it does, RViz will work correctly. You can close the clock.

> **Windows 10 users**: WSLg is not available. You must install a third-party X11 server such as [VcXsrv](https://sourceforge.net/projects/vcxsrv/). After launching it (with "Disable access control" checked), run this in your WSL2 terminal before entering Docker:
> ```bash
> export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0.0
> ```

## CRITICAL: Performance Warning (Filesystem Location)
WSL2 is incredibly fast, but only if your files live inside the Linux filesystem. If your project folder is currently on your Windows `C:\` drive (e.g., Desktop or Documents), Autoware will take 10+ hours to compile and the simulation will lag.

**You must move this folder to the Linux home directory before starting Phase 1.**

### How to move the folder to the "Fast Lane":
1. Open your Ubuntu terminal.
```bash
wsl -d Ubuntu-22.04 -u root
```
2. Create a projects directory:
```bash
mkdir -p ~/projects
```
3. Move the folder from Windows to Linux (replace `<YourWindowsUser>` with your actual Windows username):
```bash
mv /mnt/c/Users/<YourWindowsUser>/Desktop/univaq-avv-carla-autoware ~/projects/
```
4. Navigate to the new location:
```bash
cd ~/projects/univaq-avv-carla-autoware
```
*Note: To edit files from Windows, type `\\wsl$\Ubuntu-22.04\home\` into your Windows File Explorer address bar. You can use VS Code or Notepad here just like a normal folder, but it will run at native Linux speeds.*

## Phase 1: First-Time Setup & Build
*If you have already built Autoware and the Bridge once, you can skip to Phase 2.*

### Step 0: Set Permissions
Because we moved the files from Windows, we need to tell Linux that the setup scripts are allowed to execute.
1. Run this command inside your project folder:
```bash
chmod +x *.sh
```

### Step 1: Set up the CARLA ROS Bridge
The bridge translates CARLA's environment into ROS 2.
1. Open your Ubuntu terminal as root by running the following in PowerShell:
```bash
wsl -d Ubuntu-22.04 -u root
```
Once the black terminal window opens, if you aren't sure which version you are in, just run:
```bash
lsb_release -r
```
2. Navigate to your folder:
```bash
cd ~/projects/univaq-avv-carla-autoware
```
3. Before you run the script, strip out any invisible Windows carriage returns so Linux can read it cleanly:
```bash
sed -i 's/\r$//' setup_bridge.sh
```
*(Note: This silently fixes the file. It won't output anything if it works successfully).*

4. Because the script contains `source` commands (which set up environment variables for your active terminal), you cannot just "run" it like a normal program — it would execute in a temporary subshell and immediately forget the variables when it finishes. To apply the `source` commands to your current terminal, use the `source` command itself:
```bash
source setup_bridge.sh
```
*This installs ROS 2 Humble, the CARLA Python API, and builds the bridge workspace.*

5. Install the CycloneDDS RMW implementation. The Autoware Docker container uses CycloneDDS by default. If the bridge uses a different DDS (FastDDS is the ROS 2 Humble default), the two sides cannot discover each other's topics and CARLA sensor data will be completely invisible inside Docker. Run this **after** `setup_bridge.sh` completes (it requires the ROS 2 apt repository to already be configured):
```bash
sudo apt install ros-humble-rmw-cyclonedds-cpp -y
```
This also permanently adds `export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` to your `~/.bashrc`, so every new WSL terminal you open from now on will have it set automatically.

6. Close this terminal. The bridge environment is now built. The next step runs inside a Docker container, which has its own isolated environment, so we start fresh.

### Step 2: Deploy & Compile Autoware
Now we deploy the autonomous brain.
1. Start the Docker engine and open a brand new Ubuntu WSL2 terminal:
```bash
wsl -d Ubuntu-22.04 -u root
```
2. Navigate to your folder:
```bash
cd ~/projects/univaq-avv-carla-autoware
```
3. Strip out Windows carriage returns from the launch script (same reason as Step 1):
```bash
sed -i 's/\r$//' launch_autoware.sh
```
*(Note: This silently fixes the file. It won't output anything if it works successfully).*

4. Launch the Docker container:
```bash
bash launch_autoware.sh
```
The script copies `autoware_carla_integration.launch.py` and `ackermann_converter.py` into the `autoware/` folder automatically so Docker can find them at `/workspace/`. It then prints a recap of the commands to run inside the container before opening the shell.

*(Note: You are now inside the Docker container. The following steps must be run in this container terminal).*

5. Navigate to the workspace:
```bash
cd /workspace
```
*This folder is a Docker volume mount — any files you create or modify here are directly reflected on your Linux filesystem at `~/projects/univaq-avv-carla-autoware/autoware/`, and vice versa.*

6. Prepare the source directory

Autoware is split across hundreds of repositories. We will use `vcs` (Version Control System) to fetch all of them. First, create the target folder:
```bash
mkdir -p src
```

7. Because `/workspace` is a shared volume, the file ownership can get mixed up. The Docker container runs as `root`, but it sees files created by your Linux user. Git flags this as a potential security risk ("dubious ownership") and refuses to operate. This single command tells Git to trust all paths inside the container:
```bash
git config --global --add safe.directory "*"
```

8. Import and force-sync all repositories to the correct versions:
```bash
vcs import src --recursive --force < repositories/autoware.repos
```
*This file is part of the Autoware repository and lists every package and its pinned version.*

9. Inject the CARLA ROS 2 Bridge

Autoware needs the CARLA control packages to send steering and throttle commands back to the simulator. Clone it directly into Autoware's source folder:
```bash
git clone --recurse-submodules https://github.com/carla-simulator/ros-bridge.git src/ros-bridge
```

10. Refresh the APT Package Index

Before installing any system libraries, update the local package list so `apt` knows about the latest available versions:
```bash
sudo apt update
```

11. Fix potential permission issues with rosdep in Docker:
```bash
sudo rosdep fix-permissions
```

12. Update the rosdep Database

Fetch the rosdep package index, which maps ROS package names to their system library dependencies:
```bash
rosdep update
```

13. Install all missing libraries for the packages in `/src`:
```bash
rosdep install -y --from-paths src --ignore-src --rosdistro $ROS_DISTRO
```

14. Create the Persistent Workspace Bootloader

Because Docker resets its environment every time it closes, system-level dependencies (like the `simple-pid` Python package and the `ackermann_msgs` ROS package required by the bridge) get erased. We will bypass this by saving the Python package permanently to your workspace and adding a smart-installer to our quick-boot script:
```bash
pip3 install simple-pid==0.1.4 --target /workspace/custom_libs
echo 'source /workspace/install/setup.bash' > /workspace/boot.sh
echo 'export PYTHONPATH=/workspace/custom_libs:$PYTHONPATH' >> /workspace/boot.sh
echo 'dpkg -s ros-humble-ackermann-msgs >/dev/null 2>&1 || (apt-get update && apt-get install ros-humble-ackermann-msgs -y)' >> /workspace/boot.sh
```

(You will use this `boot.sh` script in Phase 2 to instantly load your environment).

15. Build the entire autonomous driving stack

This will take a significant amount of time (1–3 hours depending on your hardware). We use `--continue-on-error` so that a single failing package does not abort the entire build — `colcon` will continue building all independent packages and show you every failure at once. If some packages fail, fix the issue and re-run; `colcon` automatically skips packages that already compiled successfully:
```bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --continue-on-error
```

*Note: If the Autoware modules fail you can build again but this time you can force colcon to build them one at a time by running:*
```bash
MAKEFLAGS="-j1" colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --continue-on-error --executor sequential
```

*Note: If the `pcl_recorder` package fails (this is a known incompatible package from the CARLA ROS bridge), tell the compiler to skip it entirely by running:*
```bash
touch src/ros-bridge/pcl_recorder/COLCON_IGNORE
```
After creating this ignore file, simply re-run your `colcon build` command.

### Step 3: Create the Python Environment
Since we have custom utility scripts (like the automated recorder and the `find_car.py` teleport script), it is best practice to run them in an isolated Python environment. **Note: This project strictly requires Python 3.12.**

*(Ubuntu 22.04 ships with Python 3.10 by default. Install 3.12 by running: `sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt update && sudo apt install python3.12 python3.12-venv -y`)*

1. Open a brand new Ubuntu WSL2 terminal:
```bash
wsl -d Ubuntu-22.04 -u root
```
2. Navigate to your folder:
```bash
cd ~/projects/univaq-avv-carla-autoware
```
3. Create a new virtual environment specifically using Python 3.12:
```bash
python3.12 -m venv .venv
```
*Note: Ubuntu 22.04 ships with Python 3.10 by default. If you get a "command not found" error, install Python 3.12 by running this command first:*
```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y && sudo apt update && sudo apt install python3.12 python3.12-venv -y
```
4. Activate the environment:
```bash
source .venv/bin/activate
```
5. Install the required Python packages:
```bash
pip install -r requirements.txt
```
*(Note: From now on, whenever you want to run a custom Python script in this project, make sure to run `source .venv/bin/activate` first to activate your environment.)*

### Step 4: Download the Map for Autoware
The official CARLA-Autoware maps are hosted on the CARLA team's Bitbucket repository.
**CRITICAL:** The map folder must be placed *inside* the `autoware` directory so the Docker container can see it.
1. Navigate into your autoware folder and create the map directory:
```bash
cd ~/projects/univaq-avv-carla-autoware/autoware
mkdir Town01_map
```
2. Go to this link: [CARLA Autoware Contents (Maps)](https://bitbucket.org/carla-simulator/autoware-contents/src/master/maps/)
3. Go into `point_cloud_maps` → click `Town01.pcd` → click the three dots in the top right and select "Download" to download it inside your new `autoware/Town01_map` folder.
4. Go back, navigate to `vector_maps/lanelet2` → click `Town01.osm` → download it inside the same `autoware/Town01_map` folder.
5. Rename them exactly like this:
    * Rename `Town01.pcd` ➔ `pointcloud_map.pcd`
    * Rename `Town01.osm` ➔ `lanelet2_map.osm`
6. Check your `Town01_map` folder for a file named `map_projector_info.yaml` (it should already be included in this template repository). If it is missing, create a new text file with that exact name, open it, and paste the following:
```yaml
projector_type: Local
```

*Troubleshooting: If you accidentally downloaded the map to the main project folder instead of the autoware folder, you can move it by running:*
```bash
mv ~/projects/univaq-avv-carla-autoware/Town01_map ~/projects/univaq-avv-carla-autoware/autoware/
```

### Step 5: Download Autoware AI Models (Artifacts)
Before running the full autonomous driving stack, Autoware needs to download its pre-trained neural networks (such as the LiDAR CenterPoint model) for its perception modules to function. Without these files, the end-to-end simulator will instantly crash on startup.

1. Ensure you are inside the Docker container terminal and in the workspace directory:
```bash
cd /workspace
```
2. Run the automated artifact download script (this will take a few minutes depending on your internet connection, as the files are quite large):
```bash
./setup-dev-env.sh --download-artifacts --no-nvidia
```
3. **IMPORTANT - The Password Prompt:** The script uses an automation tool called Ansible. During the installation, it will pause and ask for a `BECOME password:`. Because you are already the root administrator inside the Docker container,** you do not need a password**. Simply press **Enter** to leave it blank and the script will continue.
4. **IMPORTANT - The NVIDIA Prompt:** The script might warn you that some components depend on CUDA/TensorRT and ask if you want to install NVIDIA libraries (`Install NVIDIA libraries? [y/N]:`). **You must type `N` and press Enter**. Your Docker container is already receiving GPU access directly from Windows; attempting to install Linux-specific drivers here will cause the installation to crash.

*Note: This download will take a few minutes depending on your internet connection, as the AI model files are quite large. They will be automatically saved to `/root/autoware_data/` inside the container*

5. **Make the Models Permanent:** By default, the downloaded models are saved to `/root/autoware_data/`, which gets erased when Docker closes. Move them to your permanent workspace folder so you only have to download them once:
```bash
mv /root/autoware_data /workspace/autoware_data
```

## Phase 2: Running the Simulation (Everyday Workflow)
### CRITICAL ORDER OF OPERATIONS: The Body Before The Brain
You must **always** spawn the physical vehicle in CARLA (Step 3) before you launch the Autoware integration (Step 4). If you launch Autoware first, it will fail to find the car's sensor topics and the integration will crash.

**The Golden Rule:** Start the World ➔ Start the Bridge ➔ Spawn the Car ➔ Boot the Brain ➔ Set Initial Pose.

> **What changed vs. the old workflow**: The CARLA relay nodes, the Ackermann type converter, and the full Autoware stack (localization, planning, control) now all launch from a single command in Step 4. Step 5 (the old separate Autoware launch) no longer exists. The pose extractor script in Step 5A now publishes directly — no copy-pasting a giant command.

### Step 1: Launch the World & Recorder (Windows)
1. Open PowerShell, navigate to your CARLA installation folder, and launch the engine:
```bash
.\CarlaUE4.exe -carla-rpc-port=2000 -windowed -ResX=800 -ResY=600
```
2. Open a brand new Ubuntu WSL2 terminal:
```bash
wsl -d Ubuntu-22.04 -u root
```
3. Navigate to your folder:
```bash
cd ~/projects/univaq-avv-carla-autoware
```
4. Activate the environment:
```bash
source .venv/bin/activate
```
5. Start the automated recorder. This saves the physics snapshot so you can replay the exact scenario later (update the host IP to your Windows IPv4 address, which you can find by running `ipconfig` in PowerShell):
```bash
python3 start_simulation.py --host 10.48.106.7 --port 2000 --log_name run_001.log
```
(*Note: Press `Ctrl+C` in this window when you are done to safely save the log*).

### Step 2: Launch the Bridge (WSL Terminal 1)
1. Open a new WSL terminal:
```bash
wsl -d Ubuntu-22.04 -u root
```
2. Source your bridge environment:
```bash
source /opt/ros/humble/setup.bash && source $HOME/carla_ws/install/setup.bash
```
3. **Critical**: force CycloneDDS before launching. The Autoware Docker container uses CycloneDDS by default. If the bridge uses FastDDS (the ROS 2 Humble default), the two cannot discover each other's topics — CARLA sensor data will be invisible inside Docker and localization will never initialize. If you completed Phase 1 Step 1.5, this is already set in your `~/.bashrc` and new terminals have it automatically. Otherwise set it manually now:
```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```
4. Connect to CARLA (update the host IP to your Windows IPv4 address):
```bash
ros2 launch carla_ros_bridge carla_ros_bridge.launch.py host:=10.48.106.7 port:=2000 timeout:=60 synchronous_mode:=False
```
> **Note on `synchronous_mode:=False`**: In asynchronous mode, CARLA runs at its own pace independently of the ROS bridge. This is the correct setting for real-time driving with Autoware. Synchronous mode (True) would make CARLA wait for a tick from the bridge before advancing, which is better for deterministic offline replay but incompatible with Autoware's real-time pipeline.

> **Note on connectivity**: If the bridge fails to connect, a Windows Firewall rule may be blocking port 2000. Run this in an Administrator PowerShell to allow it:
> ```powershell
> New-NetFirewallRule -DisplayName "CARLA RPC" -Direction Inbound -Protocol TCP -LocalPort 2000 -Action Allow
> ```

### Step 3: Spawn the Vehicle (WSL Terminal 2)
The bridge is running, but the world is empty. You must spawn a car and its sensors.

The vehicle is defined by `my_custom_car.json`, which describes:
- **Vehicle**: `vehicle.tesla.model3` with id `ego_vehicle`
- **Sensors**: a front RGB camera (800×600, 90° FOV), a 64-channel LiDAR (100 m range), a GNSS sensor, and an IMU

To spawn a different vehicle type or add sensors, edit this file following the same structure.

1. Open a new WSL terminal:
```bash
wsl -d Ubuntu-22.04 -u root
```
2. Source your bridge environment:
```bash
source /opt/ros/humble/setup.bash && source $HOME/carla_ws/install/setup.bash
```
3. Set CycloneDDS (must match the bridge terminal and Docker). If you completed Phase 1 Step 1.5 this is already in your `~/.bashrc` and set automatically in new terminals:
```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```
4. Spawn the car and its sensors:
```bash
ros2 launch carla_spawn_objects carla_spawn_objects.launch.py objects_definition_file:=$HOME/projects/univaq-avv-carla-autoware/my_custom_car.json
```
5. (Optional) If you want to teleport the camera to the car's location in the CARLA spectator view, open a new WSL terminal and run:
```bash
wsl -d Ubuntu-22.04 -u root
cd ~/projects/univaq-avv-carla-autoware
source .venv/bin/activate
python3 find_car.py --host 10.48.106.7 --role ego_vehicle
```
*(Update the host IP to your Windows IPv4 address if it has changed.)*

### Step 4: Launch the Full Stack (WSL Terminal 3 → Docker)
This single command starts everything inside Docker: the sensor relay nodes, the Ackermann type converter, the rosbag recorder, and the full Autoware stack (localization, planning, control, RViz).

> **Before proceeding**: Confirm that WSLg is working (see Prerequisites → Enable GUI Display). If `$DISPLAY` is not set in your WSL2 terminal, RViz will not open.

1. Open a new WSL terminal:
```bash
wsl -d Ubuntu-22.04 -u root
```
2. Navigate to your folder:
```bash
cd ~/projects/univaq-avv-carla-autoware
```
3. Enter the Docker container:
```bash
bash launch_autoware.sh
```
The script auto-copies `autoware_carla_integration.launch.py` and `ackermann_converter.py` into `autoware/` on every run, so edits to those files should always be made in the project root — changes made inside Docker at `/workspace/` will be overwritten next time. A recap of the commands to run inside the container is printed before the shell opens.
4. Navigate to the workspace and run your quick-boot script:
```bash
cd /workspace && source boot.sh
```
5. Link your permanent AI models so Autoware's perception modules can find them:
```bash
ln -s /workspace/autoware_data /root/autoware_data
```
6. Launch the entire stack in one command:
```bash
ros2 launch autoware_carla_integration.launch.py \
  vehicle_name:=ego_vehicle \
  map_path:=/workspace/Town01_map
```
> `vehicle_model` and `sensor_model` default to `sample_vehicle` and `carla_sensor_kit` automatically — you only need to pass them if you want to override the defaults.

This starts:
- **Sensor relays** — forward CARLA's LiDAR, camera, GNSS, and IMU topics into Autoware's namespaces
- **Ackermann converter** — translates Autoware's control commands into the format CARLA's bridge understands (fixes the type mismatch that caused the `control_cmd` rosbag error)
- **Rosbag recorder** — logs all sensor data and control commands to `/workspace/log_ego_vehicle`
- **Full Autoware stack** — NDT scan matching, EKF localizer, planning, and control nodes

> **Advanced**: Pass `launch_autoware:=false` to start only the CARLA relay nodes without the Autoware stack — useful for debugging the bridge independently.

*Note: This script records a log to `/workspace/log_ego_vehicle`. If you restart and the folder already exists, delete it first:*
```bash
rm -rf /workspace/log_ego_vehicle
```

### Step 5: Set the Initial Pose and Drive

Autoware's RViz window will open on your Windows desktop. The State Panel will show **Localization | Uninitialized** until you provide the vehicle's starting position on the map.

**A. Localize the Vehicle**

CARLA and ROS 2 use different coordinate systems. The `get_exact_pose.py` script reads the vehicle's exact position from CARLA, converts the coordinates, and publishes them directly to Autoware with a valid timestamp. It waits for Autoware's localization nodes to be ready before sending, so there is no race condition.

1. Open a new WSL2 terminal (do **not** use the Docker terminal — this runs in WSL):
```bash
wsl -d Ubuntu-22.04 -u root
```
2. Navigate to your project:
```bash
cd ~/projects/univaq-avv-carla-autoware
```
3. Activate the Python environment (only the venv is needed — ROS 2 is sourced internally by the script):
```bash
source .venv/bin/activate
```
4. Run the pose extractor:
```bash
python3 get_exact_pose.py
```
The script connects to CARLA at `10.48.106.7` by default. If your Windows IP has changed, pass it explicitly: `python3 get_exact_pose.py --host <your_ip>`.

The script invokes `ros2 topic pub` in a subprocess that sources ROS 2 Humble on its own, so there is no Python version conflict between the venv (Python 3.12) and ROS 2 (Python 3.10). It will publish to `/initialpose` automatically. In RViz, your 3D car model will snap onto the map and the State Panel will change to **Localization | OK**.

> **Warning shown?** If the script prints `No subscriber found on /initialpose after 10 seconds`, the Autoware localization stack is not up yet. Wait a few more seconds for it to finish loading and run the script again.

> **Fallback**: Pass `--no-publish` to print the command instead of running it automatically. The timestamp is baked into the printed command — paste it into Docker immediately.

> **Manual alternative**: Click "2D Pose Estimate" in the top RViz toolbar and click-drag on the road where the car is sitting in CARLA.

**B. Route the Vehicle**
1. Click "**2D Goal Pose**" in the top RViz toolbar.
2. Click and drag on a valid road lane ahead of the vehicle to set the destination and heading. Autoware will calculate and draw a colorful trajectory line.

**C. Drive**
1. In the Autoware State panel on the left, click the "**Accept Start**" button.
2. Toggle the **Autoware Control** switch at the very top of the panel to **Auto**. The car will begin driving in CARLA!

# Advanced: Multi-Agent Workflow
To run multiple autonomous vehicles interacting with each other, follow the golden rule: **One Docker Container = One Vehicle Brain**.

1. **Start the World & Bridge** (follow Steps 1 & 2 above).

2. **Spawn Multiple Vehicles**: Each vehicle needs its own JSON definition file with a unique `id` and a different `spawn_point` so they don't collide on spawn.

   Copy `my_custom_car.json` to a new file called `my_custom_car_2.json` and change the `id` field from `ego_vehicle` to `ego_vehicle_2`, and update the spawn coordinates.

   Open two separate WSL terminals, source the bridge in each, and spawn them:
   ```bash
   # Terminal A — Car 1
   ros2 launch carla_spawn_objects carla_spawn_objects.launch.py objects_definition_file:=$HOME/projects/univaq-avv-carla-autoware/my_custom_car.json
   ```
   ```bash
   # Terminal B — Car 2
   ros2 launch carla_spawn_objects carla_spawn_objects.launch.py objects_definition_file:=$HOME/projects/univaq-avv-carla-autoware/my_custom_car_2.json
   ```

   (Optional) To teleport the CARLA spectator camera to a specific vehicle, pass the `--role` flag:
   ```bash
   python3 find_car.py --host 10.48.106.7 --role ego_vehicle_2
   ```

3. **Boot Agent 1**: Open a Docker terminal (following Step 4 above), source the workspace, link the AI models, and launch for Car 1:
   ```bash
   ln -s /workspace/autoware_data /root/autoware_data
   ros2 launch autoware_carla_integration.launch.py \
     vehicle_name:=ego_vehicle \
     map_path:=/workspace/Town01_map
   ```

4. **Boot Agent 2**: Open a **completely new** WSL terminal and run `source launch_autoware.sh` again. Each invocation of `launch_autoware.sh` starts a new, independent Docker container — so Agent 2 gets its own isolated Autoware brain. Source the workspace inside it and launch for Car 2:
   ```bash
   ln -s /workspace/autoware_data /root/autoware_data
   ros2 launch autoware_carla_integration.launch.py \
     vehicle_name:=ego_vehicle_2 \
     map_path:=/workspace/Town01_map
   ```
   > `vehicle_model` and `sensor_model` default to `sample_vehicle` and `carla_sensor_kit` for both agents.

5. **Localize each agent**: For each vehicle, run `get_exact_pose.py` from a WSL terminal (outside Docker) pointing to that vehicle's role name. Since both Docker containers share the host network (`--net=host`), the script's `/initialpose` publish reaches whichever Autoware instance is currently waiting for it. Localize one agent at a time.
   > **Note on logs**: Each agent writes its rosbag to `/workspace/log_<vehicle_name>`. With two agents, you will have `/workspace/log_ego_vehicle` and `/workspace/log_ego_vehicle_2`. The same no-overwrite rule applies to both — delete or rename the old folders before re-running.

# Where are my logs?
This template generates two types of logs automatically:
* **CARLA Simulation Snapshots**: These `.log` files contain the physical state of the world (positions of all cars, pedestrians, traffic lights). They are saved on your Windows machine in your CARLA installation folder under `CarlaUE4/Saved/`.

   To replay a snapshot, connect a CARLA Python client and call:
   ```python
   import carla
   client = carla.Client("localhost", 2000)
   client.set_timeout(10.0)
   client.replay_file("run_001.log", 0, 0, 0)
   ```
   Run this snippet in a Python environment where the `carla` package is installed (your `.venv` with `requirements.txt` already has it).

* **Autoware ADAS Bags**: These are raw ROS 2 data logs containing the LiDAR point clouds, camera feeds, GNSS fixes, IMU readings, and control commands. They are saved directly to your shared `/workspace` folder as a directory (e.g., `/workspace/log_ego_vehicle`).

   To inspect a bag: `ros2 bag info /workspace/log_ego_vehicle`
   To replay a bag: `ros2 bag play /workspace/log_ego_vehicle`

***Note on ROS Bags:*** *ROS 2 is highly protective of your data and will **never** overwrite an existing log folder. If you stop the simulation and try to run the exact same `autoware_carla_integration.launch.py` command again, it will crash because `/workspace/log_ego_vehicle` already exists. You must either delete the old folder (`rm -rf /workspace/log_ego_vehicle`) or launch the integration with a new vehicle name!*
