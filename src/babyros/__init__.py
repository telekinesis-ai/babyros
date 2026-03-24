
import json
import zenoh
from babyros.node import SessionManager


import zenoh
from .node import SessionManager  # assuming configure is in babyros/__init__.py

def configure(
    adminspace_enabled=False,
    connect_endpoints=None,
    connect_exit_on_failure_client=None,
    connect_exit_on_failure_peer=None,
    connect_exit_on_failure_router=None,
    connect_retry_period_increase_factor=None,
    connect_retry_period_init_ms=None,
    connect_retry_period_max_ms=None,
    connect_timeout_ms_client=None,
    connect_timeout_ms_peer=None,
    connect_timeout_ms_router=None,
    listen_endpoints_peer=None,
    listen_endpoints_router=None,
    listen_exit_on_failure=None,
    listen_retry_period_increase_factor=None,
    listen_retry_period_init_ms=None,
    listen_retry_period_max_ms=None,
    listen_timeout_ms=None,
    mode=None,
    open_return_conditions_connect_scouted=None,
    open_return_conditions_declares=None,
    queries_default_timeout=None,
    routing_interests_timeout=None,
    routing_peer_mode=None,
    routing_router_peers_failover_brokering=None,
    scouting_delay=None,
    scouting_gossip_autoconnect_peer=None,
    scouting_gossip_autoconnect_router=None,
    scouting_gossip_autoconnect_strategy_peer_to_peer=None,
    scouting_gossip_autoconnect_strategy_peer_to_router=None,
    scouting_gossip_enabled=None,
    scouting_gossip_multihop=None,
    scouting_gossip_target_peer=None,
    scouting_gossip_target_router=None,
    scouting_multicast_address=None,
    scouting_multicast_autoconnect_client=None,
    scouting_multicast_autoconnect_peer=None,
    scouting_multicast_autoconnect_router=None,
    scouting_multicast_autoconnect_strategy_peer_to_peer=None,
    scouting_multicast_autoconnect_strategy_peer_to_router=None,
    scouting_multicast_enabled=None,
    scouting_multicast_interface=None,
    scouting_multicast_listen=None,
    scouting_multicast_ttl=None,
    scouting_timeout=None,
    timestamping_drop_future_timestamp=None,
    timestamping_enabled_client=None,
    timestamping_enabled_peer=None,
    timestamping_enabled_router=None,
    transport_link_tls_close_link_on_expiration=None,
    transport_link_tls_enable_mtls=None,
    transport_link_tls_verify_name_on_connect=None,
    transport_link_tx_batch_size=None,
    transport_link_tx_buffer_size=None,
    transport_link_tx_keep_alive=None,
    transport_link_tx_lease=None,
    transport_link_tx_queue_congestion_control_block_wait_before_close=None,
    transport_shared_memory_enabled=None,
    transport_shared_memory_message_size_threshold=None,
    transport_shared_memory_pool_size=None,
    transport_unicast_accept_pending=None,
    transport_unicast_accept_timeout=None,
    transport_unicast_max_sessions=None,
    transport_unicast_open_timeout=None
):
    """
    Configure the BabyROS Zenoh session.
    Only parameters passed as arguments will override the default.
    """
    config = zenoh.Config()

    # Always set some default important parameters
    config.insert_json5("transport/link/tx/batch_size", "1048576")  # 1MB
    config.insert_json5("transport/link/rx/buffer_size", "209715200")  # 200MB

    # Mapping kwargs to Zenoh keys
    mapping = {
        "adminspace_enabled": "adminspace/enabled",
        "connect_endpoints": "connect/endpoints",
        "connect_exit_on_failure_client": "connect/exit_on_failure/client",
        "connect_exit_on_failure_peer": "connect/exit_on_failure/peer",
        "connect_exit_on_failure_router": "connect/exit_on_failure/router",
        "connect_retry_period_increase_factor": "connect/retry/period_increase_factor",
        "connect_retry_period_init_ms": "connect/retry/period_init_ms",
        "connect_retry_period_max_ms": "connect/retry/period_max_ms",
        "connect_timeout_ms_client": "connect/timeout_ms/client",
        "connect_timeout_ms_peer": "connect/timeout_ms/peer",
        "connect_timeout_ms_router": "connect/timeout_ms/router",
        "listen_endpoints_peer": "listen/endpoints/peer",
        "listen_endpoints_router": "listen/endpoints/router",
        "listen_exit_on_failure": "listen/exit_on_failure",
        "listen_retry_period_increase_factor": "listen/retry/period_increase_factor",
        "listen_retry_period_init_ms": "listen/retry/period_init_ms",
        "listen_retry_period_max_ms": "listen/retry/period_max_ms",
        "listen_timeout_ms": "listen/timeout_ms",
        "mode": "mode",
        "open_return_conditions_connect_scouted": "open/return_conditions/connect_scouted",
        "open_return_conditions_declares": "open/return_conditions/declares",
        "queries_default_timeout": "queries_default_timeout",
        "routing_interests_timeout": "routing/interests/timeout",
        "routing_peer_mode": "routing/peer/mode",
        "routing_router_peers_failover_brokering": "routing/router/peers_failover_brokering",
        "scouting_delay": "scouting/delay",
        "scouting_gossip_autoconnect_peer": "scouting/gossip/autoconnect/peer",
        "scouting_gossip_autoconnect_router": "scouting/gossip/autoconnect/router",
        "scouting_gossip_autoconnect_strategy_peer_to_peer": "scouting/gossip/autoconnect_strategy/peer/to_peer",
        "scouting_gossip_autoconnect_strategy_peer_to_router": "scouting/gossip/autoconnect_strategy/peer/to_router",
        "scouting_gossip_enabled": "scouting/gossip/enabled",
        "scouting_gossip_multihop": "scouting/gossip/multihop",
        "scouting_gossip_target_peer": "scouting/gossip/target/peer",
        "scouting_gossip_target_router": "scouting/gossip/target/router",
        "scouting_multicast_address": "scouting/multicast/address",
        "scouting_multicast_autoconnect_client": "scouting/multicast/autoconnect/client",
        "scouting_multicast_autoconnect_peer": "scouting/multicast/autoconnect/peer",
        "scouting_multicast_autoconnect_router": "scouting/multicast/autoconnect/router",
        "scouting_multicast_autoconnect_strategy_peer_to_peer": "scouting/multicast/autoconnect_strategy/peer/to_peer",
        "scouting_multicast_autoconnect_strategy_peer_to_router": "scouting/multicast/autoconnect_strategy/peer/to_router",
        "scouting_multicast_enabled": "scouting/multicast/enabled",
        "scouting_multicast_interface": "scouting/multicast/interface",
        "scouting_multicast_listen": "scouting/multicast/listen",
        "scouting_multicast_ttl": "scouting/multicast/ttl",
        "scouting_timeout": "scouting/timeout",
        "timestamping_drop_future_timestamp": "timestamping/drop_future_timestamp",
        "timestamping_enabled_client": "timestamping/enabled/client",
        "timestamping_enabled_peer": "timestamping/enabled/peer",
        "timestamping_enabled_router": "timestamping/enabled/router",
        "transport_link_tls_close_link_on_expiration": "transport/link/tls/close_link_on_expiration",
        "transport_link_tls_enable_mtls": "transport/link/tls/enable_mtls",
        "transport_link_tls_verify_name_on_connect": "transport/link/tls/verify_name_on_connect",
        "transport_link_tx_keep_alive": "transport/link/tx/keep_alive",
        "transport_link_tx_lease": "transport/link/tx/lease",
        "transport_link_tx_queue_congestion_control_block_wait_before_close": "transport/link/tx/queue/congestion_control/block/wait_before_close",
        "transport_shared_memory_enabled": "transport/shared_memory/enabled",
        "transport_shared_memory_message_size_threshold": "transport/shared_memory/transport_optimization/message_size_threshold",
        "transport_shared_memory_pool_size": "transport/shared_memory/transport_optimization/pool_size",
        "transport_unicast_accept_pending": "transport/unicast/accept_pending",
        "transport_unicast_accept_timeout": "transport/unicast/accept_timeout",
        "transport_unicast_max_sessions": "transport/unicast/max_sessions",
        "transport_unicast_open_timeout": "transport/unicast/open_timeout",
    }

    # Apply user parameters
    for arg, key in mapping.items():
        value = locals()[arg]
        if value is not None:
            json5_value = json.dumps(value)
            config.insert_json5(key, json5_value)

    # Set to SessionManager
    SessionManager.set_session_config(config)