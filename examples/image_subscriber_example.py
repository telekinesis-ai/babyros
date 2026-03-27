"""
Example of an image subscriber using BabyROS.
"""
import time
import babyros


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
    image_subscriber = babyros.node.Subscriber(topic="camera/capture", callback=process_image)
    print("Press Ctrl+C to exit.")

    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

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