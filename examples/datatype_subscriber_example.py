"""
Zenoh Subscriber Example with Telekinesis datatype message
"""
import time
import babyros
from datatypes import datatypes


def log_bool(msg: datatypes.Bool):
    print(f"Received: {msg}")

if __name__ == "__main__":
    sub = babyros.node.Subscriber(topic="imu", callback=log_bool)
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
