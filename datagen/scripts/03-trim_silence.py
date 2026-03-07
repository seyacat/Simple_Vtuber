#!/usr/bin/env python3
"""
Script para recortar silencios de archivos de audio generados por TTS.
Analiza el espectro para encontrar donde comienza y termina el sonido real.
"""

import os
import sys
from pathlib import Path
import numpy as np

try:
    import soundfile as sf
    import librosa
except ImportError:
    print("ERROR: soundfile o librosa no están instalados.")
    print("Instalar con: pip install soundfile librosa")
    sys.exit(1)

def trim_silence(audio_data, sample_rate, threshold_db=-40, min_silence_duration=0.05):
    """
    Recorta silencios del inicio y final del audio.
    
    Args:
        audio_data: Array de numpy con datos de audio
        sample_rate: Tasa de muestreo
        threshold_db: Umbral en dB para considerar silencio (default: -40 dB)
        min_silence_duration: Duración mínima de silencio para recortar (segundos)
        
    Returns:
        Audio recortado
    """
    if len(audio_data) == 0:
        return audio_data
    
    # Convertir a mono si es estéreo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Calcular energía (RMS) en ventanas
    frame_length = int(sample_rate * 0.01)  # 10ms
    hop_length = frame_length // 2
    
    # Calcular RMS
    rms = librosa.feature.rms(
        y=audio_data,
        frame_length=frame_length,
        hop_length=hop_length
    )[0]
    
    # Convertir RMS a dB
    rms_db = 20 * np.log10(rms + 1e-10)  # Evitar log(0)
    
    # Encontrar índices donde la energía está por encima del umbral
    above_threshold = rms_db > threshold_db
    
    if not np.any(above_threshold):
        # No hay audio por encima del umbral, devolver todo
        return audio_data
    
    # Encontrar primer y último índice con audio
    audio_indices = np.where(above_threshold)[0]
    first_audio_idx = audio_indices[0]
    last_audio_idx = audio_indices[-1]
    
    # Convertir índices de frames a muestras
    start_sample = first_audio_idx * hop_length
    end_sample = min((last_audio_idx + 1) * hop_length, len(audio_data))
    
    # Aplicar margen de seguridad (agregar un poco antes y después)
    margin_samples = int(sample_rate * 0.02)  # 20ms de margen
    start_sample = max(0, start_sample - margin_samples)
    end_sample = min(len(audio_data), end_sample + margin_samples)
    
    # Recortar audio
    trimmed_audio = audio_data[start_sample:end_sample]
    
    return trimmed_audio

def process_audio_file(input_path, output_path, threshold_db=-40):
    """
    Procesa un archivo de audio: recorta silencios y guarda resultado.
    
    Args:
        input_path: Ruta al archivo de entrada
        output_path: Ruta al archivo de salida
        threshold_db: Umbral en dB para silencio
        
    Returns:
        Tupla (duración_original, duración_recortada, éxito)
    """
    try:
        # Cargar audio
        audio_data, sample_rate = sf.read(str(input_path))
        
        # Calcular duración original
        original_duration = len(audio_data) / sample_rate
        
        # Recortar silencios
        trimmed_audio = trim_silence(audio_data, sample_rate, threshold_db)
        
        # Calcular duración recortada
        trimmed_duration = len(trimmed_audio) / sample_rate
        
        # Guardar audio recortado
        sf.write(str(output_path), trimmed_audio, sample_rate, subtype='PCM_16')
        
        return original_duration, trimmed_duration, True
        
    except Exception as e:
        print(f"  ❌ Error procesando {input_path.name}: {e}")
        return 0, 0, False

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Recortar silencios de archivos de audio')
    parser.add_argument('--input-dir', type=str, default='raw_audio_edge',
                       help='Directorio con archivos de audio de entrada (relativo a datagen/)')
    parser.add_argument('--output-dir', type=str, default='trimmed_audio',
                       help='Directorio para archivos recortados (relativo a datagen/)')
    parser.add_argument('--threshold', type=float, default=-40,
                       help='Umbral en dB para considerar silencio (default: -40)')
    parser.add_argument('--test', action='store_true',
                       help='Modo prueba (procesa solo 5 archivos)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("RECORTADOR DE SILENCIOS DE AUDIO")
    print("=" * 60)
    
    # Obtener directorio base (datagen/) relativo al script
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent  # datagen/
    
    # Configurar directorios relativos a datagen/
    input_dir = base_dir / args.input_dir
    output_dir = base_dir / args.output_dir
    
    if not input_dir.exists():
        print(f"❌ Directorio de entrada no existe: {input_dir}")
        return 1
    
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Encontrar archivos de audio
    audio_files = list(input_dir.glob("*.wav"))
    
    if not audio_files:
        print(f"❌ No se encontraron archivos .wav en {input_dir}")
        return 1
    
    print(f"Archivos encontrados: {len(audio_files)}")
    print(f"Directorio de entrada: {input_dir}")
    print(f"Directorio de salida: {output_dir}")
    print(f"Umbral de silencio: {args.threshold} dB")
    
    if args.test:
        audio_files = audio_files[:5]
        print(f"⚠️  MODO PRUEBA: Procesando solo {len(audio_files)} archivos")
    
    print("\n" + "-" * 60)
    
    # Procesar archivos
    total_original = 0
    total_trimmed = 0
    successful = 0
    
    for i, input_file in enumerate(audio_files, 1):
        # Crear nombre de archivo de salida
        output_file = output_dir / input_file.name
        
        print(f"[{i}/{len(audio_files)}] Procesando: {input_file.name}")
        
        # Procesar archivo
        orig_dur, trim_dur, success = process_audio_file(
            input_file, output_file, args.threshold
        )
        
        if success:
            reduction = ((orig_dur - trim_dur) / orig_dur) * 100 if orig_dur > 0 else 0
            print(f"  ✅ Recortado: {orig_dur:.3f}s → {trim_dur:.3f}s (-{reduction:.1f}%)")
            
            total_original += orig_dur
            total_trimmed += trim_dur
            successful += 1
        else:
            print(f"  ❌ Error procesando archivo")
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    print(f"Archivos procesados: {successful}/{len(audio_files)}")
    
    if successful > 0:
        avg_original = total_original / successful
        avg_trimmed = total_trimmed / successful
        total_reduction = ((total_original - total_trimmed) / total_original) * 100
        
        print(f"\nDuración total original: {total_original:.3f}s")
        print(f"Duración total recortada: {total_trimmed:.3f}s")
        print(f"Reducción total: {total_reduction:.1f}%")
        print(f"\nDuración promedio original: {avg_original:.3f}s")
        print(f"Duración promedio recortada: {avg_trimmed:.3f}s")
        
        # Mostrar algunos ejemplos
        print(f"\nEjemplos de archivos recortados:")
        trimmed_files = list(output_dir.glob("*.wav"))[:3]
        for file in trimmed_files:
            try:
                data, sr = sf.read(str(file))
                duration = len(data) / sr
                print(f"  {file.name}: {duration:.3f}s")
            except:
                pass
    
    print(f"\n✅ Archivos recortados guardados en: {output_dir}")
    
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