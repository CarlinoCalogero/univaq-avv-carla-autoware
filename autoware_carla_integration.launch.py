from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Map CARLA Sensor Data -> AUTOWARE Inputs 
        Node(
            package='topic_tools',
            executable='relay',
            name='lidar_relay',
            arguments=[
                '/carla/ego_vehicle/lidar',               # CARLA output
                '/sensing/lidar/top/pointcloud_raw'       # Autoware input
            ]
        ),
        Node(
            package='topic_tools',
            executable='relay',
            name='camera_relay',
            arguments=[
                '/carla/ego_vehicle/rgb_front/image',     # CARLA output
                '/sensing/camera/traffic_light/image_raw' # Autoware input
            ]
        ),
        
        # 2. Send AUTOWARE Control Outputs -> CARLA Vehicle 
        # Note: Autoware outputs standard Ackermann control, CARLA needs VehicleControl. 
        # The carla_ackermann_control node handles this translation.
        Node(
            package='carla_ackermann_control',
            executable='carla_ackermann_control_node',
            name='carla_ackermann_control',
            parameters=[
                {'role_name': 'ego_vehicle'},
            ],
            remappings=[
                # Map Autoware's output to the bridge's input
                ('/carla/ego_vehicle/ackermann_cmd', '/control/command/control_cmd')
            ]
        )
    ])