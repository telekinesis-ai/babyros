"""
Core module definining BabyROS publisher, subscriber, server and client.
"""
from typing import Any, Union
import threading
import weakref
import atexit
import time
import zenoh
import numpy as np
from loguru import logger
from babyros import serializer


class SessionManager:
    """
    Manages the Zenoh session for the application.
    """
    _session = None
    _rlock = threading.RLock()
    _config = zenoh.Config()  # Default config, can be overridden by user using set_session_config
    _active_nodes = weakref.WeakSet()

    @classmethod
    def get_topics(cls):
        """
        Get a list of all active nodes in the session.
        """
        with cls._rlock:
            topic_list = []
            for node in cls._active_nodes:
                topic_list.append(node._topic)
            return topic_list

    @classmethod
    def register_node(cls, node: Union["Publisher", "Subscriber", "Server", "Client"]):
        """
        Register a new active node.
        """
        with cls._rlock:
            cls._active_nodes.add(node)

    @classmethod
    def unregister_node(cls, node: Union["Publisher", "Subscriber", "Server", "Client"]):
        """
        Unregister an active node.
        """
        with cls._rlock:
            cls._active_nodes.discard(node)

    @classmethod
    def set_session_config(cls, config: zenoh.Config = None):
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
    def delete(cls, force: bool = False):
        """
        Safely close the Zenoh session.

        Args:
            force (bool): If True, forcefully deletes all active nodes.
        """
        with cls._rlock:
            if cls._session is None:
                logger.warning("No session to delete.")
                return

            if cls._active_nodes:
                if not force:
                    raise RuntimeError(
                        f"Cannot delete session: {len(cls._active_nodes)} active node(s) still exist."
                    )

                logger.warning(
                    f"Force-deleting {len(cls._active_nodes)} active node(s)..."
                )

                # Copy to avoid mutation during iteration
                nodes = list(cls._active_nodes)

                for node in nodes:
                    try:
                        node.delete()
                    except Exception as e:
                        logger.error(f"Error deleting node: {e}")

            try:
                cls._session.close()
                logger.info("Zenoh session closed successfully.")
            except Exception as e:
                logger.error(f"Warning: Error closing session: {e}")
            finally:
                cls._session = None
                cls._active_nodes.clear()

class Publisher:
    """
    BabyROS Publisher class (based on Zenoh Publisher) for publishing messages to a topic.
    """
    def __init__(self, topic: str):
        """
        Initialize the BabyROS Publisher.

        Args:
            topic (str): The topic to publish to.
            datatype (str): The data type of the messages ("json" or "image"). Default is "json".

        Returns:
            None

        Raises:
            ValueError: If the topic is invalid or if the data type is unsupported.
        """
        if not isinstance(topic, str) or not topic:
            raise ValueError("Invalid topic: topic must be a non-empty string.")
        
        if topic[0] == "/":
            raise ValueError("Topic names should not start with '/'.")

        self._topic = topic
        self._deleted = False
        self._session = SessionManager.get_session()
        SessionManager.register_node(self)
        self._codec = serializer.ZenohCodec()
        self._pub = self._session.declare_publisher(self._topic)

    def publish(self, data: Union[dict, np.ndarray]):
        """
        Publish data to the Zenoh topic.

        Args:
            data: The data to publish, which will be serialized based on the datatype.

        """

        if self._deleted:
            logger.error(f"Publisher on topic '{self._topic}' is already deleted.")
            raise RuntimeError("Cannot publish: Publisher is deleted.")

        # Zenoh native serialization
        try:
            payload, attachment = self._codec.encode(data)
        except Exception as e:
            logger.error(f"Failed to serialize data for topic '{self._topic}': {e}")
            raise ValueError(f"Failed to serialize data: {e}") from e

        self._pub.put(payload=payload, attachment=attachment)
  
    def delete(self):
        """
        Cleanly delete publisher.
        """
        self._deleted = True
        self._pub.undeclare()
        SessionManager.unregister_node(self)
        logger.info(f"Publisher on topic '{self._topic}' deleted.")


class Subscriber:
    """
    BabyROS Subscriber node.
    """
    def __init__(self,
                 topic: str,
                 callback: callable,
                 history: str = "keep_last",
                 depth: int = 1
        ):
        """
        Initialize the subscriber.

        Args:
            topic (str): The topic to subscribe to.
            callback (callable): The callback function to handle incoming messages.
            history (str): The history policy ("keep_last" or "keep_all"). Default is "keep_last".
            depth (int): The depth of the history buffer. Default is 1.

        Returns:
            None

        Raises:
            ValueError: If any argument is invalid.
        """
        if not isinstance(topic, str) or not topic:
            raise ValueError("Invalid topic: topic must be a non-empty string.")
        if topic[0] == "/":
            raise ValueError("Topic names should not start with '/'.")
        if not callable(callback):
            raise TypeError("callback must be callable")
        if history not in ("keep_last", "keep_all"):
            raise ValueError("history must be 'keep_last' or 'keep_all'")
        if not isinstance(depth, int) or depth < 1:
            raise ValueError("depth must be int >= 1")
        
        # Populate members
        self._topic = topic
        self._callback = callback
        self._history = history
        self._depth = depth

        self._session = SessionManager.get_session()
        SessionManager.register_node(self)

        self._codec = serializer.ZenohCodec()
        self._running = True
        self._deleted = False

        if self._history == "keep_last":
            channel = zenoh.handlers.RingChannel(self._depth)
        else:  # keep_all
            channel = zenoh.handlers.FifoChannel(self._depth)

        self._sub = self._session.declare_subscriber(self._topic, channel)

        self._callback_worker = threading.Thread(target=self._callback_loop, daemon=True)
        self._callback_worker.start()

    def _callback_loop(self):
        """
        The main loop for processing incoming messages.
        """
        handler = self._sub.handler

        while self._running:
            sample = handler.try_recv()

            if sample is None:
                # 1ms polling
                time.sleep(0.001)
                continue
            
            try:
                # Convert Zenoh buffers to standard bytes
                payload = sample.payload.to_bytes()
                attachment = sample.attachment.to_bytes()

                # Let the codec handle the logic based on the attachment tag
                data = self._codec.decode(payload, attachment)
            except Exception as e:
                logger.error(f"Failed to decode message on topic '{self._topic}': {e}")
                continue
            
            try:
                self._callback(data)
            except Exception as e:
                logger.error(f"Callback error on {self._topic}: {e}")

    def delete(self):
        """
        Cleanly shut down the subscriber and wait for the worker.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        logger.info(f"Deleting Subscriber on '{self._topic}'...")
        self._running = False
        self._deleted = True

        # Wait for the worker thread to finish its last loop
        if self._callback_worker.is_alive():
            self._callback_worker.join(timeout=1.0)
            
        # Unsubscribe from the network
        self._sub.undeclare()
        SessionManager.unregister_node(self)
        logger.info(f"Subscriber on '{self._topic}' deleted.")


class Server:
    """
    BabyROS Server (based on Zenoh Queryables) class for handling requests on a topic.
    """
    def __init__(self, topic: str, callback: callable):
        """
        Initialize the BabyROS Server.

        Args:
            topic (str): The topic to subscribe to.
            callback (callable): The callback function to handle incoming requests.

        Returns:
            None

        Raises:
            None
        """
        if not isinstance(topic, str) or not topic:
            raise ValueError("Invalid topic: topic must be a non-empty string.")
        if topic[0] == "/":
            raise ValueError("Topic names should not start with '/'.")
        if not callable(callback):
            raise ValueError("Invalid callback: callback must be a callable.")
        
        self._topic = topic
        self._callback = callback # Callback should expect 'request_data'
        self._deleted = False
        self._codec = serializer.ZenohCodec()
        self._session = SessionManager.get_session()
        SessionManager.register_node(self)

        # Note: handle_query is the standard name for the callback
        self._queryable = self._session.declare_queryable(self._topic, self._handle_request)
    
    def _handle_request(self, query):
        """
        Handle a client request using Zenoh query/reply correctly.
        """
        logger.info(f"Received request on '{query.selector}'")

        try:
            request_data = None
            if query.payload is not None:
                # Decode the incoming request payload using its attachment
                request_data = self._codec.decode(
                    query.payload.to_bytes(), 
                    query.attachment.to_bytes()
                )

            # Execute user callback to get the result
            response_data = self._callback(request_data)

            # Encode the result back for the wire
            payload, attachment = self._codec.encode(response_data)

            # Reply back to the client
            query.reply(self._topic, payload, attachment=attachment)

        except Exception as e:
            logger.error(f"Server error on {self._topic}: {e}")
            query.reply_err(str(e).encode("utf-8"))

    def delete(self):
        """
        Close the server and release resources.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self._deleted = True
        self._queryable.undeclare()
        SessionManager.unregister_node(self)
        logger.info(f"Server on topic '{self._topic}' deleted.")


class Client:
    """
    BabyROS Client based on Zenoh queries.
    """

    def __init__(self, topic: str):
        """
        Initialize the BabyROS Client.

        Args:
            topic (str): The topic to send requests to.

        Returns:
            None

        Raises:
            None
        """
        if not isinstance(topic, str) or not topic:
            raise ValueError("Invalid topic: topic must be a non-empty string.")
        if topic[0] == "/":
            raise ValueError("Topic names should not start with '/'.")
        
        self._topic = topic
        self._deleted = False
        self._codec = serializer.ZenohCodec()
        self._session = SessionManager.get_session()
        SessionManager.register_node(self)

        self._querier = self._session.declare_querier(self._topic)

    def request(self, data=None):
        """
        Send a request to the specified topic with optional parameters.

        Args:
            data (dict, optional): The data to include in the request.

        Returns:
            list: The list of responses from the server.

        Raises:
            None
        """
        if self._deleted:
            logger.error(f"Client for topic '{self._topic}' is already deleted.")
            raise RuntimeError("Cannot send request: Client is deleted.")
        
        payload, attachment = (None, None)
        if data is not None:
            payload, attachment = self._codec.encode(data)

        # Perform the Zenoh GET operation
        replies = self._querier.get(payload=payload, attachment=attachment)
        
        results = []
        for reply in replies:
            if reply.ok:
                # Decode the response from the server
                sample = reply.ok
                decoded_val = self._codec.decode(
                    sample.payload.to_bytes(), 
                    sample.attachment.to_bytes()
                )
                results.append(decoded_val)
            else:
                err_msg = reply.err.payload.to_string()
                logger.error(f"Server error on {self._topic}: {err_msg}")
        
        return results

    def delete(self):
        """
        Cleanly delete the client.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self._deleted = True
        self._querier.undeclare()
        SessionManager.unregister_node(self)
        logger.info(f"Client for topic '{self._topic}' deleted.")


def _cleanup():
    try:
        SessionManager.delete(force=True)
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

atexit.register(_cleanup)
