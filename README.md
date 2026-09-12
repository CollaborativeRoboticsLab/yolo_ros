# yolo_ros

A ROS2 wrapper for YOLO object detection based on [Ultralytics](https://github.com/ultralytics/ultralytics) YOLO models.  For docker based usage, refer to the [Docker Usage](docs/docker.md) guide.

## Setup

Clone this repository with the following command and install dependencies.

```bash
git clone https://github.com/KalanaRatnayake/yolo_ros.git
cd yolo_ros
pip3 install -r requirements.txt
```

## Build the package

If required, edit the parameters at `config/yolo_ros_params.yaml' and then at the workspace root run,
```bash
colcon build
```
## Start the system

To start the camera, run,

```bash
source ./install/setup.bash
ros2 launch yolo_realsense d415.launch.py
```

To use the launch file, run,

```bash
source ./install/setup.bash
ros2 launch yolo_ros yolo.launch.py
```


## Parameter description

| ROS Parameter           | Docker ENV parameter    | Default Value               | Description |
| :---                    | :---                    | :---:                       | :---        |
| yolo_model              | YOLO_MODEL              | `yolov9t.pt`                | Model to be used. see [1] for default models and [2] for custom models |
| subscribe_depth         | SUBSCRIBE_DEPTH         | `True`                      | Whether to subscribe to depth image or not. Use if having a depth camera. An ApproximateTimeSynchronizer is used to sync RGB and depth images |
| input_rgb_topic         | INPUT_RGB_TOPIC         | `/camera/color/image_raw`   | Topic to subscribe for RGB image. Accepts `sensor_msgs/Image` |
| input_depth_topic       | INPUT_DEPTH_TOPIC       | `/camera/depth/image_rect_raw` | Topic to subscribe for depth image. Accepts `sensor_msgs/Image` |
| publish_annotated_image | PUBLISH_ANNOTATED_IMAGE | `False`                     | Whether to publish annotated image, increases callback execution time when set to `True` |
| publish_detection_topic | PUBLISH_DETECTION_TOPIC | `True`                      | Whether to publish `yolo_ros_msgs/Detections` messages on the detailed detection topic |
| publish_synchronized    | PUBLISH_SYNCHRONIZED    | `True`                      | Whether to republish the synchronized RGB image on `rgb_topic` and, when depth is enabled, the synchronized depth image on `depth_topic` |
| rgb_topic               | RGB_TOPIC               | `/yolo_ros/rgb_image`       | Topic for publishing synchronized rgb images. uses `sensor_msgs/Image` |
| depth_topic             | DEPTH_TOPIC             | `/yolo_ros/depth_image`     | Topic for publishing synchronized depth images. uses `sensor_msgs/Image` |
| annotated_topic         | ANNOTATED_TOPIC         | `/yolo_ros/annotated_image` | Topic for publishing annotated images uses `sensor_msgs/Image` |
| detailed_topic          | DETAILED_TOPIC          | `/yolo_ros/detection_result`| Topic for publishing detailed results uses `yolo_ros_msgs/Detections` |
| threshold               | THRESHOLD               | `0.25`                      | Confidence threshold for predictions |
| device                  | DEVICE                  | `'0'`                       | `cpu` for CPU, `0` for gpu, `0,1,2,3` if there are multiple GPUs |

## Service interface

The node also exposes a thin cached 2D detection service:

- Service name: `/yolo_ros/get_latest_detections`
- Service type: `yolo_ros_msgs/srv/GetLatestDetections`

Example:

```bash
ros2 service call /yolo_ros/get_latest_detections yolo_ros_msgs/srv/GetLatestDetections "{}"
```

The response returns the latest cached header, image width and height, full class list, detection ids, class ids, class names, confidences, and 2D bounding boxes.

[1] If the model is available at [ultralytics models](https://docs.ultralytics.com/models/), It will be downloaded from the cloud at the startup. We are using docker volumes to maintain downloaded weights so that weights are not downloaded at each startup.

[2] Uncomment the commented out `YOLO_MODEL` parameter line and give the custom model weight file's name as `YOLO_MODEL` parameter. Uncomment the docker bind entry that to direct to the `weights` folder and comment the docker volume entry for yolo. Copy the custom weights to the `weights` folder.
