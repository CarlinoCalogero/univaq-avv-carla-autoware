from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import AnyLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    autoware_pkg = get_package_share_directory('autoware_launch')
    
    return LaunchDescription([
        DeclareLaunchArgument('map_path', description='Path to the map'),
        DeclareLaunchArgument('vehicle_model', description='Vehicle model'),
        DeclareLaunchArgument('sensor_model', description='Sensor model'),
        DeclareLaunchArgument('vehicle_name', default_value='ego_vehicle'),

        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(
                os.path.join(autoware_pkg, 'launch', 'autoware.launch.xml')
            ),
            launch_arguments={
                'map_path': LaunchConfiguration('map_path'),
                'vehicle_model': LaunchConfiguration('vehicle_model'),
                'sensor_model': LaunchConfiguration('sensor_model'),
                'vehicle_name': LaunchConfiguration('vehicle_name'),
                
                'launch_vehicle_interface': 'false',
                'launch_perception': 'false',
                
                # Topic Remappings
                '/vehicle/status/velocity': '/vehicle/status/velocity_status',
                '/vehicle/status/steering': '/vehicle/status/steering_status',
                '/control/command': '/control/command/control_cmd',
                
                # Fixed: Initialize from GNSS
                '/sensing/gnss/pose_with_covariance': '/sensing/gnss/pose',
                '/sensing/imu/imu_data': '/sensing/imu/imu_raw',
                '/localization/kinematic_state': '/localization/kinematic_state',
            }.items()
        )
    ])