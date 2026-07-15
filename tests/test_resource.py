from pathlib import Path

from src.resource import LazyResource


def test_resource_is_initialized_on_first_use():
    resource = LazyResource("pathlib", "Path", ".")
    assert resource.initialized is False
    assert resource.get() == Path(".")
    assert resource.initialized is True
