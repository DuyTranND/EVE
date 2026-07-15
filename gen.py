from src.cam.cam import Cam
from src.openapi.openapi import Openapi


def main():
    """Capture one frame and print its OpenAI vision description."""
    camera = Cam()
    try:
        image = camera.get_image()
        encoded_image = camera.encode_image(image, quality=100)
        result = Openapi().image_to_text(encoded_image)
        print(result["choices"][0]["message"]["content"])
    finally:
        camera.stop_camera()


if __name__ == "__main__":
    main()
