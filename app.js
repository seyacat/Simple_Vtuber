// DOM Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusEl = document.getElementById('status');
const canvas = document.getElementById('waveformCanvas');
const canvasOverlay = document.getElementById('canvasOverlay');
const volumeLevelEl = document.getElementById('volumeLevel');
const frequencyValueEl = document.getElementById('frequencyValue');
const sampleRateEl = document.getElementById('sampleRate');
const bufferSizeEl = document.getElementById('bufferSize');
const audioInputSelect = document.getElementById('audioInput');

// Audio context and variables
let audioContext;
let analyser;
let source;
let dataArray;
let animationId;
let isRecording = false;

// Canvas setup
const ctx = canvas.getContext('2d');
let canvasWidth, canvasHeight;

function resizeCanvas() {
    canvasWidth = canvas.clientWidth;
    canvasHeight = canvas.clientHeight;
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
}

// Initialize canvas size
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

// Update status display
function updateStatus(active, message) {
    if (active) {
        statusEl.textContent = message || 'Microphone is active. Speak to see the waveform.';
        statusEl.className = 'status status-active';
        canvasOverlay.style.display = 'none';
    } else {
        statusEl.textContent = message || 'Microphone is not active.';
        statusEl.className = 'status status-inactive';
        canvasOverlay.style.display = 'flex';
    }
}

// Draw waveform on canvas
function drawWaveform() {
    if (!analyser || !dataArray) return;

    // Get time domain data
    analyser.getByteTimeDomainData(dataArray);

    // Clear canvas
    ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Draw grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    
    // Horizontal grid lines
    for (let i = 0; i <= 5; i++) {
        const y = (canvasHeight / 5) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvasWidth, y);
        ctx.stroke();
    }

    // Draw waveform
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#00dbde';
    ctx.beginPath();

    const sliceWidth = canvasWidth / dataArray.length;
    let x = 0;

    for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * canvasHeight / 2;

        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }

        x += sliceWidth;
    }

    ctx.lineTo(canvasWidth, canvasHeight / 2);
    ctx.stroke();

    // Calculate and display volume
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
        const value = (dataArray[i] - 128) / 128;
        sum += value * value;
    }
    
    const rms = Math.sqrt(sum / dataArray.length);
    const db = 20 * Math.log10(rms);
    const volumePercent = Math.min(100, Math.max(0, (db + 60) * (100/60)));
    
    // Update volume display
    volumeLevelEl.textContent = db.toFixed(1) + ' dB';
    
    // Draw volume bar
    const barWidth = canvasWidth * (volumePercent / 100);
    ctx.fillStyle = 'rgba(0, 219, 222, 0.3)';
    ctx.fillRect(0, canvasHeight - 10, barWidth, 8);

    // Draw center line
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, canvasHeight / 2);
    ctx.lineTo(canvasWidth, canvasHeight / 2);
    ctx.stroke();

    // Continue animation
    animationId = requestAnimationFrame(drawWaveform);
}

// Get and list available audio devices
async function getAudioDevices() {
    try {
        // First get permission to access devices
        const tempStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Stop the temporary stream
        tempStream.getTracks().forEach(track => track.stop());
        
        // Get all devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        
        // Filter audio input devices
        const audioInputs = devices.filter(device => device.kind === 'audioinput');
        
        // Clear existing options
        audioInputSelect.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = 'default';
        defaultOption.textContent = 'Default Microphone';
        audioInputSelect.appendChild(defaultOption);
        
        // Add each audio input device
        audioInputs.forEach(device => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.textContent = device.label || `Microphone ${audioInputSelect.options.length}`;
            audioInputSelect.appendChild(option);
        });
        
        // Try to restore last selected device
        const lastDeviceId = localStorage.getItem('lastAudioDeviceId');
        if (lastDeviceId) {
            // Check if the device still exists
            const deviceExists = audioInputs.some(device => device.deviceId === lastDeviceId);
            if (deviceExists) {
                audioInputSelect.value = lastDeviceId;
            }
        }
        
        return audioInputs;
    } catch (error) {
        console.error('Error getting audio devices:', error);
        return [];
    }
}

// Start microphone capture with selected device
async function startMicrophone() {
    try {
        const selectedDeviceId = audioInputSelect.value;
        
        // Build constraints based on selection
        const constraints = {
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        };
        
        // If a specific device is selected (not "default"), add deviceId constraint
        if (selectedDeviceId && selectedDeviceId !== 'default') {
            constraints.audio.deviceId = { exact: selectedDeviceId };
        }
        
        // Request microphone access with constraints
        const stream = await navigator.mediaDevices.getUserMedia(constraints);

        // Create audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        source = audioContext.createMediaStreamSource(stream);

        // Connect nodes
        source.connect(analyser);
        
        // Configure analyser
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.8;
        const bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);

        // Update info displays
        sampleRateEl.textContent = audioContext.sampleRate.toLocaleString() + ' Hz';
        bufferSizeEl.textContent = bufferLength;

        // Update UI
        isRecording = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;
        updateStatus(true, 'Microphone active. Speak to see the waveform.');

        // Start visualization
        drawWaveform();

        // Calculate and display dominant frequency
        function updateFrequency() {
            if (!analyser || !dataArray) return;
            
            analyser.getByteFrequencyData(dataArray);
            
            // Find dominant frequency
            let maxIndex = 0;
            let maxValue = 0;
            
            for (let i = 0; i < dataArray.length; i++) {
                if (dataArray[i] > maxValue) {
                    maxValue = dataArray[i];
                    maxIndex = i;
                }
            }
            
            // Calculate frequency
            const nyquist = audioContext.sampleRate / 2;
            const frequency = (maxIndex / dataArray.length) * nyquist;
            
            if (frequency > 20) { // Ignore very low frequencies
                frequencyValueEl.textContent = frequency.toFixed(0) + ' Hz';
            }
            
            if (isRecording) {
                setTimeout(updateFrequency, 200);
            }
        }
        
        updateFrequency();

    } catch (error) {
        console.error('Error accessing microphone:', error);
        updateStatus(false, 'Error accessing microphone: ' + error.message + '. Click "Start Microphone" to try again.');
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

// Stop microphone capture
function stopMicrophone() {
    if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
    }

    if (source) {
        source.disconnect();
        source = null;
    }

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    // Update UI
    isRecording = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    updateStatus(false, 'Microphone stopped.');

    // Clear canvas
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);
    
    // Reset displays
    volumeLevelEl.textContent = '0 dB';
    frequencyValueEl.textContent = '0 Hz';
}

// Event listeners for manual control
startBtn.addEventListener('click', () => {
    if (!isRecording) {
        startMicrophone();
    }
});

stopBtn.addEventListener('click', stopMicrophone);

// Handle page visibility change - just update status but don't stop recording
document.addEventListener('visibilitychange', () => {
    if (document.hidden && isRecording) {
        updateStatus(true, 'Microphone active (tab in background). Speak to see the waveform.');
    } else if (isRecording) {
        updateStatus(true, 'Microphone active. Speak to see the waveform.');
    }
});

// Initial canvas draw
ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
ctx.fillRect(0, 0, canvasWidth, canvasHeight);
ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
ctx.font = '18px Arial';
ctx.textAlign = 'center';
ctx.fillText('Starting microphone...', canvasWidth / 2, canvasHeight / 2);

// Browser compatibility check and initialization
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    updateStatus(false, 'Your browser does not support microphone access. Please use Chrome, Firefox, Edge, or Safari.');
    startBtn.disabled = true;
    audioInputSelect.disabled = true;
} else {
    // Update status
    updateStatus(false, 'Loading audio devices...');
    
    // Get and list audio devices
    getAudioDevices().then(devices => {
        if (devices.length > 0) {
            updateStatus(false, 'Starting microphone automatically...');
            startBtn.disabled = false;
            
            // Start microphone automatically after a short delay
            setTimeout(() => {
                if (!isRecording) {
                    startMicrophone();
                }
            }, 1000);
        } else {
            updateStatus(false, 'No audio input devices found. Please connect a microphone.');
            startBtn.disabled = true;
        }
    }).catch(error => {
        console.error('Error initializing audio devices:', error);
        updateStatus(false, 'Error loading audio devices. Click "Start Microphone" to try again.');
        startBtn.disabled = false;
    });
    
    // Listen for device changes
    navigator.mediaDevices.addEventListener('devicechange', async () => {
        await getAudioDevices();
    });
}

// Save selected device when user changes selection
audioInputSelect.addEventListener('change', () => {
    const selectedDeviceId = audioInputSelect.value;
    if (selectedDeviceId) {
        localStorage.setItem('lastAudioDeviceId', selectedDeviceId);
    }
});

// Update start button to refresh device list on click if no devices are listed
startBtn.addEventListener('click', async () => {
    if (!isRecording) {
        // If no devices are listed, try to refresh the list
        if (audioInputSelect.options.length <= 1) {
            updateStatus(false, 'Refreshing device list...');
            await getAudioDevices();
        }
        
        // Save the selected device before starting
        const selectedDeviceId = audioInputSelect.value;
        if (selectedDeviceId) {
            localStorage.setItem('lastAudioDeviceId', selectedDeviceId);
        }
        
        startMicrophone();
    }
});