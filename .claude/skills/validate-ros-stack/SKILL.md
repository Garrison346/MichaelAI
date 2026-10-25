---
name: validate-ros-stack
description: Build and validate the MichaelAI ROS 2 sim stack in WSL. Use after changes under ros2_ws/, before committing them, or to debug sim, SLAM, TF or Nav2 failures.
---

# Validate the MichaelAI ROS 2 stack

`ros2_ws/README.md` is the source of truth for commands. This skill adds what's
needed to run them from Claude Code on Windows and to interpret the results.

## Ground rules

- **The baseline test is the validation step.** It starts its own headless sim.
  Don't launch a GUI sim first, and don't relax its checks or change Nav2 config to get a pass.
- **Read the test before relying on it.** The ROS domain, `GZ_PARTITION`, timeouts and pass
  criteria live in `ros2_ws/src/rover_bringup/test/test_sim_baseline.launch.py` and may change.
- **Never kill processes you didn't start.** The user may have a sim open. Stop only your own
  process group.

## Running ROS from Claude Code

Claude's shell is Git Bash on Windows. ROS lives in WSL:

```bash
R=$(MSYS_NO_PATHCONV=1 wsl.exe wslpath -u "$(git rev-parse --show-toplevel)" | tr -d '\r')
MSYS_NO_PATHCONV=1 wsl.exe -e bash -c "source /opt/ros/jazzy/setup.bash && cd $R/ros2_ws && <cmd>"
```

- Without `MSYS_NO_PATHCONV=1`, Git Bash rewrites `/mnt/c/...` paths.
- Source `setup.bash` in every call, even for `gz`. Pipe output through `tr -d '\r'`.

## Steps

1. Build: `colcon build --symlink-install`, then `source install/setup.bash`.
2. Test: run the `launch_test` command from the README in the background, logging to a file.
3. Read the log, not just the exit code. Check `OK`/`FAILED`, the failing stage's message, and the
   `[baseline]` lines. An example passing run (values vary): 2/8 headings traversable, goal (0, 1),
   known cells about 1170 → 3500, about 35 s. Everything after `OK` is teardown, not a failure:
   `controller_server IS DOWN`, the container's `exit code -11` (composition crash, see the README's
   troubleshooting), and `Ran 0 tests` / `NO TESTS RAN` (empty after-shutdown phase).

## Debugging a failure

Start a separate headless sim on an unused domain and partition (`setsid ros2 launch ... &`), wait
for `/lifecycle_manager_navigation/is_active`, then probe it:
- `ros2 topic info -v` for QoS
- `tf2_echo` for TF
- a small rclpy script in the scratchpad for grid contents

Afterwards stop it with `kill -INT -<pgid>`. Known traps:
- The first `/global_costmap/costmap` message is an all-unknown placeholder.
- `/map` is reliable + transient_local and only republished about every 5 s. Volatile subscribers
  (e.g. plain `map_saver_cli`) time out.
- `pgrep -f` and `grep` match their own command line. List processes with
  `ps -eo stat,pid,args | grep "[g]z sim"`. State `T` means suspended by Ctrl+Z, not running.
- `kill -0 <pid>` succeeds on an unreaped zombie. To check for survivors, list the group:
  `ps -o stat,pid,args -g <pgid>`.
- A check that returns "0 found" needs a positive control first, to show it can find something.

## Report

List the commands run, the build result, the test outcome with the `[baseline]` values, and any
failure with evidence. Say which steps weren't run.
