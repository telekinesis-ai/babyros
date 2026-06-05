"""
Zenoh Server Example with Telekinesis datatype request/response
"""

import time
import babyros
from datatypes import datatypes


def handle_request(request: datatypes.Bool | None) -> datatypes.Bool:
    if request is None:
        print("No request payload received.")
        return datatypes.Bool(False)

    print(f"Received: {request}")
    return datatypes.Bool(not request.data)


if __name__ == "__main__":
    server = babyros.node.Server("example/topic", handle_request)
    print("Server started successfully!")

    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.delete()
