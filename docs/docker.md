# Docker Usage

To use GPU with docker while on AMD64 systems, install [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) with given instructions.

## Supported platforms

| System | ROS Version | Value for `image` | Value for `device`  | Size    | file  |
| :---   | :---        | :---              |  :---               | :---:   | :---: |
| AMD64       | Humble      | ghcr.io/kalanaratnayake/yolo-ros:humble         | `cpu`, `0`, `0,1,2` | 5.64 GB | docker/compose.amd64.yaml |
| Jetson Nano | Humble      | ghcr.io/kalanaratnayake/yolo-ros:humble-j-nano  | `cpu`, `0`          | 3.29GB  | docker/compose.jnano.yaml |

## Docker Usage with this repository

Clone this reposiotory

```bash
mkdir -p yolo_ws/src && cd yolo_ws/src
git clone https://github.com/KalanaRatnayake/yolo_ros.git && cd ..
```

### AMD64

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

### Jetson Nano

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
