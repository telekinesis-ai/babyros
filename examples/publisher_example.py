"""
BabyROS Publisher Example: plain dict and Telekinesis datatype messages.
"""

import time
import numpy as np
import babyros
from telekinesis import datatypes


if __name__ == "__main__":
    # The session is created automatically inside the Publisher.
    # compression: "lz4" (default), "zstd", or None for no compression at IPC level
    imu_pub = babyros.node.Publisher(topic="imu", compression="zstd")

    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    compressed_image = datatypes.Image(
        np.ones([3000, 3000, 3], dtype=np.float32),
        compression=datatypes.ImageCompression.ZSTD,
    )

    # Start publishing
    print("Starting sensor stream... (Press Ctrl+C to stop)")
    count = 0
    try:
        while True:
            if count % 2 == 0:
                # Plain dict of numbers/lists -> encoded as JSON.
                data = {
                    "acceleration": [0.1, 0.0, 9.8],
                    "gyro": [0.0, 0.01, 0.0],
                    "seq": count,
                }
            else:
                # Dict of Telekinesis datatypes -> encoded as Arrow IPC.
                data = {
                    "MyInt": datatypes.Int(count),
                    "MyBool": datatypes.Bool(True),
                    "MyImage": compressed_image,
                }

            imu_pub.publish(data=data)
            print(f"Sent seq {count} ({'dict' if count % 2 == 0 else 'datatype'})")

            count += 1
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[Publisher] Interrupted by user.")
    finally:
        # CRITICAL: Close the Zenoh session gracefully
        imu_pub.delete()
        print("[Publisher] Cleanup complete.")
