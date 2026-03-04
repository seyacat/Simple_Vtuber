# Diagnostic Test for ml5.js Model Loading

## Test Procedure

### Step 1: Manual Browser Console Check
1. Open the application in Chrome/Firefox
2. Open Developer Tools (F12)
3. Go to Console tab
4. Check for these specific errors:
   - CORS errors (blocked by policy)
   - 404 errors for model files
   - TensorFlow.js initialization errors
   - ml5.js loading errors

### Step 2: Network Tab Analysis
1. In Developer Tools, go to Network tab
2. Refresh the page
3. Look for requests to:
   - `Techeable/model.json`
   - `Techeable/weights.bin`
   - ml5.js CDN
   - TensorFlow.js files
4. Check status codes:
   - 200 = Success
   - 404 = File not found
   - 0 = CORS blocked

### Step 3: Local Server Test
Run these commands to test with a local server:

#### Option A: Python HTTP Server
```bash
cd d:/Simple_Vtuber
python -m http.server 8000
```
Then open: `http://localhost:8000`

#### Option B: Node.js Serve
```bash
cd d:/Simple_Vtuber
npx serve
```

#### Option C: Check Existing Vite Project
```bash
cd d:/Simple_Vtuber/vite-waveform-project
npm run dev
```

### Step 4: Model File Verification
Check these files exist and have content:

1. `Techeable/model.json` - Should be > 10KB
2. `Techeable/weights.bin` - Should be > 100KB  
3. `Techeable/metadata.json` - Should contain labels

### Step 5: Path Resolution Test
Test these URLs in browser (adjust port if different):

1. `http://localhost:8000/Techeable/model.json`
2. `http://localhost:8000/Techeable/weights.bin`
3. `http://localhost:8000/Techeable/metadata.json`

## Common Issues and Solutions

### Issue 1: CORS/File Protocol Block
**Symptoms**: Errors about "cross-origin" or "file:// protocol not allowed"
**Solution**: Run via HTTP server, not file://

### Issue 2: Incorrect Model Path
**Symptoms**: 404 errors for model files
**Solution**: 
- Change path in `app.js` line 146 to `'./Techeable/model.json'`
- Or use absolute path: `'http://localhost:8000/Techeable/model.json'`

### Issue 3: Teachable Machine Compatibility
**Symptoms**: Model loads but ml5.js can't use it
**Solution**:
- Check ml5.js documentation for Teachable Machine format
- Try different ml5.js version
- Export model in different format from Teachable Machine

### Issue 4: TensorFlow.js Missing
**Symptoms**: Errors about "tf" not defined
**Solution**: Ensure TensorFlow.js is loaded before ml5.js

## Quick Diagnostic Commands

### Check File Sizes:
```bash
dir Techeable\
```

### Check Model Structure:
```bash
type Techeable\metadata.json
```

### Start Python Server:
```bash
python -m http.server 8000
```

### Test Model URL (in browser console):
```javascript
fetch('./Techeable/model.json')
  .then(r => r.json())
  .then(data => console.log('Model layers:', data.modelTopology.config.layers.length))
  .catch(err => console.error('Fetch error:', err))
```

## Expected Results

### Successful Model Loading:
1. Console shows: "Sound classifier loaded successfully"
2. No red errors in console
3. Network tab shows 200 for model files
4. Model initializes without exceptions

### Current Error Analysis:
Based on the error `WH {model: BH, options: {…}, isClassifying: false...}`:
- `WH` appears to be ml5.js internal error wrapper
- Model object (`BH`) exists but failed initialization
- This suggests compatibility or loading issue, not missing file

## Next Steps Based on Diagnosis

### If Model File Not Found:
1. Fix path in `app.js`
2. Ensure files are in correct location
3. Check case sensitivity (Techeable vs techeable)

### If CORS Error:
1. Run via HTTP server
2. Add CORS headers if using custom server
3. Test with different browser

### If Compatibility Error:
1. Check ml5.js version compatibility
2. Try loading model with different syntax
3. Consider retraining model with updated Teachable Machine

### If TensorFlow.js Error:
1. Load TensorFlow.js explicitly before ml5.js
2. Check TensorFlow.js version
3. Test with different backend (webgl vs cpu)