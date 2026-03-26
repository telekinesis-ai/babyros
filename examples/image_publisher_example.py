"""
Camera server for handling image capture requests.
"""
import time
import numpy as np
from babyros import node

if __name__ == "__main__":
    image_publisher = node.Publisher(topic="camera/capture")
    image = np.zeros((5112, 3840, 3), dtype=np.uint8)

    print("Publishing... Press Ctrl+C to stop.")
    
    try:
        last_time = time.time()
        while True:
            time.sleep(0.4)
            image_publisher.publish(image)

            # 1. Capture the current moment
            current_time = time.time()
            
            # 2. Calculate the difference (Delta Time)
            elapsed = current_time - last_time
            
            # 3. Format nicely: .4f shows 4 decimal places (0.1ms precision)
            print(f"Delta Time: {elapsed:.4f}s | Est. {1/elapsed:.1f} FPS")
            
            # 4. Update last_time for the next iteration
            last_time = current_time

            # Add a small sleep to avoid pinning your CPU to 100%
            # time.sleep(0.03) # ~30 FPS
            
    except KeyboardInterrupt:
        print("\nStopping publisher...")
        
    finally:
        # This ensures cleanup happens even if the code crashes
        image_publisher.delete()
        node.SessionManager.delete() # This is the "Master Switch"
        print("Cleanup complete.")
