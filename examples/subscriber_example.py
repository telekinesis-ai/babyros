"""
Minimal subscriber example to go with publisher_example.py
"""
from babyros import node

def listener(sample):
    """
    Minimal listener callback
    """
    print(f"Received from topic 'hello': '{sample.payload.to_string()}'")

if __name__ == "__main__":
    sub = node.Subscriber("hello", func=listener)
    sub.run()