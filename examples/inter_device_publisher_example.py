import zenoh
import time

# 1. REPLACE THIS with Computer A's actual IP address
COMPUTER_A_IP = "10.137.125.163" 

conf = zenoh.Config()
conf.insert_json5("connect/endpoints", f'["tcp/{COMPUTER_A_IP}:7447"]')

print(f"Connecting to Computer A at {COMPUTER_A_IP}...")
session = zenoh.open(conf)

# 2. Declare the publisher
pub = session.declare_publisher("demo/example/test")

count = 0
try:
    while True:
        msg = f"Hello from Computer B! Iteration: {count}"
        print(f"Publishing: {msg}")
        pub.put(msg)
        count += 1
        time.sleep(2)
except KeyboardInterrupt:
    pass
finally:
    session.close()