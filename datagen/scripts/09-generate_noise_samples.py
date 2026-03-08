#!/usr/bin/env python3
"""
Script para generar muestras de ruido a partir del dataset.
Extrae segmentos de silencio y segmentos vocales con ruido agregado
para crear un conjunto de muestras de ruido para entrenamiento.
"""

import os
import sys
import random
import argparse
from pathlib import Path
import numpy as np

try:
    import soundfile as sf
except ImportError:
    print("ERROR: soundfile no está instalado.")
    print("Instalar con: pip install soundfile")
    sys.exit(1)

SAMPLE_RATE = 16000
DURATION = 0.3
CLIP_SAMPLES = int(SAMPLE_RATE * DURATION)
SILENCE_THRESHOLD = 0.015


def rms(signal):
    """Calcula el valor RMS de una señal."""
    return np.sqrt(np.mean(signal ** 2))


def add_noise(signal, noise_level=0.05):
    """Agrega ruido uniforme a una señal."""
    noise = np.random.uniform(-1, 1, len(signal)) * noise_level
    return signal + noise


def process_file(filepath, output_dir, sample_rate, clip_samples, silence_threshold,
                 noise_probability=0.5, noise_level=0.05, max_samples_per_file=1):
    """
    Procesa un archivo de audio para extraer segmentos de ruido.
    
    Args:
        filepath: Ruta al archivo de audio
        output_dir: Directorio de salida
        sample_rate: Tasa de muestreo objetivo
        clip_samples: Muestras por segmento
        silence_threshold: Umbral RMS para silencio
        noise_probability: Probabilidad de guardar segmentos no silenciosos con ruido
        noise_level: Nivel de ruido a agregar
        max_samples_per_file: Máximo de segmentos a guardar por archivo
        
    Returns:
        Número de segmentos guardados
    """
    try:
        audio, sr = sf.read(filepath)
        
        if sr != sample_rate:
            print(f"  ⚠️  Tasa de muestreo diferente ({sr} Hz) en {filepath}, omitiendo")
            return 0
        
        # Convertir a mono si es estéreo
        if len(audio.shape) > 1:
            audio = audio[:, 0]
        
        segments_saved = 0
        
        # Procesar segmentos de 0.3 segundos
        # Asegurar que procesamos al menos un segmento incluso si el audio es exactamente del tamaño del clip
        step = max(1, clip_samples)  # Paso de al menos 1 muestra
        start = 0
        
        while start < len(audio):
            end = min(start + clip_samples, len(audio))
            segment = audio[start:end]
            
            # Si el segmento es más corto que clip_samples, rellenar con ceros
            if len(segment) < clip_samples:
                padding = clip_samples - len(segment)
                segment = np.pad(segment, (0, padding), mode='constant')
            
            energy = rms(segment)
            
            output = None
            
            # Si es silencio, guardar como muestra de ruido
            if energy < silence_threshold:
                output = segment
            
            # Con cierta probabilidad, agregar ruido a segmentos vocales
            elif random.random() < noise_probability:
                output = add_noise(segment, noise_level)
            
            if output is not None:
                # Generar nombre de archivo único
                filename = f"noise_{random.randint(0, 99999999)}.wav"
                outpath = output_dir / filename
                
                # Guardar segmento
                sf.write(str(outpath), output, sample_rate)
                segments_saved += 1
                
                # Limitar segmentos por archivo si se especifica
                if max_samples_per_file and segments_saved >= max_samples_per_file:
                    break
            
            # Avanzar al siguiente segmento
            start += clip_samples
                
        return segments_saved
                
    except Exception as e:
        print(f"  ❌ Error procesando {filepath}: {e}")
        return 0




def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Generar muestras de ruido a partir del dataset')
    parser.add_argument('--input-dir', type=str, default='03s_segments_noisy',
                       help='Directorio con archivos de audio (relativo a datagen/)')
    parser.add_argument('--output-dir', type=str, default='03s_segments_noisy/noise',
                       help='Directorio para muestras de ruido (relativo a datagen/)')
    parser.add_argument('--sample-rate', type=int, default=SAMPLE_RATE,
                       help='Tasa de muestreo objetivo (default: 16000)')
    parser.add_argument('--duration', type=float, default=DURATION,
                       help='Duración de cada segmento en segundos (default: 0.3)')
    parser.add_argument('--silence-threshold', type=float, default=SILENCE_THRESHOLD,
                       help='Umbral RMS para detectar silencio (default: 0.015)')
    parser.add_argument('--noise-level', type=float, default=0.05,
                       help='Nivel de ruido a agregar (default: 0.05)')
    parser.add_argument('--target-samples', type=int, default=6000,
                       help='Número objetivo de muestras a generar (default: 6000)')
    parser.add_argument('--noise-probability', type=float, default=0.6,
                       help='Probabilidad de guardar segmentos no silenciosos con ruido (default: 0.6)')
    parser.add_argument('--max-per-file', type=int, default=1,
                       help='Máximo de segmentos a guardar por archivo (default: 1)')
    parser.add_argument('--test', action='store_true',
                       help='Modo prueba (procesa solo 5 archivos)')
    
    args = parser.parse_args()
    
    # Obtener directorios relativos a datagen/
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent  # datagen/
    
    input_dir = base_dir / args.input_dir
    output_dir = base_dir / args.output_dir
    
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Contar archivos existentes antes de empezar
    existing_noise_files = set()
    if output_dir.exists():
        for f in output_dir.glob("*.wav"):
            existing_noise_files.add(f.name)
    
    clip_samples = int(args.sample_rate * args.duration)
    
    print("=" * 60)
    print("GENERADOR DE MUESTRAS DE RUIDO")
    print("=" * 60)
    print(f"Directorio de entrada: {input_dir}")
    print(f"Directorio de salida: {output_dir}")
    print(f"Duración de segmentos: {args.duration}s ({clip_samples} muestras)")
    print(f"Tasa de muestreo: {args.sample_rate} Hz")
    print(f"Umbral de silencio (RMS): {args.silence_threshold}")
    print(f"Nivel de ruido: {args.noise_level}")
    print(f"Objetivo de muestras: {args.target_samples}")
    print(f"Probabilidad de ruido: {args.noise_probability}")
    print(f"Máximo por archivo: {args.max_per_file}")
    print("=" * 60)
    
    # Encontrar archivos .wav
    audio_files = list(input_dir.rglob("*.wav"))
    
    if not audio_files:
        print(f"❌ No se encontraron archivos .wav en {input_dir}")
        return 1
    
    # Modo prueba: limitar a 5 archivos
    if args.test:
        audio_files = audio_files[:5]
        print(f"⚠️  MODO PRUEBA ACTIVADO ({len(audio_files)} archivos)")
    
    print(f"Archivos .wav encontrados: {len(audio_files)}")
    print(f"Objetivo de muestras: {args.target_samples}")
    print()
    
    total_segments = 0
    processed_files = 0
    files_processed_count = 0
    
    # Mezclar archivos para procesamiento aleatorio
    random.shuffle(audio_files)
    
    # Procesar archivos hasta alcanzar el objetivo o procesar todos
    for i, audio_file in enumerate(audio_files, 1):
        # Saltar directorio de ruido
        if "noise" in str(audio_file.parent).lower():
            continue
        
        # Evitar procesar archivos que estén en el directorio de salida
        try:
            if output_dir in audio_file.parents:
                continue
        except:
            pass
            
        files_processed_count += 1
        
        # Verificar si ya alcanzamos el objetivo
        if total_segments >= args.target_samples:
            print(f"\n✅ Objetivo alcanzado: {total_segments} muestras generadas")
            break
            
        print(f"[{i}/{len(audio_files)}] Procesando: {audio_file.relative_to(base_dir)}")
        
        segments_saved = process_file(
            str(audio_file), output_dir, args.sample_rate, clip_samples,
            args.silence_threshold, args.noise_probability, args.noise_level, args.max_per_file
        )
        
        if segments_saved > 0:
            processed_files += 1
            total_segments += segments_saved
            print(f"     → Guardados {segments_saved} segmentos (Total: {total_segments})")
            
            # Mostrar progreso cada 100 segmentos
            if total_segments % 100 == 0:
                print(f"     Progreso: {total_segments}/{args.target_samples} muestras")
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE GENERACIÓN DE RUIDO")
    print("=" * 60)
    print(f"Archivos procesados: {processed_files}/{files_processed_count}")
    print(f"Archivos totales disponibles: {len(audio_files)}")
    print(f"Segmentos de ruido generados: {total_segments}")
    print(f"Objetivo solicitado: {args.target_samples}")
    print(f"Directorio de salida: {output_dir}")
    
    if total_segments > 0:
        # Encontrar archivos nuevos creados en esta ejecución
        new_noise_files = []
        if output_dir.exists():
            for f in output_dir.glob("*.wav"):
                if f.name not in existing_noise_files:
                    new_noise_files.append(f)
        
        print(f"\nArchivos de ruido existentes previamente: {len(existing_noise_files)}")
        print(f"Nuevas muestras de ruido generadas: {len(new_noise_files)}")
        
        if new_noise_files:
            if len(new_noise_files) <= 10:
                print("Archivos nuevos creados:")
                for i, f in enumerate(new_noise_files, 1):
                    print(f"  {i}. {f.name}")
            else:
                print("Primeros 5 archivos nuevos creados:")
                for i, f in enumerate(new_noise_files[:5], 1):
                    print(f"  {i}. {f.name}")
    
    # Verificar si se alcanzó el objetivo
    if total_segments >= args.target_samples:
        print(f"\n✅ Objetivo alcanzado: {total_segments} muestras generadas")
    else:
        print(f"\n⚠️  Objetivo no alcanzado: {total_segments} de {args.target_samples} muestras")
        print(f"   Considera ajustar --noise-probability o --silence-threshold")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)