open carla double click

(.venv) PS C:\Users\Utente\Desktop\carlo> python windows\spawn_vehicle.py --map Town01

(.venv) PS C:\Users\Utente\Desktop\carlo> python .\windows\follow_camera.py


user@docker-desktop:/workspace$ ros2 launch ./carla_bridge.launch.py vehicle_name:=ego_vehicle map_path:=/workspace/autoware_map/Town01 vehicle_model:=sample_vehicle sensor_model:=carla_sensor_kit

user@docker-desktop:/workspace$ python3 bridge_node.py --ros-args -p carla_host:="host.docker.internal"