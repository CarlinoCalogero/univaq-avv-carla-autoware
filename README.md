# CARLA–Autoware Bridge

A cross-environment autonomous driving simulation pipeline that connects the **CARLA simulator** (Windows) to the **Autoware** autonomous vehicle stack (WSL2/Docker) via a custom ROS 2 bridge node.

> **Origin:** University of L'Aquila (univaq-avv-carla-autoware)

---

## Table of Contents

- [Architecture](#architecture)
- [Data Flow](#data-flow)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running the Bridge](#running-the-bridge)
- [Diagnostics](#diagnostics)
- [Troubleshooting](#troubleshooting)

---

## Architecture

The system spans two OS environments connected over TCP via the WSL2 NAT bridge:

```
┌─────────────────────────────────────────────────────┐
│                    WINDOWS HOST                     │
│                                                     │
│  CARLA Simulator (CarlaUE4.exe)                     │
│    Simulates Town01 map, vehicle physics & sensors  │
│    Listens on TCP :2000, :2001, :8080               │
│                                                     │
│  spawn_vehicle.py  ──► Spawns ego vehicle + LiDAR   │
│  follow_camera.py  ──► Spectator camera follow      │
│  check_carla.py    ──► Sensor diagnostics           │
└──────────────────────────┬──────────────────────────┘
                           │ CARLA Python API (TCP :2000)
                           │ WSL2 NAT bridge
┌──────────────────────────▼──────────────────────────┐
│              WSL2 / Docker (Ubuntu 22.04)           │
│                                                     │
│  bridge_node.py (ROS 2 Node)                        │
│    Pulls sensor data from CARLA via Python API      │
│    Converts CARLA left-hand ↔ ROS right-hand coords │
│    Publishes sensor topics for Autoware             │
│    Forwards Autoware control commands to CARLA      │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │            Autoware (ROS 2 Stack)           │    │
│  │  NDT Scan Matcher  (LiDAR map localization) │    │
│  │  EKF Localizer     (sensor fusion)          │    │
│  │  Behavior Planner  (route decisions)        │    │
│  │  Motion Planner    (trajectory generation)  │    │
│  │  MPC/PID Controller (vehicle control)       │    │
│  │  RViz2             (visualization)          │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## Data Flow

### CARLA → Bridge → Autoware (sensor pipeline)

| CARLA Source | Bridge Conversion | ROS 2 Topic | Autoware Consumer |
|---|---|---|---|
| Vehicle position | Y-axis negated (coord flip) | `/sensing/gnss/pose` | EKF Localizer (initial fix) |
| LiDAR point cloud | PointCloud2, Y negated | `/sensing/lidar/concatenated/pointcloud` | NDT Scan Matcher |
| Angular velocity + gravity | IMU message | `/sensing/imu/imu_raw` | IMU Corrector → EKF |
| Speed + steering angle | VelocityReport / SteeringReport | `/vehicle/status/*` | EKF Localizer |

### Autoware → Bridge → CARLA (control pipeline)

Autoware publishes an `AckermannControlCommand` to `/control/command/control_cmd`. The bridge converts target longitudinal velocity to CARLA throttle (10% scaling) and lateral steering angle (sign-inverted for axis convention), then calls `ego_vehicle.apply_control()`.

### Startup Sequence

1. Autoware launches and waits for sensor data.
2. Bridge streams GNSS + IMU to give Autoware an initial position fix.
3. Bridge polls `/api/localization/initialize` every 2 seconds; once Autoware's EKF is ready, it sends the vehicle's current pose.
4. EKF activates → NDT begins aligning LiDAR to the Town01 point cloud map.
5. Only after localization is confirmed does the bridge forward control commands to CARLA.

> **Safety:** The vehicle is held at full brake until localization is confirmed. A 500 ms watchdog re-applies brakes if no control command is received.

---

## Project Structure

```
carla-new/
├── scripts/
│   ├── check_setup.sh          # Pre-flight environment checker (run before bridge)
│   └── get_host_ip.sh          # Discovers Windows host IP from WSL2
│
├── windows/                    # Run on Windows alongside CARLA
│   ├── spawn_vehicle.py        # Spawns ego vehicle (Lincoln MKZ) + 64-ch LiDAR
│   ├── follow_camera.py        # Moves CARLA spectator cam to follow ego vehicle
│   ├── check_carla.py          # Attaches to all sensors and prints live data
│   └── requirements.txt
│
└── wsl/                        # Run in WSL2 / Autoware Docker container
    ├── bridge_node.py          # Core ROS 2 bridge node (CARLA ↔ Autoware)
    ├── carla_bridge.launch.py  # Launches Autoware with CARLA-specific overrides
    ├── fix_ndt_threshold.sh    # Lowers NDT score threshold for synthetic LiDAR
    ├── send_dummy_command.py   # Integration test: sends fake drive commands
    └── requirements.txt
```

---

## Setup

### 1. Install CARLA 0.9.15 on Windows

Download CARLA 0.9.15 from the [official releases page](https://github.com/carla-simulator/carla/releases/tag/0.9.15).

### 2. Set Up Python Environment on Windows

Create a Python 3.10 environment and install dependencies:

```cmd
pip install -r windows\requirements.txt
```

### 3. Install Ubuntu 22.04 in WSL2

Download the [64-bit WSL image](https://releases.ubuntu.com/22.04/) and double-click to install. Then copy this project into your WSL home:

```bash
mkdir ~/projects
cp -r /mnt/c/Users/<YourUsername>/Desktop/univaq-avv-carla-autoware ~/projects/
cd ~/projects/univaq-avv-carla-autoware
pip install -r wsl/requirements.txt
```

### 4. Install ROS 2 Humble in WSL2

Follow the [official ROS 2 Humble installation guide](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html).

### 5. Install Autoware in WSL2

Follow the [Autoware installation guide](https://autowarefoundation.github.io/autoware-documentation/).

After cloning Autoware, copy the bridge scripts:

```bash
cp ~/projects/univaq-avv-carla-autoware/wsl/bridge_node.py ~/autoware/
cp ~/projects/univaq-avv-carla-autoware/wsl/carla_bridge.launch.py ~/autoware/
```

#### Download CARLA Lanelet2 Maps

Download `Town01.pcd` (point cloud) and `Town01.osm` (vector map) from [CARLA Autoware Contents](https://bitbucket.org/carla-simulator/autoware-contents/src/master/maps/) — use the **y-axis inverted** variants.

Rename and place them:

```
pointcloud_map.pcd    ← renamed from Town01.pcd
lanelet2_map.osm      ← renamed from Town01.osm
map_projector_info.yaml
```

Create `map_projector_info.yaml` with:

```yaml
projector_type: Local
```

Move all three files into Autoware:

```bash
mkdir -p ~/autoware/autoware_map/Town01/
mv /mnt/c/Users/<YourUsername>/Desktop/pointcloud_map.pcd ~/autoware/autoware_map/Town01/
mv /mnt/c/Users/<YourUsername>/Desktop/lanelet2_map.osm ~/autoware/autoware_map/Town01/
mv /mnt/c/Users/<YourUsername>/Desktop/map_projector_info.yaml ~/autoware/autoware_map/Town01/
```

### 6. Allow CARLA Ports Through Windows Firewall

CARLA listens on TCP 2000, 2001, and 8080. Run once in PowerShell as Administrator:

```powershell
New-NetFirewallRule -DisplayName "CARLA" -Direction Inbound -Protocol TCP -LocalPort 2000,2001,8080 -Action Allow
```

### 7. Find the Windows Host IP

In your WSL2 terminal:

```bash
cd ~/projects/univaq-avv-carla-autoware
source scripts/get_host_ip.sh
```

This exports `$CARLA_HOST` for use by the bridge node. Alternatively:

```bash
ip route show | grep default | awk '{print $3}'
```

### 8. Verify Everything Is Ready

```bash
cd ~/projects/univaq-avv-carla-autoware
source /opt/ros/humble/setup.bash
bash scripts/check_setup.sh
```

This checks that ROS 2, the CARLA Python API, and required message packages are installed, and that port 2000 is reachable on the Windows host.

---

## Running the Bridge

### Step 1 — Start CARLA (Windows)

Double-click `CarlaUE4.exe` and wait for the simulator window to fully load.

### Step 2 — Spawn the Ego Vehicle (Windows, Terminal 1)

```cmd
python windows\spawn_vehicle.py --map Town01
```

**Keep this terminal open** — closing it destroys the vehicle and all attached sensors.

### Step 3 — (Optional) Follow Camera (Windows, Terminal 2)

```cmd
python windows\follow_camera.py
```

Keeps the CARLA spectator camera tracking the ego vehicle. **Keep this terminal open** while in use.

### Step 4 — Start Autoware (WSL2, Terminal 3)

```bash
cd ~/autoware
bash docker/run.sh --devel
cd /workspace
source install/setup.bash
ros2 launch ./carla_bridge.launch.py \
  vehicle_name:=ego_vehicle \
  map_path:=/workspace/autoware_map/Town01 \
  vehicle_model:=sample_vehicle \
  sensor_model:=carla_sensor_kit
```

> **Note:** The launch file disables Autoware's real vehicle interface (`launch_vehicle_interface: false`) and perception stack (`launch_perception: false`), since the bridge replaces both.

### Step 5 — Start the Bridge Node (WSL2, Terminal 4)

Open a new WSL2 terminal:

```bash
cd ~/autoware
bash docker/run.sh --devel
cd /workspace
source install/setup.bash
pip install carla==0.9.15      # required each time inside Docker
python3 bridge_node.py --ros-args -p carla_host:="host.docker.internal"
```

---

## Diagnostics

### Check Carla sensors (Inside Windows Terminal)

```cmd
python .\windows\check_carla.py
```

### Check Active ROS 2 Topics (Inside Docker Terminal)

```bash
ros2 topic list
```

Key topics for confirming the bridge is working:

| Topic | Description |
|---|---|
| `/sensing/gnss/pose` | Vehicle absolute position |
| `/sensing/imu/imu_raw` | Acceleration and tilt |
| `/sensing/lidar/concatenated/pointcloud` | 3D LiDAR point cloud |
| `/vehicle/status/velocity_status` | Current speed |
| `/vehicle/status/steering_status` | Current steering angle |

Echo any topic to inspect live data:

```bash
ros2 topic echo /vehicle/status/velocity_status
```

### Check Autoware Localization (Inside Docker Terminal)

Autoware fuses IMU, wheel speed, and LiDAR into a single kinematic state:

```bash
ros2 topic echo /localization/kinematic_state
```

### Check NDT Alignment Score (Inside Docker Terminal)

NDT "locks" the vehicle to the map using LiDAR. A low score means poor alignment — the vehicle may jump or drift:

```bash
ros2 topic echo /localization/pose_estimator/ndt_scan_matcher/status
```


---

## Troubleshooting

### Vehicle doesn't move / stays braked

The bridge holds full brake until Autoware's EKF localizer is initialized. Check that:
- NDT is receiving LiDAR data (`/sensing/lidar/concatenated/pointcloud` has data)
- The localization initialize service call succeeded (visible in bridge logs)

### Bridge cannot connect to CARLA

- Confirm the Windows Firewall rule for ports 2000, 2001, 8080 is active.
- Confirm `spawn_vehicle.py` is still running on Windows.
- Re-run `source scripts/get_host_ip.sh` and use the printed IP explicitly:
  ```bash
  python3 bridge_node.py --ros-args -p carla_host:="<windows-host-ip>"
  ```

### Sensor data looks wrong (jumps, wrong orientation)

All bridge outputs negate the Y-axis and invert yaw sign to convert CARLA's left-handed coordinate system to ROS's right-handed frame. If sensor data appears mirrored, confirm you are using the **y-axis inverted** map files from the CARLA Autoware Contents repository.
