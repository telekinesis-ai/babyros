"""
Zenoh Server Example
"""

import time
from babyros import node


def handle_request(request):
    """
    Example service callback.

    Parameters
    ----------
    request : dict | None
        Data sent by the client. May be None if the client
        did not send parameters.
    """

    if request is None:
        print("Callback method! No request payload received.")
        return {"message": "No request received!"}

    print("Correct data processesed!")
    return {
        "message": "Hello from server!",
        "received": request
    }


if __name__ == "__main__":
    server = node.Server("example/topic", handle_request)

    print("Server started successfully!")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.delete()
        node.SessionManager.delete() # This is the "Master Switch"