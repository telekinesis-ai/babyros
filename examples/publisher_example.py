"""
Zenoh Publisher Example
"""
import time
import babyros


if __name__ == "__main__":
    # The session is created automatically inside the Publisher
    imu_pub = babyros.node.Publisher(topic="imu")

    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    # Start publishing
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
        print("[Publisher] Cleanup complete.")