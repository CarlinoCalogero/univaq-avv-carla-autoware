#!/bin/bash
# Lowers the NDT scan matcher score threshold from 2.3 to 1.8.
# Run this ONCE inside the Docker container before launching Autoware.
# Re-run if the container is recreated (changes are lost on container reset).

set -e

NDT_CONFIG=$(find /workspace/install -name "ndt_scan_matcher.param.yaml" 2>/dev/null | head -1)

if [ -z "$NDT_CONFIG" ]; then
    echo "[ERROR] ndt_scan_matcher.param.yaml not found under /workspace/install."
    echo "        Make sure you are running this inside the Autoware Docker container"
    echo "        and the workspace has been built (source install/setup.bash)."
    exit 1
fi

echo "[INFO] Found NDT config: $NDT_CONFIG"

# Backup on first run only
BACKUP="${NDT_CONFIG}.orig"
if [ ! -f "$BACKUP" ]; then
    cp "$NDT_CONFIG" "$BACKUP"
    echo "[INFO] Backup saved to: $BACKUP"
else
    echo "[INFO] Backup already exists: $BACKUP (restoring for clean re-patch)"
    cp "$BACKUP" "$NDT_CONFIG"
fi

echo ""
echo "[INFO] Raw lines containing '2.3' before patch:"
grep -n "2\.3" "$NDT_CONFIG" || echo "  (none found)"

# Target every YAML value line of the form "  some_key: 2.3"
# This covers all threshold parameters regardless of their key name.
sed -i -E 's/^(\s+[a-zA-Z_]+\s*:\s*)2\.3(\s*(#.*)?$)/\11.8\2/' "$NDT_CONFIG"

echo ""
echo "[INFO] Raw lines containing '1.8' after patch (should include the former 2.3 lines):"
grep -n "1\.8" "$NDT_CONFIG" || echo "  (none found — patch may not have matched; see file below)"

# Safety check: if 2.3 still appears as a value, report it
REMAINING=$(grep -cE "^\s+[a-zA-Z_]+\s*:\s*2\.3" "$NDT_CONFIG" 2>/dev/null || true)
if [ "$REMAINING" -gt 0 ]; then
    echo ""
    echo "[WARN] $REMAINING line(s) with value 2.3 remain. Showing them:"
    grep -nE "^\s+[a-zA-Z_]+\s*:\s*2\.3" "$NDT_CONFIG"
    echo "       Edit those lines manually and set the value to 1.8."
else
    echo ""
    echo "[OK] All 2.3 threshold values patched to 1.8."
fi

echo "     Restart Autoware for the change to take effect."
