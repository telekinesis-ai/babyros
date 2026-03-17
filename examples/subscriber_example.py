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


if __name__ == "__main__":
    # Initialize the subscriber
    sub = node.Subscriber(topic="imu", callback=log_imu)

    # Keep the script alive for 5 seconds
    time.sleep(5)
    sub.delete()
    node.SessionManager.delete() # This is the "Master Switch"

