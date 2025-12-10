#!/bin/bash
# Common Functions for Jetson Overlay Installers
# 
# This file provides shared utilities for device tree overlay installation scripts.
# Source this file in your installer: source /path/to/common_functions.sh

# ============================================================================
# COLOR CODES
# ============================================================================

export GREEN='\033[0;32m'
export RED='\033[0;31m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export NC='\033[0m'

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Print colored message
# Usage: print_message "color" "message"
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Print success message
# Usage: print_success "message"
print_success() {
    print_message "$GREEN" "✓ $1"
}

# Print error message
# Usage: print_error "message"
print_error() {
    print_message "$RED" "✗ $1"
}

# Print warning message
# Usage: print_warning "message"
print_warning() {
    print_message "$YELLOW" "⚠ $1"
}

# Print info message
# Usage: print_info "message"
print_info() {
    print_message "$BLUE" "ℹ $1"
}

# Print header box
# Usage: print_header "Title"
print_header() {
    local title=$1
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    printf "${BLUE}║  %-58s  ║${NC}\n" "$title"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

# Check if running as root
# Usage: check_root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root: sudo $0"
        exit 1
    fi
    print_success "Running as root"
}

# Check if file exists
# Usage: check_file_exists "filepath" "description"
check_file_exists() {
    local filepath=$1
    local description=${2:-"File"}
    
    if [ ! -f "$filepath" ]; then
        print_error "$description not found: $filepath"
        return 1
    fi
    print_success "Found $description: $filepath"
    return 0
}

# Check if directory exists
# Usage: check_dir_exists "dirpath" "description"
check_dir_exists() {
    local dirpath=$1
    local description=${2:-"Directory"}
    
    if [ ! -d "$dirpath" ]; then
        print_error "$description not found: $dirpath"
        return 1
    fi
    print_success "Found $description: $dirpath"
    return 0
}

# Check if command exists
# Usage: check_command "command_name"
check_command() {
    local cmd=$1
    
    if ! command -v "$cmd" &> /dev/null; then
        print_warning "$cmd not found"
        return 1
    fi
    print_success "$cmd is available"
    return 0
}

# ============================================================================
# INSTALLATION FUNCTIONS
# ============================================================================

# Install device-tree-compiler if needed
# Usage: install_dtc
install_dtc() {
    if check_command dtc; then
        return 0
    fi
    
    print_info "Installing device-tree-compiler..."
    apt-get update > /dev/null 2>&1
    apt-get install -y device-tree-compiler
    
    if [ $? -eq 0 ]; then
        print_success "Installed device-tree-compiler"
        return 0
    else
        print_error "Failed to install device-tree-compiler"
        return 1
    fi
}

# Compile device tree overlay
# Usage: compile_overlay "input.dts" "output.dtbo"
compile_overlay() {
    local dts_file=$1
    local dtbo_file=$2
    
    print_info "Compiling device tree overlay..."
    
    if ! check_file_exists "$dts_file" "DTS source"; then
        return 1
    fi
    
    dtc -@ -O dtb -o "$dtbo_file" "$dts_file" 2>&1
    
    if [ $? -ne 0 ]; then
        print_error "Compilation failed"
        return 1
    fi
    
    print_success "Compiled successfully: $dtbo_file"
    return 0
}

# Install overlay to /boot/
# Usage: install_overlay "overlay.dtbo"
install_overlay() {
    local dtbo_file=$1
    
    if ! check_file_exists "$dtbo_file" "Compiled overlay"; then
        return 1
    fi
    
    print_info "Installing overlay to /boot/..."
    cp "$dtbo_file" /boot/
    
    if [ $? -eq 0 ]; then
        print_success "Installed to /boot/$dtbo_file"
        return 0
    else
        print_error "Failed to install overlay"
        return 1
    fi
}

# ============================================================================
# FDT DETECTION
# ============================================================================

# Detect base device tree (FDT)
# Usage: FDT_FILE=$(detect_fdt)
detect_fdt() {
    print_info "Detecting base device tree..."
    
    local fdt_file=$(ls /boot/dtb/kernel_tegra*.dtb 2>/dev/null | head -n1)
    
    if [ -z "$fdt_file" ]; then
        print_error "Could not find base DTB file in /boot/dtb/"
        return 1
    fi
    
    print_success "Found base DTB: $fdt_file"
    echo "$fdt_file"
    return 0
}

# ============================================================================
# BOOTLOADER CONFIGURATION
# ============================================================================

# Backup extlinux.conf
# Usage: backup_extlinux "/boot/extlinux/extlinux.conf"
backup_extlinux() {
    local extlinux=$1
    local backup="${extlinux}.backup.$(date +%Y%m%d-%H%M%S)"
    
    if ! check_file_exists "$extlinux" "Bootloader config"; then
        return 1
    fi
    
    print_info "Backing up $extlinux to $backup"
    cp "$extlinux" "$backup"
    
    if [ $? -eq 0 ]; then
        print_success "Backup created"
        echo "$backup"
        return 0
    else
        print_error "Backup failed"
        return 1
    fi
}

# Extract APPEND line from primary boot entry
# Usage: APPEND_LINE=$(extract_append_line "/boot/extlinux/extlinux.conf")
extract_append_line() {
    local extlinux=$1
    
    print_info "Reading primary boot configuration..."
    
    local append_line=$(grep "APPEND" "$extlinux" | grep -v "^#" | head -n1 | sed 's/^[[:space:]]*//')
    
    if [ -z "$append_line" ]; then
        print_error "Could not find APPEND line in primary entry"
        return 1
    fi
    
    print_success "Extracted APPEND line"
    echo "$append_line"
    return 0
}

# Remove existing boot entry by label
# Usage: remove_boot_entry "/boot/extlinux/extlinux.conf" "LabelName"
remove_boot_entry() {
    local extlinux=$1
    local label=$2
    
    if grep -q "LABEL ${label}" "$extlinux"; then
        print_warning "Boot entry '${label}' already exists"
        print_info "Removing old entry..."
        
        # Remove from LABEL line to next LABEL or end of file
        sed -i "/^LABEL ${label}$/,/^LABEL\|^$/{ /^LABEL ${label}$/d; /^LABEL [^${label:0:1}]/Q; d; }" "$extlinux"
        
        if [ $? -eq 0 ]; then
            print_success "Removed old entry"
            return 0
        else
            print_error "Failed to remove old entry"
            return 1
        fi
    fi
    
    return 0
}

# Add new boot entry
# Usage: add_boot_entry "/boot/extlinux/extlinux.conf" "Label" "Menu Label" "FDT" "APPEND" "Overlay"
add_boot_entry() {
    local extlinux=$1
    local label=$2
    local menu_label=$3
    local fdt_file=$4
    local append_line=$5
    local overlay_file=$6
    
    print_info "Creating new boot entry..."
    
    cat >> "$extlinux" << EOF

LABEL ${label}
	MENU LABEL ${menu_label}
	LINUX /boot/Image
	FDT ${fdt_file}
	INITRD /boot/initrd
	${append_line}
	OVERLAYS /boot/${overlay_file}
EOF
    
    if [ $? -eq 0 ]; then
        print_success "Added boot entry: ${label}"
        return 0
    else
        print_error "Failed to add boot entry"
        return 1
    fi
}

# Set default boot entry
# Usage: set_default_boot "/boot/extlinux/extlinux.conf" "LabelName"
set_default_boot() {
    local extlinux=$1
    local label=$2
    
    print_info "Setting ${label} as default boot option..."
    
    sed -i "s/^DEFAULT .*/DEFAULT ${label}/" "$extlinux"
    
    if [ $? -eq 0 ]; then
        print_success "Set ${label} as default"
        return 0
    else
        print_error "Failed to set default boot entry"
        return 1
    fi
}

# ============================================================================
# PIN VERIFICATION
# ============================================================================

# Verify pin configuration (if pin_inspector.py is available)
# Usage: verify_pin "pin_number" "description"
verify_pin() {
    local pin=$1
    local description=${2:-"Pin $pin"}
    
    local pin_inspector="../../tools/pin_inspector.py"
    
    if [ ! -f "$pin_inspector" ]; then
        print_warning "pin_inspector.py not found, skipping verification"
        return 0
    fi
    
    print_info "To verify $description after reboot:"
    echo "  sudo python3 $pin_inspector $pin"
}

# ============================================================================
# USER INTERACTION
# ============================================================================

# Prompt for reboot
# Usage: prompt_reboot
prompt_reboot() {
    echo ""
    print_warning "REBOOT REQUIRED"
    echo ""
    echo -ne "${YELLOW}Reboot now? [y/N] ${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Rebooting..."
        reboot
    else
        print_info "Remember to reboot before testing!"
    fi
}

# Confirm action
# Usage: if confirm_action "Do something dangerous?"; then ...
confirm_action() {
    local prompt=$1
    
    echo -ne "${YELLOW}${prompt} [y/N] ${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# COMPLETE INSTALLATION WORKFLOW
# ============================================================================

# Run complete installation workflow
# Usage: install_overlay_complete "device_name" "dts_file" "boot_label" "menu_label" "pin1" "pin2"
install_overlay_complete() {
    local device_name=$1
    local dts_file=$2
    local boot_label=$3
    local menu_label=$4
    local pin1=${5:-""}
    local pin2=${6:-""}
    
    local dtbo_file="${dts_file%.dts}.dtbo"
    local extlinux="/boot/extlinux/extlinux.conf"
    
    # Header
    print_header "${device_name} Overlay Installer"
    
    # Validation
    check_root || exit 1
    install_dtc || exit 1
    check_file_exists "$dts_file" "DTS file" || exit 1
    
    # Compilation
    compile_overlay "$dts_file" "$dtbo_file" || exit 1
    
    # Installation
    install_overlay "$dtbo_file" || exit 1
    
    # FDT Detection
    local fdt_file=$(detect_fdt) || exit 1
    
    # Bootloader Configuration
    check_file_exists "$extlinux" "Bootloader config" || exit 1
    backup_extlinux "$extlinux" || exit 1
    
    remove_boot_entry "$extlinux" "$boot_label"
    
    local append_line=$(extract_append_line "$extlinux") || exit 1
    
    add_boot_entry "$extlinux" "$boot_label" "$menu_label" "$fdt_file" "$append_line" "$dtbo_file" || exit 1
    
    set_default_boot "$extlinux" "$boot_label" || exit 1
    
    # Summary
    echo ""
    print_header "Installation Complete"
    
    print_success "${device_name} overlay installed"
    print_success "Created new boot entry: '${boot_label}'"
    print_success "Set as default boot option"
    echo ""
    
    # Pin verification instructions
    if [ -n "$pin1" ]; then
        verify_pin "$pin1" "Control Pin 1"
    fi
    if [ -n "$pin2" ]; then
        verify_pin "$pin2" "Control Pin 2"
    fi
    echo ""
    
    echo "To revert to original config, edit $extlinux and change:"
    echo "  DEFAULT ${boot_label}  ->  DEFAULT primary"
    echo ""
    
    # Reboot prompt
    prompt_reboot
}

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

# Example usage in an installer script:
#
# #!/bin/bash
# source "$(dirname "$0")/../../scripts/common_functions.sh"
#
# install_overlay_complete \
#     "MyDevice" \
#     "jetson-mydevice.dts" \
#     "MyDevice" \
#     "MyDevice Configuration" \
#     "29" \
#     "31"
