#!/bin/bash
# Compile and install device tree overlay
# Usage: sudo ./compile_install_dtbo.sh <file.dts>

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Please run as root${NC}"
    echo -e "${BLUE}Usage: sudo $0 <file.dts>${NC}"
    exit 1
fi

# Check if DTS file provided
if [ $# -eq 0 ]; then
    echo -e "${RED}✗ No DTS file specified${NC}"
    echo -e "${BLUE}Usage: sudo $0 <file.dts>${NC}"
    exit 1
fi

DTS_FILE="$1"

# Check if file exists
if [ ! -f "$DTS_FILE" ]; then
    echo -e "${RED}✗ File not found: $DTS_FILE${NC}"
    exit 1
fi

# Check if it's a .dts file
if [[ ! "$DTS_FILE" =~ \.dts$ ]]; then
    echo -e "${RED}✗ File must have .dts extension${NC}"
    exit 1
fi

# Generate DTBO filename
DTBO_FILE="${DTS_FILE%.dts}.dtbo"
BASENAME=$(basename "$DTBO_FILE")

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Device Tree Overlay Compiler & Installer                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ DTS file: $DTS_FILE${NC}"
echo -e "${GREEN}✓ DTBO file: $DTBO_FILE${NC}"
echo ""

# Check for dtc
if ! command -v dtc &> /dev/null; then
    echo -e "${YELLOW}⚠ dtc not found, installing device-tree-compiler...${NC}"
    apt-get update
    apt-get install -y device-tree-compiler
    echo -e "${GREEN}✓ dtc installed${NC}"
else
    echo -e "${GREEN}✓ dtc is available${NC}"
fi

# Compile
echo ""
echo -e "${BLUE}ℹ Compiling device tree overlay...${NC}"
dtc -@ -O dtb -o "$DTBO_FILE" "$DTS_FILE"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Compilation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Compiled successfully${NC}"

# Check file size (sanity check)
SIZE=$(stat -c%s "$DTBO_FILE")
echo -e "${BLUE}ℹ Output size: $SIZE bytes${NC}"

if [ $SIZE -lt 100 ]; then
    echo -e "${YELLOW}⚠ Warning: DTBO file seems very small, compilation may have failed${NC}"
fi

# Install to /boot/
echo ""
echo -e "${BLUE}ℹ Installing to /boot/$BASENAME...${NC}"
cp "$DTBO_FILE" /boot/

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Installation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Installed to /boot/$BASENAME${NC}"

# Verify
if [ -f "/boot/$BASENAME" ]; then
    INSTALLED_SIZE=$(stat -c%s "/boot/$BASENAME")
    echo -e "${GREEN}✓ Verified: /boot/$BASENAME ($INSTALLED_SIZE bytes)${NC}"
else
    echo -e "${RED}✗ Verification failed: file not found in /boot/${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Installation Summary                                        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Compiled: $DTBO_FILE${NC}"
echo -e "${GREEN}✓ Installed: /boot/$BASENAME${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit /boot/extlinux/extlinux.conf"
echo "2. Add to APPEND line: overlays=/boot/$BASENAME"
echo "3. Reboot"
echo ""
echo "Example APPEND line:"
echo -e "${BLUE}  APPEND ... overlays=/boot/$BASENAME${NC}"
echo ""
