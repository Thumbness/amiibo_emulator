#!/usr/bin/env python3
"""
Regenerate Index Script

Run this on the Raspberry Pi to regenerate the index.json file
with correct Linux path separators.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amiibo_emulator.src.file_manager import FileManager

def main():
    print("=" * 50)
    print("Regenerating Amiibo Index for Raspberry Pi")
    print("=" * 50)
    print()
    
    # Check if amiibo_data directory exists
    if not os.path.exists("amiibo_data"):
        print("ERROR: amiibo_data directory not found!")
        print("Make sure you're running this from the amiibo_emulator directory")
        return 1
    
    # Delete old index if it exists
    index_file = "amiibo_data/index.json"
    if os.path.exists(index_file):
        print(f"Removing old index file: {index_file}")
        os.remove(index_file)
        print("✓ Old index removed")
        print()
    
    # Create new file manager (will regenerate index)
    print("Scanning for .nfc files...")
    fm = FileManager()
    
    # Display statistics
    stats = fm.get_statistics()
    print()
    print("=" * 50)
    print("Index Regeneration Complete!")
    print("=" * 50)
    print(f"Total Files: {stats['total_files']}")
    print(f"Total Categories: {stats['total_categories']}")
    print(f"Special Editions: {stats['special_editions']}")
    print()
    print("Top 5 Categories:")
    for i, (category, count) in enumerate(stats['most_popular_categories'], 1):
        print(f"  {i}. {category}: {count} files")
    print()
    print("✓ Index saved to:", index_file)
    print()
    print("You can now run the main application:")
    print("  sudo python3 main_rpi.py")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
