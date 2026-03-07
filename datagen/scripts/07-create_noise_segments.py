#!/usr/bin/env python3
"""
Script para crear segmentos de ruido de 0.3 segundos a partir de archivos de ruido.
Toma archivos de audio de datagen/noise, los divide en segmentos de 0.3s,
y los guarda en 03s_segments/noise/.
"""

import os
import sys
from pathlib import Path
import numpy as np

try:
    import soundfile as sf
except ImportError:
    print("ERROR: soundfile no está instalado.")
    print("Instalar con: pip install soundfile")
    sys.exit(1)

def split_audio_into_segments(audio_data, sample_rate, segment_duration=0.3, overlap=0.0):
    """
    Divide un archivo de audio en segmentos de duración fija.
    
    Args:
        audio_data: Array de numpy con datos de audio
        sample_rate: Tasa de muestreo
        segment_duration: Duración de cada segmento en segundos
        overlap: Solapamiento entre segmentos (0.0 = sin solapamiento)
        
    Returns:
        Lista de segmentos de audio
    """
    # Convertir a mono si es estéreo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Calcular muestras por segmento
    samples_per_segment = int(segment_duration * sample_rate)
    samples_overlap = int(samples_per_segment * overlap)
    samples_step = samples_per_segment - samples_overlap
    
    # Calcular número de segmentos
    total_samples = len(audio_data)
    if total_samples < samples_per_segment:
        # Si el audio es más corto que un segmento, rellenar con silencio
        padding = samples_per_segment - total_samples
        audio_data = np.pad(audio_data, (0, padding), mode='constant')
        total_samples = len(audio_data)
    
    num_segments = max(1, (total_samples - samples_overlap) // samples_step)
    
    segments = []
    for i in range(num_segments):
        start = i * samples_step
        end = start + samples_per_segment
        
        if end > total_samples:
            # Último segmento: rellenar con silencio si es necesario
            segment = audio_data[start:total_samples]
            padding = samples_per_segment - len(segment)
            if padding > 0:
                segment = np.pad(segment, (0, padding), mode='constant')
        else:
            segment = audio_data[start:end]
        
        segments.append(segment)
    
    return segments

def process_noise_file(input_path, output_dir, segment_duration=0.3, target_sr=16000, overlap=0.0):
    """
    Procesa un archivo de ruido dividiéndolo en segmentos de 0.3s.
    
    Args:
        input_path: Ruta al archivo de ruido
        output_dir: Directorio base de salida (se creará subdirectorio 'noise')
        segment_duration: Duración de cada segmento en segundos
        target_sr: Tasa de muestreo objetivo
        overlap: Solapamiento entre segmentos
        
    Returns:
        Número de segmentos creados, éxito
    """
    try:
        # Cargar audio
        audio_data, original_sr = sf.read(str(input_path))
        
        # Re-muestrear a target_sr si es necesario
        if original_sr != target_sr:
            from scipy import signal
            audio_data = signal.resample(audio_data, int(len(audio_data) * target_sr / original_sr))
            original_sr = target_sr
        
        # Dividir en segmentos
        segments = split_audio_into_segments(audio_data, original_sr, segment_duration, overlap)
        
        # Crear directorio de salida para ruido
        noise_dir = output_dir / "noise"
        noise_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar cada segmento
        base_name = input_path.stem
        segments_created = 0
        
        for i, segment in enumerate(segments):
            # Crear nombre de archivo
            output_filename = f"{base_name}_segment_{i:04d}.wav"
            output_path = noise_dir / output_filename
            
            # Guardar audio
            sf.write(str(output_path), segment, target_sr, subtype='PCM_16')
            segments_created += 1
        
        # Calcular estadísticas
        original_duration = len(audio_data) / original_sr
        segment_duration_actual = len(segments[0]) / original_sr if segments else 0
        
        print(f"  ✅ {input_path.name}: {original_duration:.2f}s -> {len(segments)} segmentos de {segment_duration_actual:.3f}s")
        return segments_created, True
        
    except Exception as e:
        print(f"  ❌ Error procesando {input_path.name}: {e}")
        return 0, False

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crear segmentos de ruido de 0.3 segundos')
    parser.add_argument('--input-dir', type=str, default='noise',
                       help='Directorio con archivos de ruido (relativo a datagen/)')
    parser.add_argument('--output-dir', type=str, default='03s_segments',
                       help='Directorio para segmentos de 0.3s (relativo a datagen/)')
    parser.add_argument('--duration', type=float, default=0.3,
                       help='Duración de cada segmento en segundos (default: 0.3)')
    parser.add_argument('--sample-rate', type=int, default=16000,
                       help='Tasa de muestreo objetivo (default: 16000)')
    parser.add_argument('--overlap', type=float, default=0.0,
                       help='Solapamiento entre segmentos (0.0-1.0, default: 0.0 = sin solapamiento)')
    parser.add_argument('--test', action='store_true',
                       help='Modo prueba (procesa solo 1 archivo)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CREADOR DE SEGMENTOS DE RUIDO DE 0.3 SEGUNDOS")
    print("=" * 60)
    
    # Obtener directorio base (datagen/) relativo al script
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent  # datagen/
    
    # Configurar directorios relativos a datagen/
    input_dir = base_dir / args.input_dir
    output_dir = base_dir / args.output_dir
    
    if not input_dir.exists():
        print(f"❌ Directorio de entrada no existe: {input_dir}")
        print(f"   Asegúrate de que exista datagen/noise/ con archivos .wav")
        return 1
    
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Encontrar archivos de audio
    audio_files = list(input_dir.glob("*.wav"))
    
    if not audio_files:
        print(f"❌ No se encontraron archivos .wav en {input_dir}")
        return 1
    
    # Modo prueba: procesar solo 1 archivo
    if args.test:
        audio_files = audio_files[:1]
        print("⚠️  MODO PRUEBA ACTIVADO (1 archivo)")
    
    print(f"Archivos de ruido encontrados: {len(audio_files)}")
    print(f"Directorio de entrada: {input_dir}")
    print(f"Directorio de salida: {output_dir}/noise/")
    print(f"Duración de segmento: {args.duration}s")
    print(f"Tasa de muestreo: {args.sample_rate} Hz")
    print(f"Solapamiento: {args.overlap * 100:.0f}%")
    print()
    
    # Procesar cada archivo de ruido
    total_segments = 0
    successful_files = 0
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] Procesando: {audio_file.name}")
        
        segments_created, success = process_noise_file(
            audio_file, output_dir, args.duration, args.sample_rate, args.overlap
        )
        
        if success:
            total_segments += segments_created
            successful_files += 1
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PROCESAMIENTO DE RUIDO")
    print("=" * 60)
    print(f"Archivos procesados exitosamente: {successful_files}/{len(audio_files)}")
    print(f"Segmentos de ruido creados: {total_segments}")
    print(f"Directorio de salida: {output_dir}/noise/")
    
    if total_segments > 0:
        # Mostrar primeros archivos creados
        noise_dir = output_dir / "noise"
        if noise_dir.exists():
            noise_files = list(noise_dir.glob("*.wav"))
            if noise_files:
                print(f"\nPrimeros segmentos creados:")
                for i, f in enumerate(noise_files[:5], 1):
                    print(f"  {i}. {f.name}")
    
    print(f"\n✅ Procesamiento de ruido completado")
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