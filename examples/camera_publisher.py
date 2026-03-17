import zenoh
import time
import numpy as np

if __name__ == "__main__":
    with zenoh.open(zenoh.Config()) as session:
        key = 'camera/capture'
        pub = session.declare_publisher(key)
        msg_counter = 0
        while True:
            msg_counter += 1
            print(f"\nMessage {msg_counter}-------------")

            t1 = time.time()
            image = np.zeros((5112, 3840, 3), dtype=np.uint8)
            print(f"Image creation time: {round((time.time() - t1) * 1000)} ms")

            size_mb = image.nbytes / 1e6
            print(f"Image size: {size_mb} MB")

            t2 = time.time()
            image_bytes = image.tobytes()
            print(f"Image serialization time: {round((time.time() - t2) * 1000)} ms")

            t3 = time.time()
            pub.put(image_bytes)
            print(f"Image publishing time: {round((time.time() - t3) * 1000)} ms")

            print(f"Total time for iteration: {round((time.time() - t1) * 1000)} ms")
            print(f"\nNew iteration-------------")
            time.sleep(0.1)