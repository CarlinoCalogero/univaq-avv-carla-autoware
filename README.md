# Prerequisites (The Setup)
Before touching the code, ensure you have the following installed on your Windows machine:
1. **WSL2 (Ubuntu)**: Install this via PowerShell (`wsl --install -d Ubuntu-22.04`).
2. **Docker Desktop**: Install and ensure the WSL2 integration is enabled in its settings.

# Step 1: Launch the CARLA Simulation Environment
You need CARLA running in server mode so Autoware can talk to it.
1. Open your Windows command prompt or PowerShell.
2. Navigate to your CARLA installation folder.
3. Launch CARLA. It's best to force it to use a low-quality rendering mode if your GPU is going to be strained by running Autoware simultaneously:
```bash
CarlaUE4.exe -quality-level=Low -carla-rpc-port=2000 -dx11 -windowed -ResX=800 -ResY=600
```

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
ros2 launch carla_ros_bridge carla_ros_bridge.launch.py host:=192.168.1.12 timeout:=10
```
At this point, CARLA sensor topics are officially bridged to ROS2.

# Step 3: Deploy Autoware.Universe via Docker
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
# Step 4: Map Sensors and Control (The Integration Code)
This is the core of "Injecting Autoware into CARLA". You need to map CARLA's outgoing sensor data to Autoware's inputs, and send Autoware's control outputs back to the CARLA vehicle.

In ROS2, we do this using a `launch` file with topic remapping.