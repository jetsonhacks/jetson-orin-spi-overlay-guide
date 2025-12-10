#!/bin/bash
# Install Adafruit ST7789 Device Tree Overlay for Jetson Orin

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Adafruit ST7789 Overlay Installer                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Please run as root: sudo ./install_adafruit_overlay.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running as root${NC}"

# Check for dtc
if ! command -v dtc &> /dev/null; then
    echo -e "${YELLOW}⚠ Installing device-tree-compiler...${NC}"
    apt-get update
    apt-get install -y device-tree-compiler
fi

echo -e "${GREEN}✓ dtc is available${NC}"

DTS_FILE="jetson-st7789-adafruit.dts"
DTBO_FILE="jetson-st7789-adafruit.dtbo"

# Check for DTS file
if [ ! -f "$DTS_FILE" ]; then
    echo -e "${RED}✗ $DTS_FILE not found${NC}"
    echo -e "${YELLOW}⚠ Please ensure the .dts file is in the current directory${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found $DTS_FILE${NC}"

# Compile
echo -e "${BLUE}ℹ Compiling device tree overlay...${NC}"
dtc -@ -O dtb -o "$DTBO_FILE" "$DTS_FILE"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Compilation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Compiled successfully${NC}"

# Install
echo -e "${BLUE}ℹ Installing to /boot/...${NC}"
cp "$DTBO_FILE" /boot/

echo -e "${GREEN}✓ Installed to /boot/$DTBO_FILE${NC}"

# Detect the correct FDT
echo -e "${BLUE}ℹ Detecting base device tree...${NC}"
FDT_FILE=$(ls /boot/dtb/kernel_tegra*.dtb 2>/dev/null | head -n1)

if [ -z "$FDT_FILE" ]; then
    echo -e "${RED}✗ Could not find base DTB file${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found base DTB: $FDT_FILE${NC}"

# Configure extlinux.conf
EXTLINUX="/boot/extlinux/extlinux.conf"

if [ ! -f "$EXTLINUX" ]; then
    echo -e "${RED}✗ $EXTLINUX not found${NC}"
    exit 1
fi

# Backup
BACKUP="${EXTLINUX}.backup.$(date +%Y%m%d-%H%M%S)"
echo -e "${BLUE}ℹ Backing up $EXTLINUX to $BACKUP${NC}"
cp "$EXTLINUX" "$BACKUP"

# Check if Adafruit entry already exists
if grep -q "LABEL Adafruit" "$EXTLINUX"; then
    echo -e "${YELLOW}⚠ Adafruit boot entry already exists${NC}"
    echo -e "${YELLOW}⚠ Removing old entry...${NC}"
    # Remove old entry (from LABEL Adafruit to the line before next LABEL)
    sed -i '/^LABEL Adafruit$/,/^LABEL\|^$/{ /^LABEL Adafruit$/d; /^LABEL [^A]/Q; d; }' "$EXTLINUX"
fi

# Get the APPEND line from primary entry
echo -e "${BLUE}ℹ Reading primary boot configuration...${NC}"
APPEND_LINE=$(grep "APPEND" "$EXTLINUX" | grep -v "^#" | head -n1 | sed 's/^[[:space:]]*//')

if [ -z "$APPEND_LINE" ]; then
    echo -e "${RED}✗ Could not find APPEND line in primary entry${NC}"
    exit 1
fi

# Create new boot entry
echo -e "${BLUE}ℹ Creating new boot entry...${NC}"

cat >> "$EXTLINUX" << EOF

LABEL Adafruit
	MENU LABEL Adafruit ST7789 Config (SPI0)
	LINUX /boot/Image
	FDT $FDT_FILE
	INITRD /boot/initrd
	$APPEND_LINE
	OVERLAYS /boot/$DTBO_FILE
EOF

echo -e "${GREEN}✓ Added Adafruit boot entry to $EXTLINUX${NC}"

# Set as default
echo -e "${BLUE}ℹ Setting Adafruit as default boot option...${NC}"
sed -i 's/^DEFAULT .*/DEFAULT Adafruit/' "$EXTLINUX"

echo -e "${GREEN}✓ Set Adafruit as default${NC}"

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Installation Complete                                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Adafruit overlay installed${NC}"
echo -e "${GREEN}✓ Created new boot entry: 'Adafruit'${NC}"
echo -e "${GREEN}✓ Set as default boot option${NC}"
echo ""
echo "  Pin 19 (MOSI) -> SPI0 MOSI"
echo "  Pin 23 (SCLK) -> SPI0 SCK"
echo "  Pin 24 (CS)   -> SPI0 CS0"
echo "  Pin 18 (DC)   -> spi1_mosi_pz5"
echo "  Pin 22 (RST)  -> spi1_miso_pz4"
echo ""
echo -e "${YELLOW}⚠ REBOOT REQUIRED${NC}"
echo ""
echo "After reboot, verify with:"
echo "  sudo python3 tools/pin_inspector.py 18"
echo "  sudo python3 tools/pin_inspector.py 22"
echo ""
echo "Then test with:"
echo "  sudo python3 test_adafruit_spi0.py"
echo ""
echo "To revert to original config, edit $EXTLINUX and change:"
echo "  DEFAULT Adafruit  ->  DEFAULT primary"
echo ""
echo -ne "${YELLOW}Reboot now? [y/N] ${NC}"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}ℹ Rebooting...${NC}"
    reboot
else
    echo -e "${BLUE}ℹ Remember to reboot before testing!${NC}"
fi