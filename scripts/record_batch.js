#!/usr/bin/env node

const { exec } = require('child_process');
const path = require('path');
const readline = require('readline');
const config = require('../config.json');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('='.repeat(60));
console.log('BATCH RECORDING HELPER');
console.log('='.repeat(60));
console.log('\nThis script helps you record multiple samples for training.');
console.log(`Labels: ${config.labels.join(', ')}`);
console.log(`Default duration: ${config.audio.duration} seconds`);
console.log('='.repeat(60));

function askQuestion(query) {
  return new Promise(resolve => {
    rl.question(query, answer => {
      resolve(answer);
    });
  });
}

async function main() {
  try {
    // Select label
    console.log('\nSelect label to record:');
    config.labels.forEach((label, index) => {
      console.log(`  ${index + 1}. ${label}`);
    });
    
    const labelChoice = await askQuestion('\nEnter label number (1-6): ');
    const labelIndex = parseInt(labelChoice) - 1;
    
    if (labelIndex < 0 || labelIndex >= config.labels.length) {
      console.error('Invalid label selection');
      rl.close();
      return;
    }
    
    const label = config.labels[labelIndex];
    
    // Get number of samples
    const countStr = await askQuestion(`How many samples to record for "${label}"? (default: 10): `);
    const count = countStr.trim() ? parseInt(countStr) : 10;
    
    if (isNaN(count) || count <= 0) {
      console.error('Invalid count');
      rl.close();
      return;
    }
    
    // Get starting index
    const startStr = await askQuestion(`Starting index number? (default: 1): `);
    const startIndex = startStr.trim() ? parseInt(startStr) : 1;
    
    if (isNaN(startIndex) || startIndex <= 0) {
      console.error('Invalid starting index');
      rl.close();
      return;
    }
    
    // Get duration
    const durationStr = await askQuestion(`Recording duration in seconds? (default: ${config.audio.duration}): `);
    const duration = durationStr.trim() ? parseFloat(durationStr) : config.audio.duration;
    
    if (isNaN(duration) || duration <= 0) {
      console.error('Invalid duration');
      rl.close();
      return;
    }
    
    // Confirm
    console.log('\n' + '='.repeat(60));
    console.log('RECORDING SETUP:');
    console.log(`Label: ${label}`);
    console.log(`Samples: ${count}`);
    console.log(`Starting index: ${startIndex}`);
    console.log(`Duration: ${duration} seconds`);
    console.log('='.repeat(60));
    
    const confirm = await askQuestion('\nStart recording? (y/n): ');
    
    if (confirm.toLowerCase() !== 'y') {
      console.log('Recording cancelled');
      rl.close();
      return;
    }
    
    console.log('\nStarting batch recording...');
    console.log('Press Ctrl+C at any time to cancel.\n');
    
    // Show initial countdown before first recording
    console.log('Starting in 3 seconds...');
    for (let countdown = 3; countdown >= 0; countdown--) {
      process.stdout.write(`\rCountdown: ${countdown}...`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    process.stdout.write('\r' + ' '.repeat(20) + '\r'); // Clear line
    console.log('Starting recordings...\n');
    
    // Record each sample with periodic pauses every 10 samples
    for (let i = 0; i < count; i++) {
      const currentIndex = startIndex + i;
      
      console.log(`\n[${i + 1}/${count}] Recording sample ${currentIndex} for "${label}"...`);
      
      // Check if we need to pause (every 10 samples, starting from sample 0)
      if (i % 10 === 0 && i > 0) {
        console.log('Pausing for 3 seconds...');
        
        // Visual countdown from 3 to 0
        for (let countdown = 3; countdown >= 0; countdown--) {
          process.stdout.write(`\rCountdown: ${countdown}...`);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        process.stdout.write('\r' + ' '.repeat(20) + '\r'); // Clear line
        
        console.log('Resuming recording...');
      }
      
      // Execute recording command
      const command = `node "${path.join(__dirname, 'record.js')}" --label "${label}" --index "${currentIndex}" --duration "${duration}"`;
      
      await new Promise((resolve, reject) => {
        exec(command, (error, stdout, stderr) => {
          if (error) {
            console.error(`Error recording sample ${currentIndex}:`, error.message);
            reject(error);
          } else {
            console.log(`✓ Sample ${currentIndex} recorded successfully`);
            resolve();
          }
        });
      });
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('BATCH RECORDING COMPLETED!');
    console.log(`Recorded ${count} samples for "${label}"`);
    console.log('='.repeat(60));
    
    // Ask about next action
    const nextAction = await askQuestion('\nWhat would you like to do next?\n1. Record another label\n2. Extract features\n3. Exit\n\nChoice (1-3): ');
    
    switch (nextAction) {
      case '1':
        console.log('\n');
        await main(); // Restart
        break;
      case '2':
        console.log('\nRunning feature extraction...');
        exec(`node "${path.join(__dirname, 'extract_features.js')}"`, (error, stdout, stderr) => {
          if (error) {
            console.error('Error extracting features:', error.message);
          } else {
            console.log(stdout);
          }
          rl.close();
        });
        break;
      default:
        console.log('\nExiting. Next steps:');
        console.log('1. Record more samples for other labels');
        console.log('2. Run: node scripts/extract_features.js');
        console.log('3. Run: node scripts/train_model.js');
        rl.close();
        break;
    }
    
  } catch (error) {
    console.error('Error during batch recording:', error);
    rl.close();
  }
}

// Handle Ctrl+C
rl.on('SIGINT', () => {
  console.log('\n\nBatch recording interrupted by user');
  rl.close();
  process.exit(0);
});

// Start the script
main();