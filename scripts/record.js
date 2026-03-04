#!/usr/bin/env node

const record = require('node-record-lpcm16');
const fs = require('fs');
const path = require('path');
const wav = require('wav-encoder');
const minimist = require('minimist');

// Parse command line arguments
const argv = minimist(process.argv.slice(2), {
  string: ['label', 'index', 'duration'],
  alias: {
    l: 'label',
    i: 'index',
    d: 'duration',
    h: 'help'
  },
  default: {
    duration: 0.6
  }
});

// Show help if requested
if (argv.help || !argv.label || !argv.index) {
  console.log(`
Usage: node scripts/record.js --label <label> --index <number> [options]

Options:
  --label, -l    Label for the audio (A, E, I, O, U, noise)
  --index, -i    Index number for this recording
  --duration, -d Recording duration in seconds (default: 0.6)
  --help, -h     Show this help message

Examples:
  node scripts/record.js --label A --index 1
  node scripts/record.js -l E -i 5 -d 1.0
  `);
  process.exit(0);
}

const label = argv.label.toUpperCase();
const index = argv.index;
const duration = parseFloat(argv.duration) * 1000; // Convert to milliseconds

// Validate label
const validLabels = ['A', 'E', 'I', 'O', 'U', 'NOISE'];
if (!validLabels.includes(label)) {
  console.error(`Error: Label must be one of: ${validLabels.join(', ')}`);
  process.exit(1);
}

// Create output directory if it doesn't exist
const outputDir = path.join(__dirname, '..', 'dataset', label === 'NOISE' ? 'noise' : label);
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Output file path
const outputFile = path.join(outputDir, `${label}_${index}.wav`);

console.log(`Recording ${duration/1000} seconds for label: ${label}`);
console.log(`Output file: ${outputFile}`);
console.log('Press Ctrl+C to stop recording early');

// Audio configuration
const sampleRate = 16000;
const channels = 1;

// Collect audio data
const audioData = [];
let isRecording = true;

// Start recording
const recording = record.record({
  sampleRate: sampleRate,
  threshold: 0,
  verbose: false,
  recordProgram: 'sox' // Use SoX for recording
});

// Handle recording stream
recording.stream()
  .on('data', (chunk) => {
    if (isRecording) {
      audioData.push(chunk);
    }
  })
  .on('error', (err) => {
    console.error('Recording error:', err);
    process.exit(1);
  });

// Stop recording after specified duration
setTimeout(() => {
  isRecording = false;
  recording.stop();
  
  // Convert collected data to WAV
  saveAsWav(audioData, sampleRate, channels, outputFile);
}, duration);

// Handle manual interruption
process.on('SIGINT', () => {
  console.log('\nRecording stopped by user');
  isRecording = false;
  recording.stop();
  
  if (audioData.length > 0) {
    saveAsWav(audioData, sampleRate, channels, outputFile);
  } else {
    console.log('No audio data recorded');
    process.exit(0);
  }
});

/**
 * Save audio data as WAV file
 */
async function saveAsWav(audioData, sampleRate, channels, outputPath) {
  try {
    // Combine all chunks into a single buffer
    const totalLength = audioData.reduce((sum, chunk) => sum + chunk.length, 0);
    const audioBuffer = new Float32Array(totalLength / 2); // 16-bit = 2 bytes per sample
    
    let offset = 0;
    for (const chunk of audioData) {
      // Convert 16-bit PCM to float32
      for (let i = 0; i < chunk.length; i += 2) {
        const sample = chunk.readInt16LE(i) / 32768.0;
        audioBuffer[offset++] = sample;
      }
    }
    
    // Encode as WAV
    const wavData = {
      sampleRate: sampleRate,
      channelData: [audioBuffer]
    };
    
    const wavBuffer = await wav.encode(wavData);
    fs.writeFileSync(outputPath, Buffer.from(wavBuffer));
    
    console.log(`\nRecording saved: ${outputPath}`);
    console.log(`Duration: ${(audioBuffer.length / sampleRate).toFixed(2)} seconds`);
    console.log(`Samples: ${audioBuffer.length}`);
    
    process.exit(0);
  } catch (error) {
    console.error('Error saving WAV file:', error);
    process.exit(1);
  }
}