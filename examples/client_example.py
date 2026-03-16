"""
BabyROS Client Example
"""

from babyros import node


if __name__ == "__main__":
    client = node.Client(topic="example/topic")

    # Send request to the server
    response = client.request()

    print(response)