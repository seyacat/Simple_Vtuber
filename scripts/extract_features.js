#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const wav = require('wav-decoder');
const Meyda = require('meyda');

const config = require('../config.json');
const utils = require('./utils');

async function main() {
  console.log('Starting feature extraction...');
  console.log(`Labels: ${config.labels.join(', ')}`);

  // Get all audio files
  const audioFiles = utils.getAllAudioFiles();
  console.log(`Found ${audioFiles.length} audio files`);

  if (audioFiles.length === 0) {
    console.error('No audio files found in dataset directory');
    console.error('Please record some audio files first using: node scripts/record.js --label A --index 1');
    process.exit(1);
  }

  // Count files per label
  const labelCounts = {};
  audioFiles.forEach(file => {
    labelCounts[file.label] = (labelCounts[file.label] || 0) + 1;
  });

  console.log('Files per label:');
  Object.entries(labelCounts).forEach(([label, count]) => {
    console.log(`  ${label}: ${count} files`);
  });

  // Extract features from each file
  const features = [];
  const labels = [];
  const filePaths = [];

  let processed = 0;
  const total = audioFiles.length;

  console.log('\nExtracting MFCC features...');

  for (const file of audioFiles) {
    try {
      // Read WAV file
      const buffer = fs.readFileSync(file.path);
      const audioData = await wav.decode(buffer);
      
      // Get audio signal (first channel)
      const signal = audioData.channelData[0];
      
      // Find largest power of 2 <= signal length
      let bufferSize = 1024;
      while (bufferSize > signal.length && bufferSize > 64) {
        bufferSize /= 2;
      }
      
      // Ensure bufferSize is power of 2
      if (bufferSize < 64) bufferSize = 64;
      
      const hopSize = Math.floor(bufferSize / 2);
      
      // Use first bufferSize samples (truncate if needed)
      const bufferSignal = signal.slice(0, bufferSize);
      
      const mfcc = Meyda.extract('mfcc', bufferSignal, {
        sampleRate: config.audio.sampleRate,
        bufferSize: bufferSize,
        hopSize: hopSize,
        numberOfMFCCCoefficients: config.features.mfccCoefficients
      });
      
      // MFCC returns an array of arrays (frames x coefficients)
      // We need to reshape to match the expected input shape
      if (mfcc && Array.isArray(mfcc) && mfcc.length > 0) {
        // Flatten the MFCC frames into a single feature vector
        // Or keep as 2D array depending on model requirements
        const flatFeatures = mfcc.flat();
        
        features.push(flatFeatures);
        labels.push(utils.getLabelIndex(file.label));
        filePaths.push(file.path);
        
        processed++;
        if (processed % 10 === 0 || processed === total) {
          console.log(`Processed ${processed}/${total} files`);
        }
      } else {
        console.warn(`No MFCC features extracted from ${file.path}`);
      }
    } catch (error) {
      console.error(`Error processing ${file.path}:`, error.message);
    }
  }

console.log(`\nSuccessfully extracted features from ${features.length} files`);

// Check if we have enough data
if (features.length === 0) {
  console.error('No features extracted. Check your audio files.');
  process.exit(1);
}

// Check feature dimensions
const featureLength = features[0].length;
console.log(`Feature vector length: ${featureLength}`);

// Verify all features have same length
const inconsistent = features.some(f => f.length !== featureLength);
if (inconsistent) {
  console.error('Inconsistent feature lengths detected');
  // Pad or truncate features to same length
  const targetLength = Math.max(...features.map(f => f.length));
  console.log(`Padding/truncating to ${targetLength} features`);
  
  for (let i = 0; i < features.length; i++) {
    if (features[i].length < targetLength) {
      // Pad with zeros
      features[i] = features[i].concat(new Array(targetLength - features[i].length).fill(0));
    } else if (features[i].length > targetLength) {
      // Truncate
      features[i] = features[i].slice(0, targetLength);
    }
  }
}

// Normalize features
console.log('Normalizing features...');
const { normalizedFeatures, mean, std } = utils.normalizeFeatures(features);

// Save normalization parameters
const normParamsPath = path.join(__dirname, '..', 'trained', 'normalization_params.json');
fs.ensureDirSync(path.dirname(normParamsPath));
utils.saveNormalizationParams({ mean, std }, normParamsPath);
console.log(`Normalization parameters saved to ${normParamsPath}`);

// Prepare data for saving
const featureData = {
  features: normalizedFeatures,
  labels: labels,
  labelNames: config.labels,
  filePaths: filePaths,
  featureShape: [config.model.inputShape[0], config.model.inputShape[1]],
  sampleRate: config.audio.sampleRate,
  extractionDate: new Date().toISOString()
};

// Save features to file
const featuresPath = path.join(__dirname, '..', 'dataset', 'features.json');
fs.writeJsonSync(featuresPath, featureData, { spaces: 2 });

console.log(`\nFeatures saved to ${featuresPath}`);
console.log(`Total samples: ${normalizedFeatures.length}`);
console.log(`Feature shape: ${config.model.inputShape[0]}x${config.model.inputShape[1]}`);

// Create train/validation split
console.log('\nCreating train/validation split...');
const splitData = utils.splitTrainValidation(
  normalizedFeatures.map((features, idx) => ({ features, label: labels[idx] })),
  config.training.validationSplit
);

console.log(`Training samples: ${splitData.train.length}`);
console.log(`Validation samples: ${splitData.validation.length}`);

// Save split data
const splitPath = path.join(__dirname, '..', 'dataset', 'split_data.json');
const splitInfo = {
  train: {
    indices: splitData.train.map((_, idx) => idx),
    count: splitData.train.length
  },
  validation: {
    indices: splitData.validation.map((_, idx) => normalizedFeatures.length - splitData.validation.length + idx),
    count: splitData.validation.length
  },
  splitRatio: config.training.validationSplit
};

fs.writeJsonSync(splitPath, splitInfo, { spaces: 2 });
console.log(`Split data saved to ${splitPath}`);

console.log('\nFeature extraction completed successfully!');
console.log('\nNext steps:');
console.log('1. Review the extracted features in dataset/features.json');
console.log('2. Train the model: node scripts/train_model.js');
console.log('3. Test the model: node scripts/test_model.js');
}

// Execute main function and handle errors
main().catch(error => {
  console.error('Feature extraction failed:', error);
  process.exit(1);
});