@echo off
echo [SYNC] Initiating parallel data collection...

:: 1. Launch WSL, source ROS 2, go to the folder, and run the Python script.
:: (Changed "exec bash" to "sleep 2" so the window auto-closes after saving)
start "Autoware Recorder" wsl.exe -d Ubuntu-22.04 -e bash -c "source /opt/ros/humble/setup.bash && cd ~/autoware && python3 autoware_tools.py record; sleep 2"

:: 2. Wait 2 seconds for ROS 2 to boot up in the new window
timeout /t 2 /nobreak >nul

:: 3. Start the CARLA recording script natively in this main window
python carla_tools.py record

:: Once you press Ctrl+C, Python will safely stop the recording and this window will close.