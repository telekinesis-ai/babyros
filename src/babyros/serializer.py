"""
Creates a Zenoh-compatible payload and attachment from a Python object.

Wire format (dispatched on the 4-byte tag at the start of the attachment):

  JSON  - a dict with no numpy arrays and no telekinesis datatypes.
          payload = UTF-8 JSON, attachment = b"JSON".
  NDAR  - a bare np.ndarray of any shape/dtype. payload = raw array bytes,
          attachment = b"NDAR" + JSON metadata {shape, dtype}.
  NDDC  - a dict containing one or more numpy arrays (possibly nested).
          payload = every array's raw bytes concatenated in order,
          attachment = b"NDDC" + JSON manifest describing the structure and,
          for each array, its {shape, dtype, offset, nbytes} slice of payload.
          Arrays are replaced in the structure by {"__ndarray__": <index>}.
  TDDC  - a dict whose keys are strings and whose values are all telekinesis
          datatypes. payload = Arrow IPC stream from serializer.serialize
          (keyed by the dict keys), attachment = b"TDDC".
  TDOB  - a single telekinesis datatype. payload = Arrow IPC stream,
          attachment = b"TDOB".
  TDSQ  - a non-empty list/tuple of telekinesis datatypes. payload = Arrow
          IPC stream, attachment = b"TDSQ".

Only numpy arrays whose bytes round-trip through np.frombuffer are supported
for NDAR/NDDC: plain numeric dtypes in native byte order. Object arrays,
structured/record dtypes, and non-native endianness are not preserved and
should not be sent.
"""

import json
import numpy as np
from typing import Any, Callable, Dict, List, Tuple

from loguru import logger

try:
    from telekinesis import datatypes
    from telekinesis.datatypes import serializer
except ImportError:
    logger.warning(
        "'telekinesis-datatypes' not found; telekinesis datatype serialization "
        "(TDDC/TDOB/TDSQ) is unavailable — only plain JSON dicts and numpy arrays "
        "(NDAR/NDDC) can be sent. 'telekinesis-datatypes' will be released soon."
    )
    serializer = None
    # Datatype support is off, so stub the namespace with an unmatchable
    # BaseDataType. The encode predicates then always return False and datatype
    # payloads fall through to the "No serializer" TypeError, while JSON + numpy
    # keep working and babyros imports with no datatypes package installed.
    import types

    datatypes = types.ModuleType("datatypes")

    class _UnavailableDataType:
        pass

    datatypes.BaseDataType = _UnavailableDataType


class ZenohCodec:
    """Encodes and decodes Python objects for Zenoh transport."""

    def __init__(self, compression: str | None = "lz4"):
        """Create a codec.

        Args:
            compression: Arrow IPC-level codec passed to
                ``telekinesis.datatypes.serializer.serialize`` for every
                datatype payload (TDDC/TDOB/TDSQ). ``"lz4"`` (default) or
                ``"zstd"`` shrink the payload at CPU cost — pick these for
                bandwidth-limited links. ``None`` disables IPC compression,
                which is faster end-to-end on localhost / fast LANs. Decoding
                needs no matching setting; the reader detects the codec from
                the stream. Numpy NDAR/NDDC payloads are always sent
                uncompressed.
        """
        self._compression = compression
        # Encode dispatch: ordered (predicate, serializer) pairs; first match
        # wins. Order matters — the telekinesis-datatype checks must come
        # before the generic dict / numpy-container checks so a dict of
        # datatypes is not misrouted to JSON/NDDC.
        self._encoders: List[
            Tuple[Callable[[Any], bool], Callable[[Any], Tuple[bytes, bytes]]]
        ] = [
            (self._is_datatype_dict, self._serialize_datatype_dict),
            (
                lambda d: isinstance(d, datatypes.BaseDataType),
                self._serialize_datatype_object,
            ),
            (self._is_datatype_sequence, self._serialize_datatype_sequence),
            (lambda d: isinstance(d, np.ndarray), self._serialize_array),
            (
                lambda d: isinstance(d, dict) and self._contains_ndarray(d),
                self._serialize_container,
            ),
            (lambda d: isinstance(d, dict), self._serialize_json),
        ]
        # Decode dispatch: full 4-byte tag -> deserializer(payload, attachment).
        self._decoders: Dict[bytes, Callable[[bytes, bytes], Any]] = {
            b"JSON": self._deserialize_json,  # plain dict
            b"NDAR": self._deserialize_array,  # bare ndarray
            b"NDDC": self._deserialize_container,  # dict with arrays
            b"TDDC": self._deserialize_datatype_dict,  # dict of datatypes
            b"TDOB": self._deserialize_datatype_object,  # single datatype
            b"TDSQ": self._deserialize_datatype_sequence,  # sequence of datatypes
        }

    def encode(self, data: Any) -> Tuple[bytes, bytes]:
        """Returns (payload, attachment)."""
        for predicate, serialize in self._encoders:
            if predicate(data):
                return serialize(data)
        raise TypeError(f"No serializer for {type(data)}")

    def decode(self, payload: bytes, attachment: bytes) -> Any:
        """Decode a Zenoh payload and attachment into a Python object."""
        deserializer = self._decoders.get(attachment[:4])
        if deserializer is None:
            raise ValueError(f"Unknown attachment tag: {attachment[:4]}")
        return deserializer(payload, attachment)

    # -- telekinesis datatypes (TDDC / TDOB / TDSQ) -----------------------

    @staticmethod
    def _is_datatype_dict(data: Any) -> bool:
        """True for a non-empty dict with str keys and all-datatype values."""
        return (
            isinstance(data, dict)
            and bool(data)
            and all(isinstance(k, str) for k in data)
            and all(isinstance(v, datatypes.BaseDataType) for v in data.values())
        )

    @staticmethod
    def _is_datatype_sequence(data: Any) -> bool:
        """True for a non-empty list/tuple whose items are all datatypes."""
        return (
            isinstance(data, (list, tuple))
            and bool(data)
            and all(isinstance(x, datatypes.BaseDataType) for x in data)
        )

    def _serialize_datatype_dict(self, data: dict) -> Tuple[bytes, bytes]:
        payload = serializer.serialize(
            *data.values(), names=list(data.keys()), compression=self._compression
        )
        return payload, b"TDDC"

    def _deserialize_datatype_dict(self, payload: bytes, attachment: bytes) -> dict:
        return serializer.deserialize(payload)

    def _serialize_datatype_object(self, data: Any) -> Tuple[bytes, bytes]:
        payload = serializer.serialize(data, compression=self._compression)
        return payload, b"TDOB"

    def _deserialize_datatype_object(self, payload: bytes, attachment: bytes) -> Any:
        return next(iter(serializer.deserialize(payload).values()))

    def _serialize_datatype_sequence(self, data) -> Tuple[bytes, bytes]:
        payload = serializer.serialize(*data, compression=self._compression)
        return payload, b"TDSQ"

    def _deserialize_datatype_sequence(self, payload: bytes, attachment: bytes) -> list:
        return list(serializer.deserialize(payload).values())

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

    # -- plain dict (JSON) ------------------------------------------------

    def _serialize_json(self, data: dict) -> Tuple[bytes, bytes]:
        payload = json.dumps(data, default=self._json_default).encode("utf-8")
        return payload, b"JSON"

    def _deserialize_json(self, payload: bytes, attachment: bytes) -> dict:
        return json.loads(payload.decode("utf-8"))

    # -- bare ndarray (NDAR) ----------------------------------------------

    def _serialize_array(self, arr: np.ndarray) -> Tuple[bytes, bytes]:
        arr = np.ascontiguousarray(arr)
        meta = {"shape": list(arr.shape), "dtype": str(arr.dtype)}
        attachment = b"NDAR" + json.dumps(meta).encode("utf-8")
        return arr.tobytes(), attachment

    def _deserialize_array(self, payload: bytes, attachment: bytes) -> np.ndarray:
        meta = json.loads(attachment[4:].decode("utf-8"))
        return np.frombuffer(payload, dtype=meta["dtype"]).reshape(meta["shape"])

    # -- dict containing ndarrays (NDDC) ----------------------------------

    def _serialize_container(self, data: dict) -> Tuple[bytes, bytes]:
        arrays: List[np.ndarray] = []
        structure = self._extract_arrays(data, arrays)

        chunks: List[bytes] = []
        manifest: List[dict] = []
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
        attachment = b"NDDC" + json.dumps(meta, default=self._json_default).encode(
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
