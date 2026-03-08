#!/usr/bin/env python3
"""
Script para agregar ruido a los segmentos de audio de 0.3 segundos.
Agrega ruido blanco controlado a los archivos en datagen/03s_segments/ para
mejorar la robustez del modelo a condiciones reales.
"""

import os
import sys
from pathlib import Path
import numpy as np
import random

try:
    import soundfile as sf
except ImportError:
    print("ERROR: soundfile no está instalado.")
    print("Instalar con: pip install soundfile")
    sys.exit(1)

def add_white_noise(audio_data, snr_db=20):
    """
    Agrega ruido blanco a una señal de audio con un SNR específico.
    
    Args:
        audio_data: Array de numpy con datos de audio
        snr_db: Relación señal-ruido en dB (mayor = menos ruido)
        
    Returns:
        Audio con ruido agregado
    """
    # Calcular potencia de la señal
    signal_power = np.mean(audio_data ** 2)
    
    # Calcular potencia de ruido basada en SNR
    noise_power = signal_power / (10 ** (snr_db / 10))
    
    # Generar ruido blanco gaussiano
    noise = np.random.normal(0, np.sqrt(noise_power), len(audio_data))
    
    # Agregar ruido a la señal
    noisy_signal = audio_data + noise
    
    # Asegurar que no haya clipping
    max_val = np.max(np.abs(noisy_signal))
    if max_val > 1.0:
        noisy_signal = noisy_signal / max_val
    
    return noisy_signal

def add_background_noise(audio_data, noise_data, snr_db=15):
    """
    Agrega ruido de fondo (de un archivo de ruido) a una señal de audio.
    
    Args:
        audio_data: Array de numpy con datos de audio
        noise_data: Array de numpy con datos de ruido
        snr_db: Relación señal-ruido en dB
        
    Returns:
        Audio con ruido de fondo agregado
    """
    # Asegurar que el ruido tenga la misma longitud que el audio
    if len(noise_data) < len(audio_data):
        # Repetir ruido si es más corto
        repeats = int(np.ceil(len(audio_data) / len(noise_data)))
        noise_data = np.tile(noise_data, repeats)
    
    # Recortar ruido a la longitud del audio
    noise_data = noise_data[:len(audio_data)]
    
    # Calcular potencias
    signal_power = np.mean(audio_data ** 2)
    noise_power = np.mean(noise_data ** 2)
    
    # Ajustar potencia del ruido al SNR deseado
    target_noise_power = signal_power / (10 ** (snr_db / 10))
    scaling_factor = np.sqrt(target_noise_power / (noise_power + 1e-10))
    noise_data = noise_data * scaling_factor
    
    # Agregar ruido
    noisy_signal = audio_data + noise_data
    
    # Asegurar que no haya clipping
    max_val = np.max(np.abs(noisy_signal))
    if max_val > 1.0:
        noisy_signal = noisy_signal / max_val
    
    return noisy_signal

def get_random_snr():
    """
    Selecciona aleatoriamente un nivel de SNR basado en las probabilidades:
    - 40%: audio limpio (sin ruido, representado como None)
    - 20%: 30 dB SNR
    - 15%: 25 dB SNR
    - 15%: 20 dB SNR
    - 10%: 15 dB SNR
    
    Returns:
        SNR en dB o None para audio limpio
    """
    rand = random.random()  # 0.0 a 1.0
    
    if rand < 0.40:  # 40% audio limpio
        return None
    elif rand < 0.60:  # 20% 30 dB (40% a 60%)
        return 30
    elif rand < 0.75:  # 15% 25 dB (60% a 75%)
        return 25
    elif rand < 0.90:  # 15% 20 dB (75% a 90%)
        return 20
    else:  # 10% 15 dB (90% a 100%)
        return 15

def load_noise_samples(noise_dir, sample_rate=16000):
    """
    Carga muestras de ruido desde un directorio.
    
    Args:
        noise_dir: Directorio con archivos de ruido
        sample_rate: Tasa de muestreo objetivo
        
    Returns:
        Lista de arrays de ruido
    """
    noise_samples = []
    noise_dir = Path(noise_dir)
    
    if not noise_dir.exists():
        print(f"Directorio de ruido no encontrado: {noise_dir}")
        return noise_samples
    
    # Buscar archivos de audio
    audio_extensions = ['.wav', '.flac', '.mp3', '.ogg']
    for ext in audio_extensions:
        for audio_file in noise_dir.glob(f'*{ext}'):
            try:
                audio, sr = sf.read(audio_file)
                # Convertir a mono si es necesario
                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)
                # Resamplear si es necesario
                if sr != sample_rate:
                    # Resampleo simple (para implementación básica)
                    # En producción usaría librosa.resample
                    import warnings
                    warnings.warn(f"Resampleo de {sr}Hz a {sample_rate}Hz no implementado completamente")
                noise_samples.append(audio)
                print(f"  Cargado: {audio_file.name} ({len(audio)/sr:.2f}s)")
            except Exception as e:
                print(f"  Error cargando {audio_file}: {e}")
    
    return noise_samples

def process_directory(input_dir, output_dir, use_background_noise=False, noise_samples=None):
    """
    Procesa todos los archivos de audio en un directorio, agregando ruido aleatorio.
    
    Args:
        input_dir: Directorio de entrada con archivos de audio
        output_dir: Directorio de salida para archivos con ruido
        use_background_noise: Si True, usa ruido de fondo; si False, usa ruido blanco
        noise_samples: Lista de muestras de ruido para ruido de fondo
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    if not input_dir.exists():
        print(f"Directorio de entrada no encontrado: {input_dir}")
        return 0
    
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Buscar archivos de audio
    audio_files = []
    audio_extensions = ['.wav', '.flac', '.mp3', '.ogg']
    for ext in audio_extensions:
        audio_files.extend(list(input_dir.glob(f'*{ext}')))
    
    if not audio_files:
        print(f"  No se encontraron archivos de audio en {input_dir}")
        return 0
    
    print(f"  Encontrados {len(audio_files)} archivos")
    
    # Intentar usar tqdm para barra de progreso
    try:
        from tqdm import tqdm
        use_tqdm = True
    except ImportError:
        use_tqdm = False
    
    # Contadores para estadísticas
    processed_count = 0
    clean_count = 0
    noise_counts = {30: 0, 25: 0, 20: 0, 15: 0}
    errors = []
    
    # Crear iterador con o sin barra de progreso
    iterator = tqdm(audio_files, desc="  Procesando") if use_tqdm else audio_files
    
    for audio_file in iterator:
        try:
            # Cargar audio
            audio, sr = sf.read(audio_file)
            
            # Convertir a mono si es necesario
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Obtener SNR aleatorio según probabilidades
            snr_db = get_random_snr()
            
            if snr_db is None:
                # Audio limpio (40% de probabilidad)
                noisy_audio = audio
                clean_count += 1
            else:
                # Agregar ruido con el SNR seleccionado
                if use_background_noise and noise_samples:
                    # Seleccionar muestra de ruido aleatoria
                    noise_sample = random.choice(noise_samples)
                    noisy_audio = add_background_noise(audio, noise_sample, snr_db)
                else:
                    # Usar ruido blanco
                    noisy_audio = add_white_noise(audio, snr_db)
                
                # Contar este nivel de SNR
                noise_counts[snr_db] = noise_counts.get(snr_db, 0) + 1
            
            # Guardar archivo
            output_file = output_dir / audio_file.name
            sf.write(output_file, noisy_audio, sr)
            
            processed_count += 1
                
        except Exception as e:
            errors.append(str(audio_file))
            if not use_tqdm:
                print(f"  Error procesando {audio_file.name}: {e}")
    
    # Mostrar estadísticas
    print(f"  Estadísticas de ruido:")
    print(f"    Audio limpio: {clean_count} ({clean_count/processed_count*100:.1f}%)")
    for snr in [30, 25, 20, 15]:
        count = noise_counts.get(snr, 0)
        if count > 0:
            print(f"    SNR {snr} dB: {count} ({count/processed_count*100:.1f}%)")
    
    if errors:
        print(f"  Errores en {len(errors)} archivos")
        if len(errors) <= 10:  # Mostrar solo primeros 10 errores
            for err in errors[:10]:
                print(f"    - {err}")
    
    return processed_count

def process_noise_directory(input_dir, output_dir):
    """
    Procesa archivos de ruido con una distribución diferente:
    - 50% limpio (sin ruido adicional)
    - 50% con ruido blanco adicional (SNR 10-20 dB aleatorio)
    
    Args:
        input_dir: Directorio de entrada con archivos de ruido
        output_dir: Directorio de salida para archivos procesados
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    if not input_dir.exists():
        print(f"Directorio de entrada no encontrado: {input_dir}")
        return 0
    
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Buscar archivos de audio
    audio_files = []
    audio_extensions = ['.wav', '.flac', '.mp3', '.ogg']
    for ext in audio_extensions:
        audio_files.extend(list(input_dir.glob(f'*{ext}')))
    
    if not audio_files:
        print(f"  No se encontraron archivos de audio en {input_dir}")
        return 0
    
    print(f"  Encontrados {len(audio_files)} archivos")
    
    # Intentar usar tqdm para barra de progreso
    try:
        from tqdm import tqdm
        use_tqdm = True
    except ImportError:
        use_tqdm = False
    
    # Contadores para estadísticas
    processed_count = 0
    clean_count = 0
    noisy_count = 0
    errors = []
    
    # Crear iterador con o sin barra de progreso
    iterator = tqdm(audio_files, desc="  Procesando") if use_tqdm else audio_files
    
    for audio_file in iterator:
        try:
            # Cargar audio
            audio, sr = sf.read(audio_file)
            
            # Convertir a mono si es necesario
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Decidir si agregar ruido (50% probabilidad)
            if random.random() < 0.5:
                # Audio limpio (sin ruido adicional)
                processed_audio = audio
                clean_count += 1
            else:
                # Agregar ruido blanco con SNR aleatorio entre 10 y 20 dB
                snr_db = random.uniform(10, 20)
                processed_audio = add_white_noise(audio, snr_db)
                noisy_count += 1
            
            # Guardar archivo
            output_file = output_dir / audio_file.name
            sf.write(output_file, processed_audio, sr)
            
            processed_count += 1
                
        except Exception as e:
            errors.append(str(audio_file))
            if not use_tqdm:
                print(f"  Error procesando {audio_file.name}: {e}")
    
    # Mostrar estadísticas
    print(f"  Estadísticas:")
    print(f"    Ruido limpio: {clean_count} ({clean_count/processed_count*100:.1f}%)")
    print(f"    Ruido con ruido adicional: {noisy_count} ({noisy_count/processed_count*100:.1f}%)")
    
    if errors:
        print(f"  Errores en {len(errors)} archivos")
        if len(errors) <= 10:  # Mostrar solo primeros 10 errores
            for err in errors[:10]:
                print(f"    - {err}")
    
    return processed_count

def main():
    """Función principal"""
    print("=" * 60)
    print("AGREGAR RUIDO A SEGMENTOS DE AUDIO (ALEATORIO)")
    print("=" * 60)
    print("\nDistribución de niveles de ruido:")
    print("  40% - Audio limpio (sin ruido)")
    print("  20% - SNR 30 dB (ruido muy bajo)")
    print("  15% - SNR 25 dB (ruido bajo)")
    print("  15% - SNR 20 dB (ruido moderado)")
    print("  10% - SNR 15 dB (ruido alto)")
    
    # Configuración - rutas relativas al directorio actual
    input_segments_dir = Path("datagen/03s_segments")
    output_dir = Path("datagen/03s_segments_noisy")
    noise_dir = Path("datagen/03s_segments/noise")
    
    # Parámetros de ruido
    use_background_noise = True  # Usar ruido de fondo en lugar de ruido blanco
    
    print(f"\nConfiguración:")
    print(f"  Directorio de entrada: {input_segments_dir}")
    print(f"  Directorio de salida: {output_dir}")
    print(f"  Tipo de ruido: {'background' if use_background_noise else 'white'}")
    
    # Cargar muestras de ruido si se usa ruido de fondo
    noise_samples = []
    if use_background_noise:
        print(f"\nCargando muestras de ruido de: {noise_dir}")
        noise_samples = load_noise_samples(noise_dir)
        if not noise_samples:
            print("  No se encontraron muestras de ruido, usando ruido blanco")
            use_background_noise = False
    
    # Procesar cada directorio de etiqueta (excluyendo 'noise')
    total_processed = 0
    labels = ["A", "E", "I", "O", "U"]
    
    for label in labels:
        input_label_dir = input_segments_dir / label
        output_label_dir = output_dir / label
        
        if not input_label_dir.exists():
            print(f"\nDirectorio no encontrado: {input_label_dir}")
            continue
        
        print(f"\nProcesando etiqueta: {label}")
        print(f"  Entrada: {input_label_dir}")
        print(f"  Salida: {output_label_dir}")
        
        processed = process_directory(
            input_label_dir,
            output_label_dir,
            use_background_noise,
            noise_samples
        )
        
        total_processed += processed
        print(f"  Archivos procesados: {processed}")
    
    # También procesar el directorio 'noise' si existe (para aumentar variabilidad)
    # Para archivos de ruido, siempre agregamos ruido blanco con SNR bajo
    noise_input_dir = input_segments_dir / "noise"
    noise_output_dir = output_dir / "noise"
    
    if noise_input_dir.exists():
        print(f"\nProcesando ruido (para aumentar variabilidad):")
        # Para archivos de ruido, usamos una distribución diferente
        # 50% limpio, 50% con ruido adicional (SNR 10-20 dB)
        processed = process_noise_directory(noise_input_dir, noise_output_dir)
        total_processed += processed
        print(f"  Archivos de ruido procesados: {processed}")
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)
    print(f"Total de archivos procesados: {total_processed}")
    print(f"Archivos con ruido aleatorio guardados en: {output_dir}")
    print("\nSiguientes pasos:")
    print("1. Los archivos con ruido aleatorio están listos para ser usados en entrenamiento")
    print("2. Puedes mezclar estos con los originales para aumentar el dataset")
    print("3. Para usar en el pipeline, copia o mueve los archivos según sea necesario")

if __name__ == "__main__":
    main()