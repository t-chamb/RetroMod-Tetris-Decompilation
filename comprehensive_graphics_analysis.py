#!/usr/bin/env python3

import struct
import os
import png
from collections import Counter

def decompress_lz77_safe(data, offset):
    """Safe LZ77 decompression with better error handling"""
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
        
        if size == 0 or size > 0x10000:  # Sanity check
            return None, f"Invalid size: {size}"
        
        original_pos = pos
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
                    output.append(data[pos])
                    pos += 1
                    
                control <<= 1
        
        compressed_size = pos - original_pos + 4  # Include header
        return bytes(output), f"OK ({compressed_size} compressed -> {len(output)} decompressed)"
    except Exception as e:
        return None, f"Error: {e}"

def analyze_data_patterns(data):
    """Analyze if data looks like graphics"""
    if len(data) < 64:
        return {"score": 0, "reason": "Too short"}
    
    # Count byte frequencies
    freq = Counter(data)
    unique_bytes = len(freq)
    
    # Graphics typically have moderate entropy
    if unique_bytes < 4:
        return {"score": 0, "reason": f"Too few unique bytes: {unique_bytes}"}
    if unique_bytes > 128:
        return {"score": 0, "reason": f"Too many unique bytes: {unique_bytes}"}
    
    # Check for repeated patterns (tiles)
    pattern_score = 0
    for i in range(0, min(len(data), 256), 16):
        chunk = data[i:i+16]
        if len(chunk) == 16:
            # Count non-zero bytes
            non_zero = sum(1 for b in chunk if b != 0)
            if 4 <= non_zero <= 12:  # Reasonable for tile data
                pattern_score += 1
    
    # Check for Game Boy specific patterns
    gb_patterns = [0x00, 0xFF, 0xF0, 0x0F, 0x18, 0x24, 0x42, 0x81]
    gb_score = sum(1 for pattern in gb_patterns if pattern in freq)
    
    total_score = pattern_score + gb_score + (50 - abs(unique_bytes - 32))
    return {
        "score": total_score,
        "unique_bytes": unique_bytes,
        "pattern_score": pattern_score,
        "gb_score": gb_score,
        "reason": "Analyzed"
    }

def test_different_formats(data, name):
    """Test data as different graphics formats"""
    results = []
    
    # Test as 2BPP Game Boy format
    try:
        tiles = extract_2bpp_tiles(data)
        if tiles:
            save_tileset(tiles, f"test_format_{name}_2bpp.png")
            results.append(f"2BPP: {len(tiles)} tiles")
    except:
        results.append("2BPP: Failed")
    
    # Test as 1BPP format
    try:
        tiles = extract_1bpp_tiles(data)
        if tiles:
            save_tileset(tiles, f"test_format_{name}_1bpp.png")
            results.append(f"1BPP: {len(tiles)} tiles")
    except:
        results.append("1BPP: Failed")
    
    # Test as raw bitmap
    try:
        save_raw_bitmap(data, f"test_format_{name}_raw.png")
        results.append("RAW: Saved")
    except:
        results.append("RAW: Failed")
    
    return results

def extract_2bpp_tiles(data):
    """Extract Game Boy 2BPP tiles"""
    tiles = []
    for i in range(0, len(data), 16):
        if i + 16 > len(data):
            break
        tile_data = data[i:i + 16]
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
    return tiles

def extract_1bpp_tiles(data):
    """Extract 1BPP tiles"""
    tiles = []
    for i in range(0, len(data), 8):
        if i + 8 > len(data):
            break
        tile_data = data[i:i + 8]
        tile = []
        for byte in tile_data:
            for bit in range(7, -1, -1):
                pixel = (byte >> bit) & 1
                tile.append(pixel * 3)  # Convert to 2bpp scale
        if len(tile) == 64:
            tiles.append(tile)
    return tiles

def save_tileset(tiles, filename):
    """Save tiles as PNG"""
    if not tiles:
        return False
    
    tiles_per_row = 16
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

def save_raw_bitmap(data, filename, width=128):
    """Save data as raw bitmap"""
    height = len(data) // (width // 8)
    if height < 8:
        height = 8
    
    image = []
    for y in range(height):
        row = []
        for x in range(width // 8):
            byte_idx = y * (width // 8) + x
            if byte_idx < len(data):
                byte_val = data[byte_idx]
                for bit in range(7, -1, -1):
                    pixel = 255 if (byte_val >> bit) & 1 else 0
                    row.append(pixel)
            else:
                row.extend([255] * 8)
        image.append(row)
    
    with open(filename, 'wb') as f:
        w = png.Writer(width=width, height=len(image), greyscale=True)
        w.write(f, image)

def main():
    rom_file = "Tetris (World) (ModRetro Chromatic) (Aftermarket) (Unl) 2.gbc"
    
    print("🔍 Comprehensive Graphics Analysis")
    print("=" * 60)
    
    with open(rom_file, 'rb') as f:
        rom_data = f.read()
    
    # Find all LZ77 candidates
    candidates = []
    for offset in range(0, len(rom_data) - 4):
        if rom_data[offset] == 0x10:
            size = rom_data[offset + 1] | (rom_data[offset + 2] << 8) | (rom_data[offset + 3] << 16)
            if 0x80 <= size <= 0x4000:  # Reasonable graphics size
                candidates.append((offset, size))
    
    print(f"Found {len(candidates)} LZ77 candidates")
    
    # Analyze each candidate
    os.makedirs("analysis_results", exist_ok=True)
    good_candidates = []
    
    for i, (offset, expected_size) in enumerate(candidates):
        data, status = decompress_lz77_safe(rom_data, offset)
        
        bank = offset // 0x4000
        local_offset = offset % 0x4000
        
        print(f"\n📍 Candidate {i+1}: Bank {bank:02X}, ${offset:06X} (${local_offset:04X})")
        print(f"   Expected size: {expected_size} bytes")
        print(f"   Status: {status}")
        
        if data:
            analysis = analyze_data_patterns(data)
            print(f"   Analysis: Score={analysis['score']}, {analysis['reason']}")
            
            if analysis['score'] > 20:  # Threshold for "looks like graphics"
                good_candidates.append((offset, data, analysis))
                
                # Test different formats
                print("   Testing formats...")
                name = f"bank_{bank:02X}_{offset:06X}"
                formats = test_different_formats(data, name)
                for fmt in formats:
                    print(f"     {fmt}")
    
    print(f"\n✅ Found {len(good_candidates)} promising graphics blocks")
    
    # Save raw data for the best candidates
    print("\n💾 Saving raw data for manual analysis...")
    os.makedirs("analysis_results/raw", exist_ok=True)
    
    for i, (offset, data, analysis) in enumerate(good_candidates[:10]):
        bank = offset // 0x4000
        filename = f"analysis_results/raw/bank_{bank:02X}_{offset:06X}.bin"
        with open(filename, 'wb') as f:
            f.write(data)
        print(f"   Saved {len(data)} bytes to {filename}")

if __name__ == "__main__":
    main()