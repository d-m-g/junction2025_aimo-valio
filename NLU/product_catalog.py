"""
Product Catalog Module
Loads and manages product data for entity extraction
Uses singleton pattern with caching
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Singleton instance
_catalog_instance: Optional['ProductCatalog'] = None


class ProductCatalog:
    """Manages product catalog for entity extraction with caching"""
    
    _instance: Optional['ProductCatalog'] = None
    _initialized: bool = False
    
    def __new__(cls, catalog_path: Optional[str] = None):
        """Singleton pattern - return existing instance if available"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, catalog_path: Optional[str] = None):
        """
        Initialize product catalog (only once due to singleton)
        
        Args:
            catalog_path: Optional path to product data JSON file
        """
        if self._initialized:
            return
        
        self.catalog_path = catalog_path or self._find_catalog_path()
        self._catalog: List[Dict] = []
        self._load_catalog()
        self._initialized = True
    
    def reload(self):
        """Reload catalog from file (useful for cache invalidation)"""
        self._catalog = []
        self._load_catalog()
        logger.info("Product catalog reloaded")
    
    def _find_catalog_path(self) -> Optional[str]:
        """
        Try to find product data file in common locations
        
        Returns:
            Path to catalog file or None
        """
        # Try relative to NLU folder (go up to root)
        base_path = Path(__file__).parent.parent
        
        # List of possible filenames to check
        possible_filenames = [
            'valio_aimo_product_data_junction_2025.json',  # Actual filename
            'Valio Aimo Product Data 2025.json',  # Original expected name
            'product_data.json',
            'products.json'
        ]
        
        # Check in Data folder (root/Data)
        possible_paths = []
        for filename in possible_filenames:
            possible_paths.extend([
                base_path / 'Data' / filename,  # Root/Data folder
                base_path / 'data' / filename,  # Lowercase variant
            ])
        
        # Also check root directly
        for filename in possible_filenames:
            possible_paths.append(base_path / filename)
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found product catalog at: {path}")
                return str(path)
        
        logger.warning(f"Product catalog not found. Searched in: {base_path / 'Data'}")
        return None
    
    def _load_catalog(self):
        """Load product catalog from file"""
        if not self.catalog_path:
            logger.warning("No product catalog file found. Product extraction will be limited.")
            return
        
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                self._catalog = data
            elif isinstance(data, dict):
                # Try common keys
                if 'products' in data:
                    self._catalog = data['products']
                elif 'items' in data:
                    self._catalog = data['items']
                else:
                    # Assume it's a single product or use values
                    self._catalog = [data] if data else []
            
            # Normalize product structure
            self._normalize_catalog()
            
            logger.info(f"Loaded {len(self._catalog)} products from catalog")
            
        except FileNotFoundError:
            logger.warning(f"Product catalog file not found: {self.catalog_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing product catalog JSON: {e}")
        except Exception as e:
            logger.error(f"Error loading product catalog: {e}")
    
    def _normalize_catalog(self):
        """Normalize product catalog structure and build comprehensive name mappings"""
        normalized = []
        
        for product in self._catalog:
            normalized_product = {
                'gtin': product.get('GTIN') or product.get('gtin') or product.get('id'),
                'name': product.get('name') or product.get('Name') or product.get('product_name') or '',
                'name_variants': list(product.get('name_variants', [])),  # Copy existing variants
                'category': product.get('category') or product.get('Category') or '',
                'brand': product.get('brand') or product.get('Brand') or ''
            }
            
            # Build comprehensive name variants
            name = normalized_product['name']
            if name:
                variants = set()  # Use set to avoid duplicates
                
                # Add original name variants if provided
                for variant in normalized_product['name_variants']:
                    variants.add(variant)
                
                # Basic variants
                variants.add(name.lower())
                variants.add(name.upper())
                variants.add(name.title())
                
                # Variants without special characters
                variants.add(name.replace('-', ' ').replace('_', ' '))
                variants.add(name.replace('-', '').replace('_', ''))
                
                # Brand + name combinations
                brand = normalized_product.get('brand', '')
                if brand:
                    variants.add(f"{brand} {name}")
                    variants.add(f"{name} {brand}")
                    variants.add(brand.lower())
                
                # Short name (first word or first few words)
                name_words = name.split()
                if len(name_words) > 1:
                    variants.add(name_words[0])  # First word
                    variants.add(' '.join(name_words[:2]))  # First two words
                    variants.add(' '.join(name_words[:3]))  # First three words
                
                # Remove brand from name if present
                if brand and brand.lower() in name.lower():
                    name_without_brand = name.lower().replace(brand.lower(), '').strip()
                    if name_without_brand:
                        variants.add(name_without_brand)
                
                # Check for alternative names in product data
                alt_names = [
                    product.get('alt_name'),
                    product.get('alternative_name'),
                    product.get('short_name'),
                    product.get('display_name'),
                ]
                for alt_name in alt_names:
                    if alt_name and isinstance(alt_name, str):
                        variants.add(alt_name.lower())
                        variants.add(alt_name)
                
                # Convert set back to list and filter empty strings
                normalized_product['name_variants'] = [v for v in variants if v and v.strip()]
            
            normalized.append(normalized_product)
        
        self._catalog = normalized
    
    def get_catalog(self) -> List[Dict]:
        """
        Get the product catalog
        
        Returns:
            List of product dictionaries
        """
        return self._catalog
    
    def find_product(self, name: str) -> Optional[Dict]:
        """
        Find a product by name
        
        Args:
            name: Product name to search for
            
        Returns:
            Product dictionary or None
        """
        name_lower = name.lower()
        
        for product in self._catalog:
            if product.get('name', '').lower() == name_lower:
                return product
            
            for variant in product.get('name_variants', []):
                if variant.lower() == name_lower:
                    return product
        
        return None
    
    def find_product_by_gtin(self, gtin: str) -> Optional[Dict]:
        """
        Find a product by GTIN
        
        Args:
            gtin: GTIN code
            
        Returns:
            Product dictionary or None
        """
        for product in self._catalog:
            if str(product.get('gtin', '')) == str(gtin):
                return product
        
        return None

