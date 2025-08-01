# VRAM Analysis Summary for macOS

## Tools Available:

### 1. **SameBoy** (Installed)
- Native macOS app with Developer Tools
- Access via: Cmd+Shift+D
- Features:
  - VRAM Viewer tab
  - Palette viewer
  - Tilemap viewer
  - Memory inspector

### 2. **Gearboy** (Can be built from source)
- More comprehensive VRAM debugging
- Shows tile attributes
- Real-time memory editing

### 3. **Screenshot Analysis** (Created)
- `analyze_screenshot.py` - Extracts unique tiles from screenshots
- Helps understand tile usage patterns

## The Problem We're Solving:

Our extracted graphics look garbled because:
1. We're extracting from the wrong ROM locations
2. We're not accounting for how GBC organizes graphics
3. We might be missing palette data or tile attributes

## VRAM Analysis Process:

1. **Run Tetris in SameBoy**
2. **Open Developer Tools** (Cmd+Shift+D)
3. **In VRAM Viewer, observe**:
   - Which tiles contain the actual Tetris pieces
   - How tiles are arranged in VRAM
   - Which palette each tile uses

4. **Take screenshots** at different game states:
   - Title screen
   - Main menu  
   - During gameplay with different pieces
   - Game over screen

5. **Analyze the screenshots** to find:
   - Unique tiles used
   - Tile arrangement patterns
   - Color palette usage

## Key GBC Graphics Concepts:

1. **VRAM Banks**:
   - Bank 0: Tile pixel data
   - Bank 1: Tile attributes (palette, flip, priority)

2. **Tile Data Blocks**:
   - $8000-$87FF: Block 0 (128 tiles)
   - $8800-$8FFF: Block 1 (128 tiles)
   - $9000-$97FF: Block 2 (128 tiles)

3. **Tile Maps**:
   - $9800-$9BFF: Background Map 0
   - $9C00-$9FFF: Background Map 1

## Next Steps:

1. Take screenshots from SameBoy during gameplay
2. Run `analyze_screenshot.py` on them
3. Cross-reference the tiles found with our ROM dumps
4. Find where the actual graphics are loaded from
5. Extract with proper palette information

## Alternative Approach:

If VRAM analysis doesn't work, we could:
1. Search for existing Tetris GBC disassemblies
2. Use a hex editor to manually find graphics patterns
3. Try different compression algorithms (though GBC rarely uses compression)