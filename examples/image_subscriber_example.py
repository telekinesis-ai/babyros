"""
Example of an image subscriber using BabyROS.
"""
import numpy as np
import time

from babyros import node


def process_image(image):
        """
        Process the received image.
        """
        # Process the image (e.g., display it, save it, etc.)
        print("Received image with shape:", image.shape)

if __name__ == "__main__":
    image_subscriber = node.ImageSubscriber(topic="camera/capture", callback=process_image)
    
    print("Subscriber active. Listening for 'camera/capture'...")
    print("Press Ctrl+C to exit.")

    try:
        # Keep the main thread alive while the Zenoh callback runs in the background
        while True:
            time.sleep(1) 
            
    except KeyboardInterrupt:
        print("\nShutting down subscriber...")
        
    finally:
        # Crucial: Close the Zenoh session/subscriber
        image_subscriber.delete()
        print("Cleanup complete. Goodbye!")