import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Define variables so the template can be reused for Agent 1, Agent 2, etc.
    vehicle_name = LaunchConfiguration('vehicle_name')
    
    declare_vehicle_name = DeclareLaunchArgument(
        'vehicle_name',
        default_value='ego_vehicle',
        description='The role_name of the vehicle in CARLA (e.g., ego_vehicle_1)'
    )

    # 2. Automated Autoware ADAS Logging (Rosbag)
    # This automatically records key perception and control topics.
    record_adas = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record', 
            '-o', ['/workspace/log_', vehicle_name], # Saves as /workspace/log_ego_vehicle
            '/sensing/lidar/top/pointcloud_raw',
            '/sensing/camera/traffic_light/image_raw',
            '/control/command/control_cmd'
        ],
        output='screen'
    )

    # 3. Dynamic Node Mapping
    lidar_relay = Node(
        package='topic_tools',
        executable='relay',
        name=['lidar_relay_', vehicle_name],
        arguments=[
            ['/carla/', vehicle_name, '/lidar'],               
            '/sensing/lidar/top/pointcloud_raw'       
        ]
    )

    camera_relay = Node(
        package='topic_tools',
        executable='relay',
        name=['camera_relay_', vehicle_name],
        arguments=[
            ['/carla/', vehicle_name, '/rgb_front/image'],     
            '/sensing/camera/traffic_light/image_raw' 
        ]
    )
    
    ackermann_control = Node(
        package='carla_ackermann_control',
        executable='carla_ackermann_control_node',
        name=['carla_ackermann_control_', vehicle_name],
        parameters=[
            {'role_name': vehicle_name},
        ],
        remappings=[
            (['/carla/', vehicle_name, '/ackermann_cmd'], '/control/command/control_cmd')
        ]
    )

    return LaunchDescription([
        declare_vehicle_name,
        record_adas,
        lidar_relay,
        camera_relay,
        ackermann_control
    ])