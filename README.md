# Install ubuntu 22.04 for wsl
Go to this [link](https://releases.ubuntu.com/22.04/) and download the WSL image `64-bit PC (AMD64) WSL image`. Then double click on it after download and follow installation instructions

# Download carla for windows
Download [CARLA_0.9.15.zip](https://github.com/carla-simulator/carla/releases/tag/0.9.15/), unzip it in a handy location on your Windows pc

# Install ros2 in ubuntu 22.04 wsl
The following steps are taken from this [reference](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) documentation.

You must execute all the following command in your Ubuntu 22.04 wsl terminal.

## Set locale
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

## Setup Sources
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

## Install ROS 2 packages
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

## Try some examples
If you installed `ros-humble-desktop` above you can try some examples.

In one terminal, source the setup file and then run a C++ `talker`:

```bash
source /opt/ros/humble/setup.bash
```

```bash
ros2 run demo_nodes_cpp talker
```

Open another Ubuntu 22.04 wsl terminal and run

```bash
source /opt/ros/humble/setup.bash
```

```bash
ros2 run demo_nodes_py listener
```

You should see the `talker` saying that it’s `Publishing` messages and the `listener` saying `I heard` those messages. This verifies both the C++ and Python APIs are working properly.

You can now close both terminals

# Install autoware in ubuntu 22.04 wsl
The following steps are taken from this [reference](https://autowarefoundation.github.io/autoware-documentation/main/installation/autoware/source-installation/) documentation.

You must execute all the following command in your Ubuntu 22.04 wsl terminal.

## How to set up a development environment
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

## How to set up a workspace
### Create the `src` directory and clone repositories into it.
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

### Install dependent ROS packages.
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

### Install and set up ccache to speed up consecutive builds. (optional but highly recommended)
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

# Install bridge in ubuntu 22.04 wsl
The following steps are taken from this [reference](https://autowarefoundation.github.io/autoware_universe/main/simulator/autoware_carla_interface/) documentation.

### Install CARLA Python Package
Install CARLA 0.9.15 ROS 2 Humble communication package

Download [carla-0.9.15-cp310-cp310-linux_x86_64.whl](https://github.com/gezp/carla_ros/releases/tag/carla-0.9.15-ubuntu-22.04) in you windows desktop.

Open your Ubuntu 22.04 terminal and move the file in your home directory

```bash
cp -p /mnt/c/Users/Utente/Desktop/carla-0.9.15-cp310-cp310-linux_x86_64.whl ~
```

Install the wheel with pip
```bash
pip install carla-0.9.15-cp310-cp310-linux_x86_64.whl
```

Remove the wheel

Install the wheel with pip
```bash
rm -rf carla-0.9.15-cp310-cp310-linux_x86_64.whl
```

### Download CARLA Lanelet2 Maps
Download `point_cloud/Town01.pcd` and `vector_maps/lanelet2/Town01.osm` y-axis inverted maps from [CARLA Autoware Contents](https://bitbucket.org/carla-simulator/autoware-contents/src/master/maps/) in your Windows os.

Rename `point_cloud/Town01.pcd` → `pointcloud_map.pcd`

Rename `vector_maps/lanelet2/Town01.osm` → `lanelet2_map.osm`

Create a `map_projector_info.yaml` file with:

```yaml
projector_type: Local
```

Open your wsl Ubuntu 22.04 terminal and create the map folder 

```bash
mkdir -p ~/autoware/autoware_map/Town01/
```

Move the files to this new location

```bash
cp -p /mnt/c/Users/Utente/Desktop/pointcloud_map.pcd ~/autoware/autoware_map/Town01/
```

```bash
cp -p /mnt/c/Users/Utente/Desktop/lanelet2_map.osm ~/autoware/autoware_map/Town01/
```

```bash
cp -p /mnt/c/Users/Utente/Desktop/map_projector_info.yaml ~/autoware/autoware_map/Town01/
```

## Build
To build autoware bridge run the following commands

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

**This will be reverted once the computer restarts. So it must be called every time.

### ROS_LOCALHOST_ONLY

It is crucial to ensure export ROS_LOCALHOST_ONLY=1 is removed when setting up your WSL2-to-Windows connection. If that variable is active, ROS 2 will refuse to send or receive data outside of its own virtual machine, meaning it will never see the CARLA server on Windows.

Open your WSL2 terminal and run this command to search your `.bashrc` file:

```bash
grep ROS_LOCALHOST_ONLY ~/.bashrc
```

If it prints nothing you are good to go! The line is not in your file. Skip to Step 3 just to be safe.

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

**This must be done everytime before launching autoware**

Validate the sysctl settings

```bash
sysctl net.core.rmem_max net.ipv4.ipfrag_time net.ipv4.ipfrag_high_thresh
```

### CycloneDDS Configuration

Save the following file as `cyclonedds.xml`

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd">
  <Domain Id="any">
    <General>
      <Interfaces>
        <NetworkInterface autodetermine="false" name="lo" priority="default" multicast="default" />
      </Interfaces>
      <AllowMulticast>default</AllowMulticast>
      <MaxMessageSize>65500B</MaxMessageSize>
    </General>
    <Discovery>
      <ParticipantIndex>none</ParticipantIndex>
    </Discovery>
    <Internal>
      <SocketReceiveBufferSize min="10MB"/>
      <Watermarks>
        <WhcHigh>500kB</WhcHigh>
      </Watermarks>
    </Internal>
  </Domain>
</CycloneDDS>
```

Move it inside wsl

```bash
cp -r /mnt/c/Users/Utente/Desktop/cyclonedds.xml ~
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

## Run

1. In windows go to you carla directory

```cmd
cd C:\Users\Utente\Documents\CARLA_0.9.15\WindowsNoEditor
```

2. Run carla, change map, spawn object if you need

```cmd
./CarlaUE4.exe -prefernvidia -quality-level=Low -RenderOffScreen
```

**If you omit `-RenderOffScreen` you can see carla window popping up**

3. Open a wsl terminal, set up the environment

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

## Replaying Scenarios (Simulator vs. Brain)

Because these systems are separate, you cannot replay both at the same time. Replaying a scenario requires choosing whether you want to watch the physical car in the simulator, or the AI's logic in RViz.

### The "Ghost Conflict" (Why they must be separate)

If you play a ROS 2 bag while Autoware is actively connected to a live CARLA simulation, you create a massive data collision.

* The live CARLA simulator tells Autoware: **"I am at coordinates X, Y, and my speed is 0."**

* Your ROS 2 bag tells Autoware at the exact same time: **"No, I am at coordinates A, B, and my speed is 30!"**

Autoware's localization module will panic due to the conflicting realities, trigger the emergency safety systems, and lock the brakes.

### Scenario A: Watch the 3D Simulator (CARLA)

If you want to watch the physics, traffic, and vehicle movement exactly as it happened in the 3D world:

1. Keep the CARLA server running.

2. In a Windows Command Prompt, run:

```cmd
python carla_tools.py replay --recording your_snapshot.log
```

3. CARLA will automatically reset the world, teleport the car to the starting line, and replay the physics. Autoware does not need to be running for this.

### Scenario B: Watch the AI's Logic (Autoware)

If you want to see the trajectory planning, bounding boxes, and sensor data the AI was processing in RViz:

1. Go to your main Autoware terminal and press `Ctrl+C` to cleanly shut down the live simulation (this will close RViz).

2. Start Autoware back up, but swap `e2e_simulator.launch.xml` for `logging_simulator.launch.xml`:

```bash
ros2 launch autoware_launch logging_simulator.launch.xml map_path:=$HOME/autoware/autoware_map/Town01 vehicle_model:=sample_vehicle sensor_model:=carla_sensor_kit
```

3. RViz will immediately pop back open with your map loaded.

3. In a new WSL2 terminal, run:

```bash
python3 autoware_tools.py replay --bag your_bag_folder
```

**Crucial Note: The `autoware_tools.py` replay script automatically injects the `--clock` flag to force Autoware to accept historical timestamps.**

## CLI Tools Reference

Below is the complete reference for the standalone Python tools, including all available commands and their optional parameters.

### CARLA Unified Tools (`carla_tools.py`)
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

#### replay

Replays a saved `.log` file inside the simulator.

```cmd
python carla_tools.py replay --recording <file.log> [options]
```

* `--recording`: **(Required)** The exact name of the `.log` file to replay.

* `--start`: (Optional) Recording time in seconds to start the simulation at. If positive, time is considered from the beginning of the recording. If negative, it is considered from the end. (Default: `0.0`).

* `--duration`: (Optional) Seconds to playback. `0` plays the entire recording. By the end of the playback, vehicles will be set to autopilot and pedestrians will stop. (Default: `0.0`).

* `--camera`: (Optional) ID of the actor that the camera will focus on. Set it to `0` to let the spectator move freely. (Default: `0`).

* `--time_factor`: (Optional) Playback speed multiplier. For example, `2.0` is double speed. (Default: `1.0`).

#### info

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

#### record

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

#### replay

Replays an existing ROS 2 bag back into the ROS network. (The tool automatically injects the `--clock` flag so Autoware accepts the historical data).

```bash
python3 autoware_tools.py replay --bag <bag_folder_name> [options]
```

* `--bag`: **(Required)** The exact name of the bag folder you want to replay.

* `--rate`: (Optional) Playback speed multiplier. For example, `2.0` plays the bag at 2x speed. (Default: `1.0`).

#### info

Extracts the ROS 2 bag metadata (total duration, message counts, topic list) and saves it as a `.txt` file.

```bash
python3 autoware_tools.py info --bag <bag_folder_name>
```

* `--bag`: **(Required)** The exact name of the bag folder to parse.