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

    def run(self):
        """Blocking loop that stays alive until SessionManager.stop()"""
        try:
            while SessionManager.is_running():
                time.sleep(self._sleep_time)
        except KeyboardInterrupt:
            pass
        finally:
            SessionManager.stop()


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
