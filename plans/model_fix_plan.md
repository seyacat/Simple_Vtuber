# Plan to Fix ml5.js Model Loading Error

## Problem Analysis
The ml5.js sound classifier is failing to load the model from `Techeable/model.json` with error: `Error loading sound classifier: WH {model: BH, options: {…}, isClassifying: false...}`

## Root Causes Identified
1. **Path/URL Issues**: Model path might be incorrect or inaccessible
2. **CORS/Local File Restrictions**: Browsers block local file access for security
3. **Model Compatibility**: Teachable Machine model format might not be compatible with ml5.js v1.3.1
4. **Missing Server**: Models typically require HTTP server, not file:// protocol
5. **TensorFlow.js Version**: Incompatible TensorFlow.js version with the model

## Todo List

### Phase 1: Diagnostic Steps
- [ ] **Check current model structure** - Verify model.json and weights.bin are complete
- [ ] **Test model loading with simple HTML** - Create minimal test to isolate the issue
- [ ] **Check browser console for detailed errors** - Look for CORS, 404, or TensorFlow errors
- [ ] **Verify ml5.js and TensorFlow.js versions** - Ensure compatibility with Teachable Machine format

### Phase 2: Fix Implementation
- [ ] **Fix model path reference** - Ensure correct relative path from HTML file
- [ ] **Set up local development server** - Use Python HTTP server or Vite to serve files
- [ ] **Update ml5.js loading method** - Use proper ml5.soundClassifier() syntax for local models
- [ ] **Add error handling improvements** - Better error messages and fallback mechanisms
- [ ] **Test model loading with server** - Verify model loads correctly via HTTP

### Phase 3: Alternative Solutions (if needed)
- [ ] **Convert model format** - If compatibility issue, convert Teachable Machine model to ml5.js format
- [ ] **Use different ml5.js method** - Try `ml5.soundClassifier('teachable', options)` syntax
- [ ] **Implement model caching** - Cache loaded model to prevent repeated loading failures
- [ ] **Add model validation** - Check model integrity before attempting to load

### Phase 4: Testing & Validation
- [ ] **Test vowel detection functionality** - Verify model correctly identifies vowels
- [ ] **Test fallback mechanism** - Ensure frequency-based detection works when model fails
- [ ] **Cross-browser testing** - Test in Chrome, Firefox, Edge
- [ ] **Performance testing** - Check memory usage and classification speed

## Technical Details

### Current Configuration
- **ml5.js version**: v1.3.1 (from CDN)
- **Model location**: `Techeable/model.json`
- **Model labels**: ["A","E","I","O","Ruido de fondo","U"]
- **Model type**: Teachable Machine audio classification
- **Current path in code**: `'Techeable/model.json'` (line 146 in app.js)

### Expected Fixes
1. **Path Correction**: Change to `'./Techeable/model.json'` or absolute path
2. **Server Setup**: Run `python -m http.server 8000` or use Vite dev server
3. **ml5.js Syntax**: Ensure correct usage: `ml5.soundClassifier(modelPath, options, callback)`
4. **Error Handling**: Add detailed error logging and user feedback

## Success Criteria
- [ ] Model loads without console errors
- [ ] Sound classifier initializes successfully
- [ ] Vowel detection works in real-time
- [ ] Confidence scores are displayed correctly
- [ ] Fallback to frequency detection works when needed

## Files to Modify
1. `app.js` - Model loading logic and error handling
2. `index.html` - Possibly update ml5.js/TensorFlow.js versions
3. Server configuration (if needed)

## Notes
- The app already has a fallback frequency-based vowel detection system
- Current error suggests the model object is created but fails during initialization
- The `WH` error object appears to be an ml5.js internal error wrapper
- Need to check if TensorFlow.js is loading properly (might be missing)