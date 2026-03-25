import json
import struct
import numpy as np
import zenoh
from typing import Any, Dict, Tuple

# --- SERIALIZERS ---

def serialize_json(data: Dict[str, Any]) -> Tuple[bytes, bytes]:
    try:
        payload = json.dumps(data).encode("utf-8")
        attachment = b"JSON"  # type tag
        return payload, attachment
    except Exception as e:
        raise ValueError(f"Failed to serialize JSON: {e}")


def serialize_image(image: np.ndarray) -> Tuple[bytes, bytes]:
    """
    Serialize 3D numpy image array to bytes with a self-describing attachment.
    Attachment format: b"IMG" + 3 ints (H, W, C) + 10-byte dtype
    """
    try:
        if image.ndim != 3:
            raise ValueError("Expected 3D image array (H, W, C)")
        h, w, c = image.shape
        dtype_bytes = str(image.dtype).encode("utf-8").ljust(10, b"\0")
        attachment = b"IMG" + struct.pack("iii", h, w, c) + dtype_bytes
        payload = image.tobytes()
        return payload, attachment
    except Exception as e:
        raise ValueError(f"Failed to serialize image: {e}")


def serialize_bytes(data: bytes) -> Tuple[bytes, bytes]:
    try:
        return data, b"RAW"
    except Exception as e:
        raise ValueError(f"Failed to serialize bytes: {e}")


# --- DESERIALIZERS ---

def deserialize_json(payload: bytes) -> Dict[str, Any]:
    try:
        return json.loads(payload.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Failed to deserialize JSON: {e}")


def deserialize_image(payload: bytes, attachment: bytes) -> np.ndarray:
    """
    Deserialize image payload using self-describing attachment.
    Expects attachment format: b"IMG" + 3 ints + 10-byte dtype
    """
    try:
        if len(attachment) < 3 + 12 + 10:
            raise ValueError("Invalid attachment for image")
        if attachment[:3] != b"IMG":
            raise ValueError("Attachment is not an image")

        h, w, c = struct.unpack("iii", attachment[3:15])
        dtype_str = attachment[15:25].rstrip(b"\0").decode("utf-8")
        return np.frombuffer(payload, dtype=dtype_str).reshape((h, w, c))
    except Exception as e:
        raise ValueError(f"Failed to deserialize image: {e}")


def deserialize_bytes(payload: bytes) -> bytes:
    try:
        return payload
    except Exception as e:
        raise ValueError(f"Failed to deserialize bytes: {e}")