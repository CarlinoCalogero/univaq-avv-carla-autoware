<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT HEADER -->
<br />
<div align="center">
  <h1 align="center">UNIVAQ AVV: CARLA & Autoware Co-Simulation Framework</h1>

  <p align="center">
    A complete, cross-platform co-simulation pipeline bridging the <strong>CARLA Simulator</strong> (Windows) with the <strong>Autoware Universe</strong> autonomous driving stack (Ubuntu 22.04 LTS on WSL2).
    <br />
    <em>Developed as an academic project for Autonomous Vehicles & Verification (AVV) within the Master's Degree in Computer Science at the University of L'Aquila (UNIVAQ).</em>
    <br />
    <br />
    <a href="https://github.com/CarlinoCalogero/univaq-avv-carla-autoware"><strong>Explore the repository »</strong></a>
    <br />
    <br />
    <a href="#about-the-project">About The Project</a>
    &middot;
    <a href="#getting-started">Getting Started</a>
    &middot;
    <a href="#usage">Usage</a>
    &middot;
    <a href="#contributors">Contributors</a>
    &middot;
    <a href="#contact">Contact</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#key-features">Key Features</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li>
          <a href="#installation-and-setup">Installation and Setup</a>
          <ul>
            <li><a href="#1-install-ubuntu-2204-for-wsl2">1. Install Ubuntu 22.04 for WSL2</a></li>
            <li><a href="#2-download-carla-0915-for-windows">2. Download CARLA 0.9.15 for Windows</a></li>
            <li><a href="#3-install-ros-2-humble-in-ubuntu-2204-wsl">3. Install ROS 2 Humble in Ubuntu 22.04 WSL</a></li>
            <li><a href="#4-install-autoware-universe-in-ubuntu-2204-wsl">4. Install Autoware Universe in Ubuntu 22.04 WSL</a></li>
            <li><a href="#5-install-carla-python-bridge--maps-in-wsl">5. Install CARLA Python Bridge & Maps in WSL</a></li>
            <li><a href="#6-build-autoware-carla-interface">6. Build Autoware CARLA Interface</a></li>
            <li><a href="#7-network-and-dds-configuration">7. Network and DDS Configuration</a></li>
            <li><a href="#8-configure-autoware_carla_interface">8. Configure autoware_carla_interface</a></li>
            <li><a href="#9-console-settings-for-ros-2">9. Console Settings for ROS 2</a></li>
            <li><a href="#10-setup-workspaces">10. Setup Workspaces</a></li>
          </ul>
        </li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#running-the-simulation">Running the Simulation</a></li>
        <li><a href="#spectator-camera-tracking-follow_camerapy">Spectator Camera Tracking (follow_camera.py)</a></li>
        <li><a href="#synchronized-data-collection-sync_recordbat">Synchronized Data Collection (sync_record.bat)</a></li>
        <li><a href="#replaying-scenarios">Replaying Scenarios</a></li>
        <li><a href="#cli-tools-reference">CLI Tools Reference</a></li>
        <li><a href="#multiple-agents-simulation">Multiple Agents Simulation</a></li>
      </ul>
    </li>
    <li><a href="#contributors">Contributors</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

---

<!-- ABOUT THE PROJECT -->
## About The Project

This repository provides an end-to-end, cross-platform co-simulation environment connecting the **CARLA Simulator** running natively on Windows with the **Autoware Universe** autonomous driving stack executing inside Ubuntu 22.04 on WSL2.

The project was created as a university academic project for the **Autonomous Vehicles & Verification (AVV)** curriculum within the **Master's Degree in Computer Science (Advanced Software Engineering)** at the **University of L'Aquila (UNIVAQ)**.

### Architecture Overview

* **CARLA Simulator (Windows Host):** Renders high-fidelity 3D environments (Unreal Engine 4), executes rigid-body physics, simulates sensors (LiDAR, cameras, GNSS, IMU), and computes actor dynamics.
* **Autoware Universe (WSL2 Ubuntu 22.04):** Operates as the vehicle's autonomous software stack, executing localization, perception, scenario and behavior planning, motion velocity profiling, and vehicle control commands over ROS 2 Humble.
* **Network & Middleware Bridge:** Bridges Windows and WSL2 through the virtual network adapter using Eclipse CycloneDDS, custom multicast settings, and tuned Linux socket buffers.
* **Synchronized Telemetry Tooling:** Custom CLI utilities orchestrate simultaneous logging of CARLA physical world recordings (`.log`) alongside Autoware ROS 2 rosbag telemetry (`.db3` / `metadata.yaml`).

### Key Features

* **Cross-Platform Low Latency Interface:** Leverages Windows native GPU capabilities for CARLA rendering while isolating the Linux-native ROS 2 Autoware stack inside WSL2.
* **Network & DDS Optimization:** Includes custom `cyclonedds.xml` configurations and kernel buffer adjustments to eliminate participant discovery bottlenecks and packet drops.
* **Synchronized Telemetry Capture (`sync_record.bat`):** Single-command dual-stream recording keeping simulator truth and autonomous planning states aligned.
* **Dynamic Camera Tracking (`follow_camera.py`):** Multi-mode spectator camera automation (chase, bird's-eye, front-facing) that locks onto the Autoware ego vehicle automatically.
* **Deterministic Simulation Replay (`carla_tools.py`):** Replays physics interactions and traffic scenarios directly within the CARLA environment with custom playback multipliers.
* **Multi-Agent Research Ready:** Documents traffic generation strategies and distributed multi-agent configurations via DMAVA (Distributed Multi-Autonomous Vehicle Architecture) and Zenoh middleware.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [![ROS 2][ROS2-shield]][ROS2-url]
* [![CARLA][CARLA-shield]][CARLA-url]
* [![Autoware][Autoware-shield]][Autoware-url]
* [![Ubuntu][Ubuntu-shield]][Ubuntu-url]
* [![Python][Python-shield]][Python-url]
* [![Windows][Windows-shield]][Windows-url]
* [![Cyclone DDS][CycloneDDS-shield]][CycloneDDS-url]
* [![GNU Bash][Bash-shield]][Bash-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- GETTING STARTED -->
## Getting Started

Follow the step-by-step instructions below to configure the cross-platform co-simulation pipeline between Windows and Ubuntu 22.04 on WSL2.

### Prerequisites

| Component | Required Version / Spec | Platform |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11 with WSL2 enabled | Host OS |
| **WSL Distribution** | Ubuntu 22.04 LTS (AMD64) | WSL2 |
| **Simulator** | CARLA Simulator `0.9.15` | Windows |
| **Autonomous Stack** | Autoware Universe (`main` branch) | WSL2 |
| **Middleware** | ROS 2 Humble Desktop + Eclipse CycloneDDS | WSL2 |
| **Python** | Python `3.10.x` | Windows & WSL2 |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Installation and Setup

#### 1. Install Ubuntu 22.04 for WSL2

1. Download the Ubuntu 22.04 WSL image (`64-bit PC (AMD64) WSL image`) from the official [Ubuntu Releases](https://releases.ubuntu.com/22.04/).
2. Run the installer or import the image into WSL:
   ```cmd
   wsl --install -d Ubuntu-22.04
   ```
3. Verify your WSL version is set to WSL2:
   ```cmd
   wsl --list --verbose
   ```

#### 2. Download CARLA 0.9.15 for Windows

1. Download [CARLA_0.9.15.zip](https://github.com/carla-simulator/carla/releases/tag/0.9.15/) from the official CARLA GitHub releases.
2. Extract the archive into a convenient path on your Windows machine, e.g.:
   ```text
   C:\Users\<YourUsername>\Documents\CARLA_0.9.15\WindowsNoEditor
   ```

#### 3. Install ROS 2 Humble in Ubuntu 22.04 WSL

Execute the following commands in your Ubuntu 22.04 WSL terminal:

1. **Set Locale to UTF-8:**
   ```bash
   sudo apt update && sudo apt install locales -y
   sudo locale-gen en_US en_US.UTF-8
   sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
   export LANG=en_US.UTF-8
   locale
   ```

2. **Add ROS 2 APT Repository:**
   ```bash
   sudo apt install software-properties-common curl -y
   sudo add-apt-repository universe
   export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
   curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
   sudo dpkg -i /tmp/ros2-apt-source.deb
   ```

3. **Install ROS 2 Humble Packages:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install ros-humble-desktop ros-humble-ros-base ros-dev-tools -y
   ```

4. **Verify Installation:**
   In one terminal run:
   ```bash
   source /opt/ros/humble/setup.bash
   ros2 run demo_nodes_cpp talker
   ```
   In a second terminal run:
   ```bash
   source /opt/ros/humble/setup.bash
   ros2 run demo_nodes_py listener
   ```
   Once messages appear, close both test terminals.

#### 4. Install Autoware Universe in Ubuntu 22.04 WSL

1. **Clone the Autoware Repository and run the environment setup script:**
   ```bash
   cd ~
   git clone https://github.com/autowarefoundation/autoware.git
   cd autoware
   ./setup-dev-env.sh
   ```

2. **Set Up the Workspace Repositories:**
   ```bash
   cd ~/autoware
   mkdir -p src
   vcs import src < repositories/autoware.repos
   ```
   *(Optional)* Active developers can import nightly or extra packages:
   ```bash
   vcs import src < repositories/autoware-nightly.repos
   vcs import src < repositories/extra-packages.repos
   ```

3. **Install ROS Dependencies:**
   ```bash
   source /opt/ros/humble/setup.bash
   sudo apt update && sudo apt upgrade -y
   rosdep update
   rosdep install -y --from-paths src --ignore-src --rosdistro $ROS_DISTRO
   ```

4. **Configure Ccache (Recommended for fast builds):**
   ```bash
   sudo apt install ccache -y
   mkdir -p ~/.cache/ccache
   echo "max_size = 60G" > ~/.cache/ccache/ccache.conf
   ```
   Append compiler variables to `~/.bashrc`:
   ```bash
   echo 'export CC="/usr/lib/ccache/gcc"' >> ~/.bashrc
   echo 'export CXX="/usr/lib/ccache/g++"' >> ~/.bashrc
   echo 'export CCACHE_DIR="$HOME/.cache/ccache/"' >> ~/.bashrc
   source ~/.bashrc
   ```

#### 5. Install CARLA Python Bridge & Maps in WSL

1. **Install CARLA Python Wheel:**
   Download [carla-0.9.15-cp310-cp310-linux_x86_64.whl](https://github.com/gezp/carla_ros/releases/tag/carla-0.9.15-ubuntu-22.04) from the `gezp/carla_ros` release to your Windows Desktop, then copy and install it inside WSL:
   ```bash
   cp /mnt/c/Users/<YourUsername>/Desktop/carla-0.9.15-cp310-cp310-linux_x86_64.whl ~
   pip install ~/carla-0.9.15-cp310-cp310-linux_x86_64.whl
   rm -f ~/carla-0.9.15-cp310-cp310-linux_x86_64.whl
   ```

2. **Download CARLA Town01 Lanelet2 Maps:**
   Download `point_cloud/Town01.pcd` and `vector_maps/lanelet2/Town01.osm` (y-axis inverted maps) from [CARLA Autoware Contents](https://bitbucket.org/carla-simulator/autoware-contents/src/master/maps/) to your Windows machine.
   * Rename `Town01.pcd` to `pointcloud_map.pcd`
   * Rename `Town01.osm` to `lanelet2_map.osm`
   * Create a file named `map_projector_info.yaml` with the following content:
     ```yaml
     projector_type: Local
     ```
   In WSL, create the map folder and copy the files:
   ```bash
   mkdir -p ~/autoware/autoware_map/Town01/
   cp /mnt/c/Users/<YourUsername>/Desktop/pointcloud_map.pcd ~/autoware/autoware_map/Town01/
   cp /mnt/c/Users/<YourUsername>/Desktop/lanelet2_map.osm ~/autoware/autoware_map/Town01/
   cp /mnt/c/Users/<YourUsername>/Desktop/map_projector_info.yaml ~/autoware/autoware_map/Town01/
   ```

#### 6. Build Autoware CARLA Interface

In your WSL terminal:
```bash
source /opt/ros/humble/setup.bash
cd ~/autoware
sudo apt update
sudo apt install ros-humble-geographic-msgs ros-humble-pcl-ros -y
rosdep update
find src -type d -name "pacmod_interface" -exec touch {}/COLCON_IGNORE \;
rosdep install -y --from-paths src --ignore-src --rosdistro humble --skip-keys="pacmod3_msgs"
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

#### 7. Network and DDS Configuration

1. **Enable Multicast on Loopback:**
   ```bash
   sudo ip link set lo multicast on
   ```
   *(Note: This resets after WSL restart; it should be executed before starting simulation sessions).*

2. **Verify ROS_LOCALHOST_ONLY is Unset:**
   Ensure `ROS_LOCALHOST_ONLY` is not restricting traffic to the local VM.
   ```bash
   grep ROS_LOCALHOST_ONLY ~/.bashrc
   ```
   If set, remove or comment it out (`# export ROS_LOCALHOST_ONLY=1`) in `~/.bashrc`, then execute:
   ```bash
   unset ROS_LOCALHOST_ONLY
   ```

3. **Tune Kernel DDS Buffer Settings:**
   ```bash
   sudo sysctl -w net.core.rmem_max=2147483647
   sudo sysctl -w net.ipv4.ipfrag_time=3
   sudo sysctl -w net.ipv4.ipfrag_high_thresh=134217728
   ```

4. **Install CycloneDDS Configuration:**
   Copy `config/cyclonedds.xml` from this repository into your WSL home folder:
   ```bash
   cp /mnt/c/Users/<YourUsername>/path/to/univaq-avv-carla-autoware/config/cyclonedds.xml ~
   ```
   Add the middleware configuration to your `~/.bashrc`:
   ```bash
   echo 'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp' >> ~/.bashrc
   echo 'export CYCLONEDDS_URI=file:///home/<YourWSLUsername>/cyclonedds.xml' >> ~/.bashrc
   source ~/.bashrc
   ```

#### 8. Configure autoware_carla_interface

By default, the CARLA interface connects to `localhost:2000`. You must redirect it to your Windows host vEthernet adapter IP:

1. In Windows PowerShell, run `ipconfig` and note the IPv4 address under `vEthernet (WSL)` (e.g., `172.x.x.x`).
2. In WSL, locate the launch configuration:
   ```bash
   cd ~/autoware
   find src -name "autoware_carla_interface.launch.xml"
   ```
3. Open `src/universe/autoware_universe/simulator/autoware_carla_interface/launch/autoware_carla_interface.launch.xml` and update the host argument:
   ```xml
   <arg name="host" default="<Your_Windows_vEthernet_IP>"/>
   ```
4. Rebuild the interface package:
   ```bash
   colcon build --packages-select autoware_carla_interface
   source install/setup.bash
   ```

#### 9. Console Settings for ROS 2

To improve logging readability, add the following to `~/.bashrc`:
```bash
export RCUTILS_COLORIZED_OUTPUT=1
export RCUTILS_CONSOLE_OUTPUT_FORMAT="[{severity} {time}] [{name}]: {message} ({function_name}() at {file_name}:{line_number})"
export GTEST_COLOR=1
```

#### 10. Setup Workspaces

1. **Windows Workspace:**
   Open a terminal in the project directory on Windows, create a Python 3.10 virtual environment, and install dependencies:
   ```cmd
   pip install -r .\scripts\windows\requirements.txt
   ```
2. **WSL Workspace:**
   Copy `autoware_tools.py` into your Autoware home folder:
   ```bash
   cp /mnt/c/Users/<YourUsername>/path/to/univaq-avv-carla-autoware/scripts/wsl/autoware_tools.py ~/autoware/
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- USAGE -->
## Usage

### Running the Simulation

Follow this sequence to launch the co-simulation:

1. **Start CARLA on Windows:**
   Open a Windows terminal, navigate to your CARLA installation folder, and run:
   ```cmd
   cd C:\Users\<YourUsername>\Documents\CARLA_0.9.15\WindowsNoEditor
   CarlaUE4.exe -prefernvidia -quality-level=Low -RenderOffScreen
   ```
   *(Omit `-RenderOffScreen` if you want the visual CARLA renderer window displayed).*

2. **Prepare Network & Environment in WSL2:**
   Open a WSL2 terminal:
   ```bash
   cd ~/autoware
   sudo ip link set lo multicast on
   sudo sysctl -w net.core.rmem_max=2147483647
   sudo sysctl -w net.ipv4.ipfrag_time=3
   sudo sysctl -w net.ipv4.ipfrag_high_thresh=134217728
   source install/setup.bash
   ```

3. **Launch Autoware with CARLA Simulator:**
   ```bash
   ros2 launch autoware_launch e2e_simulator.launch.xml map_path:=$HOME/autoware/autoware_map/Town01 vehicle_model:=sample_vehicle sensor_model:=carla_sensor_kit simulator_type:=carla
   ```

4. **Initialize Vehicle Navigation in RViz:**
   * Click **2D Pose Estimate** / **Init by GNSS** to initialize localization.
   * Click **2D Goal Pose** to designate a destination.
   * Wait for the trajectory planner to calculate the path.
   * Click **Engage** to command the vehicle to drive autonomously.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

### Spectator Camera Tracking (`follow_camera.py`)

To follow the autonomous vehicle smoothly within CARLA, run the camera tracking script in a Windows Command Prompt:

```cmd
cd .\scripts\windows
python follow_camera.py
```

The script polls CARLA until it identifies `ego_vehicle`, then anchors the spectator viewpoint to it.

```cmd
# Alternative viewing perspectives
python follow_camera.py --mode top          # Overhead bird's-eye view (ideal for intersections)
python follow_camera.py --mode front        # Forward-facing reverse camera looking backward

# Custom distance, elevation, and tick rate
python follow_camera.py --offset-back 5.0 --offset-z 2.0 --rate 30.0
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--mode` | string | `behind` | Camera angle: `behind`, `top`, or `front` |
| `--offset-back`| float | `8.0` | Distance behind the vehicle in meters |
| `--offset-z` | float | `4.0` | Height above the vehicle in meters |
| `--rate` | float | `30.0` | Refresh frequency in Hz |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

### Synchronized Data Collection (`sync_record.bat`)

To log simulation physics and Autoware internal states simultaneously without timeline drift:

1. Ensure CARLA and Autoware are connected and running.
2. In a Windows Command Prompt, navigate to the scripts folder and launch:
   ```cmd
   cd .\scripts\windows
   sync_record.bat
   ```
3. A synchronized WSL terminal titled `"Autoware Recorder"` will open to capture the ROS 2 bag while the main Windows console records CARLA simulator physics.
4. When finished, press `Ctrl+C` in each window. Both recordings are safely flushed and stored under `recordings/`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

### Replaying Scenarios

To inspect physical trajectories and world events without running Autoware:

1. Close Autoware and restart a fresh CARLA instance on Windows.
2. Run the replay command:
   ```cmd
   python scripts/windows/carla_tools.py replay --recording carla_snapshot_<timestamp>.log
   ```
3. CARLA will reset actor states, reposition the ego vehicle, and replay the physics session at the designated speed multiplier.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

### CLI Tools Reference

#### CARLA Tools (`scripts/windows/carla_tools.py`)

Interacts with the CARLA Python API on Windows:

* **Record Session:**
  ```cmd
  python carla_tools.py record [--additional_data] [--host localhost] [--port 2000]
  ```
  *(Saves binary simulation logs to `recordings/carla_snapshot_<timestamp>.log`).*

* **Replay Session:**
  ```cmd
  python carla_tools.py replay --recording <file.log> [--start 0.0] [--duration 0.0] [--camera 0] [--time_factor 1.0]
  ```

* **Inspect Log Metadata:**
  ```cmd
  python carla_tools.py info --recording <file.log> [--show_all]
  ```
  *(Parses `.log` contents and exports human-readable frame summaries to `.txt`).*

#### Autoware Tools (`scripts/wsl/autoware_tools.py`)

Interacts with ROS 2 inside Ubuntu 22.04 on WSL2 (requires `source /opt/ros/humble/setup.bash`):

* **Record ROS 2 Bag:**
  ```bash
  python3 autoware_tools.py record [options]
  ```
  Records core ADAS topics by default:
  * `/planning/scenario_planning/trajectory`
  * `/control/command/control_cmd`
  * `/perception/object_recognition/objects`
  * `/localization/kinematic_state`
  * `/tf`
  * `/tf_static`

  *Options:*
  * `--all`: Capture every active ROS 2 topic (*warning: large storage footprint*).
  * `--topics`: Specify custom space-separated topic list:
    ```bash
    python3 autoware_tools.py record --topics /sensing/lidar/top/pointcloud_raw /vehicle/status/velocity_status
    ```

* **Inspect Bag Metadata:**
  ```bash
  python3 autoware_tools.py info --bag <bag_folder_name>
  ```
  *(Generates `<bag_folder_name>_info.txt` summarizing duration, message counts, and topic frequencies).*

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

### Multiple Agents Simulation

#### Background Traffic Generation
To populate the simulation with ambient traffic and pedestrians around the ego vehicle, run CARLA's built-in traffic generator:
```cmd
cd C:\Users\<YourUsername>\Documents\CARLA_0.9.15\WindowsNoEditor\PythonAPI\examples
python .\generate_traffic.py -n 30 -w 10
```
Autoware perceives these actors through sensor streams (LiDAR, camera object detection) and dynamically performs obstacle avoidance and yielding maneuvers.

#### Distributed Multi-Autonomous Vehicle Architecture (DMAVA)
To operate multiple independent Autoware instances within a shared CARLA world:
* Each vehicle stack is partitioned into a separate ROS 2 namespace (e.g., `/ego_vehicle_1`, `/ego_vehicle_2`).
* Inter-agent communication and simulator interfacing scale efficiently by substituting default DDS multicasting with the **Eclipse Zenoh** protocol to prevent network saturation.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- CONTRIBUTORS -->
## Contributors

> [!NOTE]
> This repository was developed as an academic university project at the **University of L'Aquila (UNIVAQ)**. As such, **external contributions and pull requests are not currently accepted**. However, project contributors and authors are highlighted below.

<a href="https://github.com/CarlinoCalogero/univaq-avv-carla-autoware/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=CarlinoCalogero/univaq-avv-carla-autoware" alt="contrib.rocks image" />
</a>

* **Calogero Carlino** - *Master's Graduate in Computer Science (110/110 cum laude), University of L'Aquila*
  * GitHub: [@CarlinoCalogero](https://github.com/CarlinoCalogero)
  * Portfolio: [carlinocalogero.github.io](https://carlinocalogero.github.io)
  * LinkedIn: [calogero-carlino](https://www.linkedin.com/in/calogero-carlino-2a94a33b5/)
  * Email: [carlinocalogero.dev@gmail.com](mailto:carlinocalogero.dev@gmail.com)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- CONTACT -->
## Contact

**Calogero Carlino** - [carlinocalogero.dev@gmail.com](mailto:carlinocalogero.dev@gmail.com)

* **GitHub:** [https://github.com/CarlinoCalogero](https://github.com/CarlinoCalogero)
* **LinkedIn:** [https://www.linkedin.com/in/calogero-carlino-2a94a33b5/](https://www.linkedin.com/in/calogero-carlino-2a94a33b5/)
* **Portfolio Website:** [https://carlinocalogero.github.io](https://carlinocalogero.github.io)
* **Project Repository:** [https://github.com/CarlinoCalogero/univaq-avv-carla-autoware](https://github.com/CarlinoCalogero/univaq-avv-carla-autoware)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [University of L'Aquila (UNIVAQ)](https://www.univaq.it/) - Department of Information Engineering, Computer Science and Mathematics (DISIM)
* [CARLA Simulator Team](https://carla.org/) - Open-source simulator for autonomous driving research
* [Autoware Foundation](https://autoware.org/) - Open-source software stack for self-driving vehicles
* [Eclipse Cyclone DDS](https://cyclonedds.io/)
* [ROS 2 Documentation & Community](https://docs.ros.org/en/humble/)
* [Best-README-Template](https://github.com/othneildrew/Best-README-Template)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/CarlinoCalogero/univaq-avv-carla-autoware.svg?style=for-the-badge
[contributors-url]: https://github.com/CarlinoCalogero/univaq-avv-carla-autoware/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/CarlinoCalogero/univaq-avv-carla-autoware.svg?style=for-the-badge
[forks-url]: https://github.com/CarlinoCalogero/univaq-avv-carla-autoware/network/members
[stars-shield]: https://img.shields.io/github/stars/CarlinoCalogero/univaq-avv-carla-autoware.svg?style=for-the-badge
[stars-url]: https://github.com/CarlinoCalogero/univaq-avv-carla-autoware/stargazers
[issues-shield]: https://img.shields.io/github/issues/CarlinoCalogero/univaq-avv-carla-autoware.svg?style=for-the-badge
[issues-url]: https://github.com/CarlinoCalogero/univaq-avv-carla-autoware/issues
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/calogero-carlino-2a94a33b5/

<!-- Tech Badges -->
[ROS2-shield]: https://img.shields.io/badge/ROS_2-Humble-22314E?style=for-the-badge&logo=ros&logoColor=white
[ROS2-url]: https://docs.ros.org/en/humble/
[CARLA-shield]: https://img.shields.io/badge/CARLA-0.9.15-000000?style=for-the-badge&logo=car&logoColor=white
[CARLA-url]: https://carla.org/
[Autoware-shield]: https://img.shields.io/badge/Autoware_Universe-1E3A8A?style=for-the-badge&logo=autoware&logoColor=white
[Autoware-url]: https://autoware.org/
[Ubuntu-shield]: https://img.shields.io/badge/Ubuntu_22.04_LTS-E95420?style=for-the-badge&logo=ubuntu&logoColor=white
[Ubuntu-url]: https://releases.ubuntu.com/22.04/
[Python-shield]: https://img.shields.io/badge/Python_3.10-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Windows-shield]: https://img.shields.io/badge/Windows_11%2F10-0078D4?style=for-the-badge&logo=windows&logoColor=white
[Windows-url]: https://www.microsoft.com/windows
[CycloneDDS-shield]: https://img.shields.io/badge/Eclipse_Cyclone_DDS-004481?style=for-the-badge&logo=eclipse&logoColor=white
[CycloneDDS-url]: https://cyclonedds.io/
[Bash-shield]: https://img.shields.io/badge/GNU_Bash-4EAA25?style=for-the-badge&logo=gnubash&logoColor=white
[Bash-url]: https://www.gnu.org/software/bash/
