"""
Creates a Zenoh-compatible payload and attachment from a Python object.

Wire format (dispatched on the 4-byte tag at the start of the attachment):

  JSON  - a dict with no numpy arrays. payload = UTF-8 JSON, attachment = b"JSON".
  NDAR  - a bare np.ndarray of any shape/dtype. payload = raw array bytes,
          attachment = b"NDAR" + JSON metadata {shape, dtype}.
  NDCT  - a dict containing one or more numpy arrays (possibly nested).
          payload = every array's raw bytes concatenated in order,
          attachment = b"NDCT" + JSON manifest describing the structure and,
          for each array, its {shape, dtype, offset, nbytes} slice of payload.
          Arrays are replaced in the structure by {"__ndarray__": <index>}.

Only arrays whose bytes round-trip through np.frombuffer are supported: plain
numeric dtypes in native byte order. Object arrays, structured/record dtypes,
and non-native endianness are not preserved and should not be sent.
"""

import json
import numpy as np
from typing import Any, Dict, Callable


class ZenohCodec:
    def __init__(self):
        # Encode dispatch: Python type -> serializer returning (payload, attachment).
        # A dict picks JSON or NDCT at serialize time depending on its contents.
        self._registry: Dict[Any, Callable] = {
            dict: self._serialize_dict,
            np.ndarray: self._serialize_array,
        }
        # Decode dispatch: full 4-byte tag -> deserializer(payload, attachment).
        self._decoders: Dict[bytes, Callable] = {
            b"JSON": self._deserialize_json,  # plain dict
            b"NDAR": self._deserialize_array,  # bare ndarray
            b"NDCT": self._deserialize_container,  # dict with arrays
        }

    def encode(self, data: Any) -> tuple[bytes, bytes]:
        """Returns (payload, attachment)."""
        serializer = self._registry.get(type(data))
        if serializer is None:
            raise TypeError(f"No serializer for {type(data)}")
        return serializer(data)

    def decode(self, payload: bytes, attachment: bytes) -> Any:
        """Decode a Zenoh payload and attachment into a Python object."""
        deserializer = self._decoders.get(attachment[:4])
        if deserializer is None:
            raise ValueError(f"Unknown attachment tag: {attachment[:4]}")
        return deserializer(payload, attachment)

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _json_default(obj: Any) -> Any:
        """Fallback for numpy scalars (np.float64, np.int64, ...) in the JSON path."""
        if isinstance(obj, np.generic):
            return obj.item()
        raise TypeError(
            f"Object of type {obj.__class__.__name__} is not JSON serializable"
        )

    @classmethod
    def _contains_ndarray(cls, obj: Any) -> bool:
        """True if ``obj`` is, or nests, a numpy array."""
        if isinstance(obj, np.ndarray):
            return True
        if isinstance(obj, dict):
            return any(cls._contains_ndarray(v) for v in obj.values())
        if isinstance(obj, (list, tuple)):
            return any(cls._contains_ndarray(v) for v in obj)
        return False

    # -- dict: plain JSON or, when it holds arrays, the NDCT container ----

    def _serialize_dict(self, data: dict) -> tuple[bytes, bytes]:
        if self._contains_ndarray(data):
            return self._serialize_container(data)
        payload = json.dumps(data, default=self._json_default).encode("utf-8")
        return payload, b"JSON"

    def _deserialize_json(self, payload: bytes, attachment: bytes) -> dict:
        return json.loads(payload.decode("utf-8"))

    # -- bare ndarray -----------------------------------------------------

    def _serialize_array(self, arr: np.ndarray) -> tuple[bytes, bytes]:
        arr = np.ascontiguousarray(arr)
        meta = {"shape": list(arr.shape), "dtype": str(arr.dtype)}
        attachment = b"NDAR" + json.dumps(meta).encode("utf-8")
        return arr.tobytes(), attachment

    def _deserialize_array(self, payload: bytes, attachment: bytes) -> np.ndarray:
        meta = json.loads(attachment[4:].decode("utf-8"))
        return np.frombuffer(payload, dtype=meta["dtype"]).reshape(meta["shape"])

    # -- dict containing ndarrays (NDCT) ---------------------------------

    def _serialize_container(self, data: dict) -> tuple[bytes, bytes]:
        arrays: list[np.ndarray] = []
        structure = self._extract_arrays(data, arrays)

        chunks: list[bytes] = []
        manifest: list[dict] = []
        offset = 0
        for arr in arrays:
            arr = np.ascontiguousarray(arr)
            raw = arr.tobytes()
            chunks.append(raw)
            manifest.append(
                {
                    "shape": list(arr.shape),
                    "dtype": str(arr.dtype),
                    "offset": offset,
                    "nbytes": len(raw),
                }
            )
            offset += len(raw)

        meta = {"structure": structure, "arrays": manifest}
        attachment = b"NDCT" + json.dumps(meta, default=self._json_default).encode(
            "utf-8"
        )
        return b"".join(chunks), attachment

    def _deserialize_container(self, payload: bytes, attachment: bytes) -> dict:
        meta = json.loads(attachment[4:].decode("utf-8"))
        arrays = [
            np.frombuffer(
                payload[a["offset"] : a["offset"] + a["nbytes"]], dtype=a["dtype"]
            ).reshape(a["shape"])
            for a in meta["arrays"]
        ]
        return self._restore_arrays(meta["structure"], arrays)

    def _extract_arrays(self, obj: Any, arrays: list) -> Any:
        """Return a JSON-safe copy of ``obj`` with arrays replaced by markers."""
        if isinstance(obj, np.ndarray):
            arrays.append(obj)
            return {"__ndarray__": len(arrays) - 1}
        if isinstance(obj, dict):
            return {k: self._extract_arrays(v, arrays) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._extract_arrays(v, arrays) for v in obj]
        return obj

    def _restore_arrays(self, obj: Any, arrays: list) -> Any:
        """Inverse of :meth:`_extract_arrays`."""
        if isinstance(obj, dict):
            if "__ndarray__" in obj and len(obj) == 1:
                return arrays[obj["__ndarray__"]]
            return {k: self._restore_arrays(v, arrays) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._restore_arrays(v, arrays) for v in obj]
        return obj
