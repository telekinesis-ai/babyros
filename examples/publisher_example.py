"""
Zenoh Publisher Example
"""
import time
from babyros import node

if __name__ == "__main__":
    # The session is created automatically inside the Publisher
    imu_pub = node.Publisher(topic="imu")

    print("Starting sensor stream... (Press Ctrl+C to stop)")
    count = 0
    
    try:
        while True:
            data = {
                "acceleration": [0.1, 0.0, 9.8],
                "gyro": [0.0, 0.01, 0.0],
                "seq": [count]
            }
            
            imu_pub.publish(data=data)
            print(f"Sent seq: {count}")
            
            count += 1
            time.sleep(0.1)  # 10 Hz
            
    except KeyboardInterrupt:
        print("\n[Publisher] Interrupted by user.")
    finally:
        # CRITICAL: Close the Zenoh session gracefully
        imu_pub.delete()
        node.SessionManager.delete()
        print("[Publisher] Cleanup complete.")