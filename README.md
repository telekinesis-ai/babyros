![alt text](image.png)

<p align="center">
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
</p>

# BabyROS
**BabyROS** is a mini version of ROS built on top of the **Zenoh** protocol. It provides a familiar pub/sub/client/server architecture for robotics and distributed systems without the heavy overhead of a full ROS installation.

## Features
* **Powered by Zenoh:** Ultra-low latency and high-throughput communication.
* **Minimalist:** No complex middleware setup; just Python and Zenoh.
* **Familiar API:** Designed for developers transitioning from ROS/ROS2.

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/telekinesis-ai/babyros
```

Change directory
```bash
cd babyros
```

### 2. Environment Setup (Recommended)
We recommend using Miniconda or Anaconda to manage your environment:
```bash
conda create -n babyros python=3.11
```

Activate your environment:
```bash
conda activate babyros
```

You can deactivate your environment:
```bash
conda deactivate babyros
```

### 3. Installation
Install the package in editable mode for development:
```bash
pip install -e .
```

### (For Inter-Device Communication) Installation
Install the Zenoh router. Documentation available in: [Zenoh Docs](https://zenoh.io/docs/getting-started/installation/)

## Usage Example
To see BabyROS in action, you can run the provided example scripts.

### Publisher
Open a terminal and run:
```bash
python examples/publisher_example.py
```

When testing is done, kill terminal with `Ctrl+C`.

### Subscriber
In a second terminal (with the `babyros` environment active), run:
```bash
python examples/subscriber_example.py
```

When testing is done, kill terminal with `Ctrl+C`.

## Logging

BabyROS uses [loguru](https://github.com/Delgan/loguru) internally. By default, warnings and errors are always visible. DEBUG and INFO messages are hidden unless your application configures loguru to show them.

To enable babyros DEBUG/INFO logs without affecting other libraries:

```python
import sys
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="WARNING")                   # default for everything
logger.add(sys.stderr, level="DEBUG", filter="babyros")  # babyros only
```

## Open Issues
- Datatype information  
- Safety checks

## Zenoh Config Comparison Between Zenoh, BabyROS, and RMW Zenoh

| Key | BabyROS | Zenoh | RMW Zenoh |
|-----|--------|-----------|-----------|
| adminspace.enabled | False | False | True |
| connect.endpoints | [] | [] | ['tcp/localhost:7447'] |
| connect.exit_on_failure | None | None | — |
| connect.exit_on_failure.client | — | — | True |
| connect.exit_on_failure.peer | — | — | False |
| connect.exit_on_failure.router | — | — | False |
| connect.retry | None | None | — |
| connect.retry.period_increase_factor | — | — | 2.0 |
| connect.retry.period_init_ms | — | — | 1000 |
| connect.retry.period_max_ms | — | — | 4000 |
| connect.timeout_ms | None | None | — |
| connect.timeout_ms.client | — | — | 0 |
| connect.timeout_ms.peer | — | — | -1 |
| connect.timeout_ms.router | — | — | -1 |
| listen.endpoints | — | — | ['tcp/localhost:0'] |
| listen.endpoints.peer | ['tcp/[::]:0'] | ['tcp/[::]:0'] | — |
| listen.endpoints.router | ['tcp/[::]:7447'] | ['tcp/[::]:7447'] | — |
| listen.exit_on_failure | None | None | True |
| listen.retry | None | None | — |
| listen.retry.period_increase_factor | — | — | 2.0 |
| listen.retry.period_init_ms | — | — | 1000 |
| listen.retry.period_max_ms | — | — | 4000 |
| listen.timeout_ms | None | None | 0 |
| mode | None | None | peer |
| open.return_conditions.connect_scouted | None | None | True |
| open.return_conditions.declares | None | None | True |
| queries_default_timeout | None | None | 600000 |
| routing.interests.timeout | None | None | 10000 |
| routing.peer.mode | None | None | peer_to_peer |
| routing.router.peers_failover_brokering | None | None | True |
| scouting.delay | None | None | 500 |
| scouting.gossip.autoconnect | None | None | — |
| scouting.gossip.autoconnect.peer | — | — | ['router', 'peer'] |
| scouting.gossip.autoconnect.router | — | — | [] |
| scouting.gossip.autoconnect_strategy | None | None | — |
| scouting.gossip.autoconnect_strategy.peer.to_peer | — | — | greater-zid |
| scouting.gossip.autoconnect_strategy.peer.to_router | — | — | always |
| scouting.gossip.enabled | None | None | True |
| scouting.gossip.multihop | None | None | False |
| scouting.gossip.target | None | None | — |
| scouting.gossip.target.peer | — | — | ['router'] |
| scouting.gossip.target.router | — | — | ['router', 'peer'] |
| scouting.multicast.address | None | None | 224.0.0.224:7446 |
| scouting.multicast.autoconnect | None | None | — |
| scouting.multicast.autoconnect.client | — | — | ['router'] |
| scouting.multicast.autoconnect.peer | — | — | ['router', 'peer'] |
| scouting.multicast.autoconnect.router | — | — | [] |
| scouting.multicast.autoconnect_strategy | None | None | — |
| scouting.multicast.autoconnect_strategy.peer.to_peer | — | — | greater-zid |
| scouting.multicast.autoconnect_strategy.peer.to_router | — | — | always |
| scouting.multicast.enabled | None | None | False |
| scouting.multicast.interface | None | None | auto |
| scouting.multicast.listen | None | None | True |
| scouting.multicast.ttl | None | None | 1 |
| scouting.timeout | None | None | 3000 |
| timestamping.drop_future_timestamp | None | None | False |
| timestamping.enabled | None | None | — |
| timestamping.enabled.client | — | — | True |
| timestamping.enabled.peer | — | — | True |
| timestamping.enabled.router | — | — | True |
| transport.link.tls.close_link_on_expiration | None | None | False |
| transport.link.tls.enable_mtls | None | None | False |
| transport.link.tls.verify_name_on_connect | None | None | True |
| transport.link.tx.keep_alive | 4 | 4 | 2 |
| transport.link.tx.lease | 10000 | 10000 | 60000 |
| transport.link.tx.queue.congestion_control.block.wait_before_close | 5000000 | 5000000 | 60000000 |
| transport.shared_memory.enabled | True | True | False |
| transport.shared_memory.transport_optimization.message_size_threshold | 3072 | 3072 | 512 |
| transport.shared_memory.transport_optimization.pool_size | 16777216 | 16777216 | 50331648 |
| transport.unicast.accept_pending | 100 | 100 | 10000 |
| transport.unicast.accept_timeout | 10000 | 10000 | 60000 |
| transport.unicast.max_sessions | 1000 | 1000 | 10000 |
| transport.unicast.open_timeout | 10000 | 10000 | 60000 |

## License
Distributed under the Apache-2.0 License. See [LICENSE](LICENSE) for more information.