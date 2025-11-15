"""
Semantic Intent Classifier
Uses TF-IDF vectorization and cosine similarity for intent classification
Lightweight alternative to deep learning models
"""

import logging
from typing import Dict, List, Optional, Tuple

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    np = None
    logging.warning("scikit-learn not available. Semantic classification disabled.")

from intent_examples import INTENT_EXAMPLES

logger = logging.getLogger(__name__)


class SemanticIntentClassifier:
    """Classifies intents using TF-IDF and cosine similarity"""
    
    def __init__(self):
        """Initialize semantic intent classifier"""
        self.vectorizer = None
        self.intent_vectors = {}  # Cache TF-IDF vectors for intent examples
        self.intent_examples = INTENT_EXAMPLES
        
        if not SEMANTIC_AVAILABLE:
            logger.warning("Semantic classification disabled - scikit-learn not installed")
            return
        
        try:
            logger.info("Initializing TF-IDF vectorizer for semantic classification")
            # Use character n-grams (2-4 chars) for better multilingual support
            # and word n-grams (1-2 words) for semantic matching
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),  # Unigrams and bigrams
                min_df=1,  # Minimum document frequency
                max_df=0.95,  # Maximum document frequency (ignore very common words)
                lowercase=True,
                analyzer='word',
                token_pattern=r'(?u)\b\w+\b',  # Word tokenizer
                max_features=5000  # Limit vocabulary size for efficiency
            )
            
            # Pre-compute vectors for all intent examples
            self._precompute_vectors()
            logger.info("TF-IDF vectors pre-computed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize semantic model: {e}")
            self.vectorizer = None
    
    def _precompute_vectors(self):
        """Pre-compute TF-IDF vectors for all intent examples"""
        if not self.vectorizer:
            return
        
        logger.info("Pre-computing TF-IDF vectors for intent examples...")
        
        # Collect all examples for vectorizer fitting
        all_texts = []
        intent_text_map = {}  # Map text to intent for lookup
        
        for intent, lang_examples in self.intent_examples.items():
            if intent == 'unknown':
                continue  # Skip unknown intent
            
            for lang, examples in lang_examples.items():
                if examples:
                    for example in examples:
                        all_texts.append(example)
                        if intent not in intent_text_map:
                            intent_text_map[intent] = []
                        intent_text_map[intent].append(example)
        
        if not all_texts:
            logger.warning("No intent examples found for TF-IDF vectorization")
            return
        
        # Fit vectorizer on all examples
        try:
            self.vectorizer.fit(all_texts)
            
            # Compute vectors for each intent
            for intent, texts in intent_text_map.items():
                if texts:
                    try:
                        vectors = self.vectorizer.transform(texts)
                        self.intent_vectors[intent] = vectors
                    except Exception as e:
                        logger.warning(f"Failed to compute vectors for {intent}: {e}")
                        self.intent_vectors[intent] = None
        except Exception as e:
            logger.error(f"Failed to fit vectorizer: {e}")
            self.vectorizer = None
    
    def classify(self, text: str, language: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Classify intent using TF-IDF cosine similarity
        
        Args:
            text: Input text to classify
            language: Detected language code (used for filtering examples)
            top_k: Number of top intents to return
            
        Returns:
            List of (intent, similarity_score) tuples, sorted by score descending
        """
        if not self.vectorizer or not SEMANTIC_AVAILABLE:
            return []
        
        if not text or not text.strip():
            return []
        
        try:
            # Vectorize input text
            text_vector = self.vectorizer.transform([text])
            
            intent_scores = {}
            
            # Compare against all intent examples
            for intent, vectors in self.intent_vectors.items():
                if intent == 'unknown' or vectors is None:
                    continue
                
                # Compute cosine similarity with all examples for this intent
                similarities = cosine_similarity(text_vector, vectors)[0]
                
                # Take max similarity as the score for this intent
                if len(similarities) > 0:
                    max_similarity = float(np.max(similarities))
                    # Normalize to 0-1 range (cosine similarity is already 0-1)
                    intent_scores[intent] = max(0.0, min(1.0, max_similarity))
            
            # Sort by score and return top_k
            sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_intents[:top_k]
            
        except Exception as e:
            logger.error(f"Error in semantic classification: {e}", exc_info=True)
            return []
    
    def is_available(self) -> bool:
        """Check if semantic classification is available"""
        return SEMANTIC_AVAILABLE and self.vectorizer is not None
