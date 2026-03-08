const fs = require("fs");
const path = require("path");
const Meyda = require("meyda");
const wav = require("wav-decoder");

// Cargar configuración desde config.json
let config;
try {
  const configFile = fs.readFileSync("config.json", "utf8");
  const configData = JSON.parse(configFile);
  
  config = {
    audio: {
      sampleRate: configData.audio.sampleRate || 16000
    },
    features: {
      bufferSize: configData.features.bufferSize || 512,
      hopSize: configData.features.hopLength || 256, // Nota: hopLength en config.json, hopSize en JS
      mfccCoefficients: configData.features.mfccCoefficients || 13
    },
    datasetPath: "./dataset"
  };
  
  console.log("Configuración cargada desde config.json:");
  console.log(`  Sample rate: ${config.audio.sampleRate}`);
  console.log(`  Buffer size: ${config.features.bufferSize}`);
  console.log(`  Hop size: ${config.features.hopSize}`);
  console.log(`  MFCC coefficients: ${config.features.mfccCoefficients}`);
} catch (error) {
  console.error("Error cargando config.json, usando valores por defecto:", error.message);
  
  // Valores por defecto
  config = {
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
}

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