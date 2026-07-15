# EVE Robot

EVE is a Raspberry Pi companion robot with animated facial expressions, movable
ears and legs, differential-drive wheels, touch interaction, speech, camera
vision, and autonomous navigation. This repository contains the on-device
Python controller and its media assets.

The application is intended to run directly on Raspberry Pi OS. It is not
containerized because camera, GPIO, I2C, SPI, UART, and audio access are central
to the robot and are easier to operate and diagnose on the host.

## Features

- Animated face on an ILI9341 SPI display
- Ear, leg, and wheel control through an ESP controller over I2C
- Dual RGB status lights driven by GPIO PWM
- Camera capture with Picamera2
- Touch and external voice-command input over GPIO
- Speech recognition, conversation, speech synthesis, image understanding, and
  image generation through OpenAI
- MQTT exchange with an external tracking/depth/detection service
- Fuzzy-logic person following and obstacle avoidance
- Persistent friendliness score that changes EVE's reactions
- Graceful SIGINT/SIGTERM shutdown and a systemd service template

## Project Layout

```text
.
├── main.py                     Main application and worker lifecycle
├── gen.py                      Standalone camera/vision experiment
├── pyproject.toml              Package metadata and development tools
├── requirements.txt            Runtime Python dependencies
├── deploy/eve.service          Example systemd unit
├── tests/                       Hardware-independent unit tests
└── src/
    ├── config.py                Environment-based settings and paths
    ├── models.py                Robot modes and expression enums
    ├── resource.py              Lazy hardware/network resource wrapper
    ├── variables/variables.py   Shared multiprocessing state and resources
    ├── utility/
    │   ├── audio.py             Lazy audio playback
    │   ├── friendship.py        Friendliness persistence
    │   ├── images.py            Image composition
    │   ├── motion.py            Differential-drive calculations
    │   └── utils.py             Robot commands and high-level behaviors
    ├── cam/                     Picamera2 adapter
    ├── com/                     ESP motor/servo and battery communication
    ├── fuzzy/                   Fuzzy controllers and serialized models
    ├── lcd/                     Display driver and expression frames
    ├── mic/                     Microphone capture
    ├── mqtt/                    MQTT clients and payload codecs
    ├── mpu/                     MPU9250/AK8963 driver
    ├── openapi/                 OpenAI adapter and generated media
    ├── rgb/                     RGB light driver
    └── speaker/audio_package/   Prerecorded voice and sound assets
```

Hardware and network resources are created only when the application starts or
a feature first needs them. Importing configuration or pure utility modules no
longer opens devices or connects to external services.

## Hardware Assumptions

The current adapters expect the following default connections:

| Function | Interface or pins |
| --- | --- |
| ESP motor/servo controller | I2C bus 1, address `0x77` |
| Battery telemetry | `/dev/ttyS0`, 115200 baud |
| LCD | SPI CE1, DC GPIO 17, reset GPIO 23, backlight GPIO 24 |
| Left RGB | GPIO 16, 1, and 12 |
| Right RGB | GPIO 22, 4, and 27 |
| Head and chin touch | GPIO 6 and 5 |
| External command lines | GPIO 26, 13, and 25 |
| Camera | Raspberry Pi camera supported by libcamera/Picamera2 |

Review the pin assignments before powering motors or servos. Hardware defaults
that are likely to vary between installations can be overridden in `.env`.

## Raspberry Pi Setup

Use a current 64-bit Raspberry Pi OS installation with Python 3.10 or newer.
Enable I2C, SPI, serial, and camera support with `raspi-config`, then reboot.

Install system packages:

```bash
sudo apt update
sudo apt install -y \
  ffmpeg i2c-tools libportaudio2 portaudio19-dev \
  python3-dev python3-opencv python3-picamera2 python3-pyaudio \
  python3-rpi.gpio python3-smbus python3-venv
```

Create a virtual environment that can see Raspberry Pi OS packages, then install
EVE:

```bash
git clone <your-repository-url> EVE
cd EVE
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

`picamera2`, `RPi.GPIO`, `smbus`, and OpenCV are deliberately installed from
Raspberry Pi OS because they are tied to the platform and its native libraries.

## Configuration

Create a local environment file:

```bash
cp .env.example .env
chmod 600 .env
```

Important variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | Enables conversation, STT, TTS, vision, and drawing | unset |
| `EVE_HOME` | Repository/asset root | detected automatically |
| `EVE_MQTT_BROKER` | Tracking and vision MQTT broker | `aTinozg.local` |
| `EVE_MQTT_PORT` | MQTT port | `1883` |
| `EVE_MQTT_TOPIC_PREFIX` | Prefix for all EVE topics | `eve` |
| `EVE_MQTT_USERNAME` | Optional broker username | unset |
| `EVE_MQTT_PASSWORD` | Optional broker password | unset |
| `EVE_MQTT_TLS` | Enable MQTT TLS | `false` |
| `EVE_SERIAL_PORT` | Battery telemetry UART | `/dev/ttyS0` |
| `EVE_ESP_ADDRESS` | ESP I2C address, decimal or hexadecimal | `0x77` |
| `EVE_LOG_LEVEL` | Python logging level | `INFO` |

The application does not load `.env` by itself. For an interactive run, export
it into the shell:

```bash
set -a
source .env
set +a
```

The supplied systemd unit reads `.env` through `EnvironmentFile`.

## MQTT Contract

The default topic prefix is `eve`:

| Topic | Direction | Payload |
| --- | --- | --- |
| `eve/cam` | EVE publishes | Base64/JPEG bytes |
| `eve/state` | EVE publishes | Current detector request/state string |
| `eve/empty` | EVE publishes | Empty keepalive every 30 seconds |
| `eve/depth` | EVE subscribes | `left,front,right`, each initially 0-255 |
| `eve/track` | EVE subscribes | `horizontal_error,target_width` |
| `eve/detect` | EVE subscribes | JSON object of detection scores/results |
| `eve/check` | EVE subscribes | Vision-service health/status text |

The tracking, depth, and object-detection producer is a separate service and is
not included in this repository. The robot can stand idle without those values,
but follow, go-around, and mimic-detection modes require that service.

## Running EVE

With the virtual environment active and configuration exported:

```bash
eve-robot
```

The equivalent development command is:

```bash
python main.py
```

Stop with `Ctrl+C`. The shutdown path stops the wheels, saves friendliness,
joins workers, turns off the display and lights, stops the camera, disconnects
MQTT, and cleans up GPIO.

### Run at Boot with systemd

Adjust the username and paths in `deploy/eve.service` if EVE is not installed as
`/home/pi/EVE`, then run:

```bash
sudo cp deploy/eve.service /etc/systemd/system/eve.service
sudo systemctl daemon-reload
sudo systemctl enable --now eve.service
sudo systemctl status eve.service
```

Follow logs with:

```bash
journalctl -u eve.service -f
```

## Development and Tests

Pure motion, image, persistence, and MQTT payload code can be tested on a normal
Linux, macOS, or Windows development machine without Raspberry Pi hardware:

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

Do not import or execute `main.py` on a non-Raspberry Pi machine. It intentionally
loads GPIO-bound behavior code. Import modules such as `src.utility.motion`,
`src.utility.images`, and `src.mqtt.messages` for hardware-independent work.

## Media Assets

Expression directories follow a state-transition convention:

- `idle_to_<expression>` enters an expression.
- `<expression>` contains the looping or main animation.
- `<expression>_to_idle` returns to the neutral face.
- Numbered JPG files are displayed in numeric order and must remain contiguous.

The vision and drawing features modify the `show` and `paint` expression frames
at runtime. The service account therefore needs write access to the repository's
asset directories.

## Security

- Never commit `.env`, API keys, MQTT passwords, or private broker certificates.
- Runtime camera frames, microphone recordings, generated speech/images, and the
  local friendliness score are excluded through `.gitignore`.
- Revoke any credential that was previously committed to source control; deleting
  it from the latest commit does not remove it from Git history.
- Use a private MQTT broker or enable authenticated TLS outside a trusted LAN.
- Treat pickled fuzzy models as executable inputs and load them only from trusted
  repository versions.

## Known Limitations

- High-level behaviors remain timing-based and assume the current mechanical
  geometry and servo calibration.
- The MPU driver is available but disabled in the main runtime.
- Several actions mutate animation frames to show camera or generated images.
- The OpenAI integration requires internet access and a funded API account.
- Hardware integration tests must be performed on the assembled robot.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
