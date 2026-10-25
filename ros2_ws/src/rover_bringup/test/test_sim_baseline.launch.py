"""Opt-in baseline test for the TB3 reference sim (sim.launch.py, headless).

Checks, in order: sensors publish real data, SLAM publishes a map, TF is
connected, Nav2 is active, a NavigateToPose goal succeeds and moves the robot,
and the map gains known cells. Not registered with CMake, so `colcon test`
never starts Gazebo. Run explicitly (about 1-2 min):

    source install/setup.bash
    launch_test src/rover_bringup/test/test_sim_baseline.launch.py
"""

import math
import os
import time
import unittest

# Isolate from any other running sim *before* launch or rclpy read the
# environment: child processes inherit these, and rclpy.init() reads the domain.
os.environ["ROS_DOMAIN_ID"] = "87"
os.environ["GZ_PARTITION"] = "michaelai_test"
os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"

import launch_testing.actions
import rclpy
from action_msgs.msg import GoalStatus
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.action import ActionClient
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformListener

# Measured cold start in WSL: /clock at ~4 s, Nav2 active at ~8 s. Generous margin.
STAGE_TIMEOUT = 60.0
NAV_TIMEOUT = 120.0  # a 1 m goal normally takes well under 30 s
GOAL_DISTANCE = 1.0  # m from the robot's current pose
GOAL_TOLERANCE = 0.3  # m; Nav2's xy_goal_tolerance is 0.25 (nav2_params.yaml)
MIN_TRAVEL = 0.7  # m the robot must actually move

# /map and /global_costmap/costmap are latched (reliable + transient_local).
LATCHED = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                     durability=DurabilityPolicy.TRANSIENT_LOCAL)
SENSOR = 10  # /scan, /odom, /clock publishers are reliable + volatile: default QoS matches
LETHAL = 99  # costmap OccupancyGrid: 99 inscribed, 100 lethal, -1 unknown, 0 free


def generate_test_description():
    sim = PathJoinSubstitution([FindPackageShare("rover_bringup"), "launch", "sim.launch.py"])
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(sim),
            launch_arguments={"headless": "True", "use_rviz": "False"}.items(),
        ),
        launch_testing.actions.ReadyToTest(),
    ])


def stamp_ns(msg):
    return Time.from_msg(msg.header.stamp).nanoseconds


def known_cells(grid):
    return sum(1 for v in grid.data if v != -1)


def cost_at(grid, x, y):
    """Cell value at map-frame (x, y), or None if outside the grid."""
    info = grid.info
    i = math.floor((x - info.origin.position.x) / info.resolution)
    j = math.floor((y - info.origin.position.y) / info.resolution)
    if 0 <= i < info.width and 0 <= j < info.height:
        return grid.data[j * info.width + i]
    return None


class TestSimBaseline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node(
            "sim_baseline_test", parameter_overrides=[Parameter("use_sim_time", value=True)])
        cls.tf_buffer = Buffer()
        cls.tf_listener = TransformListener(cls.tf_buffer, cls.node)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    # --- helpers -----------------------------------------------------------

    def spin_until(self, done, timeout, what):
        end = time.monotonic() + timeout
        while not done():
            self.assertLess(time.monotonic(), end, f"timed out after {timeout:.0f}s: {what}")
            rclpy.spin_once(self.node, timeout_sec=0.1)

    def wait_for_msg(self, msg_type, topic, qos, accept=lambda m: True, what="message"):
        got = []
        sub = self.node.create_subscription(
            msg_type, topic, lambda m: got.append(m) if not got and accept(m) else None, qos)
        try:
            self.spin_until(lambda: got, STAGE_TIMEOUT, f"{what} on {topic}")
        finally:
            self.node.destroy_subscription(sub)
        return got[0]

    def wait_future(self, future, timeout, what):
        self.spin_until(future.done, timeout, what)
        return future.result()

    def robot_pose(self):
        """(x, y, yaw) of base_link in the map frame."""
        t = self.tf_buffer.lookup_transform("map", "base_link", Time()).transform
        q = t.rotation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        return t.translation.x, t.translation.y, yaw

    def call_is_active(self, manager):
        client = self.node.create_client(Trigger, f"/{manager}/is_active")
        self.assertTrue(client.wait_for_service(timeout_sec=STAGE_TIMEOUT), f"{manager}/is_active missing")
        end = time.monotonic() + STAGE_TIMEOUT
        while True:  # the service exists before bringup finishes; poll until active
            resp = self.wait_future(client.call_async(Trigger.Request()), 10.0, f"{manager}/is_active")
            if resp.success:
                break
            self.assertLess(time.monotonic(), end, f"{manager} nodes never became active")
            time.sleep(1.0)
        self.node.destroy_client(client)

    def pick_goal(self, costmap, x, y, yaw):
        """Goal GOAL_DISTANCE away in one of 8 headings. Every cell on the straight
        line to it must be known and below LETHAL; of those, take the lowest-cost goal.
        Cost 0 is too strict: the robot spawns among obstacles and the 0.7 m inflation
        leaves almost no zero-cost cells nearby (measured: 198 in the whole grid)."""
        step = costmap.info.resolution / 2
        n = int(GOAL_DISTANCE / step)
        candidates = []
        for k in range(8):
            a = yaw + k * math.pi / 4
            line = [cost_at(costmap, x + s * step * math.cos(a), y + s * step * math.sin(a))
                    for s in range(n + 1)]
            if all(c is not None and 0 <= c < LETHAL for c in line):
                candidates.append((line[-1], x + GOAL_DISTANCE * math.cos(a),
                                   y + GOAL_DISTANCE * math.sin(a)))
        if not candidates:
            self.fail(f"no traversable goal {GOAL_DISTANCE} m from ({x:.2f}, {y:.2f}) in 8 headings")
        cost, gx, gy = min(candidates)
        print(f"[baseline] {len(candidates)}/8 headings traversable, goal cost {cost}")
        return gx, gy

    # --- the test ----------------------------------------------------------

    def test_baseline(self):
        # 1. Sensors: sim time advances; scan, odom contain real values.
        c1 = self.wait_for_msg(Clock, "/clock", SENSOR, what="clock")
        t1 = Time.from_msg(c1.clock).nanoseconds
        self.wait_for_msg(Clock, "/clock", SENSOR,
                          accept=lambda m: Time.from_msg(m.clock).nanoseconds > t1,
                          what="advancing clock")

        def valid_scan(m):
            ok = [r for r in m.ranges if math.isfinite(r) and m.range_min <= r <= m.range_max]
            return len(m.ranges) > 0 and len(ok) >= 0.5 * len(m.ranges)
        self.wait_for_msg(LaserScan, "/scan", SENSOR, accept=valid_scan,
                          what="scan with >=50% valid ranges")

        def valid_odom(m):
            p, q = m.pose.pose.position, m.pose.pose.orientation
            norm = math.sqrt(q.x ** 2 + q.y ** 2 + q.z ** 2 + q.w ** 2)
            return all(math.isfinite(v) for v in (p.x, p.y, p.z)) and abs(norm - 1) < 1e-3
        self.wait_for_msg(Odometry, "/odom", SENSOR, accept=valid_odom, what="finite odom")

        # 2. Map published: correct resolution, has free and occupied cells, republished.
        def valid_map(m):
            return (abs(m.info.resolution - 0.05) < 1e-6 and m.info.width > 0 and m.info.height > 0
                    and 0 in m.data and any(v >= 65 for v in m.data))
        map1 = self.wait_for_msg(OccupancyGrid, "/map", LATCHED, accept=valid_map,
                                 what="map with free and occupied cells")
        map2 = self.wait_for_msg(OccupancyGrid, "/map", LATCHED,
                                 accept=lambda m: stamp_ns(m) > stamp_ns(map1),
                                 what="republished map")
        known_before = known_cells(map2)

        # 3. TF: SLAM provides map->odom, the sim provides odom->base_link.
        for parent, child in (("map", "odom"), ("odom", "base_link")):
            self.spin_until(lambda: self.tf_buffer.can_transform(parent, child, Time()),
                            STAGE_TIMEOUT, f"TF {parent}->{child}")

        # 4. Lifecycle: every Nav2 node and SLAM's map_saver are active.
        self.call_is_active("lifecycle_manager_navigation")
        self.call_is_active("lifecycle_manager_slam")
        nav = ActionClient(self.node, NavigateToPose, "navigate_to_pose")
        self.assertTrue(nav.wait_for_server(timeout_sec=STAGE_TIMEOUT), "navigate_to_pose server missing")

        # 5. Goal: derived from the current pose and the global costmap.
        # The first latched costmap is a 100x100 all-unknown placeholder published
        # before the static layer has a map (observed), so wait for real data.
        costmap = self.wait_for_msg(OccupancyGrid, "/global_costmap/costmap", LATCHED,
                                    accept=lambda m: any(v != -1 for v in m.data),
                                    what="populated costmap")
        x0, y0, yaw0 = self.robot_pose()
        gx, gy = self.pick_goal(costmap, x0, y0, yaw0)
        print(f"[baseline] start ({x0:.2f}, {y0:.2f}) goal ({gx:.2f}, {gy:.2f})")

        # 6. Navigate: must SUCCEED and actually move the robot.
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        goal.pose.pose.position.x, goal.pose.pose.position.y = gx, gy
        goal.pose.pose.orientation.w = 1.0
        handle = self.wait_future(nav.send_goal_async(goal), STAGE_TIMEOUT, "goal response")
        self.assertTrue(handle.accepted, "navigate_to_pose rejected the goal")
        try:
            result = self.wait_future(handle.get_result_async(), NAV_TIMEOUT, "navigation result")
        except AssertionError:
            handle.cancel_goal_async()
            raise
        self.assertEqual(result.status, GoalStatus.STATUS_SUCCEEDED,
                         f"navigation ended with status {result.status}, "
                         f"error {result.result.error_code} {result.result.error_msg!r}")
        done_ns = self.node.get_clock().now().nanoseconds
        x1, y1, _ = self.robot_pose()
        print(f"[baseline] reached ({x1:.2f}, {y1:.2f})")
        self.assertLessEqual(math.hypot(x1 - gx, y1 - gy), GOAL_TOLERANCE, "robot not at goal")
        self.assertGreaterEqual(math.hypot(x1 - x0, y1 - y0), MIN_TRAVEL, "robot did not move")

        # 7. Map expansion (separate from publication): a map produced after the
        # move must know strictly more cells than the one before it.
        map3 = self.wait_for_msg(OccupancyGrid, "/map", LATCHED,
                                 accept=lambda m: stamp_ns(m) > done_ns, what="post-move map")
        known_after = known_cells(map3)
        print(f"[baseline] known cells {known_before} -> {known_after}")
        self.assertGreater(known_after, known_before, "map did not gain known cells after moving")

        nav.destroy()
