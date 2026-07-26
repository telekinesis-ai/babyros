"""
Smoke test that exercises every third-party API surface used by babyros.
Run this after installing a candidate minimum version to verify compatibility.
"""

import sys
import time
import importlib.metadata
import numpy as np
import loguru
import zenoh


def check_numpy():
    # Exercise every numpy API used by serializer.ZenohCodec:
    # arr.shape, str(arr.dtype), arr.tobytes(), np.frombuffer(), .reshape()
    arr: np.ndarray = np.arange(2 * 3 * 4, dtype=np.uint8).reshape((2, 3, 4))
    h, w, c = arr.shape
    dtype_str = str(arr.dtype)
    raw = arr.tobytes()
    restored = np.frombuffer(raw, dtype=dtype_str).reshape((h, w, c))
    assert restored.shape == (h, w, c), "reshape roundtrip failed"
    assert restored.tobytes() == raw, "frombuffer roundtrip failed"
    print(f"  numpy {np.__version__} OK")


def check_loguru():
    loguru.logger.debug("debug")
    loguru.logger.info("info")
    loguru.logger.warning("warning")
    loguru.logger.error("error")
    print(f"  loguru {loguru.__version__} OK")


def check_zenoh():
    # Config.insert_json5 — used by babyros.configure()
    cfg = zenoh.Config()
    cfg.insert_json5("transport/link/tx/batch_size", "1048576")
    cfg.insert_json5("transport/link/rx/buffer_size", "209715200")

    session = zenoh.open(cfg)

    # Publisher
    pub = session.declare_publisher("babyros/test/pub")
    pub.put(b"hello")
    pub.undeclare()

    # Subscriber with default handler — checks handler.recv() and handler.try_recv()
    sub = session.declare_subscriber("babyros/test/sub")
    assert hasattr(sub.handler, "recv"), "handler.recv() not available — zenoh too old"
    assert hasattr(sub.handler, "try_recv"), "handler.try_recv() not available"
    sub.undeclare()

    # RingChannel and FifoChannel — used by Subscriber for keep_last / keep_all
    ring = zenoh.handlers.RingChannel(4)
    sub_ring = session.declare_subscriber("babyros/test/ring", ring)
    assert hasattr(sub_ring.handler, "recv"), "RingChannel handler.recv() not available"
    sub_ring.undeclare()

    fifo = zenoh.handlers.FifoChannel(4)
    sub_fifo = session.declare_subscriber("babyros/test/fifo", fifo)
    assert hasattr(sub_fifo.handler, "recv"), "FifoChannel handler.recv() not available"
    sub_fifo.undeclare()

    # Querier with timeout kwarg — used by Client
    querier = session.declare_querier("babyros/test/query", timeout=1.0)
    querier.undeclare()

    # Queryable + Server-side query API — used by Server._handle_request.
    # The handler runs in a zenoh-managed thread, so it stashes any API error
    # into handler_errors for the main thread to assert on.
    handler_errors = []

    def _handler(query):
        try:
            # query.selector, query.payload.to_bytes(), query.attachment.to_bytes()
            _ = query.selector
            if query.payload is not None:
                _ = query.payload.to_bytes()
            if query.attachment is not None:
                _ = query.attachment.to_bytes()
            # query.reply() with attachment kwarg
            query.reply("babyros/test/queryable", b"pong", attachment=b"\x00")
        except Exception as e:  # noqa: BLE001
            handler_errors.append(e)
            query.reply_err(str(e).encode("utf-8"))

    queryable = session.declare_queryable("babyros/test/queryable", _handler)

    # querier.get() with payload + attachment kwargs — used by Client.request
    querier2 = session.declare_querier("babyros/test/queryable", timeout=1.0)
    replies = list(querier2.get(payload=b"ping", attachment=b"\x01"))
    assert replies, "expected at least one reply from queryable"
    assert not handler_errors, f"server-side query API failed: {handler_errors[0]}"
    reply = replies[0]
    assert hasattr(reply, "ok"), "reply.ok not available"
    assert hasattr(reply, "err"), "reply.err not available"
    if reply.ok is not None:
        ok_bytes = reply.ok.payload.to_bytes()
        assert isinstance(ok_bytes, (bytes, bytearray)), (
            "reply.ok.payload.to_bytes() did not return bytes"
        )
    if reply.err is not None:
        err_str = reply.err.payload.to_string()
        assert isinstance(err_str, str), (
            "reply.err.payload.to_string() did not return str"
        )
    querier2.undeclare()

    # reply_err path — a handler that always errors, verifying reply.err carries it
    def _err_handler(query):
        query.reply_err(b"boom")

    err_queryable = session.declare_queryable(
        "babyros/test/queryable_err", _err_handler
    )
    err_querier = session.declare_querier("babyros/test/queryable_err", timeout=1.0)
    err_replies = list(err_querier.get())
    if err_replies and err_replies[0].err is not None:
        assert err_replies[0].err.payload.to_string() == "boom", (
            "reply_err payload roundtrip failed"
        )
    err_querier.undeclare()
    err_queryable.undeclare()
    queryable.undeclare()

    # sample.payload.to_bytes() and sample.attachment.to_bytes()
    # verified via a live put/subscriber pair
    sub2 = session.declare_subscriber("babyros/test/payload")
    pub2 = session.declare_publisher("babyros/test/payload")
    pub2.put(b"\x01\x02\x03", attachment=b"\xff")
    time.sleep(0.05)
    sample = sub2.handler.try_recv()
    if sample is not None:
        payload_bytes = sample.payload.to_bytes()
        assert isinstance(payload_bytes, (bytes, bytearray)), (
            "payload.to_bytes() did not return bytes"
        )
        if sample.attachment is not None:
            att_bytes = sample.attachment.to_bytes()
            assert isinstance(att_bytes, (bytes, bytearray)), (
                "attachment.to_bytes() did not return bytes"
            )
    pub2.undeclare()
    sub2.undeclare()

    session.close()
    print(f"  eclipse-zenoh {importlib.metadata.version('eclipse-zenoh')} OK")


if __name__ == "__main__":
    print(f"Python {sys.version}")
    try:
        check_numpy()
        check_loguru()
        check_zenoh()
        print("\nAll checks passed.")
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
