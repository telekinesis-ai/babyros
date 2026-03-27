"""
Zenoh Subscriber Example with dict message
"""
import time
import babyros


def slow_log_imu(msg: dict):
    """
    Callback function to log IMU data.
    """
    print(f"Received IMU data: Seq {msg['seq']} | Accel: {msg['acceleration']}")
    # time.sleep(3)

if __name__ == "__main__":
    sub = babyros.node.Subscriber(topic="imu", callback=slow_log_imu)
    print("Created subscriber successfully!")
    
    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    # Keep the script alive for 5 seconds
    try:
        # Keep the main thread alive while the Zenoh callback runs in the background
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Subscriber] Interrupted by user.")
    finally:
        # CRITICAL: Delete the subscriber to cleanup resources
        sub.delete()  # Cleanly delete the subscriber
        print("Complete subscriber_example successfully!")

