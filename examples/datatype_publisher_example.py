"""
Zenoh Publisher Example
"""
import time
import babyros
from datatypes import datatypes

if __name__ == "__main__":
    # The session is created automatically inside the Publisher
    datatype_pub = babyros.node.Publisher(topic="imu")

    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    # Start publishing
    print("Starting sensor stream... (Press Ctrl+C to stop)")
    count = 0
    
    try:
        while True:
            datatype_pub.publish(data={"MyInt": datatypes.Int(42), "MyBool": datatypes.Bool(True)})
            print(f"Sent seq: {count}")
            
            count += 1
            time.sleep(0.1)  # 10 Hz
            
    except KeyboardInterrupt:
        print("\n[Publisher] Interrupted by user.")
    finally:
        # CRITICAL: Close the Zenoh session gracefully
        datatype_pub.delete()
        print("[Publisher] Cleanup complete.")