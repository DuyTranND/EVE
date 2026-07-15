import pytest

from src.mqtt.messages import DepthReading, TrackReading, decode_detection


def test_depth_payload_is_normalized():
    reading = DepthReading.from_payload(b"255,127.5,0")
    assert reading.as_list() == [1.0, 0.5, 0.0]


def test_track_payload():
    assert TrackReading.from_payload(b"-12.5,80").as_list() == [-12.5, 80.0]


def test_invalid_payload_length():
    with pytest.raises(ValueError):
        DepthReading.from_payload(b"1,2")


def test_detection_must_be_an_object():
    with pytest.raises(ValueError):
        decode_detection(b"[]")
