"""
Creates a Zenoh-compatible payload and attachment from a Python object.
"""
from typing import Any, Dict, Callable
import json
import struct

import numpy as np


_LEGACY_IMAGE_METADATA_SIZE = 22


class ZenohCodec:
    def __init__(self):
        # Maps Python types to (Tag, Serializer, Deserializer)
        self._registry: Dict[Any, Dict[str, Callable]] = {
            dict: {
                "tag": b"JSON",
                "ser": lambda d: json.dumps(d).encode("utf-8"),
                "des": lambda p, a: json.loads(p.decode("utf-8"))
            },
            np.ndarray: {
                "tag": b"IMG",
                "ser": self._serialize_np,
                "des": self._deserialize_np
            }
        }

    def _serialize_np(self, arr: np.ndarray) -> bytes:
        return np.ascontiguousarray(arr).tobytes()

    def _deserialize_np(self, payload: bytes, attachment: bytes) -> np.ndarray:
        metadata = attachment[3:]

        if metadata.startswith(b"{"):
            header = json.loads(metadata.decode("utf-8"))
            dtype = np.dtype(header["dtype"])
            shape = tuple(header["shape"])
            expected_size = int(np.prod(shape, dtype=np.int64)) * dtype.itemsize
            if len(payload) != expected_size:
                raise ValueError(
                    "Image payload size does not match attachment metadata."
                )
            return np.frombuffer(payload, dtype=dtype).reshape(shape)

        # Backward compatibility for the original fixed-width attachment:
        # b"IMG" + struct.pack("iii", h, w, c) + dtype_name.ljust(10, b"\0")
        if len(metadata) < _LEGACY_IMAGE_METADATA_SIZE:
            raise ValueError("Invalid image attachment metadata.")

        h, w, c = struct.unpack("iii", metadata[:12])
        dtype = metadata[12:22].rstrip(b"\0").decode("utf-8")
        return np.frombuffer(payload, dtype=dtype).reshape((h, w, c))

    def encode(self, data: Any) -> tuple[bytes, bytes]:
        """
        Returns (payload, attachment)"""
        t = type(data)
        if t not in self._registry:
            raise TypeError(f"No serializer for {t}")

        if t == np.ndarray:
            if data.dtype.hasobject:
                raise TypeError("Object dtype arrays cannot be serialized safely.")

            metadata = {
                "shape": data.shape,
                "dtype": data.dtype.str,
            }
            attachment = self._registry[t]["tag"] + json.dumps(
                metadata,
                separators=(",", ":")
            ).encode("utf-8")
            return np.ascontiguousarray(data).tobytes(), attachment
        
        entry = self._registry[t]
        payload = entry["ser"](data)
        
        # Build attachment: Tag + Optional Metadata
        attachment = entry["tag"]
            
        return payload, attachment

    def decode(self, payload: bytes, attachment: bytes) -> Any:
        """
        Decode a Zenoh payload and attachment into a Python object.
        """
        tag = attachment[:3] # Assuming 3-char tags for simplicity
        if tag == b"JSO": # Handle JSON (tag was b"JSON", first 3 are JSO)
             return self._registry[dict]["des"](payload, attachment)
        if tag == b"IMG":
             return self._registry[np.ndarray]["des"](payload, attachment)
        
        raise ValueError(f"Unknown attachment tag: {tag}")
