"""
BabyROS Client Example
"""
import json
import babyros

if __name__ == "__main__":
    client = babyros.node.Client(topic="example/topic")

    # Get list of topics in the session
    topics = babyros.get_topics_in_session()
    print("Active topics in current session:", topics)

    request = {"param1": "value1", "param2": "value2"}
    print(json.dumps(request))
    # Send request to the server
    response = client.request(data=request)

    print(response)

    if not response:
        print("Recieved no response from server.")
    else:
        print("Response: ", response[0]["received"])
        print("Request: ", request)  
        print("Equal? ", request == response[0]["received"])

    client.delete()