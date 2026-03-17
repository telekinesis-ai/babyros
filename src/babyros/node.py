"""
Core module definining BabyROS publisher, subscriber, server and client.
"""
import threading
import json
import struct
import numpy as np
import zenoh

def get_alive_topics():
    """
    Returns a list of all key expressions currently active in the Zenoh network.
    """
    s = SessionManager.get_session()
    replies = s.get("**")

    for r in replies:
        print(r)


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
    BabyROS Subscriber class (based on Zenoh Subscriber) for receiving messages from a topic.
    """
    def __init__(self, topic, callback, frequency=10):
        self._topic = topic
        self._callback = callback
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
    BabyROS Publisher class (based on Zenoh Publisher) for publishing messages to a topic.
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
    BabyROS Server (based on Zenoh Queryables) class for handling requests on a topic.
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
        """
        Serialize data for Zenoh transport.
        """
        try:
            payload = json.dumps(data)
            return payload
        except Exception as e:
            raise ValueError(f"Failed to serialize data: {e}") from e
        
    def _deserialize(self, sample):
        """
        Deserialize Zenoh sample payload into Python data structure.
        """
        try:
            deserialized_data = json.loads(sample.payload.to_string())
            return deserialized_data
        except Exception as e:
            raise ValueError(f"Failed to deserialize data: {e}") from e
    
    def _handle_request(self, query):
        """
        Handle a client request using Zenoh query/reply correctly.
        """
        print(f"Received request on '{query.selector}'")

        try:
            request_data = None
            if query.payload is not None:
                request_data = self._deserialize(query)
            else:
                request_data = None

            # Call the user-provided callback
            response = self._callback(request_data)
            serialized_data = self._serialize(response)

            # Correct Zenoh Python reply
            query.reply(self._topic, serialized_data)

        except Exception as e:
            query.reply_err(str(e))

    def delete(self):
        """
        Close the server and release resources.
        """
        self._queryable.undeclare()


class Client:
    """
    BabyROS Client based on Zenoh queries.
    """

    def __init__(self, topic):
        self._topic = topic
        self._session = SessionManager.get_session()
        self._querier = self._session.declare_querier(self._topic)

    def _serialize(self, data):
        """
        Serialize data for Zenoh transport.
        """
        try:
            payload = json.dumps(data)
            return payload
        except Exception as e:
            raise ValueError(f"Failed to serialize data: {e}") from e

    def _deserialize(self, sample):
        """
        Deserialize Zenoh sample payload into Python data structure.
        """
        try:
            deserialized_data = json.loads(sample.payload.to_string())
            return deserialized_data
        except Exception as e:
            raise ValueError(f"Failed to deserialize data: {e}") from e

    def request(self, data=None):
        """
        Send a request to the specified topic with optional parameters.
        """
        replies = self._querier.get(payload=self._serialize(data) if data else None)
        results = []
        for reply in replies:
            if reply.ok:
                results.append(self._deserialize(reply.ok))
            else:
                print(f">> Error: {reply.err.payload.to_string()}")
        
        return results

    def delete(self):
        """
        Cleanly delete the client.
        """
        self._querier.undeclare()


class ImagePublisher:
    """
    Image Publisher for Zenoh.
    """
    def __init__(self, topic):
        self._topic = topic
        self._session = SessionManager.get_session()
        self._pub = self._session.declare_publisher(self._topic)

    def publish(self, image):
        """
        Publish an image to the topic.
        """
        h, w, c = image.shape
        # Pack metadata into a small byte string
        meta = struct.pack('iii', h, w, c)
        
        # Put the raw image, but attach the metadata separately
        # No concatenation = No memory copy
        self._pub.put(image.tobytes(), attachment=meta)
    
    def delete(self):
        """
        Cleanly delete publisher.
        """
        self._pub.undeclare()


class ImageSubscriber:
    """
    Image Subscriber for Zenoh.
    """
    def __init__(self, topic, callback):
        self._topic = topic
        self._callback = callback
        self._session = SessionManager.get_session()
        self._sub = self._session.declare_subscriber(self._topic, self._callback_wrapper)

    def _callback_wrapper(self, sample):
        # Extract dimensions from the attachment (12 bytes)
        h, w, c = struct.unpack('iii', sample.attachment.to_bytes())
        
        # Map the payload directly to an array (Zero-Copy)
        image = np.frombuffer(sample.payload.to_bytes(), dtype=np.uint8).reshape((h, w, c))
        self._callback(image)

    def delete(self):
        """
        Cleanly delete subscriber.
        """
        self._sub.undeclare()