#!/usr/bin/env python3
"""
Convert decompiled device tree overlays with numeric phandles to source files
with proper label references.

This script parses the __fixups__, __symbols__, and __local_fixups__ sections
from a decompiled DTS file and reconstructs the original source with label
references instead of numeric phandles.
"""

import re
import sys
import argparse
from pathlib import Path


class DTSConverter:
    def __init__(self, dts_content):
        self.content = dts_content
        self.fixups = {}  # Maps fragment paths to target labels
        self.symbols = {}  # Maps label names to their paths
        self.local_fixups = {}  # Maps paths to local phandle offsets
        self.phandle_to_label = {}  # Maps phandle numbers to label names
        
    def parse_fixups(self):
        """Parse __fixups__ section to find fragment targets."""
        fixups_match = re.search(
            r'__fixups__\s*\{([^}]+)\};',
            self.content,
            re.DOTALL
        )
        if not fixups_match:
            return
            
        fixups_content = fixups_match.group(1)
        # Match: label = "/fragment@N:target:0";
        for match in re.finditer(r'(\w+)\s*=\s*"(/fragment@\d+):target:\d+"', fixups_content):
            target_label = match.group(1)
            fragment_path = match.group(2)
            self.fixups[fragment_path] = target_label
    
    def parse_symbols(self):
        """Parse __symbols__ section to find label definitions."""
        symbols_match = re.search(
            r'__symbols__\s*\{([^}]+)\};',
            self.content,
            re.DOTALL
        )
        if not symbols_match:
            return
            
        symbols_content = symbols_match.group(1)
        # Match: label_name = "/path/to/node";
        for match in re.finditer(r'(\w+)\s*=\s*"([^"]+)"', symbols_content):
            label_name = match.group(1)
            path = match.group(2)
            self.symbols[label_name] = path
    
    def parse_local_fixups(self):
        """Parse __local_fixups__ section to find internal phandle references."""
        local_fixups_match = re.search(
            r'__local_fixups__\s*\{(.+?)\n\s*\};',
            self.content,
            re.DOTALL
        )
        if not local_fixups_match:
            return
            
        # Build a simple mapping of property paths that have local fixups
        local_content = local_fixups_match.group(1)
        # This is simplified - we just need to know which properties reference phandles
        for match in re.finditer(r'(pinctrl-\d+)\s*=', local_content):
            # Mark these as needing label conversion
            self.local_fixups[match.group(1)] = True
    
    def build_phandle_map(self):
        """Build mapping from phandle numbers to their label names."""
        # Find nodes with explicit phandle assignments
        for match in re.finditer(r'phandle\s*=\s*<(0x[0-9a-fA-F]+)>', self.content):
            phandle_num = match.group(1)
            
            # Find which symbol this phandle corresponds to by searching nearby context
            start = max(0, match.start() - 500)
            context = self.content[start:match.end() + 100]
            
            # Look for the node name before the phandle
            node_match = re.search(r'(\w+[-\w]*)\s*\{[^}]*phandle\s*=\s*<' + phandle_num, context)
            if node_match:
                node_name = node_match.group(1)
                # Find matching symbol
                for label, path in self.symbols.items():
                    if node_name in path:
                        self.phandle_to_label[phandle_num] = label
                        break
    
    def remove_metadata_sections(self, text):
        """Remove __fixups__, __symbols__, and __local_fixups__ sections using brace tracking."""
        sections_to_remove = ['__fixups__', '__symbols__', '__local_fixups__']
        
        for section in sections_to_remove:
            # Find the section start
            pattern = re.compile(r'\n(\s*)' + re.escape(section) + r'\s*\{')
            match = pattern.search(text)
            
            if not match:
                continue
            
            # Track brace depth to find the matching closing brace
            start_pos = match.start()
            brace_start = match.end() - 1  # Position of opening {
            depth = 1
            pos = brace_start + 1
            
            while pos < len(text) and depth > 0:
                if text[pos] == '{':
                    depth += 1
                elif text[pos] == '}':
                    depth -= 1
                pos += 1
            
            if depth == 0:
                # Found the matching close brace, look for the semicolon
                end_pos = pos
                while end_pos < len(text) and text[end_pos] in ' \t\n':
                    end_pos += 1
                if end_pos < len(text) and text[end_pos] == ';':
                    end_pos += 1
                
                # Remove the entire section
                text = text[:start_pos] + text[end_pos:]
        
        return text
    
    def convert(self):
        """Perform the conversion."""
        self.parse_fixups()
        self.parse_symbols()
        self.parse_local_fixups()
        self.build_phandle_map()
        
        result = self.content
        
        # 1. Add /plugin/ if not present
        if '/plugin/;' not in result:
            result = re.sub(r'(/dts-v1/;)', r'\1\n/plugin/;', result)
        
        # 2. Replace fragment targets
        for fragment_path, target_label in self.fixups.items():
            # Extract fragment number
            fragment_num = fragment_path.split('@')[1]
            # Replace target = <0xffffffff>; with target = <&label>;
            pattern = r'(fragment@' + fragment_num + r'\s*\{\s*)target\s*=\s*<0x[fF]+>;'
            replacement = r'\1target = <&' + target_label + '>;'
            result = re.sub(pattern, replacement, result)
        
        # 3. Replace pinctrl references with labels
        for label, path in self.symbols.items():
            # Find the phandle number for this label
            phandle_num = None
            for phandle, lab in self.phandle_to_label.items():
                if lab == label:
                    phandle_num = phandle
                    break
            
            if phandle_num:
                # Replace pinctrl-0 = <0x01>; with pinctrl-0 = <&label>;
                result = re.sub(
                    r'pinctrl-0\s*=\s*<' + phandle_num + r'>;',
                    'pinctrl-0 = <&' + label + '>;',
                    result
                )
        
        # 4. Add labels to node definitions and remove manual phandles
        for label, path in self.symbols.items():
            # Extract the node name from the path
            node_name = path.split('/')[-1]
            # Extract fragment number from path
            fragment_match = re.search(r'fragment@(\d+)', path)
            if not fragment_match:
                continue
            fragment_num = fragment_match.group(1)
            
            # Find the node in the specific fragment and add label, remove phandle
            # We need to be more specific to avoid replacing in wrong fragments
            # Pattern: match within the correct fragment
            pattern = (
                r'(fragment@' + fragment_num + r'.*?__overlay__.*?)' +
                r'(' + re.escape(node_name) + r')\s*\{\s*phandle\s*=\s*<0x[0-9a-fA-F]+>;'
            )
            replacement = r'\1' + label + r': \2 {'
            result = re.sub(pattern, replacement, result, flags=re.DOTALL)
        
        # 5. Remove __fixups__, __symbols__, and __local_fixups__ sections
        result = self.remove_metadata_sections(result)
        
        # 6. Format compatible strings (one per line if multiple)
        def format_compatible(match):
            compat_str = match.group(1)
            # Split on \0 (null char in decompiled format)
            items = compat_str.split('\\0')
            if len(items) > 1:
                formatted = ',\n\t             '.join(f'"{item}"' for item in items if item)
                return f'compatible = {formatted};'
            return match.group(0)
        
        result = re.sub(
            r'compatible\s*=\s*"([^"]+)";',
            format_compatible,
            result
        )
        
        # 7. Clean up extra blank lines
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
        
        return result


def main():
    parser = argparse.ArgumentParser(
        description='Convert decompiled DTS files to source format with label references',
        epilog='Example: %(prog)s input.dts -o output.dts'
    )
    parser.add_argument(
        'input',
        type=Path,
        help='Input decompiled DTS file'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output DTS file (default: input_converted.dts)'
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        output_file = args.input.parent / f"{args.input.stem}_converted{args.input.suffix}"
    
    # Read input
    try:
        content = args.input.read_text()
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Convert
    converter = DTSConverter(content)
    result = converter.convert()
    
    # Write output
    try:
        output_file.write_text(result)
        print(f"Converted DTS written to: {output_file}")
        print(f"\nCompile with:")
        print(f"  dtc -@ -I dts -O dtb -o {output_file.stem}.dtbo {output_file}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
