#!/usr/bin/env python3
"""
Extracción de espectrogramas MEL usando Python (librosa).
Alternativa al script Node.js para entornos donde Node no está disponible.
"""

import os
import json
import numpy as np
import librosa
import librosa.display
import soundfile as sf
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

def load_config():
    """Cargar configuración desde config.json"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config

def get_audio_files():
    """Obtener todos los archivos de audio organizados por etiqueta"""
    dataset_dir = Path('dataset')
    audio_files = []
    
    # Buscar directorios de etiquetas
    for label_dir in dataset_dir.iterdir():
        if label_dir.is_dir():
            label = label_dir.name
            # Buscar archivos .wav en el directorio de etiqueta
            for audio_file in label_dir.glob('*.wav'):
                audio_files.append({
                    'path': str(audio_file),
                    'label': label,
                    'filename': audio_file.name
                })
    
    return audio_files

def extract_mfcc(audio_path, config):
    """Extraer espectrograma MEL de un archivo de audio"""
    
    # Cargar audio
    try:
        audio, sr = sf.read(audio_path)
    except:
        # Fallback a librosa si soundfile falla
        audio, sr = librosa.load(audio_path, sr=config['audio']['sampleRate'])
    
    # Asegurar mono
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    
    # Extraer espectrograma MEL (en lugar de MFCC)
    mel_spectrogram = librosa.feature.melspectrogram(
        y=audio,
        sr=sr,
        n_mels=config['features']['melBands'],
        n_fft=config['features']['bufferSize'],
        hop_length=config['features']['hopLength'],
        window='hann'
    )
    
    # Convertir a dB (log-mel)
    mel_spectrogram_db = librosa.power_to_db(mel_spectrogram, ref=np.max)
    
    # Retornar el espectrograma 2D sin aplanar
    return mel_spectrogram_db.tolist(), sr

def extract_all_features(config):
    """Extraer características de todos los archivos de audio"""
    
    print("Buscando archivos de audio...")
    audio_files = get_audio_files()
    
    if not audio_files:
        print("No se encontraron archivos de audio en dataset/")
        print("Por favor grabe audio primero.")
        return None
    
    print(f"Encontrados {len(audio_files)} archivos de audio")
    
    # Contar por etiqueta
    label_counts = {}
    for file in audio_files:
        label_counts[file['label']] = label_counts.get(file['label'], 0) + 1
    
    print("Archivos por etiqueta:")
    for label, count in label_counts.items():
        print(f"  {label}: {count} archivos")
    
    # Mapear etiquetas a índices
    labels_config = config['labels']
    label_to_index = {label: idx for idx, label in enumerate(labels_config)}
    
    # Extraer características
    features = []
    labels = []
    file_paths = []
    failed_files = []
    
    print("\nExtrayendo espectrogramas MEL...")
    
    for file_info in tqdm(audio_files, desc="Procesando audio"):
        try:
            # Extraer características
            file_features, sr = extract_mfcc(file_info['path'], config)
            
            # Obtener índice de etiqueta
            label = file_info['label']
            if label in label_to_index:
                label_idx = label_to_index[label]
            else:
                print(f"Advertencia: Etiqueta '{label}' no está en config.json, usando índice -1")
                label_idx = -1
            
            features.append(file_features)
            labels.append(label_idx)
            file_paths.append(file_info['path'])
            
        except Exception as e:
            print(f"Error procesando {file_info['path']}: {str(e)}")
            failed_files.append(file_info['path'])
    
    print(f"\nExtracción completada:")
    print(f"  ✓ Archivos procesados: {len(features)}")
    print(f"  ✗ Archivos fallados: {len(failed_files)}")
    
    if failed_files:
        print("\nArchivos con error:")
        for f in failed_files:
            print(f"  - {f}")
    
    # Guardar resultados
    result = {
        'features': features,
        'labels': labels,
        'labelNames': labels_config,
        'filePaths': file_paths,
        'config': {
            'audio': config['audio'],
            'features': config['features']
        },
        'extractionDate': np.datetime64('now').astype(str),
        'numSamples': len(features)
    }
    
    return result

def save_features(feature_data, output_path='dataset/features_python.json'):
    """Guardar características extraídas"""
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Guardar como JSON
    with open(output_path, 'w') as f:
        json.dump(feature_data, f, indent=2)
    
    print(f"\nCaracterísticas guardadas en: {output_path}")
    
    # También guardar en formato binario para carga rápida
    np.savez_compressed(
        'dataset/features_python.npz',
        features=np.array(feature_data['features'], dtype=np.float32),
        labels=np.array(feature_data['labels'], dtype=np.int32),
        label_names=feature_data['labelNames']
    )
    
    print(f"Características binarias guardadas en: dataset/features_python.npz")
    
    # Estadísticas
    features_array = np.array(feature_data['features'])
    print(f"\nEstadísticas de características:")
    print(f"  Forma: {features_array.shape}")
    print(f"  Media: {features_array.mean():.4f}")
    print(f"  Desviación estándar: {features_array.std():.4f}")
    print(f"  Mínimo: {features_array.min():.4f}")
    print(f"  Máximo: {features_array.max():.4f}")

def main():
    """Función principal"""
    
    print("=" * 60)
    print("EXTRACCIÓN DE ESPECTROGRAMAS MEL CON PYTHON")
    print("=" * 60)
    
    # Cargar configuración
    config = load_config()
    print(f"\nConfiguración cargada:")
    print(f"  Tasa de muestreo: {config['audio']['sampleRate']} Hz")
    print(f"  Bandas MEL: {config['features']['melBands']}")
    print(f"  Etiquetas: {', '.join(config['labels'])}")
    
    # Extraer características
    feature_data = extract_all_features(config)
    
    if feature_data is None:
        print("No se pudieron extraer características.")
        return
    
    # Guardar características
    save_features(feature_data)
    
    print("\n" + "=" * 60)
    print("EXTRACCIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print("\nSiguientes pasos:")
    print("1. Entrenar modelo: python3 train_tensorflow_gpu.py")
    print("2. O usar pipeline Docker: docker-compose up pipeline-gpu")

if __name__ == '__main__':
    main()