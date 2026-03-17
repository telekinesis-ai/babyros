import time
import numpy as np
import zenoh



def on_image_received(sample):

    t1 = time.time()
    image = np.frombuffer(sample.payload.to_bytes(), dtype=np.uint8).reshape((5112, 3840, 3))
    print(f"Image deserialization time: {round((time.time() - t1) * 1000)} ms")

    size_mb = image.nbytes / 1e6
    print(f"Total MBs: {size_mb}")

with zenoh.open(zenoh.Config()) as session:
    with zenoh.open(zenoh.Config()) as session:
        sub = session.declare_subscriber('camera/capture', on_image_received)
        print("Subscriber started...")
        time.sleep(60)