
from babyros import node


if __name__ == "__main__":
    # Get the list of alive topics
    node.get_alive_topics()
    node.SessionManager.delete() # This is the "Master Switch"
