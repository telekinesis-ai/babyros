"""
Camera server for handling image capture requests.
"""
import numpy as np
from babyros import node


if __name__ == "__main__":
    image_publisher = node.ImagePublisher(topic="camera/capture")
    image = np.zeros((5112, 3840, 3), dtype=np.uint8)

    print("Publishing... Press Ctrl+C to stop.")
    
    try:
        while True:
            image_publisher.publish(image)
            # Add a small sleep to avoid pinning your CPU to 100%
            # time.sleep(0.03) # ~30 FPS
            
    except KeyboardInterrupt:
        print("\nStopping publisher...")
        
    finally:
        # This ensures cleanup happens even if the code crashes
        image_publisher.delete()
        print("Cleanup complete.")
