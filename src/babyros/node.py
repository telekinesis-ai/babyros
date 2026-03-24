"""
Core module definining BabyROS publisher, subscriber, server and client.
"""
import threading
import json
import struct
import numpy as np
import zenoh
from loguru import logger


class SessionManager:
    """
    Manages the Zenoh session for the application.
    """
    _session = None
    _rlock = threading.RLock()
    _config = zenoh.Config()  # Default config, can be overridden by user using set_session_config

    @classmethod
    def set_session_config(cls, config=None):
        """
        Set the Zenoh configuration before creating the session.
        Raises an error if session already exists.
        """
        with cls._rlock:
            if cls._session is not None:
                raise RuntimeError("Cannot set config after session has been created. Ensure that 'babyros.configure()' is called before creating any nodes.")
            if config is not None:
                cls._config = config
                logger.info("Overwritten default session config with user config.")

    @classmethod
    def get_session_config(cls):
        """
        Get the current Zenoh session configuration.
        """
        with cls._rlock:
            return cls._config

    @classmethod
    def create_session(cls):
        """
        Create a new Zenoh session using the stored config.
        Raises an error if the session already exists.
        """
        with cls._rlock:
            if cls._session is not None:
                raise RuntimeError("Session already exists")
            
            # Configure session with important defaults
            cls._config.insert_json5("transport/link/tx/batch_size", "1048576")  # 1MB
            cls._config.insert_json5("transport/link/rx/buffer_size", "209715200")  # 200MB

            cls._session = zenoh.open(cls._config)
            logger.success("Zenoh session created successfully.")

            return cls._session

    @classmethod
    def get_session(cls):
        """
        Return the existing Zenoh session, or create it if it doesn't exist.
        """
        with cls._rlock:            
            if cls._session is None:
                # Create session using create_session
                cls.create_session()
            
            return cls._session

    @classmethod
    def delete(cls):
        """
        Signal all nodes to stop and close the session.
        """
        with cls._rlock:
            if cls._session:
                try:
                    cls._session.close()
                    logger.info("Zenoh session closed successfully.")
                except Exception as e:
                    logger.error(f"Warning: Error closing session: {e}")
                finally:
                    cls._session = None
            else:
                logger.warning("No session to delete.")


class Subscriber:
    """
    BabyROS Subscriber class (based on Zenoh Subscriber) for receiving messages from a topic.
    """
    def __init__(self, topic, callback):
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
        logger.info(f"Subscriber on topic '{self._topic}' deleted.")


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
        logger.info(f"Publisher on topic '{self._topic}' deleted.")


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
        logger.info(f"Received request on '{query.selector}'")

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
        logger.info(f"Server on topic '{self._topic}' deleted.")

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
                logger.error(f"Error in client: {reply.err.payload.to_string()}")
        
        return results

    def delete(self):
        """
        Cleanly delete the client.
        """
        self._querier.undeclare()
        logger.info(f"Client for topic '{self._topic}' deleted.")


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
        logger.info(f"ImagePublisher on topic '{self._topic}' deleted.")


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
        logger.info(f"ImageSubscriber on topic '{self._topic}' deleted.")