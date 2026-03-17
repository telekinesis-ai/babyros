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

        # Initialize 'last_call' if it doesn't exist yet
        if not hasattr(process_image, "last_call"):
            process_image.last_call = time.time()
            print("First frame received. Starting timer...")
            return

        # Calculate delta
        current_time = time.time()
        elapsed = current_time - process_image.last_call
    
        # Update for next time
        process_image.last_call = current_time

        print(f"Received image: {image.shape} | Delta Time: {elapsed:.4f}s | {1/elapsed:.1f} FPS")

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
        node.SessionManager.delete()
        print("Cleanup complete. Goodbye!")