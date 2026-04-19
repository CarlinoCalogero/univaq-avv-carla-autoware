# CARLA & Autoware Co-Simulation Framework

A complete, cross-platform development environment bridging the CARLA simulator (Windows) with the Autoware AI brain (Ubuntu WSL2). This repository includes setup instructions, network bridging configurations, and custom CLI tools for synchronized data collection and replay.

## Table of Contents
1. [Install Ubuntu 22.04 for WSL](#install-ubuntu-22-04-for-wsl)
2. [Download CARLA 0.9.15 for Windows](#download-carla-0-9-15-for-windows)
3. [Install ROS 2 in Ubuntu 22.04 WSL](#install-ros-2-in-ubuntu-2204-wsl)
4. [Install Autoware in Ubuntu 22.04 WSL](#install-autoware-in-ubuntu-2204-wsl)
5. [Install Bridge in Ubuntu 22.04 WSL](#install-bridge-in-ubuntu-2204-wsl)
6. [Network Configuration](#network-configuration)
7. [Configure the autoware_carla_interface](#configure-the-autoware_carla_interface)
8. [Set up Windows Workspace](#set-up-windows-workspace)
9. [Set up Ubuntu 22.04 WSL Workspace](#set-up-ubuntu-2204-wsl-workspace)
10. [Run](#run)
11. [Data Collection & Synchronization](#data-collection--synchronization-sync_recordbat)
12. [Replaying Scenarios (Simulator vs. Brain)](#replaying-scenarios-simulator-vs-brain)
13. [CLI Tools Reference](#cli-tools-reference)

---

## Install Ubuntu 22.04 for WSL
Go to this [link](https://releases.ubuntu.com/22.04/) and download the WSL image `64-bit PC (AMD64) WSL image`. Then double click on it after download and follow installation instructions.

## Download CARLA 0.9.15 for Windows

Download [CARLA_0.9.15.zip](https://github.com/carla-simulator/carla/releases/tag/0.9.15/), unzip it in a handy location on your Windows PC.

## Install ROS 2 in Ubuntu 22.04 WSL

The following steps are taken from this [reference](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) documentation.

You must execute all the following commands in your Ubuntu 22.04 WSL terminal.

### Set locale

Make sure you have a locale which supports `UTF-8`. If you are in a minimal environment (such as a docker container), the locale may be something minimal like `POSIX`. We test with the following settings. However, it should be fine if you’re using a different UTF-8 supported locale.

```bash
locale  # check for UTF-8
```

```bash
sudo apt update && sudo apt install locales
```

```bash
sudo locale-gen en_US en_US.UTF-8
```

```bash
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
```

```bash
export LANG=en_US.UTF-8
```

```bash
locale  # verify settings
```

### Setup Sources

You will need to add the ROS 2 apt repository to your system.

First ensure that the [Ubuntu Universe repository](https://help.ubuntu.com/community/Repositories/Ubuntu) is enabled.

```bash
sudo apt install software-properties-common
```

```bash
sudo add-apt-repository universe
```

The [ros-apt-source](https://github.com/ros-infrastructure/ros-apt-source/) packages provide keys and apt source configuration for the various ROS repositories.

Installing the ros2-apt-source package will configure ROS 2 repositories for your system. Updates to repository configuration will occur automatically when new versions of this package are released to the ROS repositories.

```bash
sudo apt update && sudo apt install curl -y
```

```bash
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
```

```bash
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
```

```bash
sudo dpkg -i /tmp/ros2-apt-source.deb
```

### Install ROS 2 packages

Update your apt repository caches after setting up the repositories.

```bash
sudo apt update
```

ROS 2 packages are built on frequently updated Ubuntu systems. It is always recommended that you ensure your system is up to date before installing new packages.

```bash
sudo apt upgrade
```

Desktop Install (Recommended): ROS, RViz, demos, tutorials.

```bash
sudo apt install ros-humble-desktop
```

ROS-Base Install (Bare Bones): Communication libraries, message packages, command line tools. No GUI tools.

```bash
sudo apt install ros-humble-ros-base
```

Development tools: Compilers and other tools to build ROS packages

```bash
sudo apt install ros-dev-tools
```

### Try some examples

If you installed `ros-humble-desktop` above you can try some examples.

In one terminal, source the setup file and then run a C++ `talker`:

```bash
source /opt/ros/humble/setup.bash
```

```bash
ros2 run demo_nodes_cpp talker
```

Open another Ubuntu 22.04 WSL terminal and run

```bash
source /opt/ros/humble/setup.bash
```

```bash
ros2 run demo_nodes_py listener
```

You should see the `talker` saying that it’s `Publishing` messages and the `listener` saying `I heard` those messages. This verifies both the C++ and Python APIs are working properly.

You can now close both terminals

## Install Autoware in Ubuntu 22.04 WSL

The following steps are taken from this [reference](https://autowarefoundation.github.io/autoware-documentation/main/installation/autoware/source-installation/) documentation.

You must execute all the following commands in your Ubuntu 22.04 WSL terminal.

### How to set up a development environment

Clone autowarefoundation/autoware and move to the directory.

```bash
git clone https://github.com/autowarefoundation/autoware.git
```

```bash
cd autoware
```

If you are installing Autoware for the first time, you can automatically install the dependencies by using the provided Ansible script.

```bash
./setup-dev-env.sh
```

### How to set up a workspace

#### Create the `src` directory and clone repositories into it.

Autoware uses `vcs2l` to construct workspaces.

```bash
cd autoware
```

```bash
mkdir -p src
```

```bash
vcs import src < repositories/autoware.repos
```

If you are an active developer, you may also want to pull the nightly repositories, which contain the latest updates:

```bash
vcs import src < repositories/autoware-nightly.repos
```

Optionally, you may also download the extra repositories that contain drivers for specific hardware, but they are not necessary for building and running Autoware:

```bash
vcs import src < repositories/extra-packages.repos
```

#### Install dependent ROS packages.
Autoware requires some ROS 2 packages in addition to the core components. The tool rosdep allows an automatic search and installation of such dependencies. You might need to run rosdep update before rosdep install.

```bash
source /opt/ros/humble/setup.bash
```

```bash
# Make sure all previously installed ros-$ROS_DISTRO-* packages are upgraded to their latest version
sudo apt update && sudo apt upgrade
```

```bash
rosdep update
```

```bash
rosdep install -y --from-paths src --ignore-src --rosdistro $ROS_DISTRO
```

#### Install and set up ccache to speed up consecutive builds. (optional but highly recommended)
Ccache is a compiler cache that can significantly speed up recompilation by caching previous compilations and reusing them when the same compilation is being done again. It's highly recommended for developers looking to optimize their build times, unless there's a specific reason to avoid it.

Install Ccache

```bash
sudo apt update && sudo apt install ccache
```

Create the Ccache configuration folder and file:

```bash
mkdir -p ~/.cache/ccache
```

```bash
touch ~/.cache/ccache/ccache.conf
```

Set the maximum cache size. The default size is 5GB, but you can increase it depending on your needs. Here, we're setting it to 60GB:

```bash
echo "max_size = 60G" >> ~/.cache/ccache/ccache.conf
```

To ensure Ccache is used for compilation, add the following lines to your .bashrc file. This will redirect GCC and G++ calls through Ccache.

```bash
export CC="/usr/lib/ccache/gcc"
```

```bash
export CXX="/usr/lib/ccache/g++"
```

```bash
export CCACHE_DIR="$HOME/.cache/ccache/"
```

After adding these lines, reload your .bashrc or restart your terminal session to apply the changes.

To confirm Ccache is correctly set up and being used, you can check the statistics of cache usage:

```bash
ccache -s
```

This command displays the cache hit rate and other relevant statistics, helping you gauge the effectiveness of Ccache in your development workflow.

## Install Bridge in Ubuntu 22.04 WSL

The following steps are taken from this [reference](https://autowarefoundation.github.io/autoware_universe/main/simulator/autoware_carla_interface/) documentation.

### Install CARLA Python Package

Install CARLA 0.9.15 ROS 2 Humble communication package

Download [carla-0.9.15-cp310-cp310-linux_x86_64.whl](https://github.com/gezp/carla_ros/releases/tag/carla-0.9.15-ubuntu-22.04) on your Windows desktop.

Open your Ubuntu 22.04 terminal and move the file in your home directory

```bash
cp -p /mnt/c/Users/<YourUsername>/Desktop/carla-0.9.15-cp310-cp310-linux_x86_64.whl ~
```

Install the wheel with pip
```bash
pip install carla-0.9.15-cp310-cp310-linux_x86_64.whl
```

Remove the wheel

```bash
rm -rf carla-0.9.15-cp310-cp310-linux_x86_64.whl
```

### Download CARLA Lanelet2 Maps
Download `point_cloud/Town01.pcd` and `vector_maps/lanelet2/Town01.osm` y-axis inverted maps from [CARLA Autoware Contents](https://bitbucket.org/carla-simulator/autoware-contents/src/master/maps/) in your Windows OS.

Rename `point_cloud/Town01.pcd` → `pointcloud_map.pcd`

Rename `vector_maps/lanelet2/Town01.osm` → `lanelet2_map.osm`

Create a `map_projector_info.yaml` file with:

```yaml
projector_type: Local
```

Open your WSL Ubuntu 22.04 terminal and create the map folder 

```bash
mkdir -p ~/autoware/autoware_map/Town01/
```

Move the files to this new location

```bash
cp -p /mnt/c/Users/<YourUsername>/Desktop/pointcloud_map.pcd ~/autoware/autoware_map/Town01/
```

```bash
cp -p /mnt/c/Users/<YourUsername>/Desktop/lanelet2_map.osm ~/autoware/autoware_map/Town01/
```

```bash
cp -p /mnt/c/Users/<YourUsername>/Desktop/map_projector_info.yaml ~/autoware/autoware_map/Town01/
```

## Build

To build Autoware bridge run the following commands.

```bash
source /opt/ros/humble/setup.bash
```

```bash
cd ~/autoware
```

```bash
sudo apt update
```

```bash
sudo apt install ros-humble-geographic-msgs
```

```bash
sudo apt install ros-humble-pcl-ros
```

```bash
rosdep update
```

```bash
find src -type d -name "pacmod_interface" -exec touch {}/COLCON_IGNORE \;
```

```bash
rosdep install -y --from-paths src --ignore-src --rosdistro humble --skip-keys="pacmod3_msgs"
```

```bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

## Network configuration

### Enable multicast on lo

You may just call the following command to enable multicast on the loopback interface.

```bash
sudo ip link set lo multicast on
```

**This will be reverted once the computer restarts. So it must be called every time.**

### ROS_LOCALHOST_ONLY

It is crucial to ensure export ROS_LOCALHOST_ONLY=1 is removed when setting up your WSL2-to-Windows connection. If that variable is active, ROS 2 will refuse to send or receive data outside of its own virtual machine, meaning it will never see the CARLA server on Windows.

Open your WSL2 terminal and run this command to search your `.bashrc` file:

```bash
grep ROS_LOCALHOST_ONLY ~/.bashrc
```

If it prints nothing you are good to go! The line is not in your file.

If it prints `export ROS_LOCALHOST_ONLY=1` you need to remove or comment it out. The easiest way to edit the file in the terminal is using the nano text editor.

Open the file:

```bash
nano ~/.bashrc
```

Scroll down using your arrow keys (or use `Ctrl + W` to search for "ROS_LOCALHOST_ONLY") until you find the line.

Comment it out by adding a `#` at the very beginning of the line, like this:

```bash
# export ROS_LOCALHOST_ONLY=1
```

(Alternatively, you can just delete the whole line).

Save and exit by pressing `Ctrl + O` (letter O, not zero), hit `Enter` to confirm the file name, and then press `Ctrl + X` to exit nano

Even after removing it from the file, the variable might still be lingering in your current terminal memory. To fix this apply the updated `.bashrc`:

```bash
source ~/.bashrc
```

Unset the variable for your current active terminal session:

```bash
unset ROS_LOCALHOST_ONLY
```

To absolutely guarantee that ROS 2 is no longer restricted to localhost, run:

```bash
echo $ROS_LOCALHOST_ONLY
```

### Tune DDS settings

Autoware uses DDS for internode communication. ROS 2 documentation recommends users to tune DDS to utilize its capability. CycloneDDS is the recommended and most tested DDS implementation for Autoware.

Set the config file path and enlarge the Linux kernel maximum buffer size before launching Autoware.

```bash
# Increase the maximum receive buffer size for network packets
sudo sysctl -w net.core.rmem_max=2147483647  # 2 GiB, default is 208 KiB

# IP fragmentation settings
sudo sysctl -w net.ipv4.ipfrag_time=3  # in seconds, default is 30 s
sudo sysctl -w net.ipv4.ipfrag_high_thresh=134217728  # 128 MiB, default is 256 KiB
```

**This must be done every time before launching Autoware.**

Validate the sysctl settings

```bash
sysctl net.core.rmem_max net.ipv4.ipfrag_time net.ipv4.ipfrag_high_thresh
```

### CycloneDDS Configuration

Copy `cyclonedds.xml` inside WSL

```bash
cp -r /mnt/c/Users/<YourUsername>/path/to/repo/config/cyclonedds.xml ~
```

On ROS 2 Jazzy, the default maximum Participant Index in rmw_cyclonedds_cpp is limited to around 32, which can cause a "Failed to find a free participant index for domain 0" error when running many nodes (e.g. planning simulator). Adding the `<Discovery>` section above with `ParticipantIndex` set to `none` avoids this error.

Then open your `~/.bashrc` file

```bash
nano ~/.bashrc
```

and add the following lines

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

export CYCLONEDDS_URI=file:///absolute/path/to/cyclonedds.xml
# Replace `/absolute/path/to/cyclonedds.xml` with the actual path to the file.
# Example: export CYCLONEDDS_URI=file:///home/user/cyclonedds.xml
```

## Console settings for ROS 2

### Colorizing logger output

By default, ROS 2 logger doesn't colorize the output. To colorize it, add the following to your `~/.bashrc`:

```bash
export RCUTILS_COLORIZED_OUTPUT=1
```

### Customizing the format of logger output

By default, ROS 2 logger doesn't output detailed information such as file name, function name, or line number. To customize it, add the following to your `~/.bashrc`:

```bash
export RCUTILS_CONSOLE_OUTPUT_FORMAT="[{severity} {time}] [{name}]: {message} ({function_name}() at {file_name}:{line_number})"
```

For more options, see [here](https://docs.ros.org/en/rolling/Tutorials/Demos/Logging-and-logger-configuration.html#console-output-formatting).


### Colorized GoogleTest output
Add 

```bash
export GTEST_COLOR=1
```

to your `~/.bashrc`.

For more details, refer to [Advanced GoogleTest Topics: Colored Terminal Output](https://google.github.io/googletest/advanced.html#colored-terminal-output).

This is useful when running tests with colcon test.

## Configure the autoware_carla_interface

By default, the interface expects the CARLA server to be running on `localhost:2000`. You need to point it to your Windows host IP.

In your Autoware workspace inside WSL2, locate the configuration or launch file for the `autoware_carla_interface`

Open your WSL2 terminal and navigate to your Autoware workspace directory. (Usually, this is a folder named autoware in your home directory, but adjust the command if you named it differently).

```bash
cd ~/autoware
```

Since Autoware Universe has many folders, the easiest way to find the exact path to the CARLA interface launch file is to use the `find` command:

```bash
find src -name "autoware_carla_interface.launch.xml" 
# (If it doesn't find an .xml file, try: find src -name "autoware_carla_interface.launch.py")
```

This will print out a path that looks something like this:

```bash
src/universe/autoware_universe/simulator/autoware_carla_interface/launch/autoware_carla_interface.launch.xml
```

Copy the path that the `find` command gave you, and open it using `nano` (or type `code .` to open your whole workspace in VS Code, which is highly recommended for WSL2!).

If using `nano`, the command will look like this:

```bash
nano src/universe/autoware_universe/simulator/autoware_carla_interface/launch/autoware_carla_interface.launch.xml
```

Once the file is open, look for the parameter or argument that defines the host or hostname. It usually looks something like this:

```xml
<arg name="host" default="localhost"/>
```

(If it's a Python file or YAML file, it might look like `host: 'localhost'` or `default_value='localhost'`)

Use your arrow keys to navigate to `localhost` and delete it.

Replace it with your Windows vEthernet (WSL) IPv4 address (e.g., 172.x.x.x) found by running the `ipconfig` command

```xml
<arg name="host" default="172.25.80.1"/>
```

Save and exit nano using the steps you just learned: `Ctrl + O`, `Enter`, `Ctrl + X`.

Because you changed a file inside the `src` folder, you need to quickly rebuild that specific package so ROS 2 recognizes the changes. Run:

```bash
colcon build --packages-select autoware_carla_interface
```

Source your workspace to apply the changes:

```bash
source install/setup.bash
```

## Set up Windows Workspace

Open a terminal in your windows folder and create a Python environment using Python 3.10, then install the requirements

```cmd
pip install -r .\scripts\windows\requirements.txt
```

*Note: Always source this environment when running python scripts from Windows.*

## Set up Ubuntu 22.04 WSL Workspace

Open a new WSL terminal and copy the `autoware_tools.py` inside your autoware folder

```bash
cp -r /mnt/c/Users/<YourUsername>/path/to/repo/scripts/wsl/autoware_tools.py ~/autoware
```

## Run

1. In Windows go to your CARLA directory

```cmd
cd C:\Users\<YourUsername>\Documents\CARLA_0.9.15\WindowsNoEditor
```

2. Run CARLA, change map, spawn object if you need

```cmd
./CarlaUE4.exe -prefernvidia -quality-level=Low -RenderOffScreen
```

**If you omit `-RenderOffScreen` you can see the CARLA window popping up**

3. Open a WSL terminal, set up the environment

```bash
cd ~/autoware
sudo ip link set lo multicast on
sudo sysctl -w net.core.rmem_max=2147483647
sudo sysctl -w net.ipv4.ipfrag_time=3
sudo sysctl -w net.ipv4.ipfrag_high_thresh=134217728
source install/setup.bash
```

4. Run Autoware with CARLA

```bash
ros2 launch autoware_launch e2e_simulator.launch.xml map_path:=$HOME/autoware/autoware_map/Town01 vehicle_model:=sample_vehicle sensor_model:=carla_sensor_kit simulator_type:=carla
```

If you want the CARLA spectator camera to automatically track the Autoware vehicle as it drives, open a **new Windows Command Prompt**, navigate to your script folder

```cmd
cd .\scripts\windows\
```

source the python environment and run `follow_camera.py` tool

```cmd
python .\follow_camera.py
```

The script will patiently wait until it detects the `ego_vehicle` in the simulation and then attach the camera to it.

**Basic Usage (Chase Cam):**

```cmd
python follow_camera.py
```

**Alternative Camera Modes:**

```cmd
python follow_camera.py --mode top          # Bird's-eye view (great for intersections)
python follow_camera.py --mode front        # Front-facing camera looking backward
```

**Customizing the Camera:**

You can tweak the exact position and update speed using the following arguments:

* `--mode`: `behind` (default), `top`, or `front`.

* `--offset-back`: Distance behind the vehicle in meters (Default: `8.0`).

* `--offset-z`: Height above the vehicle in meters (Default: `4.0`).

* `--rate`: Camera update rate in Hz (Default: `30.0`).

*Example of a close-up, low-angle tracking shot:*

```cmd
python follow_camera.py --offset-back 5.0 --offset-z 2.0
```

5. Set initial pose (Init by GNSS)

6. Set goal position

7. Wait for planning

8. Engage

## Data Collection & Synchronization (`sync_record.bat`)

We use two parallel tools for data collection: `carla_tools.py` (which records the 3D world physics) and `autoware_tools.py` (which records the AI's internal thoughts via ROS 2 bags). 

To ensure the timelines match up perfectly, use the synchronized batch file.

**How to record a scenario:**
1. Ensure both your CARLA server and Autoware are running and connected (Steps 1-8 above).

2. Open a normal Windows Command Prompt, navigate to your script folder, and run the batch file:

```cmd
sync_record.bat
```

3. A new "Autoware Recorder" WSL window will automatically pop up to record the ROS 2 bag, while your main window records the CARLA simulator.

4. When your scenario is finished, click on each terminal window and press `Ctrl+C`. The scripts will safely save the files and the windows will automatically close.

All data is saved automatically in a generated `recordings/` folder next to your scripts.

## Replaying Scenarios

If you want to watch the physics, traffic, and vehicle movement exactly as it happened in the 3D world:

1. Close Autoware and CARLA and start a new CARLA session.

2. In a Windows Command Prompt, run:

```cmd
python scripts/windows/carla_tools.py replay --recording your_snapshot.log
```

3. CARLA will automatically reset the world, teleport the car to the starting line, and replay the physics. Autoware does not need to be running for this.

## CLI Tools Reference

Below is the complete reference for the standalone Python tools, including all available commands and their optional parameters.

### CARLA Unified Tools (`carla_tools.py`)

This tool was developed using the [official documentation](https://carla.readthedocs.io/en/0.9.15/adv_recorder/) as reference.

Run this script natively on **Windows** to interact with the CARLA server. 

**Global Arguments** These can be placed before any command if your CARLA server is not running locally on the default port.

* `--host`: The IP address of the CARLA Server (Default: `localhost`).

* `--port`: The port of the CARLA Server (Default: `2000`).

#### `record`

Starts a new simulation recording. Files are saved as `.log` in the `recordings/` folder.

```cmd
python carla_tools.py record [options]
```

* `--additional_data`: (Optional flag) If included, records additional data including: linear and angular velocity of vehicles and pedestrians, traffic light time settings, execution time, actors' trigger and bounding boxes, and physics controls for vehicles.

#### `replay`

Replays a saved `.log` file inside the simulator.

```cmd
python carla_tools.py replay --recording <file.log> [options]
```

* `--recording`: **(Required)** The exact name of the `.log` file to replay.

* `--start`: (Optional) Recording time in seconds to start the simulation at. If positive, time is considered from the beginning of the recording. If negative, it is considered from the end. (Default: `0.0`).

* `--duration`: (Optional) Seconds to playback. `0` plays the entire recording. By the end of the playback, vehicles will be set to autopilot and pedestrians will stop. (Default: `0.0`).

* `--camera`: (Optional) ID of the actor that the camera will focus on. Set it to `0` to let the spectator move freely. (Default: `0`).

* `--time_factor`: (Optional) Playback speed multiplier. For example, `2.0` is double speed. (Default: `1.0`).

#### `info`

Extracts data from a binary .log file into a readable .txt file.

```cmd
python carla_tools.py info --recording <file.log> [options]
```

* `--recording`: **(Required)** The exact name of the .log file to parse.

* `--show_all`: (Optional flag) By default, the tool only retrieves frames where an event was registered (summary mode). Setting this flag returns all the information for every single frame (detailed mode).

### Autoware Unified Tools (`autoware_tools.py`)

Run this script inside your Ubuntu / WSL2 terminal to interact with ROS 2. 

**Note: Before using this tool you must run**

```bash
source /opt/ros/humble/setup.bash
```

#### `record`

Starts a new ROS 2 bag recording in the background. By default, it records the core ADAS topics: 
1. `/planning/scenario_planning/trajectory`
2. `/control/command/control_cmd`
3. `/perception/object_recognition/objects`
4. `/localization/kinematic_state`
5. `/tf`
6. `/tf_static`

```bash
python3 autoware_tools.py record [options]
```

* `--all`: (Optional flag) Records ALL active ROS 2 topics. Warning: This will result in massive file sizes and may impact system performance.

* `--topics`: (Optional) A space-separated list of specific topics to record instead of the defaults.

Example:

```bash
python3 autoware_tools.py record --topics /sensing/lidar/top/pointcloud_raw /vehicle/status/velocity_status
```

#### `info`

Extracts the ROS 2 bag metadata (total duration, message counts, topic list) and saves it as a `.txt` file.

```bash
python3 autoware_tools.py info --bag <bag_folder_name>
```

* `--bag`: **(Required)** The exact name of the bag folder to parse.