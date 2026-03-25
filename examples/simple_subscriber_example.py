"""
Zenoh Subscriber Example
"""
import time
from babyros import node

# Define what to do when data arrives
def log_imu(msg):
    """
    Callback function to log IMU data.
    """
    print(f"Received IMU data: Seq {msg['seq']} | Accel: {msg['acceleration']}")

    # Emulate lag
    time.sleep(5)


if __name__ == "__main__":
    sub = node.SimpleSubscriber(topic="imu", callback=log_imu)
    print("Created subscriber successfully!")

    # Keep the script alive for 5 seconds
    try:
        # Keep the main thread alive while the Zenoh callback runs in the background
        while True:
            time.sleep(1) 
    except KeyboardInterrupt:
        print("\n[Subscriber] Interrupted by user.")
    finally:
        # CRITICAL: Close the Zenoh session gracefully
        sub.delete()  # Cleanly delete the subscriber
        node.SessionManager.delete()
        print("Complete subscriber_example successfully!")

