"""
File Manager Module for Amiibo Emulator

Handles Amiibo file organization, parsing, and categorization.
"""

import os
import json
import time
from typing import List, Dict, Optional, Tuple

class FileManager:
    """Manages Amiibo files and metadata"""
    
    def __init__(self, data_dir: str = "amiibo_data"):
        """
        Initialize File Manager
        
        Args:
            data_dir: Directory containing Amiibo files
        """
        self.data_dir = data_dir
        self.index_file = os.path.join(data_dir, "index.json")
        self.categories_dir = os.path.join(data_dir, "categories")
        self.raw_files_dir = os.path.join(data_dir, "raw_files")
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load or create index
        self.index = self._load_index()
        
        # Character and series mappings
        self.character_map = self._load_character_map()
        self.series_map = self._load_series_map()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.categories_dir, exist_ok=True)
        os.makedirs(self.raw_files_dir, exist_ok=True)
    
    def _load_index(self) -> Dict:
        """Load or create the Amiibo index"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading index: {e}")
        
        # Create new index
        return self._create_index()
    
    def _create_index(self) -> Dict:
        """Create a new index from .nfc files"""
        print("Creating new Amiibo index...")
        
        index = {
            "version": "1.0",
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "categories": [],
            "files": []
        }
        
        # Scan for .nfc files
        nfc_files = self._scan_nfc_files()
        
        # Group by category
        categories = {}
        for file_info in nfc_files:
            category = file_info['category']
            if category not in categories:
                categories[category] = {
                    'id': category.lower().replace(' ', '_'),
                    'name': category,
                    'count': 0,
                    'files': []
                }
            
            categories[category]['count'] += 1
            categories[category]['files'].append(file_info)
            index['files'].append(file_info)
        
        # Convert categories to list
        index['categories'] = list(categories.values())
        
        # Save index
        self._save_index(index)
        
        print(f"Index created with {len(index['categories'])} categories and {len(index['files'])} files")
        return index
    
    def _scan_nfc_files(self) -> List[Dict]:
        """Scan for .nfc files and extract metadata"""
        files = []
        
        # Scan categories directory for .nfc files
        if os.path.exists(self.categories_dir):
            files.extend(self._scan_directory(self.categories_dir, "Categories"))
        
        return files
    
    def _scan_directory(self, directory: str, source: str) -> List[Dict]:
        """Scan a directory for .nfc files"""
        files = []
        
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if filename.lower().endswith('.nfc'):
                    file_path = os.path.join(root, filename)
                    file_info = self._parse_file_info(file_path, source)
                    if file_info:
                        files.append(file_info)
        
        return files
    
    def _parse_file_info(self, file_path: str, source: str) -> Optional[Dict]:
        """Parse file path to extract metadata"""
        try:
            # Extract relative path
            rel_path = os.path.relpath(file_path, source)
            
            # Parse filename
            filename = os.path.basename(file_path)
            name_parts = filename.replace('.nfc', '').split('_')
            
            # Determine category from directory structure
            category = self._determine_category(file_path)
            
            # Extract character name
            character = self._extract_character_name(filename)
            
            # Get file size
            size = os.path.getsize(file_path)
            
            return {
                'path': file_path,
                'relative_path': rel_path,
                'filename': filename,
                'category': category,
                'character': character,
                'series': self._get_series_from_category(category),
                'source': source,
                'size': size,
                'special': self._is_special_edition(filename),
                'last_modified': os.path.getmtime(file_path)
            }
            
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None
    
    def _determine_category(self, file_path: str) -> str:
        """Determine category from file path"""
        # Extract directory name
        dir_name = os.path.basename(os.path.dirname(file_path))
        
        # Map directory names to categories
        category_map = {
            'Super_Mario': 'Super Mario',
            'Legend_of_Zelda': 'The Legend of Zelda',
            'Super_Smash_Bros': 'Super Smash Bros',
            'Animal_Crossing': 'Animal Crossing',
            'Kirby': 'Kirby',
            'Metroid': 'Metroid',
            'Fire_Emblem': 'Fire Emblem',
            'Splatoon': 'Splatoon',
            'Pokemon': 'Pokémon',
            'Yoshis_Wooly_World': "Yoshi's Woolly World",
            'Box_boy_Amiibo': 'BoxBoy!',
            'Chibi_Robo_Amiibo': 'Chibi-Robo!',
            'Dark_Souls_Amiibo': 'Dark Souls',
            'Detective_Pikachu_Amiibo': 'Detective Pikachu',
            'Diablo_Amiibo': 'Diablo',
            'Kellogs_Amiibo': 'Kellogg\'s',
            'Mario_Sports_Superstars': 'Mario Sports Superstars',
            'Mega_Man_Amiibo': 'Mega Man',
            'Monster_Hunter': 'Monster Hunter',
            'Pikmin_Amiibo': 'Pikmin',
            'Pokken_Tournament': 'Pokkén Tournament',
            'Power_Pros_Amiibo': 'Power Pros',
            'PowerUpBands': 'PowerUp Bands',
            'Shovel_Knight_Amiibo': 'Shovel Knight',
            'Skylanders': 'Skylanders',
            'XenoBlade Chronicles': 'Xenoblade Chronicles',
            'Yu_Gi_Oh_Amiibo': 'Yu-Gi-Oh!'
        }
        
        return category_map.get(dir_name, dir_name.replace('_', ' '))
    
    def _extract_character_name(self, filename: str) -> str:
        """Extract character name from filename"""
        # Remove .nfc extension
        name = filename.replace('.nfc', '')
        
        # Replace underscores with spaces
        name = name.replace('_', ' ')
        
        # Handle special cases
        special_cases = {
            'Gold Mario': 'Gold Mario',
            'Wedding': 'Wedding Edition',
            'Side Order': 'Side Order',
            'Neon Green': 'Neon Green',
            'Neon Pink': 'Neon Pink',
            'Lime Green': 'Lime Green',
            'Neon Purple': 'Neon Purple'
        }
        
        for old, new in special_cases.items():
            name = name.replace(old, new)
        
        return name
    
    def _get_series_from_category(self, category: str) -> str:
        """Get series name from category"""
        # This could be expanded with more detailed mappings
        return category
    
    def _is_special_edition(self, filename: str) -> bool:
        """Check if file represents a special edition"""
        special_keywords = ['Gold', 'Silver', 'Wedding', 'Anniversary', 'Special']
        return any(keyword in filename for keyword in special_keywords)
    
    def _save_index(self, index: Dict):
        """Save index to JSON file"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def get_categories(self) -> List[Dict]:
        """Get list of all categories"""
        return self.index['categories']
    
    def get_characters(self, category_id: str) -> List[Dict]:
        """Get characters in a specific category"""
        # Find category
        category = None
        for cat in self.index['categories']:
            if cat['id'] == category_id:
                category = cat
                break
        
        if not category:
            return []
        
        # Get files for this category
        characters = []
        for file_info in self.index['files']:
            if file_info['category'] == category['name']:
                characters.append(file_info)
        
        # Sort by character name
        characters.sort(key=lambda x: x['character'])
        
        return characters
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """Get information about a specific file"""
        for file_info in self.index['files']:
            if file_info['path'] == file_path:
                return file_info
        return None
    
    def search_files(self, query: str) -> List[Dict]:
        """Search files by name or category"""
        query = query.lower()
        results = []
        
        for file_info in self.index['files']:
            if (query in file_info['character'].lower() or 
                query in file_info['category'].lower() or
                query in file_info['series'].lower()):
                results.append(file_info)
        
        # Sort by relevance (character name first, then category)
        results.sort(key=lambda x: (
            0 if query in x['character'].lower() else 1,
            x['character']
        ))
        
        return results
    
    def get_random_file(self) -> Optional[Dict]:
        """Get a random Amiibo file"""
        if not self.index['files']:
            return None
        
        import random
        return random.choice(self.index['files'])
    
    def get_statistics(self) -> Dict:
        """Get statistics about the collection"""
        total_files = len(self.index['files'])
        total_categories = len(self.index['categories'])
        
        special_editions = sum(1 for f in self.index['files'] if f['special'])
        
        # Most popular categories
        category_counts = {}
        for file_info in self.index['files']:
            category = file_info['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        most_popular = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_files': total_files,
            'total_categories': total_categories,
            'special_editions': special_editions,
            'most_popular_categories': most_popular,
            'last_updated': self.index.get('last_updated', 'Unknown')
        }
    
    def refresh_index(self):
        """Refresh the index by rescanning files"""
        print("Refreshing Amiibo index...")
        self.index = self._create_index()
        print("Index refreshed successfully")
    
    def _load_character_map(self) -> Dict:
        """Load character name mappings"""
        # This would contain detailed character ID to name mappings
        # For now, return empty dict
        return {}
    
    def _load_series_map(self) -> Dict:
        """Load series name mappings"""
        # This would contain detailed game ID to series mappings
        # For now, return empty dict
        return {}

class AmiiboParser:
    """Parser for .nfc file format"""
    
    @staticmethod
    def parse_nfc_file(file_path: str) -> Optional[Dict]:
        """
        Parse .nfc file and extract Amiibo data
        
        Args:
            file_path: Path to .nfc file
        
        Returns:
            Dictionary with parsed Amiibo data
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            if len(data) < 540:
                raise ValueError(f"Invalid .nfc file size: {len(data)} bytes")
            
            # Parse NFC data structure
            parsed_data = {
                'raw_data': data,
                'file_size': len(data),
                'uid': data[0:7].hex().upper(),
                'character_id': data[8:10].hex().upper(),
                'game_id': data[10:12].hex().upper(),
                'write_counter': int.from_bytes(data[12:14], 'big'),
                'amiibo_id': data[14:22].hex().upper(),
                'character_model': data[22:24].hex().upper(),
                'series_id': data[24:26].hex().upper(),
                'figure_type': data[26],
                'version': data[27],
                'unknown1': data[28:32].hex().upper(),
                'mii_data': data[32:96],
                'unknown2': data[96:108].hex().upper(),
                'name': AmiiboParser._extract_name(data[108:140]),
                'unknown3': data[140:144].hex().upper(),
                'mii_face': data[144:152].hex().upper(),
                'mii_hair': data[152:160].hex().upper(),
                'mii_body': data[160:168].hex().upper(),
                'mii_accessories': data[168:176].hex().upper(),
                'mii_colors': data[176:184].hex().upper(),
                'unknown4': data[184:200].hex().upper(),
                'checksum': data[200:204].hex().upper(),
                'unknown5': data[204:540].hex().upper()
            }
            
            return parsed_data
            
        except Exception as e:
            print(f"Error parsing .nfc file {file_path}: {e}")
            return None
    
    @staticmethod
    def _extract_name(name_bytes: bytes) -> str:
        """Extract UTF-16 name from bytes"""
        try:
            # Remove null bytes and decode UTF-16
            name = name_bytes.replace(b'\x00', b'').decode('utf-16le', errors='ignore')
            return name.strip()
        except:
            return "Unknown"
    
    @staticmethod
    def validate_nfc_file(file_path: str) -> bool:
        """Validate .nfc file format"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Check minimum size
            if len(data) < 540:
                return False
            
            # Check for valid header (would need actual validation logic)
            # This is a simplified check
            return True
            
        except:
            return False