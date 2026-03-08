#!/usr/bin/env node

const portAudio = require('naudiodon');
const fs = require('fs');
const path = require('path');
const wav = require('wav-encoder');
const minimist = require('minimist');

// Cargar configuración desde config.json
let config;
try {
  const configFile = fs.readFileSync('config.json', 'utf8');
  config = JSON.parse(configFile);
  console.log(`Configuración cargada: sampleRate=${config.audio.sampleRate}Hz`);
} catch (error) {
  console.error('Error cargando config.json, usando valores por defecto:', error.message);
  config = {
    audio: {
      sampleRate: 16000
    }
  };
}

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
const sampleRate = config.audio.sampleRate;
const channels = 1;
const bytesPerSample = 2; // 16-bit = 2 bytes

// Calculate total bytes needed for requested duration
// duration is in milliseconds, convert to seconds: duration/1000
const samplesNeeded = Math.floor(sampleRate * (duration / 1000));
const bytesNeeded = samplesNeeded * channels * bytesPerSample;

// Collect audio data
const audioData = [];
let totalBytes = 0;
let isRecording = true;

// Create audio input stream with naudiodon
const ai = new portAudio.AudioIO({
  inOptions: {
    channelCount: channels,
    sampleFormat: portAudio.SampleFormat16Bit,
    sampleRate: sampleRate,
    deviceId: -1, // Use default device
    closeOnError: true
  }
});

// Handle recording stream
ai
  .on('data', (chunk) => {
    if (!isRecording) return;
    
    audioData.push(chunk);
    totalBytes += chunk.length;
    
    // Check if we have enough data
    if (totalBytes >= bytesNeeded) {
      isRecording = false;
      ai.quit();
      
      // Trim excess data if we got more than needed
      if (totalBytes > bytesNeeded) {
        const excessBytes = totalBytes - bytesNeeded;
        const lastChunk = audioData[audioData.length - 1];
        if (lastChunk.length > excessBytes) {
          // Trim the last chunk
          audioData[audioData.length - 1] = lastChunk.slice(0, lastChunk.length - excessBytes);
          totalBytes = bytesNeeded;
        }
      }
      
      // Convert collected data to WAV
      saveAsWav(audioData, sampleRate, channels, outputFile);
    }
  })
  .on('error', (err) => {
    console.error('Recording error:', err);
    process.exit(1);
  });

// Start recording
ai.start();
console.log('Recording started...');

// Safety timeout - stop recording if something goes wrong
setTimeout(() => {
  if (isRecording) {
    console.log('Safety timeout reached, stopping recording');
    isRecording = false;
    ai.quit();
    
    if (audioData.length > 0) {
      saveAsWav(audioData, sampleRate, channels, outputFile);
    } else {
      console.log('No audio data recorded');
      process.exit(0);
    }
  }
}, duration + 2000); // Add 2 seconds buffer

// Handle manual interruption
process.on('SIGINT', () => {
  console.log('\nRecording stopped by user');
  isRecording = false;
  ai.quit();
  
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