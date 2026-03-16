"""
BabyROS Client Example
"""
from babyros import node

if __name__ == "__main__":
    # Example usage
    client = node.Client()
    response = client.request("/example/topic")
    print(response)