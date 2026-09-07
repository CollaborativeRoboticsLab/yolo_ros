#---------------------------------------------------------------------------------------------------------------------------
#----
#----   Start base image
#----
#---------------------------------------------------------------------------------------------------------------------------

FROM ros:humble-ros-base-jammy as base

## Parameters
ENV WORKSPACE_ROOT=/yolo

#############################################################################################################################
#####
#####   Install Dependencies
#####
#############################################################################################################################

WORKDIR /

RUN apt-get update -y

RUN apt-get install -y --no-install-recommends  python3-pip \
                                                libboost-python-dev \
                                                ros-dev-tools \
                                                ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
                                                ros-$ROS_DISTRO-vision-opencv

RUN pip3 install --upgrade --no-cache-dir torch==1.13.0+cu117 \
                                          torchvision==0.14.0+cu117 \
                                          torchaudio==0.13.0 \
                                          --extra-index-url https://download.pytorch.org/whl/cu117

RUN apt-get clean

#############################################################################################################################
#####
#####   Clone and build Yolo packages
#####
#############################################################################################################################

WORKDIR ${WORKSPACE_ROOT}/src

RUN git clone https://github.com/KalanaRatnayake/yolo_ros.git

RUN pip3 install --no-cache-dir -r ${WORKSPACE_ROOT}/src/yolo_ros/requirements.txt

RUN rosdep install --from-paths ${WORKSPACE_ROOT}/src -y --ignore-src

WORKDIR ${WORKSPACE_ROOT}

RUN . /opt/ros/humble/setup.sh && colcon build

WORKDIR /

#############################################################################################################################
#####
#####   Remove workspace source and build files that are not relevent to running the system
#####
#############################################################################################################################

RUN rm -rf ${WORKSPACE_ROOT}/src
RUN rm -rf ${WORKSPACE_ROOT}/log
RUN rm -rf ${WORKSPACE_ROOT}/build

RUN rm -rf /var/lib/apt/lists/*
RUN rm -rf /tmp/*

RUN apt-get clean

#---------------------------------------------------------------------------------------------------------------------------
#----
#----   Start final release image
#----
#---------------------------------------------------------------------------------------------------------------------------


FROM ros:humble-ros-base-jammy as final

## Parameters

ENV WORKSPACE_ROOT=/yolo

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

WORKDIR /

COPY --from=base / /

COPY docker/workspace_entrypoint.sh /workspace_entrypoint.sh

RUN chmod +x /workspace_entrypoint.sh

ENTRYPOINT [ "/workspace_entrypoint.sh" ]

WORKDIR ${WORKSPACE_ROOT}

CMD ros2 run yolo_ros yolo_ros --ros-args -p "yolo_model:=$YOLO_MODEL" \
                                            -p "input_rgb_topic:=$INPUT_RGB_TOPIC" \
                                            -p "input_depth_topic:=$INPUT_DEPTH_TOPIC" \
                                            -p "subscribe_depth:=$SUBSCRIBE_DEPTH" \
                                            -p "publish_annotated_image:=$PUBLISH_ANNOTATED_IMAGE" \
                                            -p "publish_synchronized:=$PUBLISH_SYNCHRONIZED" \
                                            -p "rgb_topic:=$RGB_TOPIC" \
                                            -p "depth_topic:=$DEPTH_TOPIC" \
                                            -p "annotated_topic:=$ANNOTATED_TOPIC" \
                                            -p "detailed_topic:=$DETAILED_TOPIC" \
                                            -p "threshold:=$THRESHOLD" \
                                            -p "device:=$DEVICE"