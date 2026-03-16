import numpy as np
from babyros import node

import time


class Camera:
    """
    A dummy camera class for capturing images.
    """
    def __init__(self):
        print("Dummy camera class initialized!")
        self.capture_server = node.Server("camera/capture", self.handle_capture)

    def capture(self):
        """
        Capture an image from the camera.
        """
        return self.capture_client.request()

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


if __name__ == "__main__":
    camera = Camera()

    print("Camera Server is running... Press Ctrl+C to stop.")    

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        camera.delete()


    if capture_result:
        # 1. Decode from Base64 string to raw bytes
        raw_bytes = base64.b64decode(capture_result[0]["image"])
        
        # 2. Convert bytes back to a NumPy array
        # You must specify the dtype and then reshape to the original dimensions
        image = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((480, 640, 3))
        
        print("Received image shape: ", image.shape)
        print("Camera started successfully!")
    else:
        print("No response from camera server.")

    camera.delete()