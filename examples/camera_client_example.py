import base64
import numpy as np

from babyros import node


class Camera:
    """
    Camera class for capturing images from a camera device.
    """
    def __init__(self):
        self.camera_client = node.Client("camera/capture")

    def capture(self):
        """
        Captures an image from the camera.
        """
        capture_result = self.camera_client.request()

        if capture_result:
            # 1. Decode from Base64 string to raw bytes
            raw_bytes = base64.b64decode(capture_result[0]["image"])
            
            # 2. Convert bytes back to a NumPy array
            # You must specify the dtype and then reshape to the original dimensions
            image = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((480, 640, 3))
            
            return image
        else:
            print("No response from camera server.")
            return None

if __name__ == "__main__":
    camera = Camera()
    image = camera.capture()

    if image is not None:
        print("Captured image shape: ", image.shape)
    else:
        print("Failed to capture image.")