"""
Minimalistic publisher example to go with subscriber_example.py
"""
import random
from babyros import node

random.seed()

def hello_world():
    """
    Minimal pub example
    """
    return "Hello world!"

if __name__ == "__main__":
    pub = node.Publisher("hello", func=hello_world)
    pub.run()
