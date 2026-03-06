import os
import numpy as np
import librosa
import soundfile as sf
from tqdm import tqdm

INPUT_DIR = "dataset"
OUTPUT_DIR = "dataset_augmented"
SAMPLE_RATE = 16000

def add_noise(y):
    noise = np.random.randn(len(y))
    return y + 0.005 * noise

def pitch_shift(y, sr):
    steps = np.random.uniform(-2, 2)
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=steps)

def time_stretch(y):
    rate = np.random.uniform(0.9, 1.1)
    return librosa.effects.time_stretch(y, rate=rate)

def shift(y):
    shift_range = int(len(y) * 0.1)
    shift_val = np.random.randint(-shift_range, shift_range)
    return np.roll(y, shift_val)

def save_audio(path, y, sr):
    sf.write(path, y, sr)

os.makedirs(OUTPUT_DIR, exist_ok=True)

for label in os.listdir(INPUT_DIR):

    in_path = os.path.join(INPUT_DIR, label)
    out_path = os.path.join(OUTPUT_DIR, label)

    if not os.path.isdir(in_path):
        continue

    os.makedirs(out_path, exist_ok=True)

    files = os.listdir(in_path)

    for file in tqdm(files, desc=f"Processing {label}"):

        filepath = os.path.join(in_path, file)

        y, sr = librosa.load(filepath, sr=SAMPLE_RATE)

        base = os.path.splitext(file)[0]

        # guardar original
        save_audio(f"{out_path}/{base}_orig.wav", y, sr)

        # augmentaciones
        save_audio(f"{out_path}/{base}_noise.wav", add_noise(y), sr)
        save_audio(f"{out_path}/{base}_pitch.wav", pitch_shift(y, sr), sr)
        save_audio(f"{out_path}/{base}_stretch.wav", time_stretch(y), sr)
        save_audio(f"{out_path}/{base}_shift.wav", shift(y), sr)

        # combinaciones
        y2 = pitch_shift(add_noise(y), sr)
        save_audio(f"{out_path}/{base}_noise_pitch.wav", y2, sr)

        y3 = time_stretch(add_noise(y))
        save_audio(f"{out_path}/{base}_noise_stretch.wav", y3, sr)