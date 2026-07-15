from src.config import settings
from src.models import ANIMAL_EXPRESSIONS, EXPRESSION_NAMES, ROBOT_MODE_NAMES
from src.resource import LazyResource
from src.utility.friendship import load_friendliness

from multiprocessing import Value, Event, Array

import RPi.GPIO as GPIO



GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# mpu = MPU()
com = LazyResource("src.com.com", "COM")
cam = LazyResource("src.cam.cam", "Cam")
fuz = LazyResource("src.fuzzy.fuzzy", "Fuzzy")
lcd = LazyResource("src.lcd.lcd", "LCD")
rgb = LazyResource("src.rgb.rgb", "RGB")
mqtt = LazyResource("src.mqtt.mqtt_localhost", "MQTT")
opi = LazyResource("src.openapi.openapi", "Openapi")
mic = LazyResource("src.mic.mic", "Mic")


def initialize_hardware() -> None:
    """Initialize core resources in a deliberate order before workers start."""
    for resource in (com, cam, fuz, lcd, rgb, mqtt):
        resource.get()

express = Value('i', 0)
state   = Value('i', 0)
error   = Value('f', 0.0)
width   = Value('f', 0.0)
battery = Value('i', 100)

# Sensors
# ax, ay, az, aN, aE, aD, roll, pitch, yaw = [Value('f', 1.0) for _ in range(9)]

# Friendly
contents = load_friendliness(settings.paths.friendliness)

friendly = Value('f', contents)

# Robots
radius  = 0.085                             # m
length  = 0.17                              # m
w_m_max = 13.0                              # rad / s
v_max   = radius * w_m_max                  #  m / s
w_max   = 2 * radius * w_m_max / length     # rad / s

# Running
running = Event()
running.set()

acting = Event()
acting.clear()

look_around = Event()
look_around.clear()

# Battery
low_battery_count = Value('i', 0)

# Internet
internet = Event()
internet.clear()

# Error
err = Event()
err.clear()

# Microphone
voice = Array('B', 10 * 1024 * 1024) # 10 MB buffer
voice_len = Value('i', 0)
halucination = ["Thank you.", "You're going to.", "We're here.", "Thanks for watching!", " ", "You", "Thank you for watching!", "you", ""]

chatting = Event()
chatting.clear()

express_dictionary = list(EXPRESSION_NAMES)
"""Backward-compatible expression lookup; prefer ``Expression`` in new code."""

state_dictionary = list(ROBOT_MODE_NAMES)
"""Backward-compatible mode lookup; prefer ``RobotMode`` in new code."""

animal_dictionary = {name: int(expression) for name, expression in ANIMAL_EXPRESSIONS.items()}
