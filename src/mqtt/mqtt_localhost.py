import paho.mqtt.client as mqtt

from multiprocessing import Process, Event
from src.config import settings
from src.mqtt.messages import DepthReading, TrackReading, decode_detection


class MQTT():
    def __init__(self):
        config = settings.mqtt
        self.broker = config.broker
        self.port = config.port
        prefix = config.topic_prefix.rstrip("/")
        self.camera_topic = f"{prefix}/cam"
        self.empty_topic = f"{prefix}/empty"
        self.depth_topic = f"{prefix}/depth"
        self.track_topic = f"{prefix}/track"
        self.state_topic = f"{prefix}/state"
        self.detect_topic = f"{prefix}/detect"
        self.check_topic = f"{prefix}/check"

        self.client_publish = mqtt.Client()
        self.client_publish.on_connect = self.on_connect_publish
        self._configure_client(self.client_publish)
        self.client_publish.connect(self.broker, self.port)
        self.client_publish.loop_start()

        self.maintain_stop = Event()
        self.maintain_process = Process(target = self.maintain)
        self.maintain_process.start()

        self.client_depth = mqtt.Client()
        self.client_depth.on_connect = self.on_connect_depth
        self.client_depth.on_message = self.on_message_depth
        self._configure_client(self.client_depth)
        self.client_depth.connect(self.broker, self.port)
        self.client_depth.loop_start()

        self.client_track = mqtt.Client()
        self.client_track.on_connect = self.on_connect_track
        self.client_track.on_message = self.on_message_track
        self._configure_client(self.client_track)
        self.client_track.connect(self.broker, self.port)
        self.client_track.loop_start()

        self.client_detect = mqtt.Client()
        self.client_detect.on_connect = self.on_connect_detect
        self.client_detect.on_message = self.on_message_detect
        self._configure_client(self.client_detect)
        self.client_detect.connect(self.broker, self.port)
        self.client_detect.loop_start()

        self.client_status = mqtt.Client()
        self.client_status.on_connect = self.on_connect_status
        self.client_status.on_message = self.on_message_status
        self._configure_client(self.client_status)
        self.client_status.connect(self.broker, self.port)
        self.client_status.loop_start()

        self.depth = [-1.0, -1.0, -1.0]

        self.track = [-999, -999]

        self.detect = {}

        self.status = ""

    @staticmethod
    def _configure_client(client):
        config = settings.mqtt
        if config.username:
            client.username_pw_set(config.username, config.password)
        if config.use_tls:
            client.tls_set()

    def on_connect_depth(self, client, userdata, flags, rc):
        print(f"Connected to depth topic with result code {rc}")
        self.client_depth.subscribe(self.depth_topic, qos = 0)

    def on_message_depth(self, client, userdata, msg):
        self.depth = DepthReading.from_payload(msg.payload).as_list()

    def on_connect_track(self, client, userdata, flags, rc):
        print(f"Connected to track topic with result code {rc}")
        self.client_track.subscribe(self.track_topic, qos = 0)

    def on_connect_status(self, client, userdata, flags, rc):
        print(f"Connected to status topic with result code {rc}")
        self.client_status.subscribe(self.check_topic, qos = 0)

    def on_message_status(self, client, userdata, msg):
        data = msg.payload
        self.status = data.decode()

    def on_message_track(self, client, userdata, msg):
        self.track = TrackReading.from_payload(msg.payload).as_list()

    def on_connect_detect(self, client, userdata, flags, rc):
        print(f"Connected to detect topic with result code {rc}")
        self.client_detect.subscribe(self.detect_topic, qos = 0)

    def on_message_detect(self, client, userdata, msg):
        self.detect = decode_detection(msg.payload)

    def on_connect_publish(self, client_publish, userdata, flags, rc):
        print(f"Connected to publish node with result code {rc}")

    def upload_image(self, encoded_image):
        self.client_publish.publish(self.camera_topic, encoded_image, retain = False, qos = 0)

    def upload_state(self, data):
        self.client_publish.publish(self.state_topic, data, retain = False, qos = 0)

    def maintain(self):
        while not self.maintain_stop.is_set():
            self.client_publish.publish(self.empty_topic, "", retain = False, qos = 0)
            self.maintain_stop.wait(30)
        print("Stop")

    def disconnect(self):
        self.maintain_stop.set()
        self.maintain_process.join(timeout=5)
        self.client_publish.loop_stop()
        self.client_publish.disconnect()
        for client in (self.client_depth, self.client_track, self.client_detect, self.client_status):
            client.loop_stop()
            client.disconnect()
        print("Disconnected successfully!")
