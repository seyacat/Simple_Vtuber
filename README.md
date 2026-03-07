# Vocal Recognition Model Project

A machine learning system for vowel recognition (A, E, I, O, U) and noise classification using audio features and TensorFlow.js.

## 📁 Model Locations

### 1. **Python-trained Models** (`/trained_python_fast/`)
- **`model.keras`** - Keras model file (primary trained model)
- **`training_history.json`** - Training metrics and history
- **`saved_model/`** - TensorFlow SavedModel format
  - `saved_model.pb` - Protocol buffer model definition
  - `keras_metadata.pb` - Keras metadata
  - `variables/` - Model variables
  - `assets/` - Additional assets

### 2. **Web-ready Models** (`/trained_web/`)
- **`tfjs_model/`** - TensorFlow.js format for browser deployment
  - `model.json` - Model architecture
  - `group1-shard1of1.bin` - Model weights

### 3. **Training Artifacts** (`/trained/`)
- **`normalization_params.json`** - Feature normalization parameters

### 4. **Public Models** (`/public/models/`)
- Location for web-accessible models used by the frontend application

## 🛠️ Scripts Overview

### **Data Collection & Processing**
- **`scripts/record.js`** - Record single audio samples
- **`scripts/record_batch.js`** - Record multiple audio samples in batch mode
- **`scripts/aumeta_dataset.py`** - Python script for dataset augmentation
- **`scripts/extract_features.js`** - Extract MFCC features from audio files

### **Model Training**
- **`scripts/train_model.js`** - Train model using TensorFlow.js
- **`scripts/run_train.ps1`** - PowerShell script for training pipeline
- **`batch_train.py`** - Python batch training script
- **`train_tensorflow_gpu.py`** - GPU-accelerated TensorFlow training
- **`start_training.ps1`** - Start training process

### **Model Conversion & Deployment**
- **`scripts/convert_model.js`** - Convert between model formats
- **`scripts/convert_to_web.js`** - Convert model to web format
- **`scripts/convert_keras_to_tfjs.ps1`** - PowerShell script for Keras to TF.js conversion
- **`convert_to_tfjs.py`** - Python script for model conversion
- **`convert_to_numpy.py`** - Convert data to numpy format
- **`update_web_model.py`** - Update web-deployed models

### **Testing & Evaluation**
- **`scripts/test_model.js`** - Test model performance
- **`scripts/utils.js`** - Utility functions shared across scripts

### **Feature Extraction**
- **`extract_features_python.py`** - Python-based feature extraction
- **`fast_data_loader.py`** - Fast data loading utilities

## 🚀 Quick Start

### Prerequisites
- Node.js (for JavaScript scripts)
- Python 3.x with TensorFlow (for Python scripts)
- Audio recording capabilities

### Basic Usage
1. **Record audio samples**: `npm run record` or `npm run record-batch`
2. **Extract features**: `npm run extract`
3. **Train model**: `npm run train`
4. **Test model**: `npm run test`

Or use the all-in-one command: `npm run train-all`

## ⚙️ Configuration

Project settings are defined in `config.json`:
- Audio parameters (sample rate, duration, channels)
- Feature extraction (MFCC coefficients, buffer size)
- Training parameters (epochs, batch size, learning rate)
- Model architecture (input shape, output classes)
- Labels: ["A", "E", "I", "O", "U", "noise"]

## 🐳 Docker Support

- **`Dockerfile`** - Basic Docker configuration
- **`Dockerfile.complete`** - Complete Docker setup
- **`docker-compose.yml`** - Docker Compose configuration
- **`docker_entrypoint.sh`** - Docker entrypoint script
- **`setup_docker_training.sh`** - Setup script for Docker training

## 🌐 Web Application

- **`index.html`** - Main web interface
- **`app.js`** - Main application logic
- **`app_tfjs.js`** - TensorFlow.js application
- **`app_ml5_backup.js`** - ML5.js backup implementation
- **`style.css`** - Styling
- **`vite-waveform-project/`** - Vite-based waveform visualization project

## 📊 Project Structure

```
d:/Vocals_Recognition_Model/
├── scripts/              # All processing scripts
├── trained_python_fast/ # Python-trained models
├── trained_web/         # Web-ready models
├── trained/             # Training artifacts
├── public/              # Web assets
├── vite-waveform-project/ # Waveform visualization
└── *.js, *.py           # Main application files
```

## 🔧 Dependencies

- **TensorFlow.js** (`@tensorflow/tfjs`) - Machine learning
- **Meyda** - Audio feature extraction
- **Naudiodon** - Audio recording
- **fs-extra** - File system utilities

See `package.json` and `requirements.txt` for complete dependency lists.

## 📝 Notes

- The system recognizes 5 vowels (A, E, I, O, U) plus a "noise" class
- Models are trained on MFCC (Mel-frequency cepstral coefficients) features
- Multiple model formats are maintained for different deployment scenarios
- Both JavaScript and Python implementations are available