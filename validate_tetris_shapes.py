#!/usr/bin/env python3

import os
from PIL import Image
import numpy as np

def load_and_analyze_image(filepath):
    """Load PNG and analyze for Tetris-like patterns"""
    try:
        img = Image.open(filepath)
        # Convert to grayscale if not already
        if img.mode != 'L':
            img = img.convert('L')
        
        # Convert to numpy array
        pixels = np.array(img)
        
        # Basic analysis
        height, width = pixels.shape
        tiles_x = width // 8
        tiles_y = height // 8
        
        # Look for non-empty tiles
        meaningful_tiles = 0
        tetris_candidates = []
        
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                # Extract 8x8 tile
                tile = pixels[ty*8:(ty+1)*8, tx*8:(tx+1)*8]
                
                # Count non-background pixels (not white/255)
                non_bg = np.sum(tile < 250)
                total_pixels = 64
                
                if 8 <= non_bg <= 56:  # Has some content but not solid
                    meaningful_tiles += 1
                    
                    # Check for Tetris-like patterns
                    if has_tetris_pattern(tile):
                        tetris_candidates.append((tx, ty, tile))
        
        return {
            'width': width,
            'height': height,
            'tiles_total': tiles_x * tiles_y,
            'meaningful_tiles': meaningful_tiles,
            'tetris_candidates': len(tetris_candidates),
            'candidates': tetris_candidates[:3]  # First 3 candidates
        }
    except Exception as e:
        return {'error': str(e)}

def has_tetris_pattern(tile):
    """Check if 8x8 tile looks like it could contain part of a Tetris piece"""
    # Look for connected shapes, not just noise
    
    # Check for horizontal/vertical lines (common in Tetris pieces)
    for row in tile:
        non_bg_in_row = np.sum(row < 250)
        if 3 <= non_bg_in_row <= 7:  # Partial line
            return True
    
    for col in range(8):
        column = tile[:, col]
        non_bg_in_col = np.sum(column < 250)
        if 3 <= non_bg_in_col <= 7:  # Partial line
            return True
    
    # Check for rectangular blocks (common in Tetris)
    for y in range(6):  # 2x2 blocks
        for x in range(6):
            block = tile[y:y+2, x:x+2]
            if np.sum(block < 250) >= 3:  # Mostly filled 2x2
                return True
    
    return False

def print_tile_ascii(tile):
    """Print tile as ASCII for visual inspection"""
    chars = [' ', '░', '▒', '█']
    result = []
    for row in tile:
        line = ""
        for pixel in row:
            if pixel >= 250:
                line += ' '  # Background
            elif pixel >= 170:
                line += '░'  # Light
            elif pixel >= 85:
                line += '▒'  # Medium
            else:
                line += '█'  # Dark
        result.append(line)
    return '\n'.join(result)

def main():
    print("🔍 Validating Tetris Shapes in Extracted Graphics")
    print("=" * 60)
    
    final_test_dir = "final_test"
    if not os.path.exists(final_test_dir):
        print("❌ final_test directory not found")
        return
    
    # Focus on the most promising files
    priority_files = [
        "bank_01_2E00_planar.png",
        "bank_05_3600_planar.png", 
        "tetris_I_piece_01_0543_2bpp_standard.png",
        "tetris_I_piece_04_2220_2bpp_standard.png",
        "bank_01_2400_2bpp_standard.png",
        "bank_02_0000_2bpp_standard.png"
    ]
    
    print("🎯 Analyzing priority files for Tetris patterns:")
    
    results = []
    
    for filename in priority_files:
        filepath = os.path.join(final_test_dir, filename)
        if os.path.exists(filepath):
            print(f"\n📁 {filename}")
            analysis = load_and_analyze_image(filepath)
            
            if 'error' in analysis:
                print(f"   ❌ Error: {analysis['error']}")
                continue
            
            print(f"   📊 Tiles: {analysis['tiles_total']} total, {analysis['meaningful_tiles']} meaningful")
            print(f"   🎮 Tetris candidates: {analysis['tetris_candidates']}")
            
            if analysis['tetris_candidates'] > 0:
                print(f"   ✅ FOUND TETRIS-LIKE PATTERNS!")
                results.append((filename, analysis))
                
                # Show first candidate as ASCII
                if analysis['candidates']:
                    tx, ty, tile = analysis['candidates'][0]
                    print(f"   🔍 Sample pattern at tile ({tx}, {ty}):")
                    ascii_tile = print_tile_ascii(tile)
                    for line in ascii_tile.split('\n'):
                        print(f"      {line}")
            else:
                print(f"   ❌ No clear Tetris patterns found")
    
    # Also check a few random files to be thorough
    print(f"\n🔄 Checking additional files for completeness:")
    
    all_files = [f for f in os.listdir(final_test_dir) if f.endswith('.png')]
    other_files = [f for f in all_files if f not in priority_files]
    
    # Check 5 random others
    for filename in other_files[:5]:
        filepath = os.path.join(final_test_dir, filename)
        analysis = load_and_analyze_image(filepath)
        
        if 'error' not in analysis and analysis['tetris_candidates'] > 0:
            print(f"   ✅ {filename}: {analysis['tetris_candidates']} candidates")
            results.append((filename, analysis))
    
    print(f"\n🎉 VALIDATION SUMMARY:")
    print(f"Files with Tetris-like patterns: {len(results)}")
    
    if results:
        print(f"\n🏆 CONFIRMED GRAPHICS EXTRACTIONS:")
        for filename, analysis in results:
            print(f"   ✅ {filename}")
            print(f"      - {analysis['meaningful_tiles']} meaningful tiles")
            print(f"      - {analysis['tetris_candidates']} Tetris-like patterns")
    else:
        print(f"\n❌ NO CLEAR TETRIS PATTERNS FOUND")
        print(f"The extracted graphics may be:")
        print(f"  - In a different format than expected")
        print(f"  - Requiring palette/color mapping")
        print(f"  - Compressed or encoded differently")
        print(f"  - Located in regions we haven't tried yet")

if __name__ == "__main__":
    main()