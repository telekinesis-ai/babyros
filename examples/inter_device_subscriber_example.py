import zenoh
import time

# 1. Configure to LISTEN on all interfaces (0.0.0.0) at port 7447
conf = zenoh.Config()
conf.insert_json5("listen/endpoints", '["tcp/0.0.0.0:7447"]')

print("Opening Zenoh session and listening on port 7447...")
session = zenoh.open(conf)

def listener(sample):
    print(f">> Received {sample.kind} ('{sample.key_expr}'): '{sample.payload.to_string()}'")

# 2. Declare the subscriber
sub = session.declare_subscriber("demo/example/test", listener)

print("Press Ctrl+C to stop...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    session.close()