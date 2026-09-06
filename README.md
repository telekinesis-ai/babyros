![alt text](image.png)

<p align="center">
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
</p>

# BabyROS
**BabyROS** is a mini version of ROS built on top of the **Zenoh** protocol. It provides a familiar pub/sub/client/server architecture for robotics and distributed systems without the heavy overhead of a full ROS installation.

* **Powered by Zenoh:** Ultra-low latency and high-throughput communication.
* **Minimalist:** No complex middleware setup; just Python and Zenoh.
* **Familiar API:** Designed for developers transitioning from ROS/ROS2.

Open source under [Apache 2.0](LICENSE).

Full documentation: [docs.telekinesis.ai](https://docs.telekinesis.ai/).

For Zenoh config comparison between Zenoh, BabyROS, and RMW Zenoh information: [Config](/docs/zenoh_config_differences.md).


## Installation

For a complete walkthrough, refer to the [Installation guide.](https://docs.telekinesis.ai/getting-started/advanced-installation/install-babyros.html).

### For Inter-Device Communication
Install the Zenoh router. Documentation available in: [Zenoh Docs](https://zenoh.io/docs/getting-started/installation/)

## Quickstart

```bash
git clone https://github.com/telekinesis-ai/babyros.git
cd babyros
```

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

## Open Issues
- Datatype information  
- Safety checks


## Join The Telekinesis Community

Telekinesis Agentic Skill Library is just the beginning. We're building a community of contributors who grow the Physical AI Skill ecosystem—researchers, hobbyists, and engineers alike. If you have a Skill, we want to see it. Release it, let others use and improve it, and watch it deploy in real-world systems.

[Join our Discord community](https://discord.gg/S5v8bYAnc6) to connect, share, and build together.

## Documentation

- Full documentation: [docs.telekinesis.ai](https://docs.telekinesis.ai/)

## Citation

```bibtex
@software{telekinesis_ai,
  author = {Telekinesis GmbH},
  title  = {BabyROS},
  year   = {2026},
  url    = {https://github.com/telekinesis-ai/babyros},
  note   = {Apache-2.0}
}
```

## Support

- [GitHub Issues](https://github.com/telekinesis-ai/babyros/issues) — Report bugs or request features
- [Discord](https://discord.gg/S5v8bYAnc6) — Community support and discussions
