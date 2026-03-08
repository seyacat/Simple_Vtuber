const fs = require("fs");
const path = require("path");
const Meyda = require("meyda");
const wav = require("wav-decoder");

const config = {
  audio: {
    sampleRate: 16000
  },

  features: {
    bufferSize: 512,
    hopSize: 256,
    mfccCoefficients: 13
  },

  datasetPath: "./dataset"
};

async function loadWav(filePath) {
  const buffer = fs.readFileSync(filePath);
  const decoded = await wav.decode(buffer);
  return decoded.channelData[0];
}

function extractMFCC(signal) {

  const frames = [];
  const { bufferSize, hopSize, mfccCoefficients } = config.features;

  for (let i = 0; i + bufferSize <= signal.length; i += hopSize) {

    const frame = signal.slice(i, i + bufferSize);

    const mfcc = Meyda.extract("mfcc", frame, {
      sampleRate: config.audio.sampleRate,
      bufferSize: bufferSize,
      numberOfMFCCCoefficients: mfccCoefficients
    });

    if (mfcc) {
      frames.push(mfcc);
    }
  }

  return frames;
}

async function processFile(filePath) {

  const signal = await loadWav(filePath);

  const mfccFrames = extractMFCC(signal);

  if (!mfccFrames.length) return;

  const outputPath = filePath.replace(".wav", ".json");

  fs.writeFileSync(
    outputPath,
    JSON.stringify({
      features: mfccFrames
    })
  );

  console.log("Guardado:", outputPath);
}

async function walk(dir) {

  const files = fs.readdirSync(dir);

  for (const file of files) {

    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      await walk(fullPath);
    }

    if (file.endsWith(".wav")) {
      await processFile(fullPath);
    }
  }
}

walk(config.datasetPath);