# CARLA ↔ Autoware Bridge

A minimal integration that lets **Autoware** (running in WSL2) control a car inside **CARLA** (running on Windows).

```
┌─────────────────────────────────────────────────────────────────────┐
│  Windows                                                            │
│  ┌──────────────────┐      TCP:2000      ┌─────────────────────┐   │
│  │  CARLA Simulator │◄──────────────────►│  bridge_node.py     │   │
│  │  (ego_vehicle)   │                    │  (runs in WSL2)     │   │
│  └──────────────────┘                    └──────────┬──────────┘   │
│                                                     │ ROS2 DDS     │
│  ┌───────────────────────────────────────────────── │ ─────────┐   │
│  │  WSL2                                            │          │   │
│  │          ┌──────────────────────────────────┐   │          │   │
│  │          │  Autoware / any ROS2 controller  │◄──┘          │   │
│  │          │  /control/command/control_cmd     │              │   │
│  │          └──────────────────────────────────┘              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Project Layout

```
carla-autoware-bridge/
├── windows/
│   ├── spawn_vehicle.py       # Step 1 – Spawns ego car in CARLA (run on Windows)
│   └── requirements.txt
├── wsl/
│   ├── bridge_node.py         # Step 3 – Bidirectional ROS2 ↔ CARLA bridge
│   ├── send_dummy_command.py  # Step 4 – Test: moves the car and reports result
│   └── requirements.txt
├── scripts/
│   ├── get_host_ip.sh         # Helper: detects Windows host IP from WSL
│   └── check_setup.sh         # Helper: verifies all prerequisites
└── README.md
```

---

## How It Works

### Topic Map

| Direction | ROS2 Topic | Message Type | CARLA Side |
|-----------|-----------|--------------|------------|
| Autoware → CARLA | `/control/command/control_cmd` | `AckermannControlCommand` | `VehicleControl.throttle/steer/brake` |
| CARLA → Autoware | `/sensing/gnss/pose` | `NavSatFix` | Vehicle location (converted to lat/lon) |
| CARLA → Autoware | `/sensing/imu/imu_raw` | `Imu` | Vehicle acceleration + angular velocity |
| CARLA → Autoware | `/localization/kinematic_state` | `Odometry` | Vehicle pose + velocity |
| CARLA → Autoware | `/vehicle/status/velocity_status` | `VelocityReport` | Speed in m/s |
| CARLA → Autoware | `/vehicle/status/steering_status` | `SteeringReport` | Steering angle |

### Control Conversion

`AckermannControlCommand` → `carla.VehicleControl`:

- `longitudinal.speed` (m/s) → proportional throttle/brake via a simple P-controller
- `lateral.steering_tire_angle` (rad) → `steer` normalized to `[-1, 1]` using the vehicle's max steering angle (70° for Lincoln MKZ)

### Coordinate System

CARLA uses a **left-hand** coordinate system. The bridge flips the Y axis when publishing ROS2 topics so Autoware sees a standard **right-hand** frame.

---

## Prerequisites

### Windows

| Requirement | Notes |
|------------|-------|
| CARLA 0.9.13 – 0.9.15 | Download from https://carla.org/ |
| Python 3.8+ | Must match CARLA's Python API version |
| `carla` Python package | `pip install carla==0.9.15` or use the `.egg` from the CARLA install |

### WSL2

| Requirement | Notes |
|------------|-------|
| Ubuntu 22.04 in WSL2 | WSL1 will NOT work (networking differences) |
| ROS2 Humble | https://docs.ros.org/en/humble/Installation.html |
| Autoware Universe | (optional) provides the proper message types |
| `carla` Python package | `pip install carla==0.9.15` (same version as Windows) |
| `autoware_auto_control_msgs` | From Autoware install, or use `ackermann_msgs` fallback |

---

## Step-by-Step Setup

### 1. Install CARLA on Windows

1. Download CARLA from https://github.com/carla-simulator/carla/releases
2. Extract to e.g. `C:\CARLA`
3. Start the server: double-click `CarlaUE4.exe` (or run `CarlaUE4.exe -RenderOffScreen` for headless)
4. Install the Python API:
   ```cmd
   pip install carla==0.9.15
   ```
   Or add the egg to your script if pip isn't available:
   ```python
   sys.path.append('C:/CARLA/PythonAPI/carla/dist/carla-0.9.15-py3.8-win-amd64.egg')
   ```

### 2. Install Autoware in WSL2

Follow the official guide: https://autowarefoundation.github.io/autoware-documentation/

Or for a minimal ROS2-only setup (for testing):
```bash
sudo apt install ros-humble-ackermann-msgs ros-humble-nav-msgs ros-humble-sensor-msgs
pip install carla==0.9.15
```

### 3. Allow CARLA Port Through Windows Firewall

CARLA listens on TCP 2000 (+ 2001, 8080). Allow inbound connections in Windows Defender Firewall, or run once in PowerShell (as Administrator):

```powershell
New-NetFirewallRule -DisplayName "CARLA" -Direction Inbound -Protocol TCP -LocalPort 2000,2001,8080 -Action Allow
```

### 4. Find the Windows Host IP (from WSL)

```bash
source scripts/get_host_ip.sh
# Prints something like: CARLA_HOST=172.28.160.1
```

Alternatively:
```bash
ip route show | grep default | awk '{print $3}'
```

### 5. Verify Everything Is Ready

```bash
source /opt/ros/humble/setup.bash
bash scripts/check_setup.sh
```

---

## Running the Bridge

Open **four terminals** (mix of Windows CMD and WSL).

---

### Terminal 1 – Windows: Start CARLA

```cmd
C:\CARLA\CarlaUE4.exe
```

Wait until the CARLA window / loading screen appears.

---

### Terminal 2 – Windows: Spawn the Ego Vehicle

```cmd
cd C:\Users\<you>\Desktop\Test\carlo
python windows\spawn_vehicle.py
```

You should see the Lincoln MKZ appear in the CARLA world.  
**Keep this terminal open** — closing it destroys the vehicle.

Expected output:
```
Connecting to CARLA at localhost:2000 ...
Connected. Map: Town01
Spawning 'vehicle.lincoln.mkz_2020' at spawn point 0 ...
Vehicle spawned  id=42
  x=   -4.80  y=  -30.21  z=   0.00  speed=  0.0 km/h  ...
```

---

### Terminal 3 – WSL: Run the Bridge Node

```bash
source /opt/ros/humble/setup.bash
source scripts/get_host_ip.sh    # sets $CARLA_HOST

python3 wsl/bridge_node.py --ros-args -p carla_host:=$CARLA_HOST
```

Expected output:
```
[carla_autoware_bridge] Connecting to CARLA at 172.28.160.1:2000 ...
[carla_autoware_bridge] Connected. Map: Town01
[carla_autoware_bridge] Found ego_vehicle: vehicle.lincoln.mkz_2020  id=42
[carla_autoware_bridge] Bridge ready.
```

The bridge now:
- Publishes CARLA sensor data to Autoware topics at 20 Hz
- Waits for control commands on `/control/command/control_cmd`

---

### Terminal 4 – WSL: Send a Dummy Command (Test)

```bash
source /opt/ros/humble/setup.bash
source scripts/get_host_ip.sh

python3 wsl/send_dummy_command.py \
    --carla-host $CARLA_HOST \
    --target-speed 5.0 \
    --duration 10
```

This publishes a forward drive command (5 m/s) for 10 seconds.  
**Watch the CARLA window** — the car should start moving forward.

Expected output:
```
[dummy_command_sender] Monitoring ego_vehicle id=42  start=(-4.80, -30.21)
[dummy_command_sender] Sending target_speed=5.0 m/s (18.0 km/h) for 10 s
------------------------------------------------------------
[dummy_command_sender] [ 1.0s]  pos=(-4.80, -27.33)  dist_moved=2.88 m  speed=2.90 m/s (10.4 km/h)
[dummy_command_sender] [ 2.0s]  pos=(-4.80, -23.80)  dist_moved=6.41 m  speed=4.97 m/s (17.9 km/h)
...
============================================================
TEST RESULT
============================================================
  Initial position : (-4.80, -30.21)
  Final position   : (-4.80,   8.56)
  Total distance   : 38.77 m

  ✓  PASS – vehicle moved in CARLA!
============================================================
```

---

## Using with Autoware

Once the bridge is running, Autoware sees a standard ROS2 vehicle interface:

```bash
# Check sensor topics arriving from CARLA
ros2 topic echo /sensing/gnss/pose
ros2 topic echo /sensing/imu/imu_raw
ros2 topic echo /vehicle/status/velocity_status

# Manually send a control command (Autoware-style)
ros2 topic pub /control/command/control_cmd \
  autoware_auto_control_msgs/msg/AckermannControlCommand \
  "{longitudinal: {speed: 3.0, acceleration: 1.0}, lateral: {steering_tire_angle: 0.0}}"
```

For full Autoware integration, point Autoware's vehicle interface at these topics — no additional configuration is needed.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Connection refused` on port 2000 | CARLA not running, or Windows Firewall blocking port |
| `Ego vehicle not found` | Run `spawn_vehicle.py` first and keep it open |
| Car doesn't move in CARLA | Check bridge_node is running; check CARLA_HOST is correct |
| `carla` not importable in WSL | `pip install carla==<same version as CARLA server>` |
| `autoware_auto_control_msgs` not found | Install Autoware, or the bridge falls back to `ackermann_msgs` automatically |
| Topics published but no movement | Verify the bridge subscribed: `ros2 topic info /control/command/control_cmd` |
| WSL cannot reach Windows host | Use `ip route show` to find the gateway; ensure firewall rule added |

---

## Customization

### Different vehicle
```cmd
python windows\spawn_vehicle.py --vehicle vehicle.tesla.model3
```

### Different speed / steering limits
Edit `CARLA_MAX_STEER_RAD` in `wsl/bridge_node.py` for other vehicles.

### Different map
Load a new map before spawning:
```python
client.load_world('Town03')
```

### Sensor rate
```bash
python3 wsl/bridge_node.py --ros-args -p carla_host:=$CARLA_HOST -p publish_rate:=50.0
```
