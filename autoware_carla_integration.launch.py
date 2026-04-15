from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # ------------------------------------------------------------------ #
    # Launch arguments
    # ------------------------------------------------------------------ #
    vehicle_name  = LaunchConfiguration('vehicle_name')
    map_path      = LaunchConfiguration('map_path')
    vehicle_model = LaunchConfiguration('vehicle_model')
    sensor_model  = LaunchConfiguration('sensor_model')
    launch_autoware = LaunchConfiguration('launch_autoware')

    declare_vehicle_name = DeclareLaunchArgument(
        'vehicle_name',
        default_value='ego_vehicle',
        description='Role name of the ego vehicle in CARLA'
    )
    declare_map_path = DeclareLaunchArgument(
        'map_path',
        default_value='/workspace/Town01_map',
        description='Absolute path to the map folder (must contain pointcloud_map.pcd and lanelet2_map.osm)'
    )
    declare_vehicle_model = DeclareLaunchArgument(
        'vehicle_model',
        default_value='sample_vehicle',
        description='Autoware vehicle model package name'
    )
    declare_sensor_model = DeclareLaunchArgument(
        'sensor_model',
        default_value='carla_sensor_kit',
        description='Autoware sensor model package name'
    )
    declare_launch_autoware = DeclareLaunchArgument(
        'launch_autoware',
        default_value='true',
        description='Set to false to skip launching the full Autoware stack (useful for debugging relay nodes only)'
    )

    # ------------------------------------------------------------------ #
    # Sensor relay nodes
    # Forward CARLA sensor topics into Autoware's expected namespaces.
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # Ackermann type converter
    #
    # Replaces the old carla_ackermann_control_node with a broken remapping.
    # This converter subscribes to Autoware's control output topic
    # (autoware_auto_control_msgs/AckermannControlCommand) and republishes
    # it as ackermann_msgs/AckermannDrive so the CARLA ROS bridge can
    # execute the command. Eliminates the "multiple types" rosbag error.
    # ------------------------------------------------------------------ #
    ackermann_converter = ExecuteProcess(
        cmd=['python3', '/workspace/ackermann_converter.py', vehicle_name],
        output='screen'
    )

    # ------------------------------------------------------------------ #
    # Automated ADAS logging (rosbag)
    # Records sensor inputs and control commands for post-run analysis.
    # ------------------------------------------------------------------ #
    record_adas = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '-o', ['/workspace/log_', vehicle_name],
            '/sensing/lidar/top/pointcloud_raw',
            '/sensing/camera/traffic_light/image_raw',
            '/sensing/gnss/ublox/nav_sat_fix',
            '/sensing/imu/tamagawa/imu_raw',
            '/control/command/control_cmd',
        ],
        output='screen'
    )

    # ------------------------------------------------------------------ #
    # Full Autoware stack
    #
    # Uses e2e_simulator.launch.xml which is designed for simulation
    # environments (CARLA, AWSIM). It sets up the simulation clock,
    # RViz, and sim-specific parameters — unlike autoware.launch.xml
    # which is the real-vehicle launcher and does not open RViz.
    # Set launch_autoware:=false to skip (e.g. for bridge-only debugging).
    # ------------------------------------------------------------------ #
    autoware_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('autoware_launch'),
                'launch',
                'e2e_simulator.launch.xml'
            ])
        ),
        launch_arguments={
            'map_path':                                  map_path,
            'vehicle_model':                             vehicle_model,
            'vehicle_launch_pkg':                        'sample_vehicle_launch',
            'sensor_model':                              sensor_model,
            'sensor_launch_pkg':                         'carla_sensor_kit_launch',
            'map_projection_loader.map_projector_type':  'local',
        }.items(),
        condition=IfCondition(launch_autoware)
    )

    return LaunchDescription([
        declare_vehicle_name,
        declare_map_path,
        declare_vehicle_model,
        declare_sensor_model,
        declare_launch_autoware,
        lidar_relay,
        camera_relay,
        gnss_relay,
        imu_relay,
        ackermann_converter,
        record_adas,
        autoware_launch,
    ])
