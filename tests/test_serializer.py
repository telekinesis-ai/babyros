import importlib.util
from pathlib import Path
import struct
import unittest

import numpy as np


def load_serializer():
    path = Path(__file__).resolve().parents[1] / "src" / "babyros" / "serializer.py"
    spec = importlib.util.spec_from_file_location("babyros_serializer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


serializer = load_serializer()


class ZenohCodecArrayTests(unittest.TestCase):
    def setUp(self):
        self.codec = serializer.ZenohCodec()

    def assert_array_round_trips(self, arr):
        payload, attachment = self.codec.encode(arr)
        decoded = self.codec.decode(payload, attachment)

        self.assertEqual(decoded.shape, arr.shape)
        self.assertEqual(decoded.dtype, arr.dtype)
        np.testing.assert_array_equal(decoded, arr)

    def test_round_trips_grayscale_image(self):
        self.assert_array_round_trips(np.arange(12, dtype=np.uint8).reshape(3, 4))

    def test_round_trips_color_image(self):
        self.assert_array_round_trips(np.arange(24, dtype=np.uint16).reshape(2, 4, 3))

    def test_round_trips_non_contiguous_array(self):
        arr = np.arange(48, dtype=np.float32).reshape(4, 4, 3)[:, ::2, :]
        self.assertFalse(arr.flags.c_contiguous)
        self.assert_array_round_trips(arr)

    def test_round_trips_dtype_with_long_name(self):
        arr = np.array(np.arange(6), dtype="datetime64[ns]").reshape(2, 3)
        self.assert_array_round_trips(arr)

    def test_rejects_object_dtype(self):
        arr = np.array([{"unsafe": "pointer"}], dtype=object)

        with self.assertRaises(TypeError):
            self.codec.encode(arr)

    def test_rejects_payload_that_does_not_match_metadata(self):
        arr = np.arange(12, dtype=np.uint8).reshape(3, 4)
        payload, attachment = self.codec.encode(arr)

        with self.assertRaises(ValueError):
            self.codec.decode(payload[:-1], attachment)

    def test_decodes_legacy_image_attachment(self):
        arr = np.arange(24, dtype=np.uint8).reshape(2, 4, 3)
        attachment = b"IMG" + struct.pack("iii", 2, 4, 3) + b"uint8".ljust(10, b"\0")

        decoded = self.codec.decode(arr.tobytes(), attachment)

        self.assertEqual(decoded.shape, arr.shape)
        self.assertEqual(decoded.dtype, arr.dtype)
        np.testing.assert_array_equal(decoded, arr)


if __name__ == "__main__":
    unittest.main()
