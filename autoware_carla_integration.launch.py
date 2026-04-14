from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Define variables so the template can be reused for Agent 1, Agent 2, etc.
    vehicle_name = LaunchConfiguration('vehicle_name')

    declare_vehicle_name = DeclareLaunchArgument(
        'vehicle_name',
        default_value='ego_vehicle',
        description='The role_name of the vehicle in CARLA (e.g., ego_vehicle_2)'
    )

    # Automated Autoware ADAS Logging (Rosbag)
    # Records all sensor inputs and control outputs for post-run analysis.
    record_adas = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '-o', ['/workspace/log_', vehicle_name],
            '/sensing/lidar/top/pointcloud_raw',
            '/sensing/camera/traffic_light/image_raw',
            '/sensing/gnss/ublox/nav_sat_fix',
            '/sensing/imu/tamagawa/imu_raw',
            '/control/command/control_cmd'
        ],
        output='screen'
    )

    # --- Sensor Relay Nodes ---
    # Each relay forwards a CARLA sensor topic into Autoware's expected namespace.

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

    gnss_relay = Node(
        package='topic_tools',
        executable='relay',
        name=['gnss_relay_', vehicle_name],
        arguments=[
            ['/carla/', vehicle_name, '/gnss'],
            '/sensing/gnss/ublox/nav_sat_fix'
        ]
    )

    imu_relay = Node(
        package='topic_tools',
        executable='relay',
        name=['imu_relay_', vehicle_name],
        arguments=[
            ['/carla/', vehicle_name, '/imu'],
            '/sensing/imu/tamagawa/imu_raw'
        ]
    )

    # --- Ackermann Control Node ---
    # Receives Autoware's control commands and forwards them to CARLA.
    # NOTE: carla_ackermann_control_node internally subscribes to
    # /carla/{role_name}/ackermann_cmd. The remapping below redirects that
    # subscription to Autoware's /control/command/control_cmd so the node
    # receives Autoware's output directly.
    # If you see a "type mismatch" warning at runtime, your ros-bridge version
    # may expect AckermannDrive instead of AckermannControlCommand — check the
    # ros-bridge changelog for your cloned commit.
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
        gnss_relay,
        imu_relay,
        ackermann_control
    ])
