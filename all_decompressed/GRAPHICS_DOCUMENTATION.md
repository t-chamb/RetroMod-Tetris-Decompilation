# ModRetro Tetris Graphics Documentation

## Overview
This homebrew Tetris uses LZ77 compression for graphics storage.
Total: 88 compressed blocks, ~1.6MB decompressed graphics.

## Graphics Categories

### 1. Tetromino Pieces (Bank 00)
- **0x15CA-0x1606**: 4 blocks of 96 tiles each
- Contains the 7 Tetris pieces in various rotations
- Each block might be a different visual style or animation frame

### 2. UI Elements (Bank 00)
- **0x3223**: 64 tiles - Menu borders and frames
- **0x3277, 0x329F**: 48 tiles each - Buttons and UI components

### 3. Large Tilesets (Bank 02)
- **0x801A-0x6C76**: ~70 blocks of 1440 tiles each
- Likely contains all game backgrounds, multiple themes
- Over 100,000 tiles total!

### 4. Fonts and Text (Banks 03, 0E)
- **Bank 03, 0x78F0**: 272 tiles
- **Bank 0E, 0x5F09**: 112 tiles
- Multiple font styles for menus and gameplay

### 5. Title/Menu Graphics (Bank 03)
- **0x7DC5**: 3854 tiles - Largest single block!
- Likely the title screen and main menu graphics

### 6. Animations (Banks 07, 08)
- **Bank 07, 0x6414**: 385 tiles
- **Bank 08, 0x5D86**: 273 tiles
- Line clear animations, effects

## Decompression Routine
The game uses standard LZ77 compression:
- Marker: 0x10
- 3-byte size header (little endian)
- Standard LZ77 control bytes and references

## Integration with mgbdis
To properly disassemble:
1. Decompress all graphics at build time
2. Replace compressed data references with INCBIN to decompressed files
3. Include decompression routine in the disassembly
