"""Application configuration and repository paths.

All runtime-specific values are read from environment variables here so the
rest of the codebase does not depend on a particular Raspberry Pi username or
installation directory.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(os.getenv("EVE_HOME", Path(__file__).resolve().parent.parent)).resolve()
SRC_ROOT = PROJECT_ROOT / "src"


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Paths:
    root: Path = PROJECT_ROOT
    source: Path = SRC_ROOT
    expressions: Path = SRC_ROOT / "lcd" / "face_expression"
    sounds: Path = SRC_ROOT / "speaker" / "audio_package"
    fuzzy_models: Path = SRC_ROOT / "fuzzy"
    openai_data: Path = SRC_ROOT / "openapi"
    drawing_results: Path = SRC_ROOT / "openapi" / "draw_result"
    friendliness: Path = SRC_ROOT / "friendly.txt"
    latest_camera_image: Path = SRC_ROOT / "what_is_this.jpg"


@dataclass(frozen=True)
class MQTTConfig:
    broker: str = field(default_factory=lambda: os.getenv("EVE_MQTT_BROKER", "aTinozg.local"))
    port: int = field(default_factory=lambda: _env_int("EVE_MQTT_PORT", 1883))
    username: str | None = field(default_factory=lambda: os.getenv("EVE_MQTT_USERNAME"))
    password: str | None = field(default_factory=lambda: os.getenv("EVE_MQTT_PASSWORD"))
    use_tls: bool = field(default_factory=lambda: os.getenv("EVE_MQTT_TLS", "false").lower() == "true")
    topic_prefix: str = field(default_factory=lambda: os.getenv("EVE_MQTT_TOPIC_PREFIX", "eve"))


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    chat_model: str = field(default_factory=lambda: os.getenv("EVE_OPENAI_CHAT_MODEL", "gpt-4o"))
    vision_model: str = field(default_factory=lambda: os.getenv("EVE_OPENAI_VISION_MODEL", "gpt-4o"))
    transcription_model: str = field(default_factory=lambda: os.getenv("EVE_OPENAI_TRANSCRIPTION_MODEL", "whisper-1"))
    speech_model: str = field(default_factory=lambda: os.getenv("EVE_OPENAI_SPEECH_MODEL", "tts-1"))
    image_model: str = field(default_factory=lambda: os.getenv("EVE_OPENAI_IMAGE_MODEL", "dall-e-2"))


@dataclass(frozen=True)
class HardwareConfig:
    i2c_bus: int = field(default_factory=lambda: _env_int("EVE_I2C_BUS", 1))
    esp_address: int = field(default_factory=lambda: int(os.getenv("EVE_ESP_ADDRESS", "0x77"), 0))
    serial_port: str = field(default_factory=lambda: os.getenv("EVE_SERIAL_PORT", "/dev/ttyS0"))
    serial_baudrate: int = field(default_factory=lambda: _env_int("EVE_SERIAL_BAUDRATE", 115200))
    camera_size: int = field(default_factory=lambda: _env_int("EVE_CAMERA_SIZE", 640))


@dataclass(frozen=True)
class Settings:
    paths: Paths = field(default_factory=Paths)
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    log_level: str = field(default_factory=lambda: os.getenv("EVE_LOG_LEVEL", "INFO"))


settings = Settings()
