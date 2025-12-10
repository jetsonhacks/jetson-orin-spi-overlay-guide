#!/bin/bash
# Example: Simplified Installer Using Common Functions
#
# This demonstrates how to use common_functions.sh to create
# a clean, maintainable installer script.

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../scripts/common_functions.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

DEVICE_NAME="MyDevice"
DEVICE_SLUG="mydevice"
DTS_FILE="jetson-${DEVICE_SLUG}.dts"
BOOT_LABEL="${DEVICE_NAME}"
BOOT_MENU_LABEL="${DEVICE_NAME} Configuration"

# Pin numbers for verification
PIN_1=29
PIN_2=31

# ============================================================================
# SIMPLE INSTALLATION
# ============================================================================

# Option 1: Use the complete workflow function (easiest)
install_overlay_complete \
    "$DEVICE_NAME" \
    "$DTS_FILE" \
    "$BOOT_LABEL" \
    "$BOOT_MENU_LABEL" \
    "$PIN_1" \
    "$PIN_2"

# ============================================================================
# CUSTOM INSTALLATION (if you need more control)
# ============================================================================

# Uncomment below to see how to use individual functions:

# # Header
# print_header "${DEVICE_NAME} Overlay Installer"
# 
# # Validation
# check_root || exit 1
# install_dtc || exit 1
# check_file_exists "$DTS_FILE" "DTS file" || exit 1
# 
# # Compilation
# DTBO_FILE="${DTS_FILE%.dts}.dtbo"
# compile_overlay "$DTS_FILE" "$DTBO_FILE" || exit 1
# 
# # Installation
# install_overlay "$DTBO_FILE" || exit 1
# 
# # FDT Detection
# FDT_FILE=$(detect_fdt) || exit 1
# 
# # Bootloader Configuration
# EXTLINUX="/boot/extlinux/extlinux.conf"
# check_file_exists "$EXTLINUX" "Bootloader config" || exit 1
# backup_extlinux "$EXTLINUX" || exit 1
# remove_boot_entry "$EXTLINUX" "$BOOT_LABEL"
# APPEND_LINE=$(extract_append_line "$EXTLINUX") || exit 1
# add_boot_entry "$EXTLINUX" "$BOOT_LABEL" "$BOOT_MENU_LABEL" "$FDT_FILE" "$APPEND_LINE" "$DTBO_FILE" || exit 1
# set_default_boot "$EXTLINUX" "$BOOT_LABEL" || exit 1
# 
# # Summary
# print_header "Installation Complete"
# print_success "${DEVICE_NAME} overlay installed"
# 
# # Reboot
# prompt_reboot
