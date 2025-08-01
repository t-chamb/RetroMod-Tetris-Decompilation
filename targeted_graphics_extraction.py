#!/usr/bin/env python3

import struct
import os
import png
from collections import Counter

def decompress_lz77_safe(data, offset):
    """Safe LZ77 decompression with validation"""
    try:
        output = bytearray()
        pos = offset
        
        if pos >= len(data) or data[pos] != 0x10:
            return None, "No LZ77 marker"
        pos += 1
        
        if pos + 3 > len(data):
            return None, "Size header truncated"
        size = data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16)
        pos += 3
        
        if size == 0 or size > 0x10000:
            return None, f"Invalid size: {size}"
        
        start_pos = pos
        while len(output) < size and pos < len(data):
            if pos >= len(data):
                break
                
            control = data[pos]
            pos += 1
            
            for i in range(8):
                if len(output) >= size or pos >= len(data):
                    break
                    
                if control & 0x80:  # Compressed
                    if pos + 2 > len(data):
                        break
                    byte1, byte2 = data[pos], data[pos + 1]
                    pos += 2
                    
                    distance = ((byte1 & 0xF) << 8) | byte2
                    length = (byte1 >> 4) + 3
                    
                    if distance == 0:
                        break
                        
                    for j in range(length):
                        if len(output) > distance:
                            output.append(output[len(output) - distance - 1])
                        else:
                            output.append(0)
                else:  # Literal
                    if pos < len(data):
                        output.append(data[pos])
                        pos += 1
                    
                control <<= 1
        
        compressed_size = pos - start_pos
        return bytes(output), f"OK ({compressed_size} -> {len(output)})"
    except Exception as e:
        return None, f"Error: {e}"

def extract_raw_tiles(data, offset, count=64):
    """Extract raw 2BPP tiles from data"""
    tiles = []
    pos = offset
    
    for tile_num in range(count):
        if pos + 16 > len(data):
            break
            
        tile_data = data[pos:pos + 16]
        tile = []
        
        for row in range(8):
            if row * 2 + 1 < len(tile_data):
                byte1 = tile_data[row * 2]
                byte2 = tile_data[row * 2 + 1]
                for bit in range(7, -1, -1):
                    pixel = ((byte1 >> bit) & 1) | (((byte2 >> bit) & 1) << 1)
                    tile.append(pixel)
        
        if len(tile) == 64:
            tiles.append(tile)
        pos += 16
    
    return tiles

def save_tileset(tiles, filename, tiles_per_row=16):
    """Save tiles as PNG"""
    if not tiles:
        return False
    
    rows = (len(tiles) + tiles_per_row - 1) // tiles_per_row
    colors = [255, 170, 85, 0]  # Game Boy palette
    
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

def analyze_region_quality(data):
    """Score how much a region looks like graphics"""
    if len(data) < 64:
        return 0
    
    # Check byte distribution
    freq = Counter(data)
    unique_bytes = len(freq)
    
    # Graphics have moderate entropy
    if unique_bytes < 8 or unique_bytes > 80:
        return 0
    
    # Check for tile-like patterns
    tile_score = 0
    for i in range(0, min(len(data), 512), 16):
        chunk = data[i:i+16]
        if len(chunk) == 16:
            non_zero = sum(1 for b in chunk if b != 0)
            if 4 <= non_zero <= 12:
                tile_score += 1
    
    return tile_score + (40 - abs(unique_bytes - 32))

def main():
    rom_file = "Tetris (World) (ModRetro Chromatic) (Aftermarket) (Unl) 2.gbc"
    
    with open(rom_file, 'rb') as f:
        rom_data = f.read()
    
    print("🎯 Targeted Graphics Extraction")
    print("=" * 50)
    
    os.makedirs("targeted_extraction", exist_ok=True)
    
    # Low-entropy regions from homebrew analysis
    target_regions = [
        (0x002800, "Bank00_2800"),
        (0x003800, "Bank00_3800"), 
        (0x004400, "Bank01_0400"),
        (0x004800, "Bank01_0800"),
        (0x005800, "Bank01_1800"),
        (0x006400, "Bank01_2400"),
        (0x006C00, "Bank01_2C00"),
        (0x007000, "Bank01_3000"),
        (0x008000, "Bank02_0000"),
        (0x008400, "Bank02_0400")
    ]
    
    print("🔍 Testing low-entropy regions as raw tiles:")
    
    for offset, name in target_regions:
        if offset + 1024 > len(rom_data):
            continue
            
        # Try as raw tiles
        tiles = extract_raw_tiles(rom_data, offset, 64)
        if tiles:
            filename = f"targeted_extraction/{name}_raw.png"
            if save_tileset(tiles, filename):
                # Analyze quality
                region_data = rom_data[offset:offset + 1024]
                quality = analyze_region_quality(region_data)
                print(f"✅ {name}: {len(tiles)} tiles, quality={quality}")
    
    print("\n🗜️  Re-testing LZ77 blocks in promising regions:")
    
    # Look for LZ77 blocks specifically in low-entropy areas
    for offset, name in target_regions:
        region_start = offset
        region_end = min(offset + 4096, len(rom_data))
        
        # Search for 0x10 markers in this region
        for search_offset in range(region_start, region_end - 4):
            if rom_data[search_offset] == 0x10:
                # Try decompression
                data, status = decompress_lz77_safe(rom_data, search_offset)
                if data and len(data) >= 256:
                    quality = analyze_region_quality(data)
                    if quality > 20:
                        # Extract as tiles
                        tiles = extract_raw_tiles(data, 0, min(len(data) // 16, 128))
                        if tiles:
                            rel_offset = search_offset - region_start
                            filename = f"targeted_extraction/{name}_lz77_{rel_offset:04X}.png"
                            if save_tileset(tiles, filename):
                                print(f"✅ {name}+{rel_offset:04X}: LZ77 {status}, {len(tiles)} tiles, quality={quality}")
    
    print("\n🎨 Testing alternative tile formats:")
    
    # Test some promising regions with different interpretations
    test_regions = [
        (0x002800, "Bank00_2800"),
        (0x008000, "Bank02_0000")
    ]
    
    for offset, name in test_regions:
        if offset + 1024 > len(rom_data):
            continue
            
        region_data = rom_data[offset:offset + 1024]
        
        # Test as 1BPP tiles
        tiles_1bpp = []
        for i in range(0, len(region_data), 8):
            if i + 8 > len(region_data):
                break
            tile_data = region_data[i:i + 8]
            tile = []
            for byte in tile_data:
                for bit in range(7, -1, -1):
                    pixel = ((byte >> bit) & 1) * 3  # Convert to 2bpp scale
                    tile.append(pixel)
            if len(tile) == 64:
                tiles_1bpp.append(tile)
        
        if tiles_1bpp:
            filename = f"targeted_extraction/{name}_1bpp.png"
            if save_tileset(tiles_1bpp, filename):
                print(f"✅ {name}: 1BPP format, {len(tiles_1bpp)} tiles")
        
        # Test as interleaved format (some homebrew games use this)
        tiles_interleaved = []
        for i in range(0, len(region_data) - 16, 32):
            if i + 32 > len(region_data):
                break
                
            # Take bytes 0,2,4,6,8,10,12,14 as plane 1
            # Take bytes 1,3,5,7,9,11,13,15 as plane 2
            plane1 = region_data[i:i+16:2]
            plane2 = region_data[i+1:i+16:2]
            
            if len(plane1) == 8 and len(plane2) == 8:
                tile = []
                for row in range(8):
                    byte1 = plane1[row]
                    byte2 = plane2[row]
                    for bit in range(7, -1, -1):
                        pixel = ((byte1 >> bit) & 1) | (((byte2 >> bit) & 1) << 1)
                        tile.append(pixel)
                if len(tile) == 64:
                    tiles_interleaved.append(tile)
        
        if tiles_interleaved:
            filename = f"targeted_extraction/{name}_interleaved.png"
            if save_tileset(tiles_interleaved, filename):
                print(f"✅ {name}: Interleaved format, {len(tiles_interleaved)} tiles")
    
    print("\n🎉 Extraction complete! Check targeted_extraction/ folder")
    print("Look for images that show recognizable Tetris patterns:")
    print("  - Tetris pieces (I, O, T, S, Z, J, L shapes)")
    print("  - Numbers/letters (score display)")
    print("  - Border/frame patterns")

if __name__ == "__main__":
    main()