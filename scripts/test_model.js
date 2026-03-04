#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const tf = require('@tensorflow/tfjs');

const config = require('../config.json');
const utils = require('./utils');

async function main() {
  console.log('Starting model testing...');

// Check if model exists
const modelDir = path.join(__dirname, '..', 'trained');
const modelJsonPath = path.join(modelDir, 'model.json');

if (!fs.existsSync(modelJsonPath)) {
  console.error(`Model not found: ${modelJsonPath}`);
  console.error('Please train the model first: node scripts/train_model.js');
  process.exit(1);
}

// Check if features exist
const featuresPath = path.join(__dirname, '..', 'dataset', 'features.json');
if (!fs.existsSync(featuresPath)) {
  console.error(`Features file not found: ${featuresPath}`);
  console.error('Please extract features first: node scripts/extract_features.js');
  process.exit(1);
}

// Load model
console.log(`Loading model from ${modelDir}...`);
const model = await loadModelFromDirectory(modelDir);
console.log('Model loaded successfully');

// Load features
console.log('Loading features...');
const featureData = fs.readJsonSync(featuresPath);
const { features, labels, labelNames } = featureData;

console.log(`Loaded ${features.length} samples for testing`);

// Reshape features
const [height, width, channels] = config.model.inputShape;
const totalElements = height * width * channels;

const reshapedFeatures = features.map(f => {
  if (f.length === totalElements) {
    return reshapeTo2D(f, height, width);
  } else {
    const padded = padOrTruncate(f, totalElements);
    return reshapeTo2D(padded, height, width);
  }
});

// Convert to tensor
const featuresTensor = tf.tensor3d(reshapedFeatures, [features.length, height, width]);

// Make predictions
console.log('Making predictions...');
const predictions = model.predict(featuresTensor);
const predictedIndices = predictions.argMax(-1).arraySync();
const predictionProbabilities = predictions.arraySync();

// Calculate accuracy
let correct = 0;
const confusionMatrix = Array(config.model.outputClasses)
  .fill()
  .map(() => Array(config.model.outputClasses).fill(0));

for (let i = 0; i < labels.length; i++) {
  const trueLabel = labels[i];
  const predictedLabel = predictedIndices[i];
  
  confusionMatrix[trueLabel][predictedLabel]++;
  
  if (trueLabel === predictedLabel) {
    correct++;
  }
}

const accuracy = (correct / labels.length) * 100;

// Calculate per-class metrics
const classMetrics = [];
for (let classIdx = 0; classIdx < config.model.outputClasses; classIdx++) {
  const className = labelNames[classIdx];
  
  // True positives: predicted as class and actually class
  const tp = confusionMatrix[classIdx][classIdx];
  
  // False positives: predicted as class but actually other classes
  let fp = 0;
  for (let otherClass = 0; otherClass < config.model.outputClasses; otherClass++) {
    if (otherClass !== classIdx) {
      fp += confusionMatrix[otherClass][classIdx];
    }
  }
  
  // False negatives: actually class but predicted as other classes
  let fn = 0;
  for (let otherClass = 0; otherClass < config.model.outputClasses; otherClass++) {
    if (otherClass !== classIdx) {
      fn += confusionMatrix[classIdx][otherClass];
    }
  }
  
  // True negatives: not class and not predicted as class
  let tn = 0;
  for (let trueClass = 0; trueClass < config.model.outputClasses; trueClass++) {
    for (let predClass = 0; predClass < config.model.outputClasses; predClass++) {
      if (trueClass !== classIdx && predClass !== classIdx) {
        tn += confusionMatrix[trueClass][predClass];
      }
    }
  }
  
  const precision = tp + fp > 0 ? tp / (tp + fp) : 0;
  const recall = tp + fn > 0 ? tp / (tp + fn) : 0;
  const f1Score = precision + recall > 0 ? 2 * (precision * recall) / (precision + recall) : 0;
  
  classMetrics.push({
    class: className,
    truePositives: tp,
    falsePositives: fp,
    falseNegatives: fn,
    trueNegatives: tn,
    precision: precision,
    recall: recall,
    f1Score: f1Score,
    support: labels.filter(l => l === classIdx).length
  });
}

// Display results
console.log('\n' + '='.repeat(60));
console.log('MODEL EVALUATION RESULTS');
console.log('='.repeat(60));

console.log(`\nOverall Accuracy: ${accuracy.toFixed(2)}% (${correct}/${labels.length})`);

console.log('\nConfusion Matrix:');
console.log('True \\ Predicted | ' + labelNames.map(n => n.padEnd(8)).join(' '));
console.log('-'.repeat(60));

for (let i = 0; i < config.model.outputClasses; i++) {
  const row = confusionMatrix[i];
  const rowStr = row.map(count => count.toString().padEnd(8)).join(' ');
  console.log(`${labelNames[i].padEnd(15)} | ${rowStr}`);
}

console.log('\nPer-Class Metrics:');
console.log('Class    | Precision | Recall   | F1-Score | Support');
console.log('-'.repeat(60));

classMetrics.forEach(metric => {
  console.log(
    `${metric.class.padEnd(8)} | ${metric.precision.toFixed(4).padEnd(9)} | ` +
    `${metric.recall.toFixed(4).padEnd(8)} | ${metric.f1Score.toFixed(4).padEnd(8)} | ` +
    `${metric.support}`
  );
});

// Calculate macro averages
const macroPrecision = classMetrics.reduce((sum, m) => sum + m.precision, 0) / classMetrics.length;
const macroRecall = classMetrics.reduce((sum, m) => sum + m.recall, 0) / classMetrics.length;
const macroF1 = classMetrics.reduce((sum, m) => sum + m.f1Score, 0) / classMetrics.length;

console.log('\nMacro Averages:');
console.log(`Precision: ${macroPrecision.toFixed(4)}`);
console.log(`Recall: ${macroRecall.toFixed(4)}`);
console.log(`F1-Score: ${macroF1.toFixed(4)}`);

// Save evaluation results
const evaluationPath = path.join(__dirname, '..', 'trained', 'evaluation.json');
const evaluationData = {
  accuracy: accuracy,
  correct: correct,
  total: labels.length,
  confusionMatrix: confusionMatrix,
  classMetrics: classMetrics,
  macroAverages: {
    precision: macroPrecision,
    recall: macroRecall,
    f1Score: macroF1
  },
  evaluationDate: new Date().toISOString(),
  modelInfo: {
    inputShape: config.model.inputShape,
    outputClasses: config.model.outputClasses,
    labels: labelNames
  }
};

fs.writeJsonSync(evaluationPath, evaluationData, { spaces: 2 });
console.log(`\nEvaluation results saved to ${evaluationPath}`);

// Display some example predictions
console.log('\nExample Predictions (first 10 samples):');
console.log('Index | True Label | Predicted Label | Confidence | Correct');
console.log('-'.repeat(70));

for (let i = 0; i < Math.min(10, labels.length); i++) {
  const trueLabel = labelNames[labels[i]];
  const predictedLabel = labelNames[predictedIndices[i]];
  const confidence = Math.max(...predictionProbabilities[i]) * 100;
  const isCorrect = labels[i] === predictedIndices[i];
  
  console.log(
    `${i.toString().padEnd(5)} | ${trueLabel.padEnd(10)} | ${predictedLabel.padEnd(14)} | ` +
    `${confidence.toFixed(1).padEnd(10)}% | ${isCorrect ? '✓' : '✗'}`
  );
}

// Clean up
featuresTensor.dispose();
predictions.dispose();

console.log('\nTesting completed!');
console.log('\nRecommendations:');
if (accuracy < 85) {
  console.log('⚠️  Accuracy below 85%. Consider:');
  console.log('   - Recording more training samples');
  console.log('   - Adjusting model architecture');
  console.log('   - Checking audio quality');
} else if (accuracy < 95) {
  console.log('✅ Good accuracy! For improvement:');
  console.log('   - Add data augmentation');
  console.log('   - Fine-tune hyperparameters');
} else {
  console.log('🎉 Excellent accuracy! Model is ready for production.');
}
}

/**
 * Load model from directory (custom loader for Node.js)
 */
async function loadModelFromDirectory(modelDir) {
  const modelJsonPath = path.join(modelDir, 'model.json');
  
  if (!fs.existsSync(modelJsonPath)) {
    throw new Error(`Model JSON not found: ${modelJsonPath}`);
  }
  
  // Read model JSON
  const modelJSON = fs.readJsonSync(modelJsonPath);
  
  // Load weights
  const weightsManifest = modelJSON.weightsManifest[0];
  const weightsBinPath = path.join(modelDir, weightsManifest.paths[0]);
  
  if (!fs.existsSync(weightsBinPath)) {
    throw new Error(`Weights file not found: ${weightsBinPath}`);
  }
  
  // Read weights binary file
  const weightsBuffer = fs.readFileSync(weightsBinPath);
  const weightsArray = new Uint8Array(weightsBuffer);
  
  // Create weight tensors
  const weightTensors = [];
  let offset = 0;
  
  for (const weightSpec of weightsManifest.weights) {
    const size = weightSpec.shape.reduce((a, b) => a * b, 1);
    const bytes = size * 4; // float32 = 4 bytes
    
    // Extract slice from weights array
    const weightSlice = weightsArray.slice(offset, offset + bytes);
    const floatArray = new Float32Array(weightSlice.buffer, weightSlice.byteOffset, size);
    
    // Create tensor
    const tensor = tf.tensor(floatArray, weightSpec.shape);
    weightTensors.push(tensor);
    
    offset += bytes;
  }
  
  // Load model topology
  const model = await tf.models.modelFromJSON(modelJSON.modelTopology);
  
  // Set weights
  model.setWeights(weightTensors);
  
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
    return array.concat(new Array(targetLength - array.length).fill(0));
  } else {
    return array.slice(0, targetLength);
  }
}

// Execute main function and handle errors
main().catch(error => {
  console.error('Model testing failed:', error);
  process.exit(1);
});