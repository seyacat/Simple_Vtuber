# TensorFlow.js Vowel Recognition Training Guide

This guide explains how to train a vowel recognition model using TensorFlow.js locally, replacing the previous ml5.js/Teachable Machine approach.

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Record training data
npm run record-batch

# 3. Extract features
npm run extract

# 4. Train model
npm run train

# 5. Test model
npm run test

# 6. Update web app (see below)
```

## Detailed Steps

### 1. Project Setup

Ensure you have Node.js installed (version 14 or higher). Then install dependencies:

```bash
npm install
```

This installs:
- `@tensorflow/tfjs` & `@tensorflow/tfjs-node` - TensorFlow.js for Node.js
- `node-record-lpcm16` - Audio recording
- `wav-decoder` & `wav-encoder` - WAV file processing
- `meyda` - MFCC feature extraction
- `fs-extra` - File system utilities

### 2. Recording Training Data

You need to record audio samples for each vowel (A, E, I, O, U) and background noise.

#### Option A: Interactive Batch Recording (Recommended)
```bash
npm run record-batch
```

This interactive script will guide you through recording multiple samples for each label with countdowns and pauses.

#### Option B: Manual Recording
```bash
# Record individual samples
node scripts/record.js --label A --index 1
node scripts/record.js --label A --index 2
node scripts/record.js --label E --index 1
# etc.

# With custom duration
node scripts/record.js --label A --index 3 --duration 1.0
```

#### Recording Tips:
- Record in a quiet environment
- Speak each vowel clearly
- Record 20-30 samples per vowel for good results
- Include background noise samples (silence, keyboard typing, etc.)
- Files are saved to `dataset/{label}/` folders

### 3. Feature Extraction

Extract MFCC (Mel-frequency cepstral coefficients) features from the recorded WAV files:

```bash
npm run extract
```

This script:
1. Reads all WAV files from the dataset directory
2. Extracts MFCC features using the Meyda library
3. Normalizes features (zero mean, unit variance)
4. Saves features to `dataset/features.json`
5. Creates train/validation split

### 4. Model Training

Train a CNN model on the extracted features:

```bash
npm run train
```

Training details:
- **Model**: CNN with 2 convolutional layers, max pooling, and dense layers
- **Input shape**: 43x232x1 (MFCC features)
- **Output**: 6 classes (A, E, I, O, U, noise)
- **Epochs**: 40 (with early stopping)
- **Batch size**: 32
- **Validation split**: 20%

The trained model is saved to `trained/` folder:
- `model.json` - Model architecture
- `weights.bin` - Model weights
- `training_history.json` - Training metrics

### 5. Model Testing

Evaluate the trained model:

```bash
npm run test
```

This script:
1. Loads the trained model
2. Makes predictions on all samples
3. Calculates accuracy, precision, recall, F1-score
4. Generates a confusion matrix
5. Saves evaluation results to `trained/evaluation.json`

### 6. Update Web App

To use the new TensorFlow.js model in the web app:

1. **Update `index.html`**:
   - Remove ml5.js script tag
   - Add TensorFlow.js script tag

2. **Update `app.js`**:
   - Replace ml5.soundClassifier with TensorFlow.js model loading
   - Update audio processing for real-time inference

See the "Web App Integration" section below for detailed instructions.

## File Structure

```
d:/Simple_Vtuber/
├── dataset/              # Audio files and features
│   ├── A/               # Vowel A samples
│   ├── E/               # Vowel E samples
│   ├── I/               # Vowel I samples
│   ├── O/               # Vowel O samples
│   ├── U/               # Vowel U samples
│   ├── noise/           # Background noise samples
│   ├── features.json    # Extracted MFCC features
│   └── split_data.json  # Train/validation split
├── trained/             # Trained models
│   ├── model.json      # Model architecture
│   ├── weights.bin     # Model weights
│   ├── training_history.json
│   ├── evaluation.json
│   └── normalization_params.json
├── scripts/             # Training scripts
│   ├── record.js       # Single recording
│   ├── record_batch.js # Batch recording helper
│   ├── extract_features.js
│   ├── train_model.js
│   ├── test_model.js
│   └── utils.js
├── config.json         # Configuration
├── package.json        # Dependencies
└── TRAINING_GUIDE.md   # This file
```

## Configuration

Edit `config.json` to adjust settings:

```json
{
  "audio": {
    "sampleRate": 16000,     // Audio sample rate
    "duration": 0.6,         // Recording duration in seconds
    "channels": 1,           // Mono audio
    "threshold": 0           // Silence threshold
  },
  "features": {
    "mfccCoefficients": 40,  // Number of MFCC coefficients
    "bufferSize": 1024,      // FFT buffer size
    "hopLength": 512,        // Hop length between frames
    "windowFunction": "hann" // Window function
  },
  "training": {
    "epochs": 40,            // Maximum training epochs
    "batchSize": 32,         // Batch size
    "validationSplit": 0.2,  // Validation data percentage
    "learningRate": 0.001,   // Learning rate
    "earlyStoppingPatience": 10 // Early stopping patience
  },
  "labels": ["A", "E", "I", "O", "U", "noise"], // Class labels
  "model": {
    "inputShape": [43, 232, 1], // Input shape (height, width, channels)
    "outputClasses": 6          // Number of output classes
  }
}
```

## Web App Integration

### Update `index.html`:

Replace the ml5.js script with TensorFlow.js:

```html
<!-- Remove this line -->
<script src="https://unpkg.com/ml5@latest/dist/ml5.min.js"></script>

<!-- Add TensorFlow.js -->
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@latest/dist/tf.min.js"></script>
```

### Update `app.js`:

Replace the ml5.soundClassifier code with TensorFlow.js model loading:

```javascript
// Replace ml5 initialization
async function initializeSoundClassifier() {
  try {
    // Load TensorFlow.js model
    model = await tf.loadLayersModel('./trained/model.json');
    console.log('TensorFlow.js model loaded');
    
    // Update your audio processing to extract MFCC features
    // and use model.predict() for real-time inference
  } catch (error) {
    console.error('Error loading TensorFlow.js model:', error);
  }
}
```

You'll need to implement real-time MFCC feature extraction in the browser. Consider using the Web Audio API or a library like Meyda for browser-based MFCC extraction.

## Troubleshooting

### Audio Recording Issues
- **"No microphone found"**: Check microphone permissions and connections
- **"sox not found"**: Install SoX (Sound eXchange) audio tool
- **Poor audio quality**: Adjust microphone settings, reduce background noise

### Feature Extraction Issues
- **"No MFCC features extracted"**: Check WAV file format and sample rate
- **Memory errors**: Reduce number of samples or feature dimensions

### Training Issues
- **Low accuracy**: Record more training samples, adjust model architecture
- **Overfitting**: Add dropout, use data augmentation, collect more diverse samples
- **Training too slow**: Reduce batch size, simplify model architecture

### Model Loading Issues
- **CORS errors**: Serve files through a local web server
- **Model not found**: Check file paths and ensure model files exist

## Performance Tips

1. **Recording**:
   - Record in a consistent environment
   - Use a good quality microphone
   - Include varied speaking styles and volumes

2. **Training**:
   - Start with 20-30 samples per class
   - Use data augmentation (pitch shift, time stretch, noise addition)
   - Monitor validation loss for overfitting

3. **Inference**:
   - Optimize model size for browser performance
   - Use WebGL backend for faster inference
   - Implement confidence thresholds to reduce false positives

## Next Steps

After successful training:

1. Integrate the model into your web app
2. Implement real-time vowel detection
3. Add visual feedback for detected vowels
4. Create a user interface for model retraining
5. Deploy the application with the new TensorFlow.js model

## Support

If you encounter issues:
1. Check the error messages in the console
2. Verify all dependencies are installed
3. Ensure audio files are in correct format (16kHz, mono, WAV)
4. Review the configuration settings in `config.json`

For additional help, refer to the TensorFlow.js documentation and the project's issue tracker.