"""
BabyROS Transient Local Publisher Example

Demonstrates the ROS1 "latched topic" pattern: a static map is published once
at startup, then the publisher just stays alive. 
Because durability is TRANSIENT_LOCAL, a Subscriber(durability=TRANSIENT_LOCAL) 
that starts AFTER this map was published will still receive it.
"""

import time
import numpy as np
import babyros


def build_static_map(width: int = 20, height: int = 20) -> dict:
    """
    Build a toy occupancy grid: 0 = free, 100 = occupied, -1 = unknown.
    Stands in for a map that's expensive to (re)compute, so it's published
    once rather than on a loop.
    """
    grid = np.zeros((height, width), dtype=np.int8)
    grid[0, :] = grid[-1, :] = 100  # walls
    grid[:, 0] = grid[:, -1] = 100
    grid[5:8, 10:15] = 100  # an obstacle

    return {
        "resolution": 0.05,  # meters/cell
        "origin": [0.0, 0.0, 0.0],
        "grid": grid,
    }


if __name__ == "__main__":

    durability = babyros.node.Durability.TRANSIENT_LOCAL
    # depth=1: only the latest map matters to a late-joining subscriber.
    map_pub = babyros.node.Publisher(topic="map", durability=durability, depth=1)

    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    # Publish once at startup, exactly like a real map server would.
    map_data = build_static_map()
    map_pub.publish(data=map_data)
    print("Published static map. Cached for late-joining subscribers.")

    print(
        "Map publisher is up (Press Ctrl+C to stop). "
        "Start transient_local_subscriber_example.py any time now - "
        "it will still receive the map above."
    )
    try:
        while True:
            time.sleep(5)
            print("[Publisher] Still alive; cached map remains available.")
    except KeyboardInterrupt:
        print("\n[Publisher] Interrupted by user.")
    finally:
        # CRITICAL: Close the Zenoh session gracefully
        map_pub.delete()
        print("[Publisher] Cleanup complete.")
