"""
BabyROS Transient Local Subscriber Example

Pairs with transient_local_publisher_example.py. Start the publisher first,
let it publish its one-shot map, and THEN start this subscriber - because
durability=TRANSIENT_LOCAL, it still receives that map even though it
declared well after publish() was called.
"""

import time
import numpy as np
import babyros


def log_map(msg: dict):
    """
    Callback function to log a received occupancy grid map.
    """
    grid = msg["grid"]
    occupied = int(np.count_nonzero(grid == 100))
    print(
        f"Received map: {grid.shape[1]}x{grid.shape[0]} cells "
        f"@ {msg['resolution']} m/cell, origin={msg['origin']}, "
        f"occupied cells={occupied}"
    )


if __name__ == "__main__":
    durability = babyros.node.Durability.TRANSIENT_LOCAL
    sub = babyros.node.Subscriber(
        topic="map", callback=log_map, durability=durability, depth=1
    )
    print("Created transient-local subscriber. Waiting for the cached map...")

    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Subscriber] Interrupted by user.")
    finally:
        # CRITICAL: Delete the subscriber to cleanup resources
        sub.delete()
        print("[Subscriber] Cleanup complete.")
