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
        self._sub.undeclare()


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
        self._pub.undeclare()


class Server:
    """
    BabyROS Server class for handling requests on a topic, based on Zenoh Queryables.
    """
    def __init__(self, topic, callback):
        self._topic = topic
        self._callback = callback # Callback should expect 'request_data'
        self._session = SessionManager.get_session()
        # Note: handle_query is the standard name for the callback
        self._queryable = self._session.declare_queryable(
            self._topic, 
            self._handle_request
        )

    def _serialize(self, data):
        # json.dumps returns a string, Zenoh wants bytes or ZBytes
        return json.dumps(data).encode('utf-8')

    def _handle_request(self, query):
        """
        The query object contains the selector and potential value (params).
        """
        # If the client sent parameters in the query
        incoming_value = None
        if query.value is not None:
            incoming_value = json.loads(query.value.payload.to_string())

        # Execute the user-provided logic
        response_data = self._callback(incoming_value)
        
        # Create a Sample to reply
        # We use the query's own key_selector to ensure the reply matches
        sample = zenoh.Sample(query.key_selector, self._serialize(response_data))
        query.reply(sample)

    def close(self):
        self._queryable.undeclare()


class Client:
    def __init__(self):
        self._session = SessionManager.get_session()

    def request(self, topic, params=None):
        """
        topic: The key expression
        params: Optional dict to send to the server
        """
        # Serialize params if provided
        value = json.dumps(params).encode('utf-8') if params else None
        
        # .get() returns a 'Reply' receiver
        replies = self._session.get(topic, value=value)

        results = []
        # The receiver is an iterable of 'Reply' objects
        for reply in replies:
            if reply.is_ok():
                try:
                    # Correct way to grab the payload bytes
                    payload_bytes = reply.ok.payload.payload
                    results.append(self._deserialize(payload_bytes))
                except Exception as e:
                    print(f"Error parsing reply: {e}")
            elif reply.is_err():
                print(f"Received error from network: {reply.err.payload.to_string()}")
        
        return results

    def _deserialize(self, payload):
        # Zenoh buffers have a to_string() method which is very handy
        return json.loads(payload.decode('utf-8'))