cmake_minimum_required(VERSION 3.8)
project(rover_bringup)

find_package(ament_cmake REQUIRED)

# Launch-only package: nothing to compile, just install launch files to
# share/rover_bringup so `ros2 launch rover_bringup ...` can find them.
# Add `config` here once the first config file exists (git can't track an
# empty directory, and install() fails if it's missing on a fresh clone).
install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
