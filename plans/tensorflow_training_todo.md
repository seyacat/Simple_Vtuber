# TensorFlow.js Vowel Recognition - Todo List

## Phase 1: Project Setup & Dependencies
- [ ] Create/update `package.json` with TensorFlow.js dependencies
- [ ] Run `npm install` to install all required packages
- [ ] Create directory structure: `dataset/`, `trained/`, `scripts/`
- [ ] Create basic configuration in `config.json`

## Phase 2: Audio Recording System
- [ ] Create `scripts/record.js` - Command-line WAV recorder
- [ ] Implement audio device detection and selection
- [ ] Add recording duration control (0.6 seconds default)
- [ ] Create batch recording helper script
- [ ] Test recording functionality with microphone

## Phase 3: Feature Extraction Pipeline
- [ ] Create `scripts/extract_features.js` - MFCC extractor
- [ ] Implement WAV file reading using `wav-decoder`
- [ ] Extract MFCC features using `meyda` library
- [ ] Normalize features (zero mean, unit variance)
- [ ] Save features to `dataset/features.json`
- [ ] Create label mapping for 6 classes

## Phase 4: Model Training Implementation
- [ ] Create `scripts/train_model.js` - CNN trainer
- [ ] Design CNN architecture (43x232x1 input → 6 outputs)
- [ ] Implement data loading with train/validation split
- [ ] Configure training callbacks (early stopping, checkpoint)
- [ ] Save model to `trained/` folder in TF.js format
- [ ] Export training history and metrics

## Phase 5: Model Evaluation & Testing
- [ ] Create `scripts/test_model.js` - Model evaluator
- [ ] Load trained model and test dataset
- [ ] Calculate accuracy, precision, recall, F1-score
- [ ] Generate confusion matrix
- [ ] Create performance report in `trained/evaluation.json`

## Phase 6: Web App Integration
- [ ] Update `index.html` - Replace ml5.js with TensorFlow.js CDN
- [ ] Modify `app.js` - Replace ml5.soundClassifier with tf.loadLayersModel
- [ ] Implement real-time audio feature extraction in browser
- [ ] Add model loading status and error handling
- [ ] Update UI to show TensorFlow.js predictions
- [ ] Test inference performance and accuracy

## Phase 7: Documentation & Usage Guide
- [ ] Create `TRAINING_GUIDE.md` with step-by-step instructions
- [ ] Document all script commands and parameters
- [ ] Add examples for recording each vowel
- [ ] Create troubleshooting section
- [ ] Update main `README.md` with new approach

## Quick Start Commands
```bash
# 1. Setup
npm install

# 2. Record training data (repeat for each vowel)
node scripts/record.js A 1
node scripts/record.js A 2
# ... repeat for E, I, O, U, noise

# 3. Extract features
node scripts/extract_features.js

# 4. Train model
node scripts/train_model.js

# 5. Test model
node scripts/test_model.js

# 6. Run web app
# Open index.html in browser
```

## File Structure to Create
```
scripts/
├── record.js              # Record WAV files
├── extract_features.js    # Extract MFCC features
├── train_model.js         # Train CNN model
├── test_model.js          # Evaluate model
└── utils.js              # Shared utilities

dataset/
├── A/                    # WAV files for vowel A
├── E/                    # WAV files for vowel E  
├── I/                    # WAV files for vowel I
├── O/                    # WAV files for vowel O
├── U/                    # WAV files for vowel U
├── noise/                # WAV files for noise/background
└── features.json         # Extracted MFCC features

trained/
├── model.json           # Model architecture
├── weights.bin          # Model weights
└── evaluation.json      # Performance metrics
```

## Dependencies to Install
```bash
npm install @tensorflow/tfjs @tensorflow/tfjs-node
npm install node-record-lpcm16 wav-decoder wav-encoder meyda fs-extra
```

## Success Validation Checklist
- [ ] Can record WAV files for all 6 labels
- [ ] MFCC extraction produces valid feature vectors
- [ ] Model training completes without errors
- [ ] Validation accuracy > 85%
- [ ] Web app loads TensorFlow.js model successfully
- [ ] Real-time vowel detection works in browser
- [ ] All scripts are documented and easy to use

## Notes
- Keep existing `techeable/` folder as backup during transition
- Test each phase independently before proceeding
- Consider adding data augmentation for better generalization
- Monitor training loss/accuracy to prevent overfitting