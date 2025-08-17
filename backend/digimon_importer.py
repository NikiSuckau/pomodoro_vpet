"""
Digimon Import System

This module handles importing new Digimon sprite sets from zip files,
validating the format, and updating the registry.
"""

import os
import json
import zipfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class DigimonImporter:
    """
    Handles importing and managing Digimon sprite sets.
    """
    
    def __init__(self, sprites_dir: str = "sprites"):
        """
        Initialize the Digimon importer.
        
        Args:
            sprites_dir: Directory where sprites are stored
        """
        self.sprites_dir = sprites_dir
        self.registry_file = os.path.join(sprites_dir, "digimon_registry.json")
        self.required_sprites = [f"{i}.png" for i in range(12)]  # 0.png to 11.png
    
    def validate_zip_contents(self, zip_path: str) -> Tuple[bool, str]:
        """
        Validate that a zip file contains the required sprite format.
        
        Args:
            zip_path: Path to the zip file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # Filter out directories and hidden files
                png_files = [f for f in file_list if f.endswith('.png') and not f.startswith('.') and '/' not in f]
                
                # Check if we have exactly 12 PNG files
                if len(png_files) != 12:
                    return False, f"Expected 12 PNG files, found {len(png_files)}"
                
                # Check if all required sprite numbers are present
                expected_files = set(self.required_sprites)
                actual_files = set(png_files)
                
                if expected_files != actual_files:
                    missing = expected_files - actual_files
                    extra = actual_files - expected_files
                    error_msg = ""
                    if missing:
                        error_msg += f"Missing sprites: {sorted(missing)}"
                    if extra:
                        if error_msg:
                            error_msg += "; "
                        error_msg += f"Extra files: {sorted(extra)}"
                    return False, error_msg
                
                return True, "Valid sprite format"
                
        except zipfile.BadZipFile:
            return False, "Invalid zip file"
        except Exception as e:
            return False, f"Error reading zip file: {str(e)}"
    
    def extract_digimon_name_from_zip(self, zip_path: str) -> str:
        """
        Extract Digimon name from zip filename.
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            Digimon name extracted from filename
        """
        base_name = os.path.basename(zip_path)
        # Remove .zip extension
        name_without_ext = os.path.splitext(base_name)[0]
        # Remove _penc suffix if present
        if name_without_ext.endswith('_penc'):
            name_without_ext = name_without_ext[:-5]
        return name_without_ext
    
    def load_registry(self) -> Dict:
        """
        Load the Digimon registry from JSON file.
        
        Returns:
            Registry dictionary
        """
        if not os.path.exists(self.registry_file):
            # Create default registry
            default_registry = {
                "available_digimon": [],
                "last_updated": datetime.now().isoformat(),
                "format_version": "1.0"
            }
            self.save_registry(default_registry)
            return default_registry
        
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            return {
                "available_digimon": [],
                "last_updated": datetime.now().isoformat(),
                "format_version": "1.0"
            }
    
    def save_registry(self, registry: Dict) -> None:
        """
        Save the Digimon registry to JSON file.
        
        Args:
            registry: Registry dictionary to save
        """
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def is_digimon_already_imported(self, digimon_name: str) -> bool:
        """
        Check if a Digimon is already imported.
        
        Args:
            digimon_name: Name of the Digimon to check
            
        Returns:
            True if already imported, False otherwise
        """
        registry = self.load_registry()
        for digimon in registry.get("available_digimon", []):
            if digimon.get("name", "").lower() == digimon_name.lower():
                return True
        return False
    
    def import_digimon(self, zip_path: str) -> Tuple[bool, str]:
        """
        Import a Digimon from a zip file.
        
        Args:
            zip_path: Path to the zip file containing sprites
            
        Returns:
            Tuple of (success, message)
        """
        # Validate zip contents
        is_valid, error_msg = self.validate_zip_contents(zip_path)
        if not is_valid:
            return False, f"Invalid zip format: {error_msg}"
        
        # Extract Digimon name
        digimon_name = self.extract_digimon_name_from_zip(zip_path)
        
        # Check if already imported
        if self.is_digimon_already_imported(digimon_name):
            return False, f"{digimon_name} is already imported"
        
        # Create destination directory
        dest_dir = os.path.join(self.sprites_dir, f"{digimon_name}_penc")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(dest_dir, exist_ok=True)
            
            # Extract sprites to destination
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for sprite_file in self.required_sprites:
                    zip_ref.extract(sprite_file, dest_dir)
            
            # Update registry
            registry = self.load_registry()
            new_digimon = {
                "name": digimon_name,
                "directory": f"{digimon_name}_penc",
                "imported_date": datetime.now().isoformat()[:10],  # YYYY-MM-DD format
                "default": False
            }
            
            registry["available_digimon"].append(new_digimon)
            registry["last_updated"] = datetime.now().isoformat()
            
            self.save_registry(registry)
            
            logger.info(f"Successfully imported {digimon_name}")
            return True, f"Successfully imported {digimon_name}"
            
        except Exception as e:
            # Clean up partial import
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            logger.error(f"Error importing {digimon_name}: {e}")
            return False, f"Error importing {digimon_name}: {str(e)}"
    
    def get_available_digimon(self) -> List[Dict]:
        """
        Get list of all available Digimon.
        
        Returns:
            List of Digimon information dictionaries
        """
        registry = self.load_registry()
        return registry.get("available_digimon", [])
    
    def get_digimon_sprite_path(self, digimon_name: str) -> Optional[str]:
        """
        Get the sprite directory path for a specific Digimon.
        
        Args:
            digimon_name: Name of the Digimon
            
        Returns:
            Path to sprite directory, or None if not found
        """
        registry = self.load_registry()
        for digimon in registry.get("available_digimon", []):
            if digimon.get("name", "").lower() == digimon_name.lower():
                sprite_dir = os.path.join(self.sprites_dir, digimon.get("directory", ""))
                if os.path.exists(sprite_dir):
                    return sprite_dir
        return None
    
    def remove_digimon(self, digimon_name: str) -> Tuple[bool, str]:
        """
        Remove a Digimon from the system.
        
        Args:
            digimon_name: Name of the Digimon to remove
            
        Returns:
            Tuple of (success, message)
        """
        registry = self.load_registry()
        digimon_list = registry.get("available_digimon", [])
        
        # Find the Digimon to remove
        digimon_to_remove = None
        for i, digimon in enumerate(digimon_list):
            if digimon.get("name", "").lower() == digimon_name.lower():
                # Don't allow removing default Digimon
                if digimon.get("default", False):
                    return False, f"Cannot remove default Digimon: {digimon_name}"
                digimon_to_remove = (i, digimon)
                break
        
        if digimon_to_remove is None:
            return False, f"Digimon not found: {digimon_name}"
        
        try:
            index, digimon_info = digimon_to_remove
            
            # Remove directory
            sprite_dir = os.path.join(self.sprites_dir, digimon_info.get("directory", ""))
            if os.path.exists(sprite_dir):
                shutil.rmtree(sprite_dir)
            
            # Remove from registry
            digimon_list.pop(index)
            registry["last_updated"] = datetime.now().isoformat()
            self.save_registry(registry)
            
            logger.info(f"Successfully removed {digimon_name}")
            return True, f"Successfully removed {digimon_name}"
            
        except Exception as e:
            logger.error(f"Error removing {digimon_name}: {e}")
            return False, f"Error removing {digimon_name}: {str(e)}"

