"""Phase 1 reference simulation: Nav2's TurtleBot3 sim with SLAM.

Wraps nav2_bringup's tb3_simulation_launch.py (Gazebo + RViz + Nav2) so the
working sim launches from this repo:

    ros2 launch rover_bringup sim.launch.py
    ros2 launch rover_bringup sim.launch.py headless:=True use_rviz:=False  # no GUI

Phase 2 replaces the TurtleBot with MichaelAI's own rover
(rover_description + rover_sim).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    nav2_sim = PathJoinSubstitution([
        FindPackageShare("nav2_bringup"),
        "launch",
        "tb3_simulation_launch.py",
    ])

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_sim),
        launch_arguments={
            "slam": "True",  # build the map live with SLAM Toolbox (no prebuilt map)
            "headless": LaunchConfiguration("headless"),
            "use_rviz": LaunchConfiguration("use_rviz"),
        }.items(),
    )

    return LaunchDescription([
        # Defaults are for interactive use. Jazzy's tb3 launch itself defaults
        # to headless=True, so we override it to show Gazebo.
        DeclareLaunchArgument("headless", default_value="False",
                              description="Hide the Gazebo GUI (server only)"),
        DeclareLaunchArgument("use_rviz", default_value="True",
                              description="Start RViz2"),
        simulation,
    ])
