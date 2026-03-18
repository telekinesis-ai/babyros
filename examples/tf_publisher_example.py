from babyros import node, tf
import time

if __name__ == "__main__":
    broadcaster = tf.TransformBroadcaster()

    try:
        while True:
            # Tell the world where the robot is (moving on X axis)
            broadcaster.send_transform(
                parent_frame="world",
                child_frame="base_link",
                translation=[time.time() % 10, 0, 0], 
                rotation=[0, 0, 0, 1]
            )
            time.sleep(0.1)
    except KeyboardInterrupt:
        raise KeyboardInterrupt("Shutting down TF broadcaster...")
    finally:
        broadcaster = None
        node.SessionManager.delete()