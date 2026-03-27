"""
Zenoh Server Example
"""

import time
import babyros


def handle_request(request):
    """
    Example service callback.

    Args:
        request (dict | None): Data sent by the client. May be None if the client
        did not send parameters.

    Returns:
        dict: The response to be sent back to the client.

    Raises:
        None
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
    server = babyros.node.Server("example/topic", handle_request)
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
