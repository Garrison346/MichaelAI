# MichaelAI ROS 2 workspace

ROS 2 Jazzy code for the rover. For now it holds a single package, `rover_bringup`,
which launches Nav2's **TurtleBot3 reference simulation** with SLAM. The custom rover
(Phase 2) and the C++ explorer (Phase 3) don't exist yet. The Python fire classifier
lives outside this workspace (`src/perception/`).

All commands below run in **WSL Ubuntu 24.04**, not Windows.

## 1. Setup (once)

Packages this workspace was developed against:

```bash
sudo apt install ros-jazzy-desktop ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-minimal-tb3-sim ros-jazzy-slam-toolbox ros-jazzy-ros-gz \
  ros-jazzy-teleop-twist-keyboard python3-colcon-common-extensions python3-rosdep
```

ROS dependencies are declared in `src/*/package.xml`, not in the root `requirements.txt`.
rosdep needs a one-time init before it can resolve them:

```bash
sudo rosdep init && rosdep update
cd ros2_ws && rosdep install --from-paths src --ignore-src -y
```

## 2. Build

Always build from `ros2_ws/`. Running colcon anywhere else creates stray `build/ install/ log/`.

```bash
source /opt/ros/jazzy/setup.bash
cd /mnt/c/Users/Eason/Downloads/MichaelAI/ros2_ws    # adjust to your checkout
colcon build --symlink-install --packages-select rover_bringup
source install/setup.bash                            # in every new terminal
```

## 3. Run the simulation

```bash
ros2 launch rover_bringup sim.launch.py                               # Gazebo + RViz
ros2 launch rover_bringup sim.launch.py headless:=True use_rviz:=False  # no GUI
```

`sim.launch.py` always enables SLAM. `--show-args` also lists the included Nav2 file's
`slam` default (`False`), but the wrapper overrides it.

## 4. Baseline test (opt-in)

`test/test_sim_baseline.launch.py` starts the sim headless and checks, in order:
- `/clock` advances, and `/scan` and `/odom` carry valid data
- `/map` has free and occupied cells and is republished
- TF `map→odom→base_link` resolves
- every Nav2 node and SLAM's `map_saver` is active
- a `NavigateToPose` goal 1 m away **succeeds and moves the robot**
- the map gains known cells after the move

The goal isn't hard-coded. It's chosen from the robot's pose and the global costmap.

It isn't registered with CMake, so `colcon test` never starts Gazebo. Run it explicitly
(about 35 s):

```bash
launch_test src/rover_bringup/test/test_sim_baseline.launch.py
```

The test sets its own `ROS_DOMAIN_ID=87` and `GZ_PARTITION=michaelai_test`, so a sim running
in another terminal neither sees it nor affects it (verified). Lines prefixed `[baseline]` show the
chosen goal, the final pose and the map growth. Shutdown noise after `OK` (for example
`controller_server IS DOWN`) is the stack tearing down, not a failure.

## 5. Manual checks

```bash
ros2 topic hz /scan                                   # ~5 Hz
ros2 topic hz /map                                    # one map every ~5 s
ros2 run tf2_ros tf2_echo map base_link
```

**Saving the map.** Use the `map_saver` that's already running (writes `~/map.pgm` + `~/map.yaml`):

```bash
ros2 service call /map_saver/save_map nav2_msgs/srv/SaveMap "{map_topic: map, map_url: $HOME/map}"
```

Plain `map_saver_cli -f ~/map` fails with "Failed to spin map subscription": `/map` is latched and
only republished every ~5 s, but the CLI subscribes as volatile and gives up after about 2 s. To use the CLI,
add `--ros-args -p map_subscribe_transient_local:=true`.

**Driving.** `teleop_twist_keyboard` publishes straight to `/cmd_vel`, bypassing Nav2's
smoother and collision monitor:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**`/cmd_vel_teleop` does nothing on its own. This is by design.** Its only subscriber is Nav2's
`AssistedTeleop` behavior, which forwards commands (through the collision checks) only while an
`/assisted_teleop` goal is active:

```bash
ros2 action send_goal /assisted_teleop nav2_msgs/action/AssistedTeleop "{time_allowance: {sec: 20}}"
# meanwhile, in another terminal:
ros2 topic pub -r 10 /cmd_vel_teleop geometry_msgs/msg/Twist "{linear: {x: 0.1}}"
```

The goal then ends `ABORTED` with `error_code: 731`, which is `TIMEOUT`: the time allowance
ran out, as expected.

## 6. Reference: what the stack provides

Observed in this sim with `ros2 topic info -v`, `ros2 action list -t` and the installed `nav2_params.yaml`.

| Interface | Type | Notes |
|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | 5 Hz, 360 rays, 20 m max; reliable/volatile |
| `/odom` | `nav_msgs/Odometry` | reliable/volatile |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM Toolbox, 0.05 m cells, every ~5 s; **reliable + transient_local** |
| `/global_costmap/costmap` | `nav_msgs/OccupancyGrid` | 0 free, 99 inscribed, 100 lethal, -1 unknown; transient_local. Its first message is an all-unknown placeholder |
| TF `map→odom→base_link` | | `map` origin = robot start pose |
| `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | for the future explorer: send goals, read feedback |
| `/cmd_vel` | `geometry_msgs/Twist` (unstamped) | final command to Gazebo |

Velocity chain (from `nav2_bringup/launch/navigation_launch.py`): controller/behaviors → `cmd_vel_nav`
→ velocity_smoother → `cmd_vel_smoothed` → collision_monitor → `/cmd_vel` → ros_gz_bridge.

**Not verified yet:** loading a saved map back (localization mode), long or multi-goal
navigation, and behavior in worlds other than `tb3_sandbox`.

## Troubleshooting

- **Sim from a previous run is still alive** (stale topics, Gazebo slow to start):
  `pkill -f "gz sim"; pkill -f component_container`.
- **Slow builds**: the repo lives on the Windows drive (`/mnt/c`), and file access there is slow
  from WSL. It works; a clone inside the WSL filesystem (e.g. `~/projects`) is faster.
- **`rosdep install` fails with "sources list not found"**: run `sudo rosdep init && rosdep update`.
