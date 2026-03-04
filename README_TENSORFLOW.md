# TensorFlow.js Vowel Recognition System

This project has been updated to use TensorFlow.js for local training and inference, replacing the previous ml5.js/Teachable Machine approach.

## What's New

### 1. Local Training Pipeline
- **Recording**: Node.js scripts to record WAV files for each vowel (A, E, I, O, U, noise)
- **Feature Extraction**: MFCC feature extraction using Meyda library
- **Training**: CNN model training with TensorFlow.js Node
- **Evaluation**: Comprehensive model testing with accuracy metrics

### 2. Updated Web App
- **TensorFlow.js**: Replaced ml5.js with TensorFlow.js for inference
- **Real-time Detection**: Updated audio processing for vowel detection
- **Modern Architecture**: Better performance and compatibility

### 3. Project Structure
```
d:/Simple_Vtuber/
├── dataset/              # Audio files and features
├── trained/             # Trained TensorFlow.js models
├── scripts/             # Training and recording scripts
├── config.json         # Configuration settings
├── package.json        # Updated dependencies
├── app.js             # Updated TensorFlow.js web app
├── index.html         # Updated with TensorFlow.js
└── TRAINING_GUIDE.md  # Complete training instructions
```

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Record Training Data
```bash
npm run record-batch
```
Follow the interactive prompts to record samples for each vowel.

### 3. Train the Model
```bash
npm run extract
npm run train
npm run test
```

### 4. Use the Web App
Open `index.html` in a modern web browser. The app will:
- Load the TensorFlow.js model from `trained/` folder
- Access your microphone (with permission)
- Display real-time waveform visualization
- Detect vowels (A, E, I, O, U) using the trained model

## Key Features

### Training Scripts
- `scripts/record.js` - Record individual WAV samples
- `scripts/record_batch.js` - Interactive batch recording
- `scripts/extract_features.js` - MFCC feature extraction
- `scripts/train_model.js` - CNN model training
- `scripts/test_model.js` - Model evaluation

### Web App Features
- Real-time audio waveform visualization
- Volume level display
- Vowel detection with confidence scores
- TensorFlow.js model loading and inference
- Responsive design

## Configuration

Edit `config.json` to adjust:
- Audio recording settings (sample rate, duration)
- MFCC feature extraction parameters
- Training hyperparameters (epochs, batch size, learning rate)
- Model architecture

## Migration from ml5.js/Teachable Machine

The previous ml5.js implementation has been replaced with TensorFlow.js:

| Previous (ml5.js) | New (TensorFlow.js) |
|-------------------|---------------------|
| `ml5.soundClassifier()` | `tf.loadLayersModel()` |
| Teachable Machine format | TensorFlow.js SavedModel format |
| Web-based training | Local Node.js training |
| Limited customization | Full control over model architecture |

## Requirements

- Node.js 14+ for training scripts
- Modern web browser with Web Audio API support
- Microphone for recording and real-time detection
- SoX (Sound eXchange) for audio recording (optional but recommended)

## Troubleshooting

### Common Issues

1. **Microphone not working**: Check browser permissions and microphone connections
2. **Model not loading**: Ensure `trained/model.json` and `trained/weights.bin` exist
3. **Training errors**: Verify audio files are in correct format (16kHz, mono, WAV)
4. **CORS errors**: Serve files through a local web server (e.g., `python -m http.server`)

### Performance Tips

- Record in a quiet environment for better accuracy
- Use 20-30 samples per vowel for initial training
- Monitor validation accuracy during training
- Adjust model architecture in `config.json` if needed

## Next Steps

After successful setup:

1. Record more diverse samples to improve accuracy
2. Experiment with different model architectures
3. Implement data augmentation for better generalization
4. Add visual feedback for detected vowels
5. Deploy the application with the trained model

## Support

For issues or questions:
1. Check the console for error messages
2. Review the `TRAINING_GUIDE.md` file
3. Verify all dependencies are installed
4. Ensure audio files are in correct format

The TensorFlow.js implementation provides better performance, more control, and local training capabilities compared to the previous ml5.js approach.