"""
BabyROS Client Example with Telekinesis datatype request/response
"""
import babyros
from datatypes import datatypes

if __name__ == "__main__":
    client = babyros.node.Client(topic="example/topic")

    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    request = datatypes.Bool(True)
    print(f"Sending: {request}")

    response = client.request(data=request)

    if not response:
        print("Received no response from server.")
    else:
        print(f"Response: {response[0]}")

    client.delete()
