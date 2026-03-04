const fs = require('fs-extra');
const path = require('path');
const config = require('../config.json');

/**
 * Get all WAV files from dataset directory
 * @returns {Array} Array of file objects with path and label
 */
function getAllAudioFiles() {
  const datasetPath = path.join(__dirname, '..', 'dataset');
  const files = [];
  
  for (const label of config.labels) {
    const labelDir = path.join(datasetPath, label === 'noise' ? 'noise' : label);
    
    if (fs.existsSync(labelDir)) {
      const labelFiles = fs.readdirSync(labelDir)
        .filter(file => file.endsWith('.wav'))
        .map(file => ({
          path: path.join(labelDir, file),
          label: label,
          filename: file
        }));
      
      files.push(...labelFiles);
    }
  }
  
  return files;
}

/**
 * Get label index from label name
 * @param {string} label - Label name
 * @returns {number} Label index
 */
function getLabelIndex(label) {
  return config.labels.indexOf(label);
}

/**
 * Get label name from index
 * @param {number} index - Label index
 * @returns {string} Label name
 */
function getLabelName(index) {
  return config.labels[index];
}

/**
 * Split array into training and validation sets
 * @param {Array} array - Array to split
 * @param {number} validationSplit - Validation split ratio (0-1)
 * @returns {Object} {train, validation}
 */
function splitTrainValidation(array, validationSplit = 0.2) {
  const shuffled = [...array].sort(() => Math.random() - 0.5);
  const splitIndex = Math.floor(shuffled.length * (1 - validationSplit));
  
  return {
    train: shuffled.slice(0, splitIndex),
    validation: shuffled.slice(splitIndex)
  };
}

/**
 * Create one-hot encoding for labels
 * @param {number} index - Label index
 * @param {number} numClasses - Number of classes
 * @returns {Array} One-hot encoded array
 */
function oneHotEncode(index, numClasses) {
  const encoding = new Array(numClasses).fill(0);
  encoding[index] = 1;
  return encoding;
}

/**
 * Normalize features (zero mean, unit variance)
 * @param {Array} features - Array of feature vectors
 * @returns {Object} {normalizedFeatures, mean, std}
 */
function normalizeFeatures(features) {
  if (features.length === 0) {
    return { normalizedFeatures: [], mean: 0, std: 1 };
  }
  
  // Calculate mean and std for each feature dimension
  const numFeatures = features[0].length;
  const means = new Array(numFeatures).fill(0);
  const stds = new Array(numFeatures).fill(0);
  
  // Calculate mean
  for (const feature of features) {
    for (let i = 0; i < numFeatures; i++) {
      means[i] += feature[i];
    }
  }
  
  for (let i = 0; i < numFeatures; i++) {
    means[i] /= features.length;
  }
  
  // Calculate standard deviation
  for (const feature of features) {
    for (let i = 0; i < numFeatures; i++) {
      const diff = feature[i] - means[i];
      stds[i] += diff * diff;
    }
  }
  
  for (let i = 0; i < numFeatures; i++) {
    stds[i] = Math.sqrt(stds[i] / features.length);
    // Avoid division by zero
    if (stds[i] === 0) stds[i] = 1;
  }
  
  // Normalize features
  const normalizedFeatures = features.map(feature => 
    feature.map((value, i) => (value - means[i]) / stds[i])
  );
  
  return {
    normalizedFeatures,
    mean: means,
    std: stds
  };
}

/**
 * Save normalization parameters to file
 * @param {Object} params - Normalization parameters
 * @param {string} filePath - Output file path
 */
function saveNormalizationParams(params, filePath) {
  fs.writeJsonSync(filePath, params, { spaces: 2 });
}

/**
 * Load normalization parameters from file
 * @param {string} filePath - Input file path
 * @returns {Object} Normalization parameters
 */
function loadNormalizationParams(filePath) {
  return fs.readJsonSync(filePath);
}

/**
 * Apply normalization to features using pre-computed parameters
 * @param {Array} features - Features to normalize
 * @param {Object} params - Normalization parameters {mean, std}
 * @returns {Array} Normalized features
 */
function applyNormalization(features, params) {
  return features.map(feature =>
    feature.map((value, i) => (value - params.mean[i]) / params.std[i])
  );
}

module.exports = {
  getAllAudioFiles,
  getLabelIndex,
  getLabelName,
  splitTrainValidation,
  oneHotEncode,
  normalizeFeatures,
  saveNormalizationParams,
  loadNormalizationParams,
  applyNormalization
};