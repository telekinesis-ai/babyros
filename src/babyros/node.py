"""
Core module definining BabyROS publisher, subscriber, server and client.
"""
import threading
import json
import time
import struct
import numpy as np
import zenoh
from loguru import logger
from babyros.serializer import serialize_json, serialize_image, deserialize_image, deserialize_json

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


class Publisher:
    """
    BabyROS Publisher class (based on Zenoh Publisher) for publishing messages to a topic.
    """
    def __init__(self, topic, datatype="json"):
        self._topic = topic
        self._datatype = datatype
        self._session = SessionManager.get_session()
        self._pub = self._session.declare_publisher(self._topic)

    def publish(self, data):
        """
        Publish data to the Zenoh topic.
        """
        # Zenoh native serialization
        if self._datatype == "json":
            payload, attachment = serialize_json(data)
        elif self._datatype == "image":
            payload, attachment = serialize_image(data)
        else:
            raise ValueError("Failed to serialize data. Parameter datatype has to be json or image.")
        
        self._pub.put(payload=payload, attachment=attachment)

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


class Subscriber:
    """
    Advanced BabyROS Subscriber node.
    """
    def __init__(self,
                 topic, 
                 callback, 
                 history="keep_last",
                 depth=1
        ):
        self._topic = topic
        self._callback = callback
        self._session = SessionManager.get_session()
        self._running = True

        if history not in ("keep_last", "keep_all"):
            raise ValueError("history must be 'keep_last' or 'keep_all'")

        if depth < 1:
            raise ValueError("depth must be >= 1")

        if history == "keep_last":
            channel = zenoh.handlers.RingChannel(depth)
            self._depth = depth
        else:  # keep_all
            channel = zenoh.handlers.FifoChannel()
            self._depth = None  # not meaningful

        self._history = history

        self._sub = self._session.declare_subscriber(self._topic, channel)

        self._callback_worker = threading.Thread(target=self._callback_loop, daemon=True)
        self._callback_worker.start()

    def _callback_loop(self):
        handler = self._sub.handler

        while self._running:
            sample = handler.try_recv()

            if sample is None:
                # 1ms polling
                time.sleep(0.001)
                continue
            
            attachment = sample.attachment.to_bytes()
            payload = sample.payload.to_bytes()

            if attachment[:3] == b"IMG":
                data = deserialize_image(payload, attachment)
            elif attachment == b"JSON":
                data = deserialize_json(payload)
            else:
                raise ValueError("Attachment unrecognized!")

            try:
                self._callback(data)
            except Exception as e:
                logger.error(f"Callback error on {self._topic}: {e}")

    def _deserialize(self, sample):
        try:
            return json.loads(sample.payload.to_string())
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            return None

    def delete(self):
        """Cleanly shut down the subscriber and wait for the worker."""
        logger.info(f"Deleting AdvancedSubscriber on '{self._topic}'...")
        self._running = False
        
        # Wait for the worker thread to finish its last loop
        if self._callback_worker.is_alive():
            self._callback_worker.join(timeout=1.0)
            
        # Unsubscribe from the network
        self._sub.undeclare()

        logger.info(f"AdvancedSubscriber on '{self._topic}' deleted.")    


class Server:
    """
    BabyROS Server (based on Zenoh Queryables) class for handling requests on a topic.
    """
    def __init__(self, topic, callback):
        self._topic = topic
        self._callback = callback # Callback should expect 'request_data'
        self._session = SessionManager.get_session()

        # Note: handle_query is the standard name for the callback
        self._queryable = self._session.declare_queryable(self._topic, self._handle_request)

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
