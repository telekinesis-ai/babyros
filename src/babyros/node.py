"""
Core BabyROS nodes: Publisher, Subscriber, Client, Server
"""
import time
import zenoh


class Subscriber:
    """
    Subscriber node
    """
    def __init__(self, topic, func, frequency=10):
        self._func = func
        self._frequency = frequency
        self._sleep_time = 1/self._frequency
        self._topic = topic
        self._session = zenoh.open(zenoh.Config())
        self._sub = self._session.declare_subscriber(self._topic, self._func)

    
    def run(self):
        """
        Subscriber node
        """
        while True:
            time.sleep(self._sleep_time)



class Publisher:
    """
    Publisher node
    """
    def __init__(self, topic, func, frequency=10):
        self._func = func
        self._frequency = frequency
        self._sleep_time = 1/self._frequency
        self._topic = topic
        self._session = zenoh.open(zenoh.Config())
        self._pub = self._session.declare_publisher(self._topic)

    def run(self):
        """
        Launch publisher
        """
        while True:
             out = self._func()

             # TODO: how to know the datatype from before?
             buf = f"{out}"

             print(f"Publishing on topic '{self._topic}': '{buf}'")
             self._pub.put(buf)

             time.sleep(self._sleep_time)
