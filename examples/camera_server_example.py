"""
Camera server for handling image capture requests.
"""
import numpy as np
import base64
import time
from babyros import node


class CameraServer:
    """
    A dummy camera class for capturing images.
    """
    def __init__(self):
        print("Dummy camera class initialized!")
        self.capture_server = node.Server("camera/capture", self.handle_capture)

    def handle_capture(self, request):
        """
        Handle a capture request.
        """
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        # 2. Convert bytes to a Base64 string for JSON compatibility
        encoded_image = base64.b64encode(image.tobytes()).decode('utf-8')
        response = {"image": encoded_image}
        return response

    def delete(self):
        """
        Delete the camera resources.
        """
        self.capture_server.delete()
        node.SessionManager.delete()


if __name__ == "__main__":
    camera_server = CameraServer()

    print("Camera Server is running... Press Ctrl+C to stop.")    

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        camera_server.delete()