#!/bin/bash
# Template: Install Device Tree Overlay for Jetson Orin
# 
# INSTRUCTIONS:
# 1. Copy this file and rename: install_<yourdevice>_overlay.sh
# 2. Replace "DEVICE_NAME" with your device name (e.g., "MyDevice")
# 3. Replace "yourdevice" with your device name in lowercase
# 4. Update the pin numbers and descriptions
# 5. Make executable: chmod +x install_<yourdevice>_overlay.sh
# 6. Run: sudo ./install_<yourdevice>_overlay.sh

set -e

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE VALUES
# ============================================================================

DEVICE_NAME="MyDevice"          # Display name (e.g., "MyDevice", "OLED Display")
DEVICE_SLUG="mydevice"          # Lowercase, no spaces (e.g., "mydevice", "oled")
DTS_FILE="jetson-${DEVICE_SLUG}.dts"
DTBO_FILE="jetson-${DEVICE_SLUG}.dtbo"

# Pin numbers used by your device (for verification)
PIN_1=29                        # First control pin (e.g., DC, RST, CS)
PIN_2=31                        # Second control pin (if applicable)
# Add more pins as needed: PIN_3=33, etc.

# Boot entry configuration
BOOT_LABEL="${DEVICE_NAME}"                    # e.g., "MyDevice"
BOOT_MENU_LABEL="${DEVICE_NAME} Configuration" # e.g., "MyDevice Configuration"

# ============================================================================
# COLOR CODES
# ============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# MAIN SCRIPT - Generally no need to modify below this line
# ============================================================================

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ${DEVICE_NAME} Overlay Installer                               ${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Please run as root: sudo $0${NC}"
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

# Check if entry already exists
if grep -q "LABEL ${BOOT_LABEL}" "$EXTLINUX"; then
    echo -e "${YELLOW}⚠ ${BOOT_LABEL} boot entry already exists${NC}"
    echo -e "${YELLOW}⚠ Removing old entry...${NC}"
    # Remove old entry (from LABEL to the line before next LABEL)
    sed -i "/^LABEL ${BOOT_LABEL}$/,/^LABEL\|^$/{ /^LABEL ${BOOT_LABEL}$/d; /^LABEL [^${BOOT_LABEL:0:1}]/Q; d; }" "$EXTLINUX"
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

LABEL ${BOOT_LABEL}
	MENU LABEL ${BOOT_MENU_LABEL}
	LINUX /boot/Image
	FDT $FDT_FILE
	INITRD /boot/initrd
	$APPEND_LINE
	OVERLAYS /boot/$DTBO_FILE
EOF

echo -e "${GREEN}✓ Added ${BOOT_LABEL} boot entry to $EXTLINUX${NC}"

# Set as default
echo -e "${BLUE}ℹ Setting ${BOOT_LABEL} as default boot option...${NC}"
sed -i "s/^DEFAULT .*/DEFAULT ${BOOT_LABEL}/" "$EXTLINUX"

echo -e "${GREEN}✓ Set ${BOOT_LABEL} as default${NC}"

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Installation Complete                                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ ${DEVICE_NAME} overlay installed${NC}"
echo -e "${GREEN}✓ Created new boot entry: '${BOOT_LABEL}'${NC}"
echo -e "${GREEN}✓ Set as default boot option${NC}"
echo ""

# Display pin information (customize based on your device)
echo "Pin Configuration:"
echo "  Pin ${PIN_1} - Control Signal 1"
echo "  Pin ${PIN_2} - Control Signal 2"
echo ""

echo -e "${YELLOW}⚠ REBOOT REQUIRED${NC}"
echo ""
echo "After reboot, verify with:"
echo "  sudo python3 ../../tools/pin_inspector.py ${PIN_1}"
echo "  sudo python3 ../../tools/pin_inspector.py ${PIN_2}"
echo ""
echo "To revert to original config, edit $EXTLINUX and change:"
echo "  DEFAULT ${BOOT_LABEL}  ->  DEFAULT primary"
echo ""
echo -ne "${YELLOW}Reboot now? [y/N] ${NC}"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}ℹ Rebooting...${NC}"
    reboot
else
    echo -e "${BLUE}ℹ Remember to reboot before testing!${NC}"
fi
