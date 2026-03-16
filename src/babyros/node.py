"""
Zenoh Node
"""
import time
import threading
import json
import zenoh


class SessionManager:
    """
    Manages the Zenoh session for the application.å
    """
    _session = None
    _lock = threading.Lock()
    # Master switch for the whole application
    _running = threading.Event()

    @classmethod
    def get_session(cls):
        """
        Get the Zenoh session, creating it if necessary.
        """
        with cls._lock:
            if cls._session is None:
                cls._session = zenoh.open(zenoh.Config())
                cls._running.set()
        return cls._session
    
    @classmethod
    def is_running(cls):
        """
        Check if the Zenoh session is running.
        """
        return cls._running.is_set()

    @classmethod
    def stop(cls):
        """Signal all nodes to stop and close the session."""
        with cls._lock:
            cls._running.clear()
            if cls._session:
                cls._session.close()
                cls._session = None


class Subscriber:
    """
    Subscriber class for receiving messages from a Zenoh topic.
    """
    def __init__(self, topic, callback, frequency=10):
        self._topic = topic
        self._callback = callback
        self._sleep_time = 1/frequency
        self._session = SessionManager.get_session()
        
        # Zenoh-native: background thread starts here
        self._sub = self._session.declare_subscriber(self._topic, self._callback_wrapper)

    def _callback_wrapper(self, sample):
        # Zenoh native deserialization (handles JSON/ZBytes)
        data = self._deserialize(sample)
        self._callback(data)

    def _deserialize(self, sample):
        """
        Deserialize Zenoh sample payload into Python data structure.
        """
        try:
            deserialized_data = json.loads(sample.payload.to_string())
            return deserialized_data
        except Exception as e:
            raise ValueError(f"Failed to deserialize data: {e}") from e

    def delete(self):
        """
        Cleanly delete subscriber.
        """
        self._sub.delete()


class Publisher:
    """
    Publisher class for publishing messages to a Zenoh topic.
    """
    def __init__(self, topic):
        self._topic = topic
        self._session = SessionManager.get_session()
        self._pub = self._session.declare_publisher(self._topic)

    def publish(self, data):
        """
        Publish data to the Zenoh topic.
        """
        # Zenoh native serialization
        serialized_data = self._serialize(data)
        self._pub.put(serialized_data)

    def _serialize(self, data):
        """
        Serialize data for Zenoh transport.
        """
        try:
            payload = zenoh.ZBytes(json.dumps(data))
            return payload
        except Exception as e:
            raise ValueError(f"Failed to serialize data: {e}") from e
        
    def delete(self):
        """
        Cleanly delete publisher.
        """
        self._pub.delete()


class Server:
    """
    BabyROS Server, built on Zenoh Queryable
    """
    def __init__(self, topic, callback):
        self._topic = topic
        self._callback = callback
        self._session = SessionManager.get_session()
        self._queryable = self._session.declare_queryable(self._topic, self._handle_request)

    def _serialize(self, data):
        """
        Serialize Python data structure into Zenoh-compatible format.
        """
        try:
            payload = zenoh.ZBytes(json.dumps(data))
            return payload
        except Exception as e:
            raise ValueError(f"Failed to serialize data: {e}") from e

    def _handle_request(self, request):
        """
        Wrapper for the queryable callback.
        """
        response_data = self._callback()
        # Send the response back through the query object
        request.reply(
            zenoh.Sample(self._topic, self._serialize(response_data))
        )

    def get(self, request):
        """
        Handle a GET request on the queryable topic.
        """
        response = {"message": f"Received request: {request}"}
        return response

    def close(self):
        """
        Cleanly close the server.
        """
        try:
            self._queryable.undeclare()
        except Exception as e:
            raise ValueError(f"Failed to close Server: {e}") from e

class Client:
    """
    BabyROS Client, built on Zenoh Querier
    """
    def __init__(self):
        self._session = SessionManager.get_session()

    def request(self, topic, data=None):
        """
        Send a request to a Zenoh topic and wait for a response.
        """
        replies = self._session.get(topic, zenoh.Queue())

        results = []
        for reply in replies.receiver:
            try:
                # Access the data within the reply
                data = self._deserialize(reply.ok.payload.payload)
                results.append(data)
            except Exception as e:
                print(f"Error parsing reply: {e}")
        
        return results

    def _deserialize(self, payload):
        """
        Deserialize Zenoh payload into Python data structure.
        """
        try:
            data = json.loads(payload.to_string())
            return data
        except Exception as e:
            raise ValueError(f"Failed to deserialize data: {e}") from e

    def close(self):
        """
        Close the Zenoh session.
        """
        self._session.close()