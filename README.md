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

## Usage Example
To see BabyROS in action, you can run the provided example scripts.

### Publisher
Open a terminal and run:
```bash
python examples/publisher_example.py
```

Expected output:
```bash
Publishing on topic 'hello': 'Hello world!'
```

Kill terminal with `Ctrl+C`.

### Subscriber
In a second terminal (with the `babyros` environment active), run:
```bash
python examples/subscriber_example.py
```

Expected output:
```bash
Received from topic 'hello': 'Hello world!'
```

Kill terminal with `Ctrl+C`.

## Open Issues
- Datatype information  
- Safety checks

## License
Distributed under the Apache-2.0 License. See [LICENSE](LICENSE) for more information.