"""
Zenoh Subscriber Example with Telekinesis datatype message
"""
import time
import babyros

def log_data(msg):
    """Handle received datatype messages (dict or single datatype)."""
    if isinstance(msg, dict):
        print(f"Received dict with keys: {list(msg.keys())}")
        for key, value in msg.items():
            print(f"  {key}: {value}")
    else:
        print(f"Received: {msg}")

if __name__ == "__main__":
    sub = babyros.node.Subscriber(topic="imu", callback=log_data)
    print("Created subscriber successfully!")

    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Subscriber] Interrupted by user.")
    finally:
        sub.delete()
        print("Complete subscriber_example successfully!")
