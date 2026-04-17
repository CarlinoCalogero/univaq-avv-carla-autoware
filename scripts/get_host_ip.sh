#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# get_host_ip.sh
# Detects the Windows host IP as seen from WSL2 and exports CARLA_HOST.
#
# Usage:
#   source scripts/get_host_ip.sh
#   echo $CARLA_HOST   # -> e.g. 172.28.160.1
# ─────────────────────────────────────────────────────────────────────────────

HOST_IP=$(ip route show | grep -i default | awk '{ print $3 }' | head -1)

if [[ -z "$HOST_IP" ]]; then
    echo "[get_host_ip] ERROR: Could not determine Windows host IP."
    echo "  Try: cat /etc/resolv.conf | grep nameserver | awk '{print \$2}'"
    return 1 2>/dev/null || exit 1
fi

export CARLA_HOST="$HOST_IP"
echo "[get_host_ip] CARLA_HOST=$CARLA_HOST"
echo ""
echo "  Use with bridge_node.py:"
echo "    python3 wsl/bridge_node.py --ros-args -p carla_host:=$CARLA_HOST"
echo ""
echo "  Use with send_dummy_command.py:"
echo "    python3 wsl/send_dummy_command.py --carla-host $CARLA_HOST"
