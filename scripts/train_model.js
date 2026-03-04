#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const tf = require('@tensorflow/tfjs');

const config = require('../config.json');
const utils = require('./utils');

async function main() {
  console.log('Starting model training...');
console.log(`Model input shape: ${config.model.inputShape.join('x')}`);
console.log(`Output classes: ${config.model.outputClasses}`);
console.log(`Labels: ${config.labels.join(', ')}`);

// Load features
const featuresPath = path.join(__dirname, '..', 'dataset', 'features.json');
if (!fs.existsSync(featuresPath)) {
  console.error(`Features file not found: ${featuresPath}`);
  console.error('Please run feature extraction first: node scripts/extract_features.js');
  process.exit(1);
}

console.log(`Loading features from ${featuresPath}...`);
const featureData = fs.readJsonSync(featuresPath);

const { features, labels, labelNames } = featureData;
console.log(`Loaded ${features.length} samples with ${labels.length} labels`);

// Verify data
if (features.length !== labels.length) {
  console.error(`Mismatch: ${features.length} features vs ${labels.length} labels`);
  process.exit(1);
}

// Reshape features to match model input shape
console.log('Reshaping features...');
const [height, width, channels] = config.model.inputShape;
const totalElements = height * width * channels;

// Check if features need to be reshaped
let reshapedFeatures;
if (features[0].length === totalElements) {
  // Features already have correct total elements
  reshapedFeatures = features.map(f => 
    Array.isArray(f[0]) ? f : // Already 2D
    reshapeTo2D(f, height, width)
  );
} else {
  console.warn(`Feature length ${features[0].length} doesn't match expected ${totalElements}`);
  console.warn('Attempting to pad/truncate...');
  
  reshapedFeatures = features.map(f => {
    const padded = padOrTruncate(f, totalElements);
    return reshapeTo2D(padded, height, width);
  });
}

// Convert to tensors
console.log('Converting data to tensors...');
// Create 3D tensor and expand to 4D with channels dimension
const featuresTensor = tf.tensor3d(
  reshapedFeatures,
  [features.length, height, width]
).expandDims(-1); // Add channels dimension at the end

const labelsTensor = tf.oneHot(
  tf.tensor1d(labels, 'int32'),
  config.model.outputClasses
);

// Create model
console.log('Creating CNN model...');
const model = createModel(height, width, channels, config.model.outputClasses);

// Compile model
model.compile({
  optimizer: tf.train.adam(config.training.learningRate),
  loss: 'categoricalCrossentropy',
  metrics: ['accuracy']
});

// Print model summary
console.log('\nModel Summary:');
model.summary();

// Prepare callbacks
const callbacks = [
  tf.callbacks.earlyStopping({
    monitor: 'val_loss',
    patience: config.training.earlyStoppingPatience,
    restoreBestWeights: false
  })
];

// Train model
console.log('\nStarting training...');
console.log(`Epochs: ${config.training.epochs}, Batch size: ${config.training.batchSize}`);

const history = await model.fit(featuresTensor, labelsTensor, {
  epochs: config.training.epochs,
  batchSize: config.training.batchSize,
  validationSplit: config.training.validationSplit,
  callbacks: callbacks,
  verbose: 1
});

// Save model
console.log('\nSaving model...');
const modelSavePath = path.join(__dirname, '..', 'trained');
fs.ensureDirSync(modelSavePath);

// Save model using custom save handler for Node.js
await saveModel(model, modelSavePath);

console.log(`Model saved to ${modelSavePath}`);

// Save training history
const historyPath = path.join(__dirname, '..', 'trained', 'training_history.json');
const historyData = {
  epochs: history.epoch.length,
  history: {
    loss: history.history.loss,
    accuracy: history.history.acc,
    val_loss: history.history.val_loss,
    val_accuracy: history.history.val_acc
  },
  finalMetrics: {
    loss: history.history.loss[history.history.loss.length - 1],
    accuracy: history.history.acc[history.history.acc.length - 1],
    val_loss: history.history.val_loss[history.history.val_loss.length - 1],
    val_accuracy: history.history.val_acc[history.history.val_acc.length - 1]
  },
  trainingDate: new Date().toISOString(),
  config: config.training
};

fs.writeJsonSync(historyPath, historyData, { spaces: 2 });
console.log(`Training history saved to ${historyPath}`);

// Clean up tensors to free memory
featuresTensor.dispose();
labelsTensor.dispose();

console.log('\nTraining completed successfully!');
console.log('\nNext steps:');
console.log('1. Test the model: node scripts/test_model.js');
console.log('2. Update web app to use the new model');
}

/**
 * Save model manually for Node.js environment in TensorFlow.js format
 */
async function saveModel(model, savePath) {
  console.log('Saving model architecture and weights...');
  
  // Get model topology and weights
  const modelJSON = model.toJSON();
  const weights = await model.getWeights();
  
  // Create weights manifest
  const weightSpecs = [];
  const weightData = [];
  
  for (let i = 0; i < weights.length; i++) {
    const weight = weights[i];
    const data = weight.dataSync();
    
    weightSpecs.push({
      name: `weight_${i}`,
      shape: weight.shape,
      dtype: 'float32'
    });
    
    // Convert Float32Array to ArrayBuffer
    const buffer = data.buffer.slice(
      data.byteOffset,
      data.byteOffset + data.byteLength
    );
    weightData.push(new Uint8Array(buffer));
  }
  
  // Concatenate all weight data into a single buffer
  let totalLength = 0;
  for (const arr of weightData) {
    totalLength += arr.length;
  }
  
  const combinedWeights = new Uint8Array(totalLength);
  let offset = 0;
  for (const arr of weightData) {
    combinedWeights.set(arr, offset);
    offset += arr.length;
  }
  
  // Save weights.bin file
  const weightsBinPath = path.join(savePath, 'weights.bin');
  fs.writeFileSync(weightsBinPath, Buffer.from(combinedWeights));
  
  // Create and save model.json with weights manifest
  const tfjsModelJSON = {
    modelTopology: modelJSON,
    weightsManifest: [{
      paths: ['./weights.bin'],
      weights: weightSpecs
    }]
  };
  
  const modelJSONPath = path.join(savePath, 'model.json');
  fs.writeJsonSync(modelJSONPath, tfjsModelJSON, { spaces: 2 });
  
  console.log('Model saved in TensorFlow.js format at:', savePath);
  console.log(`- ${modelJSONPath}`);
  console.log(`- ${weightsBinPath} (${combinedWeights.length} bytes)`);
}

/**
 * Create CNN model for vowel recognition
 */
function createModel(height, width, channels, numClasses) {
  const model = tf.sequential();
  
  // First convolutional layer
  model.add(tf.layers.conv2d({
    filters: 8,
    kernelSize: [2, 8],
    activation: 'relu',
    inputShape: [height, width, channels],
    padding: 'same'
  }));
  
  model.add(tf.layers.maxPooling2d({
    poolSize: [2, 2],
    strides: [2, 2]
  }));
  
  // Second convolutional layer
  model.add(tf.layers.conv2d({
    filters: 16,
    kernelSize: [2, 4],
    activation: 'relu',
    padding: 'same'
  }));
  
  model.add(tf.layers.maxPooling2d({
    poolSize: [2, 2],
    strides: [2, 2]
  }));
  
  // Flatten and dense layers
  model.add(tf.layers.flatten());
  
  model.add(tf.layers.dense({
    units: 64,
    activation: 'relu'
  }));
  
  model.add(tf.layers.dropout({
    rate: 0.5
  }));
  
  model.add(tf.layers.dense({
    units: 32,
    activation: 'relu'
  }));
  
  // Output layer
  model.add(tf.layers.dense({
    units: numClasses,
    activation: 'softmax'
  }));
  
  return model;
}

/**
 * Reshape 1D array to 2D array
 */
function reshapeTo2D(array, rows, cols) {
  const result = [];
  for (let i = 0; i < rows; i++) {
    result.push(array.slice(i * cols, (i + 1) * cols));
  }
  return result;
}

/**
 * Pad or truncate array to target length
 */
function padOrTruncate(array, targetLength) {
  if (array.length === targetLength) {
    return array;
  } else if (array.length < targetLength) {
    // Pad with zeros
    return array.concat(new Array(targetLength - array.length).fill(0));
  } else {
    // Truncate
    return array.slice(0, targetLength);
  }
}

// Execute main function and handle errors
main().catch(error => {
  console.error('Model training failed:', error);
  process.exit(1);
});