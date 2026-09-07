# yolo_ros

## Docker Usage by adding to compose.yml file

To use GPU with docker while on AMD64 systems, install [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) with given instructions.

### Supported platforms

| System      | ROS Version | Value for `image`                               | Value for `device`  | Size    | file  |
| :---        | :---        | :---                                            |  :---               | :---:   | :---: |
| AMD64       | Humble      | ghcr.io/kalanaratnayake/yolo-ros:humble         | `cpu`, `0`, `0,1,2` | 5.64 GB | docker/compose.amd64.yaml |
| Jetson Nano | Humble      | ghcr.io/kalanaratnayake/yolo-ros:humble-j-nano  | `cpu`, `0`          | 3.29GB  | docker/compose.jnano.yaml |

## Docker Usage with this repository

Clone this reposiotory

```bash
mkdir -p yolo_ws/src && cd yolo_ws/src
git clone https://github.com/KalanaRatnayake/yolo_ros.git && cd ..
```

<details> 
<summary> <h3> on AMD64 </h3> </summary>

Pull the Docker image and start compose (No need to run `docker compose build`)
```bash
cd src/yolo_ros/docker
docker compose -f compose.amd64.yaml pull
docker compose -f compose.amd64.yaml up
```

To clean the system,
```bash
cd src/yolo_ros/docker
docker compose -f compose.amd64.yaml down
docker volume rm docker_yolo
```
</details>

<details> 
<summary> <h3> on JetsonNano </h3> </summary>

Pull the Docker image and start compose (No need to run `docker compose build`)
```bash
cd src/yolo_ros/docker
docker compose -f compose.jnano.yaml pull
docker compose -f compose.jnano.yaml up
```

To clean the system,
```bash
cd src/yolo_ros/docker
docker compose -f compose.jnano.yaml down
docker volume rm docker_yolo
```
</details>

<br>

## Native Usage

Clone this repository with and install dependencies.

```bash
git clone https://github.com/KalanaRatnayake/yolo_ros.git
cd yolo_ros
pip3 install -r requirements.txt
```

### Build the package

If required, edit the parameters at `config/yolo_ros_params.yaml' and then at the workspace root run,
```bash
colcon build
```
### Start the system

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

<br>
<br>

## Parameter decription

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

## Latency description

Here is a summary of whether latest models work with yolo_ros node (in docker) on various platforms and the time it takes to execute a single interation of `YoloROS.image_callback` function. Values are measured as an average of 100 executions of the function and Input is a 640x480 RGB image at 30 fps.

Laptop -> Ryzen 9 16 core with RTX3070 mobile GPU with Ubuntu 22.04
Jetson Nano -> Overclocked with [Qengineering Ubuntu 20.04 in Headless mode](https://github.com/Qengineering/Jetson-Nano-Ubuntu-20-image?tab=readme-ov-file#headless)

| Model | Laptop (amd64) | Jetson Nano |
| :---  |  ---: | ---: |
| `yolov10x.pt` | 27 ms |  975 ms |
| `yolov10l.pt` | 20 ms |  800 ms |
| `yolov10b.pt` | 17 ms |  750 ms |
| `yolov10m.pt` | 17 ms |  650 ms |
| `yolov10s.pt` | 14 ms |  210 ms |
| `yolov10n.pt` | 13 ms |  140 ms |
| `yolov9e.pt`  | 34 ms | 1600 ms |
| `yolov9c.pt`  | 21 ms |  700 ms |
| `yolov9m.pt`  | 20 ms |  500 ms |
| `yolov9s.pt`  | 25 ms |  300 ms |
| `yolov9t.pt`  | 24 ms |  180 ms |
| `yolov8x.pt`  | 28 ms | 2000 ms |
| `yolov8l.pt`  | 19 ms | 1200 ms |
| `yolov8m.pt`  | 16 ms |  700 ms |
| `yolov8s.pt`  | 12 ms |  300 ms |
| `yolov8n.pt`  | 12 ms |  140 ms |
