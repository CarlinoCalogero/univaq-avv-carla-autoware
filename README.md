## Step-by-Step Setup

### 1. Install CARLA 0.9.15 on Windows

Download CARLA 0.9.15 from the [official website](https://github.com/carla-simulator/carla/releases)

### 2. Set up python environment in Windows

Create a new python 3.10 environment and install the Python API from requirements:

```cmd
pip install -r .\windows\requirements.txt
```

### 3. Install Ubuntu 22.04 in WSL2

Go to this [link](https://releases.ubuntu.com/22.04/) and download the WSL image `64-bit PC (AMD64) WSL image`. Then double click on it after download and follow installation instructions

After installation copy this project in a new directory

```bash
mkdir ~/projects
cp -r /mnt/c/Users/Utente/Desktop/univaq-avv-carla-autoware ~/projects
cd ~/projects/univaq-avv-carla-autoware
```

then install the Python API from requirements:

```bash
pip install -r wls/requirements.txt
```

### 4. Install ros2 in Ubuntu 22.04 in WSL2

Follow this [reference](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) documentation and install ros2 for ubuntu wsl.

### 5. Install Autoware in Ubuntu 22.04 in WSL2

Follow the official guide: https://autowarefoundation.github.io/autoware-documentation/

#### Copying the scripts

After having cloned autoware move to the folder location

```bash
cd ~/autoware
```

and copy inside `bridge_node.py` 

```bash
cp -r ~/projects/univaq-avv-carla-autoware/wsl/bridge_node.py ~/autoware
```

and `carla_bridge.launch.py`

```bash
cp -r ~/projects/Utente/Desktop/univaq-avv-carla-autoware/wsl/carla_bridge.launch.py ~/autoware
```

and `fix_ndt_threshold.sh`

```bash
cp -r ~/projects/univaq-avv-carla-autoware/wsl/fix_ndt_threshold.sh ~/autoware
```

#### Download CARLA Lanelet2 Maps

Download `point_cloud/Town01.pcd` and `vector_maps/lanelet2/Town01.osm` y-axis inverted maps from [CARLA Autoware Contents](https://bitbucket.org/carla-simulator/autoware-contents/src/master/maps/) in your Windows os

- Rename `point_cloud/Town01.pcd` → `pointcloud_map.pcd`
- Rename `vector_maps/lanelet2/Town01.osm` → `lanelet2_map.osm`
- Create a `map_projector_info.yaml` file with:

```yaml
projector_type: Local
```

Open your wsl Ubuntu 22.04 terminal and create the map folder in your autoware folder

```bash
mkdir -p ~/autoware/autoware_map/Town01/
```

Move the files to this new location

```bash
mv /mnt/c/Users/Utente/Desktop/pointcloud_map.pcd ~/autoware/autoware_map/Town01/
```

```bash
mv /mnt/c/Users/Utente/Desktop/lanelet2_map.osm ~/autoware/autoware_map/Town01/
```

```bash
mv /mnt/c/Users/Utente/Desktop/map_projector_info.yaml ~/autoware/autoware_map/Town01/
```

### 6. Allow CARLA Port Through Windows Firewall

CARLA listens on TCP 2000 (+ 2001, 8080). Allow inbound connections in Windows Defender Firewall, or run once in PowerShell (as Administrator):

```powershell
New-NetFirewallRule -DisplayName "CARLA" -Direction Inbound -Protocol TCP -LocalPort 2000,2001,8080 -Action Allow
```

### 7. Find the Windows Host IP

In your Ubuntu 22.04 in WSL2 terminal run the following

```bash
cd ~/projects/univaq-avv-carla-autoware
source scripts/get_host_ip.sh
```

Alternatively:
```bash
ip route show | grep default | awk '{print $3}'
```

### 8. Verify Everything Is Ready

In your Ubuntu 22.04 in WSL2 terminal run the following

```bash
cd ~/projects/univaq-avv-carla-autoware
source /opt/ros/humble/setup.bash
bash scripts/check_setup.sh
```

## Running the Bridge

### Start CARLA

Start Carla by double clickng on `CarlaUE4.exe`

Wait until the CARLA window / loading screen appears.

### Terminal 1 – Windows: Spawn the Ego Vehicle

In your windows terminal, navigate to this project folder, source the python 3.10 environment and run the command

```cmd
python windows\spawn_vehicle.py --map Town01
```

**Keep this terminal open** — closing it destroys the vehicle.

### Terminal 2 – Windows: Vehicle camera follow

You can also see your car in Carla. Navigate to this project folder, source the python 3.10 environment and run the command

```cmd
python .\windows\follow_camera.py
```

**Keep this terminal open** — closing it terminates the camera follow.

### WSL: Send a Dummy Command (Test)

In your Ubuntu 22.04 in WSL2 terminal run the following

```bash
cd ~/projects/univaq-avv-carla-autoware
source /opt/ros/humble/setup.bash
source scripts/get_host_ip.sh

python3 wsl/send_dummy_command.py \
    --carla-host $CARLA_HOST \
    --target-speed 5.0 \
    --duration 10
```

This publishes a forward drive command (5 m/s) for 10 seconds.  
**Watch the CARLA window** — the car should start moving forward.

---

### Terminal 3 – WSL: Run Autoware

Open your Ubuntu 22.04 WSL terminal and navigate to your autoware location

```bash
cd ~/autoware
```

then start the docker container

```bash
bash docker/run.sh --devel
```

Move to the workspace root — Docker starts at /autoware, not /workspace

```bash
cd /workspace
```

Source the Autoware workspace

```bash
source install/setup.bash
```

Run Autoware

```bash
ros2 launch ./carla_bridge.launch.py vehicle_name:=ego_vehicle map_path:=/workspace/autoware_map/Town01 vehicle_model:=sample_vehicle sensor_model:=carla_sensor_kit
```

### Terminal 4 – WSL: Run the Bridge Node

Open another Ubuntu 22.04 WSL terminal and navigate to your autoware location

```bash
cd ~/autoware
```

then start the docker container

```bash
bash docker/run.sh --devel
```

Move to the workspace root — Docker starts at /autoware, not /workspace

```bash
cd /workspace
```

Source the Autoware workspace

```bash
source install/setup.bash
```

Install the carla API (must be done every time since we are on docker)

```bash
pip install carla==0.9.15
```

Patch the NDT score threshold (run once; repeat if the container is recreated)

```bash
bash fix_ndt_threshold.sh
```

Run the bridge node

```bash
python3 bridge_node.py --ros-args -p carla_host:="host.docker.internal"
```