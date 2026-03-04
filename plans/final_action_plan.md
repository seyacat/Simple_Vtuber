# Final Action Plan: Fix ml5.js Model Loading

## Issue Confirmed
**Failing URL**: `https://localhost:8080/techeable/metadata.json`
**Should be**: `http://localhost:8000/Techeable/metadata.json`

## Root Cause
TensorFlow.js speech commands model loader constructs metadata URL incorrectly:
- Uses page URL as base (`https://localhost:8080/`)
- Appends lowercase folder name (`techeable/`)
- Instead of using model.json directory as base

## Immediate Fixes Required

### 1. Server Configuration
- Run server on consistent port (8000 recommended)
- Ensure case-sensitive file serving matches `Techeable/` folder

### 2. Code Changes in `app.js`
**Option A: Use absolute URL** (Recommended)
```javascript
// Line 146 in app.js
const baseUrl = window.location.origin; // Gets http://localhost:8000
const soundModel = baseUrl + '/Techeable/model.json';
```

**Option B: Fix relative path resolution**
```javascript
const soundModel = './Techeable/model.json';
// Ensure server serves from correct base directory
```

### 3. Folder Structure Verification
- Confirm folder is named `Techeable/` (capital T)
- All files present: `model.json`, `metadata.json`, `weights.bin`

## Implementation Steps

### Step 1: Start Correct Server
```bash
cd d:/Simple_Vtuber
python -m http.server 8000
```

### Step 2: Update `app.js` Model Loading
1. Change line 146 to use absolute URL
2. Add error logging for metadata loading
3. Verify classifier object has `classify` method

### Step 3: Test
1. Open `http://localhost:8000`
2. Check console for 404 errors
3. Test vowel detection functionality

## Expected Outcome
- No 404 errors for metadata.json
- Model loads completely
- Classifier.classify() method available
- Real-time vowel detection works

## Fallback Plan
If path issues persist:
1. Copy `metadata.json` to root directory as temporary fix
2. Use ml5.js workaround for local models
3. Implement custom model loading with TensorFlow.js directly

## Success Criteria
- [ ] `metadata.json` loads without 404 error
- [ ] Console shows "Sound classifier loaded successfully"
- [ ] `classifier.classify` is a function
- [ ] Vowel detection updates in real-time