#!/usr/bin/env python3

import struct
import os
from collections import Counter

def analyze_homebrew_rom(filename):
    """Analyze homebrew ROM for custom patterns"""
    with open(filename, 'rb') as f:
        rom_data = f.read()
    
    print("🏠 Homebrew ROM Analysis")
    print("=" * 50)
    print(f"ROM Size: {len(rom_data)} bytes ({len(rom_data)//1024}KB)")
    
    # Check ROM header
    if len(rom_data) >= 0x150:
        print("\n📋 ROM Header Analysis:")
        
        # Nintendo logo check (should be at 0x104)
        nintendo_logo = rom_data[0x104:0x134]
        expected_logo = bytes([
            0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B, 0x03, 0x73, 0x00, 0x83, 0x00, 0x0C, 0x00, 0x0D,
            0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E, 0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99,
            0xBB, 0xBB, 0x67, 0x63, 0x6E, 0x0E, 0xEC, 0xCC, 0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E
        ])
        
        if nintendo_logo == expected_logo:
            print("✅ Nintendo logo: Valid")
        else:
            print("❌ Nintendo logo: Invalid/Modified")
            print("   This suggests custom bootloader or homebrew toolkit")
        
        # Title
        title = rom_data[0x134:0x144].decode('ascii', errors='ignore').rstrip('\x00')
        print(f"🏷️  Title: '{title}'")
        
        # CGB flag
        cgb_flag = rom_data[0x143]
        print(f"🎨 CGB Flag: 0x{cgb_flag:02X} ", end="")
        if cgb_flag == 0x80:
            print("(GBC compatible)")
        elif cgb_flag == 0xC0:
            print("(GBC only)")
        else:
            print("(DMG/original GB)")
        
        # ROM size
        rom_size_code = rom_data[0x148]
        print(f"💾 ROM Size Code: 0x{rom_size_code:02X}")
        
        # RAM size
        ram_size_code = rom_data[0x149]
        print(f"🧠 RAM Size Code: 0x{ram_size_code:02X}")
    
    # Look for homebrew development signatures
    print("\n🔍 Homebrew Signatures:")
    
    # Common homebrew tools
    homebrew_sigs = {
        b'GBDK': 'Game Boy Development Kit',
        b'RGBDS': 'Rednex Game Boy Development System', 
        b'ASMotor': 'ASMotor assembler',
        b'WLA-DX': 'WLA DX assembler',
        b'BGB': 'BGB debugger/emulator',
        b'SameBoy': 'SameBoy emulator',
        b'MGBDIS': 'mgbdis disassembler'
    }
    
    for sig, name in homebrew_sigs.items():
        if sig in rom_data:
            print(f"✅ Found: {name}")
    
    # Look for custom compression markers
    print("\n🗜️  Custom Compression Analysis:")
    
    # Count different compression markers
    markers = {}
    for i in range(len(rom_data) - 1):
        byte = rom_data[i]
        if byte in [0x10, 0x11, 0x20, 0x30, 0x40]:  # Common compression markers
            markers[byte] = markers.get(byte, 0) + 1
    
    for marker, count in sorted(markers.items()):
        print(f"   0x{marker:02X}: {count} occurrences")
    
    # Analyze byte frequency for entropy
    print("\n📊 Data Entropy Analysis:")
    freq = Counter(rom_data)
    entropy_score = len(freq) / 256 * 100
    print(f"   Unique bytes: {len(freq)}/256 ({entropy_score:.1f}%)")
    
    # Most common bytes
    most_common = freq.most_common(5)
    print("   Most common bytes:")
    for byte, count in most_common:
        percentage = count / len(rom_data) * 100
        print(f"     0x{byte:02X}: {count} times ({percentage:.1f}%)")
    
    # Look for repeated patterns (possible graphics)
    print("\n🎨 Graphics Pattern Analysis:")
    
    # Find regions with low entropy (possible graphics)
    chunk_size = 1024
    low_entropy_regions = []
    
    for i in range(0, len(rom_data) - chunk_size, chunk_size):
        chunk = rom_data[i:i + chunk_size]
        chunk_freq = Counter(chunk)
        unique_ratio = len(chunk_freq) / min(256, len(chunk))
        
        # Graphics typically have moderate entropy (not too high, not too low)
        if 0.1 < unique_ratio < 0.4:
            low_entropy_regions.append((i, unique_ratio))
    
    print(f"   Found {len(low_entropy_regions)} potential graphics regions:")
    for addr, ratio in low_entropy_regions[:10]:  # Show first 10
        bank = addr // 0x4000
        local = addr % 0x4000
        print(f"     Bank {bank:02X}:${local:04X} (${addr:06X}) - entropy {ratio:.3f}")
    
    # Check for tile-like patterns
    print("\n🧩 Tile Pattern Analysis:")
    tile_patterns = 0
    for i in range(0, len(rom_data) - 16, 16):
        chunk = rom_data[i:i + 16]
        
        # Check if it looks like 2BPP tile data
        non_zero = sum(1 for b in chunk if b != 0)
        if 4 <= non_zero <= 12:  # Reasonable for tile data
            # Check for bit patterns typical of sprites/tiles
            has_pattern = any(b in [0x18, 0x24, 0x42, 0x81, 0x7E, 0xC3] for b in chunk)
            if has_pattern:
                tile_patterns += 1
    
    print(f"   Found {tile_patterns} potential tile patterns")
    
    return {
        'size': len(rom_data),
        'low_entropy_regions': low_entropy_regions,
        'tile_patterns': tile_patterns,
        'compression_markers': markers
    }

def main():
    rom_file = "Tetris (World) (ModRetro Chromatic) (Aftermarket) (Unl) 2.gbc"
    
    if not os.path.exists(rom_file):
        print(f"❌ ROM file not found: {rom_file}")
        return
    
    analysis = analyze_homebrew_rom(rom_file)
    
    print("\n🎯 Recommendations:")
    
    if analysis['compression_markers'].get(0x10, 0) > 20:
        print("✅ High 0x10 marker count suggests LZ77 compression")
        print("   - Continue with LZ77 decompression approach")
        print("   - Check for custom LZ77 variants")
    
    if analysis['tile_patterns'] > 50:
        print("✅ Many tile patterns found")
        print("   - Try extracting as raw 2BPP tiles")
        print("   - Look in low-entropy regions first")
    
    if analysis['low_entropy_regions']:
        print("✅ Low entropy regions found")
        print("   - These are prime candidates for graphics data")
        print("   - Try both compressed and uncompressed extraction")
    
    print("\n💡 Next Steps:")
    print("1. Focus on the low-entropy regions for graphics")
    print("2. Try raw tile extraction on promising regions")
    print("3. Use VRAM capture to validate results")
    print("4. Look for homebrew-specific compression variants")

if __name__ == "__main__":
    main()