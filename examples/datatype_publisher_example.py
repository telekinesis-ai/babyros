"""
Zenoh Publisher Example
"""
import time
import numpy as np

import babyros
from telekinesis import datatypes


if __name__ == "__main__":
    # The session is created automatically inside the Publisher
    # compression: "lz4" (default), "zstd", or None for no compression at IPC level
    datatype_pub = babyros.node.Publisher(topic="imu", compression="zstd")

    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    # Start publishing
    print("Starting sensor stream... (Press Ctrl+C to stop)")
    count = 0
    compressed_image = datatypes.Image(np.ones([3000,30000,3], dtype=np.float32), compression=datatypes.ImageCompression.ZSTD)

    try:
        while True:
            datatype_pub.publish(data={"MyInt": datatypes.Int(42), "MyBool": datatypes.Bool(True), "MyImage": compressed_image})
            print(f"Sent seq: {count}")
            
            count += 1
            time.sleep(0.1)  # 10 Hz
            
    except KeyboardInterrupt:
        print("\n[Publisher] Interrupted by user.")
    finally:
        # CRITICAL: Close the Zenoh session gracefully
        datatype_pub.delete()
        print("[Publisher] Cleanup complete.")