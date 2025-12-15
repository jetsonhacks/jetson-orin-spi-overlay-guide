#!/usr/bin/env python3
"""
Jetson Orin Nano Comprehensive Pin Inspector
Analyzes 40-pin expansion header pins from first principles using kernel debugfs

This tool helps diagnose pin configurations, mux settings, and GPIO availability
on NVIDIA Jetson platforms. Essential for troubleshooting display driver issues.

Usage:
    sudo python3 pin_inspector.py <PIN_NUMBER> [--blink]
    
Examples:
    sudo python3 pin_inspector.py 29              # Inspect pin 29 (DC pin)
    sudo python3 pin_inspector.py 31              # Inspect pin 31 (RST pin)
    sudo python3 pin_inspector.py 29 --blink      # Test pin 29 with blink
"""

import os
import re
import sys
import subprocess

# Official pin mappings from NVIDIA headers
HEADER_PIN_NAMES = {
    7:  "soc_gpio59_pac6",
    11: "uart1_rts_pr4",
    12: "soc_gpio41_ph7",
    13: "spi3_sck_py0",
    15: "soc_gpio39_pn1",
    16: "spi3_cs1_py4",
    18: "spi3_cs0_py3",
    19: "spi1_mosi_pz5",
    21: "spi1_miso_pz4",
    22: "spi3_miso_py1",
    23: "spi1_sck_pz3",
    24: "spi1_cs0_pz6",
    26: "spi1_cs1_pz7",
    29: "soc_gpio32_pq5",
    31: "soc_gpio33_pq6",
    32: "soc_gpio19_pg6",
    33: "soc_gpio21_ph0",
    35: "soc_gpio44_pi2",
    36: "uart1_cts_pr5",
    37: "spi3_mosi_py2",
    38: "soc_gpio43_pi1",
    40: "soc_gpio42_pi0",
    # I2C pins
    3:  "gen2_i2c_sda_pdd0",
    5:  "gen2_i2c_scl_pcc7",
    27: "gen1_i2c_sda_pi4",
    28: "gen1_i2c_scl_pi3",
    # UART pins
    8:  "uart1_tx_pr2",
    10: "uart1_rx_pr3",
}

# Pinmux register addresses for Jetson Orin Nano/NX
# These addresses are derived from the Jetson Orin Series Technical Reference Manual (TRM)
# Base address: PADCTL_A0 = 0x02430000 (from device tree: pinmux@2430000)
# Register addresses are organized by GPIO port (PAC, PQ, PZ, etc.), not controller pin order
# This matches the approach used by NVIDIA's jetson-gpio-pinmux-lookup tool
# 
# The running system does NOT expose pin-to-register mappings, so these must come from TRM
# or be hardcoded (industry-standard practice for embedded systems)
ORIN_PINMUX_REGISTERS = {
    # Calculated as base (0x02430000) + offset from TRM Section 8.4 (Pinmux Registers)
    "soc_gpio59_pac6":   0x02430070,  # Pin 7
    "uart1_rts_pr4":     0x024300D0,  # Pin 11
    "soc_gpio41_ph7":    0x02430058,  # Pin 12
    "spi3_sck_py0":      0x024300F8,  # Pin 13
    "soc_gpio39_pn1":    0x02430050,  # Pin 15
    "spi3_cs1_py4":      0x02430108,  # Pin 16
    "spi3_cs0_py3":      0x02430104,  # Pin 18
    "spi1_mosi_pz5":     0x024301E0,  # Pin 19
    "spi1_miso_pz4":     0x024301DC,  # Pin 21
    "spi3_miso_py1":     0x024300FC,  # Pin 22
    "spi1_sck_pz3":      0x024301D8,  # Pin 23
    "spi1_cs0_pz6":      0x024301E4,  # Pin 24
    "spi1_cs1_pz7":      0x024301E8,  # Pin 26
    "soc_gpio32_pq5":    0x02430090,  # Pin 29
    "soc_gpio33_pq6":    0x02430094,  # Pin 31
    "soc_gpio19_pg6":    0x024300E8,  # Pin 32
    "soc_gpio21_ph0":    0x024300F0,  # Pin 33
    "soc_gpio44_pi2":    0x02430064,  # Pin 35
    "uart1_cts_pr5":     0x024300D4,  # Pin 36
    "spi3_mosi_py2":     0x02430100,  # Pin 37
    "soc_gpio43_pi1":    0x02430060,  # Pin 38
    "soc_gpio42_pi0":    0x0243005C,  # Pin 40
    # I2C pins
    "gen2_i2c_sda_pdd0": 0x024301BC,  # Pin 3
    "gen2_i2c_scl_pcc7": 0x024301B8,  # Pin 5
    "gen1_i2c_sda_pi4":  0x0243006C,  # Pin 27
    "gen1_i2c_scl_pi3":  0x02430068,  # Pin 28
    # UART pins
    "uart1_tx_pr2":      0x024300C8,  # Pin 8
    "uart1_rx_pr3":      0x024300CC,  # Pin 10
}

PINCTRL_BASE = "/sys/kernel/debug/pinctrl"
GPIO_BASE = "/sys/class/gpio"

class PinInfo:
    """Container for comprehensive pin information"""
    
    def __init__(self, pin_num):
        self.pin_num = pin_num
        self.soc_name = HEADER_PIN_NAMES.get(pin_num, "unknown")
        self.controller = None
        self.controller_pin_num = None
        self.pinmux_register = None
        self.register_value = None
        self.available_functions = []
        self.current_function = None
        self.current_mux_owner = None
        self.current_gpio_owner = None
        self.is_hogged = False
        self.gpio_chip = None
        self.gpio_line = None
        self.gpio_number = None  # Global GPIO number for Jetson.GPIO
        self.gpio_port = None    # Port notation like "PQ"
        self.gpio_offset = None  # Offset within port like "5"
        self.gpio_direction = None
        self.gpio_value = None
        
    def __str__(self):
        lines = [
            f"\n{'='*70}",
            f"PIN {self.pin_num} ANALYSIS",
            f"{'='*70}",
            f"Board Pin (Header):  {self.pin_num}",
            f"SoC Pin Name:        {self.soc_name}",
        ]
        
        # Add port notation if available
        if self.gpio_port and self.gpio_offset is not None:
            lines.append(f"GPIO Notation:       GPIO3_{self.gpio_port}.{self.gpio_offset:02d}")
        
        lines.append(f"Pinmux Controller:   {self.controller or 'NOT FOUND'}")
        
        if self.controller_pin_num is not None:
            lines.append(f"Controller Pin #:    {self.controller_pin_num}")
        
        if self.gpio_number is not None:
            lines.append(f"GPIO Number:         {self.gpio_number}")
        
        if self.pinmux_register:
            lines.append(f"Pinmux Register:     {hex(self.pinmux_register)} (from TRM)")
            
            if self.register_value is not None:
                decoded = decode_register_value(self.register_value)
                # Show hex and binary
                binary = bin(self.register_value)[2:].zfill(12)  # Show lower 12 bits
                lines.append(f"Register Value:      {hex(self.register_value)} ({binary} binary)")
                lines.append(f"\n--- REGISTER DECODE ---")
                
                # Show mode with SFIO function name if available
                mode_str = decoded['mode']
                if decoded['mode'] == 'SFIO' and self.current_function:
                    mode_str = f"{decoded['mode']} ({self.current_function})"
                elif decoded['mode'] == 'SFIO' and not self.current_function:
                    mode_str = f"{decoded['mode']} (no specific function configured)"
                lines.append(f"Mode:                {mode_str}")
                
                if decoded['direction']:
                    lines.append(f"Direction:           {decoded['direction']}")
                lines.append(f"Input Enable:        {decoded['input_enable']}")
                lines.append(f"Tristate:            {decoded['tristate']}")
                lines.append(f"Pull:                {decoded['pull']}")
                lines.append(f"Low Power:           {decoded['lpdr']}")
            
        lines.append(f"\n--- CURRENT STATE ---")
        
        # Show current function with clear labeling
        if self.current_function:
            if self.current_function in ["gp", "rsvd0", "rsvd1", "rsvd2", "rsvd3"]:
                func_label = f"{self.current_function} (GPIO function)"
            else:
                func_label = f"{self.current_function} (SFIO function)"
            lines.append(f"Current Function:    {func_label}")
        else:
            # No function configured in device tree
            if self.register_value is not None:
                decoded = decode_register_value(self.register_value)
                if decoded['mode'] == 'SFIO':
                    # Register shows SFIO mode but no DT configuration
                    lines.append(f"Current Function:    Not configured (register shows SFIO mode)")
                elif decoded['mode'] == 'GPIO':
                    # Register shows GPIO mode but no DT configuration
                    lines.append(f"Current Function:    Not configured (register shows GPIO mode)")
                else:
                    lines.append(f"Current Function:    Not configured")
            else:
                lines.append(f"Current Function:    Not configured")
        
        # Clarify what ownership means
        mux_status = self.current_mux_owner or 'UNCLAIMED'
        if mux_status == 'UNCLAIMED':
            mux_status += ' (no driver claimed)'
        lines.append(f"Mux Owner:           {mux_status}")
        
        gpio_status = self.current_gpio_owner or 'UNCLAIMED'
        if gpio_status == 'UNCLAIMED':
            gpio_status += ' (available for use)'
        lines.append(f"GPIO Owner:          {gpio_status}")
        
        lines.append(f"Hogged at boot:      {'YES' if self.is_hogged else 'NO'}")
        
        if self.gpio_chip and self.gpio_line is not None:
            lines.append(f"\n--- GPIO INFO ---")
            lines.append(f"GPIO Chip:           {self.gpio_chip}")
            lines.append(f"GPIO Line:           {self.gpio_line}")
            lines.append(f"Direction:           {self.gpio_direction or 'unknown'}")
            if self.gpio_value is not None:
                lines.append(f"Current Value:       {self.gpio_value}")
        
        if self.available_functions:
            lines.append(f"\n--- AVAILABLE FUNCTIONS ---")
            for func in self.available_functions:
                marker = " (GPIO)" if func in ["gp", "rsvd0", "rsvd1", "rsvd2", "rsvd3"] else ""
                lines.append(f"  - {func}{marker}")
        
        lines.append(f"{'='*70}")
        
        # Add quick reference section
        if is_gpio_configured(self):
            lines.append(f"\n--- QUICK REFERENCE ---")
            lines.append(f"Platform:            Jetson Orin Nano/NX")
            if self.gpio_number:
                lines.append(f"GPIO Number:         {self.gpio_number} (for sysfs or libraries)")
                lines.append(f"Example usage:       GPIO.setup({self.pin_num}, GPIO.IN)  # If using Jetson.GPIO")
            if self.register_value is not None:
                decoded = decode_register_value(self.register_value)
                status_parts = []
                if decoded['mode'] == 'GPIO':
                    status_parts.append('GPIO mode')
                if decoded['direction']:
                    status_parts.append(decoded['direction'].lower())
                if decoded['pull'] != 'None':
                    status_parts.append(decoded['pull'].lower())
                status = ', '.join(status_parts) if status_parts else 'configured'
                lines.append(f"Current state:       {status}")
            lines.append(f"Verify register:     sudo busybox devmem {hex(self.pinmux_register)}")
        
        lines.append("")
        return "\n".join(lines)

def find_pin_in_controller(pin_name, controller_path):
    """Find pin in a specific controller's pins file and extract GPIO number"""
    pins_file = os.path.join(controller_path, "pins")
    if not os.path.exists(pins_file):
        return None, None
        
    try:
        with open(pins_file, 'r') as f:
            for line in f:
                # Format: pin 105 (SOC_GPIO32_PQ5) 105:tegra234-gpio  2430000.pinmux
                # The number before ':tegra234-gpio' is the global GPIO number
                if pin_name.upper() in line.upper():
                    # Extract controller pin number
                    ctrl_pin_match = re.search(r'pin (\d+)', line)
                    ctrl_pin = int(ctrl_pin_match.group(1)) if ctrl_pin_match else None
                    
                    # Extract GPIO number (appears as "NNN:tegra234-gpio")
                    gpio_match = re.search(r'(\d+):tegra234-gpio', line)
                    gpio_num = int(gpio_match.group(1)) if gpio_match else None
                    
                    return ctrl_pin, gpio_num
    except IOError:
        pass
    return None, None

def get_available_functions(pin_name, controller_path):
    """Get all functions available for this pin"""
    funcs_file = os.path.join(controller_path, "pinmux-functions")
    if not os.path.exists(funcs_file):
        return []
        
    functions = []
    try:
        with open(funcs_file, 'r') as f:
            for line in f:
                if pin_name in line:
                    # Format: function 7: rsvd0, groups = [ ... pin_name ... ]
                    match = re.search(r'function \d+: (\w+),', line)
                    if match:
                        functions.append(match.group(1))
    except IOError:
        pass
    
    return sorted(set(functions))

def get_current_pinmux_state(pin_name, controller_path):
    """Get current mux and GPIO ownership"""
    pinmux_file = os.path.join(controller_path, "pinmux-pins")
    if not os.path.exists(pinmux_file):
        return None, None, False
        
    try:
        with open(pinmux_file, 'r') as f:
            for line in f:
                if pin_name.upper() in line.upper():
                    # Format: pin 105 (SOC_GPIO32_PQ5): (MUX UNCLAIMED) tegra234-gpio:453
                    mux_match = re.search(r'\): ([^\s]+)', line)
                    gpio_match = re.search(r'([^\s]+):(\d+)', line)
                    
                    mux_owner = mux_match.group(1) if mux_match else None
                    if mux_owner == "(MUX" or mux_owner == "UNCLAIMED)":
                        mux_owner = None
                        
                    gpio_owner = None
                    if gpio_match and "UNCLAIMED" not in line:
                        gpio_owner = gpio_match.group(1)
                    
                    is_hogged = "HOG" in line.upper()
                    
                    return mux_owner, gpio_owner, is_hogged
    except IOError:
        pass
    
    return None, None, False

def get_current_pin_function(pin_name, controller_path):
    """Get the currently configured function for this pin"""
    # The pinmux-pins file has the actual format:
    # Configured: pin 105 (SOC_GPIO32_PQ5): 2430000.pinmux (GPIO UNCLAIMED) (HOG) function rsvd0 group soc_gpio32_pq5
    # Unconfigured: pin 144 (SOC_GPIO59_PAC6): (MUX UNCLAIMED) (GPIO UNCLAIMED)
    
    pinmux_file = os.path.join(controller_path, "pinmux-pins")
    if not os.path.exists(pinmux_file):
        return None
        
    try:
        with open(pinmux_file, 'r') as f:
            for line in f:
                if pin_name.upper() in line.upper():
                    # Look for "function <name>" pattern
                    match = re.search(r'function (\w+)', line)
                    if match:
                        return match.group(1)
                    # If no function keyword found, pin has no DT configuration
                    return None
    except IOError:
        pass
    
    return None


def get_pinmux_register_address(pin_name):
    """Get the pinmux register address from lookup table"""
    # Use hardcoded table for Orin Nano/NX
    # This matches the approach used by jetson-gpio-pinmux-lookup tool
    return ORIN_PINMUX_REGISTERS.get(pin_name.lower())

def read_register_value(register_address):
    """Read the current value of a pinmux register using devmem"""
    if not register_address:
        return None
    
    try:
        # Use busybox devmem to read the register
        result = subprocess.run(
            ['busybox', 'devmem', hex(register_address)],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            # devmem returns hex value like "0x00000054"
            value_str = result.stdout.strip()
            if value_str.startswith('0x') or value_str.startswith('0X'):
                return int(value_str, 16)
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    
    return None

def decode_register_value(value):
    """Decode a pinmux register value into human-readable configuration"""
    if value is None:
        return None
    
    decoded = {
        'raw_value': value,
        'mode': 'GPIO' if (value & (1 << 10)) == 0 else 'SFIO',
        'tristate': 'Enabled' if (value & (1 << 6)) != 0 else 'Disabled',
        'input_enable': 'Enabled' if (value & (1 << 4)) != 0 else 'Disabled',
        'direction': None,
        'pull': None,
        'lpdr': 'Enabled' if (value & (1 << 11)) != 0 else 'Disabled',
    }
    
    # Determine direction based on input enable and mode
    if decoded['mode'] == 'GPIO':
        if decoded['input_enable'] == 'Enabled':
            decoded['direction'] = 'Input' if decoded['tristate'] == 'Enabled' else 'Bidirectional'
        else:
            decoded['direction'] = 'Output'
    
    # Decode pull configuration (bits 3:2)
    pull_bits = (value >> 2) & 0x3
    pull_map = {
        0: 'None',
        1: 'Pull-down',
        2: 'Pull-up',
        3: 'Reserved'
    }
    decoded['pull'] = pull_map.get(pull_bits, 'Unknown')
    
    return decoded

def find_gpio_chip_and_line(gpio_owner_str):
    """Find GPIO chip and line from owner string like tegra234-gpio:453"""
    if not gpio_owner_str or "UNCLAIMED" in gpio_owner_str:
        return None, None
        
    match = re.search(r':(\d+)', gpio_owner_str)
    if not match:
        return None, None
        
    global_gpio = int(match.group(1))
    
    # Try to find which gpiochip this belongs to
    try:
        result = subprocess.run(['gpioinfo'], capture_output=True, text=True)
        current_chip = None
        for line in result.stdout.split('\n'):
            if 'gpiochip' in line:
                current_chip = line.split()[0]
            elif f'line {global_gpio}:' in line or f'line  {global_gpio}:' in line:
                # Extract line number within chip
                match = re.search(r'line\s+(\d+):', line)
                if match:
                    return current_chip, int(match.group(1))
    except:
        pass
    
    return None, None

def extract_gpio_port_offset(soc_name):
    """Extract GPIO port and offset from SoC pin name like soc_gpio32_pq5"""
    # Format: soc_gpio32_pq5 -> Port: PQ, Offset: 5
    # Or: spi1_mosi_pz5 -> Port: PZ, Offset: 5
    match = re.search(r'_p([a-z]{1,2})(\d+)', soc_name, re.IGNORECASE)
    if match:
        port = match.group(1).upper()
        offset = int(match.group(2))
        return port, offset
    return None, None

def get_gpio_number_from_owner(gpio_owner_str):
    """Extract global GPIO number from owner string like tegra234-gpio:453"""
    if not gpio_owner_str or "UNCLAIMED" in gpio_owner_str:
        return None
    
    match = re.search(r':(\d+)', gpio_owner_str)
    if match:
        return int(match.group(1))
    return None

def get_gpio_direction_value(gpio_owner_str):
    """Get GPIO direction and value if accessible"""
    if not gpio_owner_str:
        return None, None
        
    match = re.search(r':(\d+)', gpio_owner_str)
    if not match:
        return None, None
        
    gpio_num = match.group(1)
    gpio_path = os.path.join(GPIO_BASE, f"gpio{gpio_num}")
    
    direction = None
    value = None
    
    if os.path.exists(gpio_path):
        try:
            with open(os.path.join(gpio_path, "direction"), 'r') as f:
                direction = f.read().strip()
        except IOError:
            pass
            
        try:
            with open(os.path.join(gpio_path, "value"), 'r') as f:
                value = f.read().strip()
        except IOError:
            pass
    
    return direction, value

def inspect_pin(pin_num):
    """Comprehensive pin inspection"""
    info = PinInfo(pin_num)
    
    if info.soc_name == "unknown":
        print(f"Pin {pin_num} is not a GPIO/configurable pin (power/ground)")
        return None
    
    # Extract port and offset from SoC name
    info.gpio_port, info.gpio_offset = extract_gpio_port_offset(info.soc_name)
    
    # Search all pinctrl controllers
    for ctrl_dir in os.listdir(PINCTRL_BASE):
        ctrl_path = os.path.join(PINCTRL_BASE, ctrl_dir)
        if not os.path.isdir(ctrl_path):
            continue
            
        ctrl_pin, gpio_from_pins = find_pin_in_controller(info.soc_name, ctrl_path)
        if ctrl_pin is not None:
            info.controller = ctrl_dir
            info.controller_pin_num = ctrl_pin
            
            # Use GPIO number from pins file if available (most reliable)
            if gpio_from_pins:
                info.gpio_number = gpio_from_pins
            
            info.available_functions = get_available_functions(info.soc_name, ctrl_path)
            
            mux, gpio, hogged = get_current_pinmux_state(info.soc_name, ctrl_path)
            info.current_mux_owner = mux
            info.current_gpio_owner = gpio
            info.is_hogged = hogged
            
            # Get current pin function configuration
            info.current_function = get_current_pin_function(info.soc_name, ctrl_path)
            
            # Get pinmux register address
            info.pinmux_register = get_pinmux_register_address(info.soc_name)
            
            # Read actual register value
            if info.pinmux_register:
                info.register_value = read_register_value(info.pinmux_register)
            
            # Extract GPIO number from gpio_owner as fallback
            if gpio and not info.gpio_number:
                info.gpio_number = get_gpio_number_from_owner(gpio)
            
            if gpio:
                info.gpio_chip, info.gpio_line = find_gpio_chip_and_line(gpio)
                info.gpio_direction, info.gpio_value = get_gpio_direction_value(gpio)
            
            break
    
    return info

def generate_dts_fragment(info):
    """Generate pinmux configuration fragment for device tree overlay"""
    if not info.controller or not info.available_functions:
        return None
    
    # Determine best GPIO function
    gpio_funcs = [f for f in info.available_functions if f in ["gp", "rsvd0", "rsvd1", "rsvd2", "rsvd3"]]
    if not gpio_funcs:
        print("\nWARNING: No GPIO-suitable functions found for this pin!")
        return None
    
    # Prefer rsvd0, then gp, then others
    if "rsvd0" in gpio_funcs:
        gpio_func = "rsvd0"
    elif "gp" in gpio_funcs:
        gpio_func = "gp"
    else:
        gpio_func = gpio_funcs[0]
    
    # Generate fragment - this will be hogged automatically when loaded
    dts = f"""                /* Pin {info.pin_num} ({info.soc_name}) */
                hdr40-pin{info.pin_num} {{
                    nvidia,pins = "{info.soc_name}";
                    nvidia,function = "{gpio_func}";
                    nvidia,pull = <0x0>;           /* 0=none, 1=down, 2=up */
                    nvidia,tristate = <0x0>;       /* 0=drive, 1=tristate */
                    nvidia,enable-input = <0x1>;   /* 0=output only, 1=input enabled */
                }};
"""
    
    return dts

def is_gpio_configured(info):
    """Check if pin is properly configured as GPIO via device tree"""
    # A pin is properly configured if:
    # 1. It's hogged (claimed at boot), OR
    # 2. It has a current_function set (configured in DT)
    #
    # Just having the register in GPIO mode is NOT enough!
    # Unconfigured pins can be in GPIO mode but floating/undefined
    
    if info.is_hogged:
        # Pin is explicitly hogged at boot - properly configured
        return True
    
    if info.current_function:
        # Pin has a function set in device tree
        gpio_funcs = ["gp", "rsvd0", "rsvd1", "rsvd2", "rsvd3"]
        if info.current_function in gpio_funcs:
            # Function is GPIO-related - properly configured
            return True
    
    # Pin might show GPIO mode in register but has no DT configuration
    # This is NOT properly configured and should not be used
    return False

def blink_pin(pin_num, cycles=10, interval=2.0):
    """Blink a GPIO pin using available GPIO interface"""
    import time
    
    # Get pin info to validate configuration
    info = inspect_pin(pin_num)
    if not info:
        print(f"Error: Could not inspect pin {pin_num}")
        return False
    
    # Check if pin is properly configured for GPIO
    if not is_gpio_configured(info):
        print(f"\nERROR: Pin {pin_num} is NOT properly configured for GPIO use")
        print(f"\nCurrent state:")
        print(f"  Hogged at boot: {info.is_hogged}")
        print(f"  Mux owner: {info.current_mux_owner or 'UNCLAIMED'}")
        print(f"  Current function: {info.current_function or 'Not configured'}")
        print(f"\nPin {pin_num} needs a device tree overlay to configure it for GPIO.")
        print(f"The overlay shown below will properly configure this pin.")
        print(f"\nDo NOT attempt to use GPIO on unconfigured pins - this can cause")
        print(f"undefined behavior, incorrect voltage levels, or hardware conflicts.")
        return False
    
    if not info.gpio_number:
        print(f"Error: Could not determine GPIO number for pin {pin_num}")
        print("       This should not happen for a properly configured GPIO pin")
        return False
    
    gpio_num = info.gpio_number
    
    # Try libgpiod first (modern approach)
    try:
        import gpiod
        return blink_with_libgpiod(gpio_num, pin_num, cycles, interval)
    except ImportError:
        pass  # Try sysfs fallback
    except Exception as e:
        print(f"libgpiod failed: {e}")
        print("Trying sysfs fallback...")
    
    # Fall back to sysfs
    return blink_with_sysfs(gpio_num, pin_num, cycles, interval)

def blink_with_libgpiod(gpio_num, pin_num, cycles, interval):
    """Blink using libgpiod (modern GPIO character device interface)"""
    import time
    import gpiod
    
    # Find the GPIO chip (usually gpiochip0 for tegra234-gpio)
    chip = gpiod.Chip('gpiochip0')
    
    try:
        # Request the GPIO line as output
        line = chip.get_line(gpio_num)
        line.request(consumer="pin_inspector", type=gpiod.LINE_REQ_DIR_OUT)
        
        print(f"\nBlinking pin {pin_num} (GPIO {gpio_num}) using libgpiod")
        print(f"Cycles: {cycles}, Interval: {interval}s")
        print("Press Ctrl+C to stop\n")
        
        for i in range(cycles):
            line.set_value(1)
            print(f"Cycle {i+1}/{cycles}: HIGH", end="", flush=True)
            time.sleep(interval)
            
            line.set_value(0)
            print(" -> LOW")
            time.sleep(interval)
        
        print(f"\nBlink test complete!")
        line.release()
        return True
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        line.release()
        return False
    except Exception as e:
        print(f"\nERROR during GPIO operation: {e}")
        try:
            line.release()
        except:
            pass
        return False

def blink_with_sysfs(gpio_num, pin_num, cycles, interval):
    """Blink using legacy sysfs interface (fallback for older systems)"""
    import time
    
    gpio_path = f"/sys/class/gpio/gpio{gpio_num}"
    export_path = "/sys/class/gpio/export"
    unexport_path = "/sys/class/gpio/unexport"
    
    # Check if sysfs interface exists
    if not os.path.exists("/sys/class/gpio"):
        print("\nERROR: GPIO interfaces not available")
        print("\nYour system uses the modern GPIO character device interface (/dev/gpiochip*).")
        print("The legacy sysfs interface (/sys/class/gpio) has been disabled.")
        print("\nTo use GPIO on this system:")
        print("  1. Install libgpiod: sudo apt-get install python3-libgpiod")
        print("  2. Re-run this script")
        print("\nAlternatively, enable sysfs GPIO in the kernel (not recommended).")
        return False
    
    if not os.path.exists(export_path):
        print("\nERROR: sysfs GPIO interface is disabled on this kernel")
        print("\nYour kernel has disabled the legacy /sys/class/gpio interface.")
        print("Install libgpiod to use the modern GPIO character device interface:")
        print("  sudo apt-get install python3-libgpiod")
        return False
    
    # Check if already exported
    already_exported = os.path.exists(gpio_path)
    
    try:
        # Export GPIO if needed
        if not already_exported:
            print(f"Exporting GPIO {gpio_num}...")
            with open(export_path, 'w') as f:
                f.write(str(gpio_num))
            time.sleep(0.1)
        
        # Set direction to output
        direction_file = os.path.join(gpio_path, "direction")
        with open(direction_file, 'w') as f:
            f.write("out")
        
        value_file = os.path.join(gpio_path, "value")
        
        print(f"\nBlinking pin {pin_num} (GPIO {gpio_num}) using sysfs")
        print(f"Cycles: {cycles}, Interval: {interval}s")
        print("Press Ctrl+C to stop\n")
        
        for i in range(cycles):
            with open(value_file, 'w') as f:
                f.write("1")
            print(f"Cycle {i+1}/{cycles}: HIGH", end="", flush=True)
            time.sleep(interval)
            
            with open(value_file, 'w') as f:
                f.write("0")
            print(" -> LOW")
            time.sleep(interval)
        
        print(f"\nBlink test complete!")
        
        if not already_exported:
            print(f"Unexporting GPIO {gpio_num}...")
            with open(unexport_path, 'w') as f:
                f.write(str(gpio_num))
        
        return True
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        if not already_exported:
            try:
                with open(unexport_path, 'w') as f:
                    f.write(str(gpio_num))
            except:
                pass
        return False
    except PermissionError:
        print(f"\nERROR: Permission denied accessing GPIO")
        print(f"       Run with sudo: sudo python3 pin_inspector.py {pin_num} --blink")
        return False
    except Exception as e:
        print(f"\nERROR during GPIO operation: {e}")
        if not already_exported:
            try:
                with open(unexport_path, 'w') as f:
                    f.write(str(gpio_num))
            except:
                pass
        return False

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Jetson Orin Pin Inspector - Diagnose 40-pin header GPIO configuration")
        print("\nUsage: sudo python3 pin_inspector.py <PIN_NUMBER> [--blink]")
        print("\nExamples:")
        print("  sudo python3 pin_inspector.py 29              # Inspect pin 29 (DC)")
        print("  sudo python3 pin_inspector.py 31              # Inspect pin 31 (RST)")
        print("  sudo python3 pin_inspector.py 29 --blink      # Test with blink")
        print("\nCommon ST7789 display pins:")
        print("  Pin 29: DC (Data/Command)")
        print("  Pin 31: RST (Reset)")
        print("  Pin 19: MOSI (SPI1)")
        print("  Pin 23: SCK (SPI1)")
        print("  Pin 24: CS0 (SPI1)")
        sys.exit(1)
    
    if os.geteuid() != 0:
        print("WARNING: Running without sudo. Some information may be unavailable.")
        print("         GPIO operations require sudo.\n")
    
    try:
        pin_num = int(sys.argv[1])
    except ValueError:
        print("Error: PIN_NUMBER must be an integer")
        sys.exit(1)
    
    if pin_num < 1 or pin_num > 40:
        print("Error: PIN_NUMBER must be between 1 and 40")
        sys.exit(1)
    
    want_blink = "--blink" in sys.argv or "-b" in sys.argv
    
    print(f"Inspecting pin {pin_num}...")
    info = inspect_pin(pin_num)
    
    if info:
        print(info)
        
        # Add explanation for hogged pins
        if info.is_hogged:
            print("NOTE: 'Hogged at boot' means the device tree pre-configured this pin")
            print("      at boot time. This is normal for GPIO pins - they're ready to use!\n")
        
        # Check if GPIO configured and offer to blink
        if is_gpio_configured(info):
            print("READY: Pin is configured as GPIO and ready to use!")
            
            if want_blink:
                if os.geteuid() != 0:
                    print("\nERROR: GPIO operations require sudo privileges")
                    print("       Run with: sudo python3 pin_inspector.py", pin_num, "--blink")
                else:
                    blink_pin(pin_num)
            else:
                print("\nTIP: Add --blink to test GPIO output")
                print(f"     sudo python3 pin_inspector.py {pin_num} --blink")
        else:
            print("WARNING: Pin is NOT configured as GPIO")
            print("         You must configure it with a device tree overlay first.")
            print("         The overlay below shows how to properly configure this pin.\n")
            
            if want_blink:
                print("\nERROR: Cannot blink - pin is not properly configured")
                print("       Install the device tree overlay shown below, then reboot.")
        
        dts = generate_dts_fragment(info)
        if dts:
            print("--- DEVICE TREE FRAGMENT (for overlay) ---")
            print(dts)
            print("NOTES:")
            print("   - This fragment configures the pinmux for GPIO mode")
            print("   - When loaded in an overlay, it will automatically hog the GPIO")
            print("   - Add this to your overlay's pinmux section")
            print("   - For output mode: change nvidia,enable-input to <0x0>")
            print("   - For pull-up: change nvidia,pull to <0x2>")
            print("   - For pull-down: change nvidia,pull to <0x1>")

if __name__ == "__main__":
    main()
