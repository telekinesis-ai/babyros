"""
BabyROS Client Example: sends both a plain dict request and a Telekinesis
datatype request to the same server.
"""

import babyros
from telekinesis import datatypes


if __name__ == "__main__":
    # compression: "lz4" (default), "zstd", or None for no compression at IPC level
    client = babyros.node.Client(topic="example/topic", compression="zstd")

    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    # Plain dict request
    request = {"param1": "value1", "param2": "value2"}
    print(f"Sending dict: {request}")
    response = client.request(data=request)

    if not response:
        print("Received no response from server.")
    else:
        print("Response:", response[0]["received"])
        print("Equal?", request == response[0]["received"])

    # Telekinesis datatype request
    request = datatypes.Bool(True)
    print(f"\nSending datatype: {request}")
    response = client.request(data=request)

    if not response:
        print("Received no response from server.")
    else:
        print(f"Response: {response[0]}")

    client.delete()
