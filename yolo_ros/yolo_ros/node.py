import rclpy
import time

from message_filters import Subscriber
from message_filters import ApproximateTimeSynchronizer

from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

from sensor_msgs.msg import Image
from yolo_ros_msgs.msg import Detections
from yolo_ros_msgs.srv import GetLatestDetections

from cv_bridge import CvBridge

from ultralytics import YOLO

class YoloROS(Node):

    def __init__(self):
        super().__init__('yolo_ros')

        self.declare_parameter("yolo_model",                "yolov8n.pt")
        self.declare_parameter("input_rgb_topic",           "/camera/color/image_raw")
        self.declare_parameter("input_depth_topic",         "/camera/depth/image_rect_raw")
        self.declare_parameter("subscribe_depth",           False)
        self.declare_parameter("publish_annotated_image",   False)
        self.declare_parameter("publish_detection_topic",   True)
        self.declare_parameter("publish_synchronized",      True)
        self.declare_parameter("rgb_topic",                 "/yolo_ros/rgb_image")
        self.declare_parameter("depth_topic",               "/yolo_ros/depth_image")
        self.declare_parameter("annotated_topic",           "/yolo_ros/annotated_image")
        self.declare_parameter("detailed_topic",            "/yolo_ros/detection_result")
        self.declare_parameter("threshold",                 0.25)
        self.declare_parameter("device",                    "cpu")

        self.yolo_model                 = self.get_parameter("yolo_model").get_parameter_value().string_value
        self.input_rgb_topic            = self.get_parameter("input_rgb_topic").get_parameter_value().string_value
        self.input_depth_topic          = self.get_parameter("input_depth_topic").get_parameter_value().string_value
        self.subscribe_depth            = self.get_parameter("subscribe_depth").get_parameter_value().bool_value
        self.publish_annotated_image    = self.get_parameter("publish_annotated_image").get_parameter_value().bool_value
        self.publish_detection_topic    = self.get_parameter("publish_detection_topic").get_parameter_value().bool_value
        self.publish_synchronized       = self.get_parameter("publish_synchronized").get_parameter_value().bool_value
        self.rgb_topic                  = self.get_parameter("rgb_topic").get_parameter_value().string_value
        self.depth_topic                = self.get_parameter("depth_topic").get_parameter_value().string_value
        self.annotated_topic            = self.get_parameter("annotated_topic").get_parameter_value().string_value
        self.detailed_topic             = self.get_parameter("detailed_topic").get_parameter_value().string_value
        self.threshold                  = self.get_parameter("threshold").get_parameter_value().double_value
        self.device                     = self.get_parameter("device").get_parameter_value().string_value

        self.bridge = CvBridge()

        self.model = YOLO(self.yolo_model)
        self.model.fuse()

        self.subscriber_qos_profile = QoSProfile(reliability=QoSReliabilityPolicy.BEST_EFFORT,
                                                 history=QoSHistoryPolicy.KEEP_LAST,
                                                 depth=1)

        if self.subscribe_depth:
            self.rgb_message_filter     = Subscriber(self, Image, self.input_rgb_topic, qos_profile=self.subscriber_qos_profile)
            self.depth_message_filter   = Subscriber(self, Image, self.input_depth_topic, qos_profile=self.subscriber_qos_profile)

            self.synchornizer = ApproximateTimeSynchronizer([self.rgb_message_filter, self.depth_message_filter], 10, 1)
            self.synchornizer.registerCallback(self.sync_callback)

        else:
            self.subscription = self.create_subscription(Image, self.input_rgb_topic, self.image_callback, qos_profile=self.subscriber_qos_profile)

        self.publisher_results  = None
        if self.publish_detection_topic:
            self.publisher_results = self.create_publisher(Detections, self.detailed_topic, 10)

        self.publisher_rgb = None
        if self.publish_synchronized:
            self.publisher_rgb = self.create_publisher(Image, self.rgb_topic, 10)

        self.publisher_depth = None
        if self.subscribe_depth and self.publish_synchronized:
            self.publisher_depth = self.create_publisher(Image, self.depth_topic, 10)

        self.latest_detection_ids = []
        self.latest_class_names = []
        self.latest_confidence = []
        self.latest_bbx_center_x = []
        self.latest_bbx_center_y = []
        self.latest_bbx_size_w = []
        self.latest_bbx_size_h = []
        self.latest_image_width = 0
        self.latest_image_height = 0

        self.latest_detections_service = self.create_service(
            GetLatestDetections,
            '/yolo_ros/get_latest_detections',
            self.get_latest_detections_callback,
        )

        if self.publish_annotated_image:
            self.publisher_image    = self.create_publisher(Image, self.annotated_topic, 10)

        self.counter = 0
        self.time = 0

        self.detection_msg = Detections()
        self.class_list_set = False

    def get_latest_detections_callback(self, request, response):
        del request

        response.header = self.detection_msg.header
        response.image_width = int(self.latest_image_width)
        response.image_height = int(self.latest_image_height)
        response.full_class_list = list(self.detection_msg.full_class_list)
        response.detections = self.detection_msg.detections
        response.detection_ids = list(self.latest_detection_ids)
        response.class_id = list(self.detection_msg.class_id)
        response.class_name = list(self.latest_class_names)
        response.confidence = list(self.latest_confidence)
        response.bbx_center_x = list(self.latest_bbx_center_x)
        response.bbx_center_y = list(self.latest_bbx_center_y)
        response.bbx_size_w = list(self.latest_bbx_size_w)
        response.bbx_size_h = list(self.latest_bbx_size_h)
        response.success = True
        response.message = 'Returned latest cached detections.'
        return response

    def _publish_detection_results(self):
        if self.publisher_results is not None:
            self.publisher_results.publish(self.detection_msg)

    def _clear_latest_detection_cache(self):
        self.latest_detection_ids = []
        self.latest_class_names = []
        self.latest_confidence = []
        self.latest_bbx_center_x = []
        self.latest_bbx_center_y = []
        self.latest_bbx_size_w = []
        self.latest_bbx_size_h = []
        self.latest_image_width = 0
        self.latest_image_height = 0

    def _update_latest_detection_cache(self):
        self.latest_detection_ids = []
        self.latest_class_names = []
        self.latest_confidence = []
        self.latest_bbx_center_x = []
        self.latest_bbx_center_y = []
        self.latest_bbx_size_w = []
        self.latest_bbx_size_h = []
        self.latest_image_height = int(self.input_image.shape[0])
        self.latest_image_width = int(self.input_image.shape[1])

        for index, (bbox, cls, conf) in enumerate(
            zip(self.result[0].boxes.xywh, self.result[0].boxes.cls, self.result[0].boxes.conf)
        ):
            class_index = int(cls)
            class_name = self.result[0].names.get(class_index, str(class_index))

            self.latest_detection_ids.append(index)
            self.latest_class_names.append(class_name)
            self.latest_confidence.append(float(conf))
            self.latest_bbx_center_x.append(int(bbox[0]))
            self.latest_bbx_center_y.append(int(bbox[1]))
            self.latest_bbx_size_w.append(int(bbox[2]))
            self.latest_bbx_size_h.append(int(bbox[3]))

        self.detection_msg.class_id = list(int(cls) for cls in self.result[0].boxes.cls)
        self.detection_msg.confidence = list(self.latest_confidence)
        self.detection_msg.bbx_center_x = list(self.latest_bbx_center_x)
        self.detection_msg.bbx_center_y = list(self.latest_bbx_center_y)
        self.detection_msg.bbx_size_w = list(self.latest_bbx_size_w)
        self.detection_msg.bbx_size_h = list(self.latest_bbx_size_h)

    def sync_callback(self, rgb_msg, depth_msg):
        start = time.time_ns()

        self.input_image = self.bridge.imgmsg_to_cv2(rgb_msg, desired_encoding="bgr8")

        self.result = self.model.predict(source = self.input_image,
                                         conf=self.threshold,
                                         device=self.device,
                                         verbose=False)

        self.detection_msg.header       = rgb_msg.header

        if (not self.class_list_set) and (self.result is not None):
            for i in range(len(self.result[0].names)):
                self.detection_msg.full_class_list.append(self.result[0].names.get(i))
                self.class_list_set = True

        if self.result is not None:
            self.detection_msg.detections = True

            self._update_latest_detection_cache()

            self._publish_detection_results()
            if self.publisher_rgb is not None:
                self.publisher_rgb.publish(rgb_msg)
            if self.publisher_depth is not None:
                self.publisher_depth.publish(depth_msg)

            if self.publish_annotated_image:
                self.output_image = self.result[0].plot(conf=True, line_width=1, font_size=1, font="Arial.ttf", labels=True, boxes=True)
                result_msg        = self.bridge.cv2_to_imgmsg(self.output_image, encoding="bgr8")
                
                self.publisher_image.publish(result_msg)
        else:
            self.detection_msg.detections = False

            self.detection_msg.class_id = []
            self.detection_msg.confidence = []
            self.detection_msg.bbx_center_x = []
            self.detection_msg.bbx_center_y = []
            self.detection_msg.bbx_size_w = []
            self.detection_msg.bbx_size_h = []
            self._clear_latest_detection_cache()

            self._publish_detection_results()

        self.counter += 1
        self.time += time.time_ns() - start

        if (self.counter == 100):
            self.get_logger().info('RGB and Depth synchronized callback execution time for 100 loops: %d ms' % ((self.time/100)/1000000))
            self.time = 0
            self.counter = 0

    def image_callback(self, rgb_image):
        start = time.time_ns()

        self.input_image = self.bridge.imgmsg_to_cv2(rgb_image, desired_encoding="bgr8")

        self.result = self.model.predict(source = self.input_image,
                                         conf=self.threshold,
                                         device=self.device,
                                         verbose=False)

        self.detection_msg.header       = rgb_image.header

        if (not self.class_list_set) and (self.result is not None):
            for i in range(len(self.result[0].names)):
                self.detection_msg.full_class_list.append(self.result[0].names.get(i))
                self.class_list_set = True

        if self.result is not None:
            self.detection_msg.detections = True

            self._update_latest_detection_cache()

            self._publish_detection_results()
            if self.publisher_rgb is not None:
                self.publisher_rgb.publish(rgb_image)

            if self.publish_annotated_image:
                self.output_image = self.result[0].plot(conf=True, line_width=1, font_size=1, font="Arial.ttf", labels=True, boxes=True)
                result_msg        = self.bridge.cv2_to_imgmsg(self.output_image, encoding="bgr8")
                
                self.publisher_image.publish(result_msg)
        else:
            self.detection_msg.detections = False

            self.detection_msg.class_id = []
            self.detection_msg.confidence = []
            self.detection_msg.bbx_center_x = []
            self.detection_msg.bbx_center_y = []
            self.detection_msg.bbx_size_w = []
            self.detection_msg.bbx_size_h = []
            self._clear_latest_detection_cache()

            self._publish_detection_results()

        self.counter += 1
        self.time += time.time_ns() - start

        if (self.counter == 100):
            self.get_logger().info('RGB callback execution time for 100 loops: %d ms' % ((self.time/100)/1000000))
            self.time = 0
            self.counter = 0


def main(args=None):
    rclpy.init(args=args)

    node = YoloROS()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()