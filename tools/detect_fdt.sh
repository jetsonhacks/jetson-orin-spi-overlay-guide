#!/bin/bash
# FDT Detection Utility for Jetson Orin
# Detects and displays the correct base device tree file

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}FDT Detection Utility${NC}"
echo ""

# Method 1: Find DTB files in /boot/dtb/
echo -e "${BLUE}Checking /boot/dtb/ for device tree files...${NC}"
DTB_FILES=$(ls /boot/dtb/kernel_tegra*.dtb 2>/dev/null || true)

if [ -z "$DTB_FILES" ]; then
    echo -e "${RED}✗ No DTB files found in /boot/dtb/${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found DTB file(s):${NC}"
echo "$DTB_FILES" | while read -r file; do
    echo "  - $file"
done
echo ""

# Method 2: Get first (primary) DTB
FDT_FILE=$(echo "$DTB_FILES" | head -n1)
echo -e "${BLUE}Primary FDT:${NC}"
echo "  $FDT_FILE"
echo ""

# Method 3: Check device tree compatible string
echo -e "${BLUE}Device Tree Compatible String:${NC}"
if [ -f /proc/device-tree/compatible ]; then
    cat /proc/device-tree/compatible | tr '\0' '\n' | while read -r line; do
        echo "  - $line"
    done
else
    echo -e "${YELLOW}⚠ /proc/device-tree/compatible not found${NC}"
fi
echo ""

# Method 4: Check model
echo -e "${BLUE}Hardware Model:${NC}"
if [ -f /proc/device-tree/model ]; then
    cat /proc/device-tree/model
    echo ""
else
    echo -e "${YELLOW}⚠ /proc/device-tree/model not found${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Recommended FDT for bootloader configuration:            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  FDT $FDT_FILE"
echo ""
echo "Add this line to your boot entry in /boot/extlinux/extlinux.conf:"
echo ""
echo -e "${BLUE}LABEL MyConfig${NC}"
echo -e "${BLUE}    MENU LABEL My Custom Configuration${NC}"
echo -e "${BLUE}    LINUX /boot/Image${NC}"
echo -e "${GREEN}    FDT $FDT_FILE${NC}  ${YELLOW}← Add this line${NC}"
echo -e "${BLUE}    INITRD /boot/initrd${NC}"
echo -e "${BLUE}    APPEND \${cbootargs} ...${NC}"
echo -e "${BLUE}    OVERLAYS /boot/my-overlay.dtbo${NC}"
echo ""

# Output for scripting
if [ "$1" == "--quiet" ] || [ "$1" == "-q" ]; then
    echo "$FDT_FILE"
    exit 0
fi

exit 0
