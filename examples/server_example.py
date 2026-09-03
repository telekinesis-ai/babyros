"""
BabyROS Server Example: handles both plain dict and Telekinesis datatype
requests, replying in the same shape as the request.
"""

import time
import babyros
from telekinesis import datatypes


def handle_request(request):
    """
    Example service callback.

    Args:
        request: dict, a Telekinesis datatype, or None if the client sent no
            parameters.

    Returns:
        A response matching the shape of the request.
    """
    if request is None:
        print("No request payload received.")
        return {"message": "No request received!"}

    if isinstance(request, dict):
        print(f"Received dict: {request}")
        return {"message": "Hello from server!", "received": request}

    print(f"Received datatype: {request}")
    if isinstance(request, datatypes.Bool):
        return datatypes.Bool(not request.data)
    return request


if __name__ == "__main__":
    # compression: "lz4" (default), "zstd", or None for no compression at IPC level
    server = babyros.node.Server("example/topic", handle_request, compression="zstd")
    print("Server started successfully!")

    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.delete()
