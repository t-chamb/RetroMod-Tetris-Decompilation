#!/usr/bin/env python3

import struct
import os
import png
from collections import Counter
import subprocess

def find_tetris_patterns(rom_data):
    """Look for classic Tetris piece patterns in ROM"""
    
    # Classic Tetris piece patterns in 2BPP format
    tetris_patterns = {
        'I_piece': [
            [0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00],  # Horizontal I
            [0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18]   # Vertical I
        ],
        'O_piece': [
            [0x00, 0x00, 0x66, 0x66, 0x66, 0x66, 0x00, 0x00]   # Square O
        ],
        'T_piece': [
            [0x00, 0x00, 0x18, 0x18, 0x7E, 0x7E, 0x00, 0x00]   # T shape
        ]
    }
    
    print("🔍 Searching for Tetris piece patterns...")
    found_patterns = []
    
    for piece_name, patterns in tetris_patterns.items():
        for pattern_idx, pattern in enumerate(patterns):
            pattern_bytes = bytes(pattern)
            
            # Search for this pattern in ROM
            pos = 0
            while True:
                pos = rom_data.find(pattern_bytes, pos)
                if pos == -1:
                    break
                
                bank = pos // 0x4000
                local_addr = pos % 0x4000
                found_patterns.append({
                    'piece': piece_name,
                    'pattern': pattern_idx,
                    'address': pos,
                    'bank': bank,
                    'local': local_addr
                })
                print(f"   Found {piece_name}[{pattern_idx}] at Bank {bank:02X}:${local_addr:04X} (${pos:06X})")
                pos += 1
    
    return found_patterns

def extract_surrounding_graphics(rom_data, address, size=1024):
    """Extract graphics around a found pattern"""
    start = max(0, address - size // 2)
    end = min(len(rom_data), address + size // 2)
    return rom_data[start:end], start

def test_all_possible_formats(data, name):
    """Test data in every possible graphics format"""
    formats_tested = {}
    
    # Standard 2BPP
    try:
        tiles = extract_2bpp_standard(data)
        if tiles and has_meaningful_patterns(tiles):
            save_tileset(tiles, f"final_test/{name}_2bpp_standard.png")
            formats_tested['2bpp_standard'] = len(tiles)
    except: pass
    
    # 2BPP with different bit ordering
    try:
        tiles = extract_2bpp_reversed(data)
        if tiles and has_meaningful_patterns(tiles):
            save_tileset(tiles, f"final_test/{name}_2bpp_reversed.png")
            formats_tested['2bpp_reversed'] = len(tiles)
    except: pass
    
    # 1BPP
    try:
        tiles = extract_1bpp(data)
        if tiles and has_meaningful_patterns(tiles):
            save_tileset(tiles, f"final_test/{name}_1bpp.png")
            formats_tested['1bpp'] = len(tiles)
    except: pass
    
    # Planar format (planes separated)
    try:
        tiles = extract_planar(data)
        if tiles and has_meaningful_patterns(tiles):
            save_tileset(tiles, f"final_test/{name}_planar.png")
            formats_tested['planar'] = len(tiles)
    except: pass
    
    # 4BPP format (for GBC)
    try:
        tiles = extract_4bpp(data)
        if tiles and has_meaningful_patterns(tiles):
            save_tileset(tiles, f"final_test/{name}_4bpp.png")
            formats_tested['4bpp'] = len(tiles)
    except: pass
    
    return formats_tested

def extract_2bpp_standard(data):
    """Standard Game Boy 2BPP"""
    tiles = []
    for i in range(0, len(data), 16):
        if i + 16 > len(data): break
        tile_data = data[i:i + 16]
        tile = []
        for row in range(8):
            if row * 2 + 1 < len(tile_data):
                byte1 = tile_data[row * 2]
                byte2 = tile_data[row * 2 + 1]
                for bit in range(7, -1, -1):
                    pixel = ((byte1 >> bit) & 1) | (((byte2 >> bit) & 1) << 1)
                    tile.append(pixel)
        if len(tile) == 64: tiles.append(tile)
    return tiles

def extract_2bpp_reversed(data):
    """2BPP with bit order reversed"""
    tiles = []
    for i in range(0, len(data), 16):
        if i + 16 > len(data): break
        tile_data = data[i:i + 16]
        tile = []
        for row in range(8):
            if row * 2 + 1 < len(tile_data):
                byte1 = tile_data[row * 2]
                byte2 = tile_data[row * 2 + 1]
                for bit in range(8):  # Forward instead of reverse
                    pixel = ((byte1 >> bit) & 1) | (((byte2 >> bit) & 1) << 1)
                    tile.append(pixel)
        if len(tile) == 64: tiles.append(tile)
    return tiles

def extract_1bpp(data):
    """1 bit per pixel"""
    tiles = []
    for i in range(0, len(data), 8):
        if i + 8 > len(data): break
        tile_data = data[i:i + 8]
        tile = []
        for byte in tile_data:
            for bit in range(7, -1, -1):
                pixel = ((byte >> bit) & 1) * 3
                tile.append(pixel)
        if len(tile) == 64: tiles.append(tile)
    return tiles

def extract_planar(data):
    """Planar format - all plane 1 bytes, then all plane 2 bytes"""
    tiles = []
    half = len(data) // 2
    plane1 = data[:half]
    plane2 = data[half:]
    
    for i in range(0, min(len(plane1), len(plane2)), 8):
        if i + 8 > len(plane1): break
        tile = []
        for row in range(8):
            if row < len(plane1[i:i+8]) and row < len(plane2[i:i+8]):
                byte1 = plane1[i + row]
                byte2 = plane2[i + row]
                for bit in range(7, -1, -1):
                    pixel = ((byte1 >> bit) & 1) | (((byte2 >> bit) & 1) << 1)
                    tile.append(pixel)
        if len(tile) == 64: tiles.append(tile)
    return tiles

def extract_4bpp(data):
    """4 bits per pixel (GBC mode)"""
    tiles = []
    for i in range(0, len(data), 32):  # 32 bytes per tile in 4BPP
        if i + 32 > len(data): break
        tile_data = data[i:i + 32]
        tile = []
        for row in range(8):
            row_start = row * 4
            if row_start + 4 <= len(tile_data):
                for byte_idx in range(4):
                    byte_val = tile_data[row_start + byte_idx]
                    # Extract 2 pixels per byte
                    pixel1 = (byte_val >> 4) & 0xF
                    pixel2 = byte_val & 0xF
                    tile.extend([pixel1 % 4, pixel2 % 4])  # Clamp to 2bpp for display
        if len(tile) == 64: tiles.append(tile)
    return tiles

def has_meaningful_patterns(tiles):
    """Check if tiles contain meaningful patterns vs noise"""
    if not tiles or len(tiles) < 4:
        return False
    
    # Count non-empty tiles
    non_empty = 0
    for tile in tiles[:16]:  # Check first 16 tiles
        non_zero_pixels = sum(1 for p in tile if p != 0)
        if 4 <= non_zero_pixels <= 60:  # Not empty, not solid
            non_empty += 1
    
    return non_empty >= 2

def save_tileset(tiles, filename, tiles_per_row=16):
    """Save tiles as PNG"""
    if not tiles: return False
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    rows = (len(tiles) + tiles_per_row - 1) // tiles_per_row
    colors = [255, 170, 85, 0]
    
    image = []
    for row in range(rows):
        for y in range(8):
            row_pixels = []
            for col in range(tiles_per_row):
                tile_idx = row * tiles_per_row + col
                if tile_idx < len(tiles):
                    tile = tiles[tile_idx]
                    for x in range(8):
                        pixel_value = tile[y * 8 + x]
                        row_pixels.append(colors[pixel_value])
                else:
                    row_pixels.extend([255] * 8)
            image.append(row_pixels)
    
    with open(filename, 'wb') as f:
        w = png.Writer(width=len(image[0]), height=len(image), greyscale=True)
        w.write(f, image)
    return True

def brute_force_graphics_search(rom_data):
    """Try to find graphics by brute force searching every possible location"""
    print("🔥 Brute force graphics search...")
    
    os.makedirs("final_test", exist_ok=True)
    promising_regions = []
    
    # Test every 1KB region in the ROM
    for offset in range(0, len(rom_data) - 1024, 512):
        region = rom_data[offset:offset + 1024]
        
        # Quick quality check
        freq = Counter(region)
        unique_bytes = len(freq)
        
        if 16 <= unique_bytes <= 64:  # Reasonable for graphics
            bank = offset // 0x4000
            local = offset % 0x4000
            
            # Test all formats
            formats = test_all_possible_formats(region, f"bank_{bank:02X}_{local:04X}")
            
            if formats:
                promising_regions.append((offset, formats))
                print(f"   Bank {bank:02X}:${local:04X} - Found formats: {formats}")
    
    return promising_regions

def main():
    rom_file = "Tetris (World) (ModRetro Chromatic) (Aftermarket) (Unl) 2.gbc"
    
    print("🎯 Final Graphics Extraction Attempt")
    print("=" * 60)
    
    with open(rom_file, 'rb') as f:
        rom_data = f.read()
    
    # Step 1: Look for known Tetris patterns
    tetris_patterns = find_tetris_patterns(rom_data)
    
    if tetris_patterns:
        print(f"\n✅ Found {len(tetris_patterns)} Tetris patterns!")
        
        # Extract graphics around each pattern
        for pattern in tetris_patterns[:5]:  # Test first 5
            addr = pattern['address']
            data, start_addr = extract_surrounding_graphics(rom_data, addr)
            
            bank = start_addr // 0x4000
            local = start_addr % 0x4000
            name = f"tetris_{pattern['piece']}_{bank:02X}_{local:04X}"
            
            formats = test_all_possible_formats(data, name)
            if formats:
                print(f"   Pattern at ${addr:06X} -> formats: {formats}")
    else:
        print("❌ No classic Tetris patterns found")
    
    # Step 2: Brute force search
    print(f"\n🔥 Brute force searching entire ROM...")
    promising = brute_force_graphics_search(rom_data)
    
    if promising:
        print(f"\n✅ Found {len(promising)} promising regions!")
        print("\nBest candidates:")
        for offset, formats in promising[:10]:
            bank = offset // 0x4000
            local = offset % 0x4000
            print(f"   Bank {bank:02X}:${local:04X} - {formats}")
    
    print(f"\n🎉 Analysis complete!")
    print(f"Check the final_test/ folder for extracted graphics.")
    print(f"Look for files with recognizable Tetris patterns:")
    print(f"  - Piece shapes (I, O, T, L, J, S, Z)")
    print(f"  - Numbers and letters")  
    print(f"  - Border/UI elements")

if __name__ == "__main__":
    main()