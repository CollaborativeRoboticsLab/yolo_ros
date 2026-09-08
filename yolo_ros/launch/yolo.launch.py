import os

import ament_index_python.packages
import launch
import launch_ros.actions
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration

import yaml


def generate_launch_description():
    share_dir = ament_index_python.packages.get_package_share_directory('yolo_ros')

    params_file = os.path.join(share_dir, 'config', 'yolo_ros_params.yaml')
    rviz_config_file = os.path.join(share_dir, 'config', 'yolo.rviz')
    use_rviz = LaunchConfiguration('use_rviz')

    with open(params_file, 'r') as f:
        params = yaml.safe_load(f)['yolo_ros_node']['ros__parameters']

    yolo_ros_node = launch_ros.actions.Node(package='yolo_ros',
                                            executable='yolo_ros',
                                            output='both',
                                            parameters=[params]
                                            )

    rviz_node = launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', rviz_config_file],
        condition=IfCondition(use_rviz),
    )

    ld = LaunchDescription()

    ld.add_action(
        DeclareLaunchArgument(
            'use_rviz',
            default_value='false',
            description='Launch RViz with the YOLO image view config.',
        )
    )
    ld.add_action(yolo_ros_node)
    ld.add_action(rviz_node)

    return ld