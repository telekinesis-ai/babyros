"""
BabyROS Client Example
"""
from babyros import node
import json

if __name__ == "__main__":
    client = node.Client(topic="example/topic")

    request = {"param1": "value1", "param2": "value2"}
    print(json.dumps(request))
    # Send request to the server
    response = client.request(data=request)

    print(response)

    print("Response: ", response[0]["received"])
    print("Request: ", request)  
    print("Equal? ", request == response[0]["received"]) 

    client.delete()
    node.SessionManager.delete() # This is the "Master Switch"