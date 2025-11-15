# Changelog - Major Improvements

## Version 2.0.0 - All Improvements Implemented

### 🎉 Major Features Added

#### 1. Configuration Management (`config.py`)
- Environment variable support
- Centralized configuration
- Configurable CORS, validation limits, confidence thresholds
- Easy deployment customization

#### 2. Input Validation & Sanitization (`validators.py`)
- Text length validation (1-5000 chars)
- Input sanitization (removes control characters)
- Context validation
- Session ID validation
- Batch request validation
- Clear error messages with error codes

#### 3. Enhanced Error Handling (`errors.py`)
- Structured error responses with error codes
- Custom exception classes (ValidationError, ParseError, InternalError)
- Proper HTTP status codes
- Error details in responses

#### 4. Product Catalog Caching (`product_catalog.py`)
- Singleton pattern implementation
- Catalog loaded once and cached
- Reload method for cache invalidation
- Better performance with large catalogs

#### 5. Fuzzy Product Matching (`entity_extractor.py`)
- Uses rapidfuzz library for fuzzy string matching
- Handles typos and misspellings
- Configurable similarity threshold
- Falls back gracefully if library not available

#### 6. Batch Processing Endpoint (`/nlu/parse/batch`)
- Process multiple texts in one request
- Max 100 texts per batch (configurable)
- Individual error handling per item
- Processing time tracking

#### 7. Confidence Threshold Filtering
- Filters low-confidence entities
- Configurable thresholds per entity type
- Uncertainty flag in responses
- Better quality control

#### 8. Session/Conversation Context (`session_manager.py`)
- Tracks conversation history per session
- Context-aware intent classification
- Session TTL (1 hour default)
- Session endpoints (GET, DELETE)
- History tracking (last 10 interactions)

#### 9. Enhanced Health Check (`/health`)
- Component status checking
- Product catalog status
- Uptime tracking
- Configuration info
- Proper HTTP status codes (200/503)

#### 10. Unit Tests Structure (`tests/`)
- Test framework setup
- Validator tests
- Ready for expansion

### 📝 API Changes

#### New Endpoints
- `POST /nlu/parse/batch` - Batch processing
- `GET /nlu/session/<session_id>` - Get session info
- `DELETE /nlu/session/<session_id>` - Delete session

#### Enhanced Endpoints
- `POST /nlu/parse` - Now includes:
  - `uncertain` flag
  - `processing_time_ms`
  - Better error handling
  - Session context support

- `GET /health` - Now includes:
  - Component status
  - Product count
  - Uptime
  - Configuration info

### 🔧 Configuration Options

Environment variables:
- `NLU_HOST` - API host (default: 0.0.0.0)
- `NLU_PORT` - API port (default: 5000)
- `NLU_DEBUG` - Debug mode (default: false)
- `NLU_CORS_ORIGINS` - CORS origins (comma-separated)
- `NLU_MAX_TEXT_LENGTH` - Max text length (default: 5000)
- `NLU_MAX_BATCH_SIZE` - Max batch size (default: 100)
- `NLU_MIN_INTENT_CONFIDENCE` - Min intent confidence (default: 0.3)
- `NLU_MIN_ENTITY_CONFIDENCE` - Min entity confidence (default: 0.4)

### 📦 New Dependencies

- `rapidfuzz==3.5.2` - Fuzzy string matching

### 🐛 Bug Fixes

- Fixed product catalog path detection
- Improved confidence scoring (no more 100% for vague text)
- Better sentiment detection (added "agree", "accept", etc.)
- Fixed CORS issues

### ⚡ Performance Improvements

- Product catalog caching (singleton)
- Optimized entity extraction
- Batch processing support
- Processing time tracking

### 🔒 Security Improvements

- Input sanitization
- Request validation
- Configurable CORS
- Error message sanitization

### 📚 Documentation

- Comprehensive error codes
- API documentation updates
- Configuration guide
- Testing guide

### 🧪 Testing

- Unit test structure
- Test validators
- Ready for integration tests

## Migration Guide

### For Existing Users

1. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Update API calls:**
   - Responses now include `uncertain` and `processing_time_ms`
   - Errors now have structured format with `error_code`

3. **Use sessions:**
   - Pass `session_id` to maintain conversation context
   - Sessions improve intent classification accuracy

4. **Configuration:**
   - Set environment variables for production
   - Or modify `config.py` defaults

### Breaking Changes

- Error responses now have structured format:
  ```json
  {
    "error": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
  ```

- Health check response format changed (more detailed)

## Next Steps

See `IMPROVEMENTS.md` for future enhancements:
- Machine learning integration
- More languages
- Advanced analytics
- Docker deployment

