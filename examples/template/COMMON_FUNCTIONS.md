# Using Common Functions Library

The repository includes a shared functions library that simplifies installer creation.

## Files

- `device-overlay-template.dts` - Device tree source template
- `install_overlay_template.sh` - Full-featured installer template
- `install_simple_example.sh` - Simplified installer using common_functions.sh
- `README.md` - This file

## Two Approaches

### Approach 1: Standalone Installer (install_overlay_template.sh)

Complete, self-contained script with all functions inline.

**Pros:**
- No dependencies
- Easy to distribute as single file
- Clear to read and understand

**Use when:**
- Creating standalone examples
- Distributing to users who may not have the full repo

### Approach 2: Using Common Functions (install_simple_example.sh)

Minimal script that uses shared `common_functions.sh` library.

**Pros:**
- Much shorter and cleaner
- Consistent behavior across installers
- Easy to maintain and update
- Reusable functions

**Use when:**
- Creating multiple installers in same repo
- Want consistent error handling
- Need maintainable code

## Using Common Functions

### Basic Usage

```bash
#!/bin/bash
set -e

# Source the library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../scripts/common_functions.sh"

# Use the complete workflow
install_overlay_complete \
    "MyDevice" \
    "jetson-mydevice.dts" \
    "MyDevice" \
    "MyDevice Configuration" \
    "29" \
    "31"
```

That's it! The `install_overlay_complete` function handles:
- Root check
- DTC installation
- Compilation
- Installation to /boot
- FDT detection
- Bootloader configuration
- Backup creation
- Setting as default
- Summary display
- Reboot prompt

### Available Functions

#### Printing
```bash
print_success "Operation succeeded"
print_error "Operation failed"
print_warning "Be careful"
print_info "FYI"
print_header "Section Title"
```

#### Validation
```bash
check_root                              # Verify running as root
check_file_exists "file.txt" "My file"  # Check file exists
check_command "dtc"                     # Check command available
```

#### Installation
```bash
install_dtc                                    # Install device-tree-compiler
compile_overlay "input.dts" "output.dtbo"      # Compile overlay
install_overlay "overlay.dtbo"                 # Copy to /boot
```

#### FDT
```bash
FDT_FILE=$(detect_fdt)                  # Find base device tree
```

#### Bootloader
```bash
backup_extlinux "/boot/extlinux/extlinux.conf"
APPEND=$(extract_append_line "/boot/extlinux/extlinux.conf")
remove_boot_entry "/boot/extlinux/extlinux.conf" "MyLabel"
add_boot_entry "/boot/extlinux/extlinux.conf" "MyLabel" "Menu Label" "$FDT" "$APPEND" "my.dtbo"
set_default_boot "/boot/extlinux/extlinux.conf" "MyLabel"
```

#### User Interaction
```bash
prompt_reboot                           # Ask to reboot
if confirm_action "Delete files?"; then
    # User confirmed
fi
```

### Custom Installation Flow

If you need more control:

```bash
#!/bin/bash
set -e
source "../../scripts/common_functions.sh"

print_header "Custom Installer"

check_root || exit 1
install_dtc || exit 1

# Your custom logic here
print_info "Doing custom preprocessing..."

compile_overlay "my.dts" "my.dtbo" || exit 1
install_overlay "my.dtbo" || exit 1

FDT=$(detect_fdt) || exit 1

# More custom logic
print_success "Custom steps completed"

prompt_reboot
```

## Comparison

### Standalone Template (~150 lines)

```bash
#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
# ... more colors

# Configuration
DEVICE_NAME="MyDevice"
# ... more config

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo "Error"
    exit 1
fi

# Install dtc
if ! command -v dtc; then
    apt-get install -y device-tree-compiler
fi

# Compile
dtc -@ -O dtb -o "$DTBO" "$DTS"

# ... 100+ more lines
```

### Using Common Functions (~20 lines)

```bash
#!/bin/bash
set -e

source "../../scripts/common_functions.sh"

install_overlay_complete \
    "MyDevice" \
    "jetson-mydevice.dts" \
    "MyDevice" \
    "MyDevice Configuration" \
    "29" \
    "31"
```

## When to Use Which

### Use Standalone Template When:
- ✅ Creating one-off example
- ✅ Distributing single file to users
- ✅ Want complete visibility of all steps
- ✅ No access to common_functions.sh

### Use Common Functions When:
- ✅ Creating multiple installers
- ✅ Working within this repository
- ✅ Want consistency across installers
- ✅ Need maintainable code
- ✅ Want to leverage tested functions

## Example: Converting Standalone to Common Functions

**Before (standalone):**
```bash
#!/bin/bash
# ... 150 lines of code
```

**After (with common functions):**
```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../scripts/common_functions.sh"

install_overlay_complete \
    "Waveshare" \
    "jetson-st7789-waveshare.dts" \
    "Waveshare" \
    "Waveshare ST7789 Config" \
    "13" \
    "22"
```

## Adding Custom Steps

You can mix common functions with custom logic:

```bash
#!/bin/bash
set -e
source "../../scripts/common_functions.sh"

print_header "Custom Device Installer"

# Standard steps
check_root || exit 1
install_dtc || exit 1

# Custom preprocessing
print_info "Checking hardware compatibility..."
if [ ! -f /sys/class/gpio/export ]; then
    print_error "GPIO not available"
    exit 1
fi

# Standard compilation
compile_overlay "my.dts" "my.dtbo" || exit 1

# Custom validation
print_info "Running custom tests..."
./test_hardware.sh

# Standard installation
install_overlay "my.dtbo" || exit 1

# Continue with bootloader config...
FDT=$(detect_fdt) || exit 1
# ... etc
```

## See Also

- [Device Tree Basics](../../docs/DEVICE_TREE_BASICS.md)
- [FDT Configuration](../../docs/FDT_CONFIGURATION.md)
- [Common Functions Source](../../scripts/common_functions.sh)

---

Return to [Main README](../../README.md)
