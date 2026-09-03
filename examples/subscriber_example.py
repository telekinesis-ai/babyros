"""
BabyROS Subscriber Example: handles both plain dict and Telekinesis
datatype messages, since the same Subscriber decodes either.
"""

import time
import babyros


def log_data(msg):
    """Log a received message, whether it's a plain dict or a datatype."""
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
        # Keep the main thread alive while the Zenoh callback runs in the background
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Subscriber] Interrupted by user.")
    finally:
        # CRITICAL: Delete the subscriber to cleanup resources
        sub.delete()
        print("Complete subscriber_example successfully!")
