#!/usr/bin/env python3
"""
Script para crear segmentos de exactamente 0.3 segundos a partir de audio recortado.
Si el audio es más corto, lo rellena con silencio.
Si es más largo, extrae los primeros 0.3 segundos.
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

def create_03s_segment(audio_data, sample_rate, target_duration=0.3):
    """
    Crea un segmento de exactamente target_duration segundos.
    - Si el audio es más corto: rellena con silencio al inicio y final
    - Si el audio es más largo: toma los primeros target_duration segundos
    
    Args:
        audio_data: Array de numpy con datos de audio
        sample_rate: Tasa de muestreo
        target_duration: Duración objetivo en segundos (default: 0.3)
        
    Returns:
        Segmento de audio de exactamente target_duration segundos
    """
    # Convertir a mono si es estéreo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Calcular muestras objetivo
    target_samples = int(target_duration * sample_rate)
    
    # Si el audio es exactamente del tamaño objetivo, devolverlo
    if len(audio_data) == target_samples:
        return audio_data
    
    # Si el audio es más corto, rellenar con silencio
    if len(audio_data) < target_samples:
        padding = target_samples - len(audio_data)
        # Dividir padding entre inicio y final
        pad_start = padding // 2
        pad_end = padding - pad_start
        
        # Rellenar con ceros (silencio)
        padded_audio = np.pad(audio_data, (pad_start, pad_end), mode='constant')
        return padded_audio
    
    # Si el audio es más largo, extraer primeros 0.3s
    if len(audio_data) > target_samples:
        return audio_data[:target_samples]

def process_audio_file(input_path, output_dir, target_duration=0.3, target_sr=16000):
    """
    Procesa un archivo de audio: crea segmento de 0.3s, re-muestrea a 16kHz y organiza por vocal.
    
    Args:
        input_path: Ruta al archivo de entrada
        output_dir: Directorio base de salida
        target_duration: Duración objetivo en segundos
        target_sr: Tasa de muestreo objetivo
        
    Returns:
        Tupla (duración_entrada, duración_salida, vocal, éxito)
    """
    try:
        # Cargar audio
        audio_data, original_sr = sf.read(str(input_path))
        
        # Calcular duración original
        original_duration = len(audio_data) / original_sr
        
        # Crear segmento de 0.3s a la tasa de muestreo original
        segment = create_03s_segment(audio_data, original_sr, target_duration)
        
        # Re-muestrear a 16kHz si es necesario
        if original_sr != target_sr:
            # Calcular factor de re-muestreo
            from scipy import signal
            segment = signal.resample(segment, int(len(segment) * target_sr / original_sr))
        
        # Calcular duración final
        final_duration = len(segment) / target_sr
        
        # Determinar vocal del nombre del archivo (ej: "A_a_20260307_103004.wav" -> "A")
        filename = input_path.name
        vowel = 'unknown'
        if '_' in filename:
            parts = filename.split('_')
            if parts[0] in ['A', 'E', 'I', 'O', 'U']:
                vowel = parts[0]
        
        # Crear directorio para la vocal
        vowel_dir = output_dir / vowel
        vowel_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear nombre de archivo de salida (mantener nombre original)
        output_path = vowel_dir / filename
        
        # Guardar audio
        sf.write(str(output_path), segment, target_sr, subtype='PCM_16')
        
        return original_duration, final_duration, vowel, True
        
    except Exception as e:
        print(f"  ❌ Error procesando {input_path.name}: {e}")
        return 0, 0, 'unknown', False

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crear segmentos de 0.3 segundos')
    parser.add_argument('--input-dir', type=str, default='filtered_audio',
                       help='Directorio con archivos de audio filtrados (relativo a datagen/)')
    parser.add_argument('--output-dir', type=str, default='03s_segments',
                       help='Directorio para segmentos de 0.3s (relativo a datagen/)')
    parser.add_argument('--duration', type=float, default=0.3,
                       help='Duración objetivo en segundos (default: 0.3)')
    parser.add_argument('--sample-rate', type=int, default=16000,
                       help='Tasa de muestreo objetivo (default: 16000)')
    parser.add_argument('--test', action='store_true',
                       help='Modo prueba (procesa solo 5 archivos)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CREADOR DE SEGMENTOS DE 0.3 SEGUNDOS")
    print("=" * 60)
    
    # Obtener directorio base (datagen/) relativo al script
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent  # datagen/
    
    # Configurar directorios relativos a datagen/
    input_dir = base_dir / args.input_dir
    output_dir = base_dir / args.output_dir
    
    if not input_dir.exists():
        print(f"❌ Directorio de entrada no existe: {input_dir}")
        print(f"   Ejecuta primero: python trim_silence.py")
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
    print(f"Duración objetivo: {args.duration}s")
    print(f"Tasa de muestreo objetivo: {args.sample_rate} Hz")
    
    if args.test:
        audio_files = audio_files[:5]
        print(f"⚠️  MODO PRUEBA: Procesando solo {len(audio_files)} archivos")
    
    print("\n" + "-" * 60)
    
    # Procesar archivos
    successful = 0
    vowel_counts = {'A': 0, 'E': 0, 'I': 0, 'O': 0, 'U': 0, 'unknown': 0}
    
    for i, input_file in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] Procesando: {input_file.name}")
        
        # Procesar archivo
        orig_dur, final_dur, vowel, success = process_audio_file(
            input_file, output_dir, args.duration, args.sample_rate
        )
        
        if success:
            diff = final_dur - args.duration
            diff_ms = diff * 1000  # Convertir a milisegundos
            
            if abs(diff) < 0.001:  # 1ms de tolerancia
                print(f"  ✅ {vowel}: {orig_dur:.3f}s → {final_dur:.3f}s")
            elif diff > 0:
                print(f"  ⚠️  {vowel} (largo): {orig_dur:.3f}s → {final_dur:.3f}s (+{diff_ms:.1f}ms)")
            else:
                print(f"  ⚠️  {vowel} (corto): {orig_dur:.3f}s → {final_dur:.3f}s ({diff_ms:.1f}ms)")
            
            successful += 1
            vowel_counts[vowel] = vowel_counts.get(vowel, 0) + 1
        else:
            print(f"  ❌ Error procesando archivo")
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    print(f"Archivos procesados: {successful}/{len(audio_files)}")
    
    if successful > 0:
        # Mostrar distribución por vocal
        print(f"\nDistribución por vocal:")
        for vowel in ['A', 'E', 'I', 'O', 'U', 'unknown']:
            count = vowel_counts.get(vowel, 0)
            if count > 0:
                print(f"  {vowel}: {count} archivos")
        
        # Verificar duraciones y estructura de directorios
        print(f"\nEstructura de directorios creada en {output_dir}:")
        for vowel in ['A', 'E', 'I', 'O', 'U', 'unknown']:
            vowel_dir = output_dir / vowel
            if vowel_dir.exists():
                vowel_files = list(vowel_dir.glob("*.wav"))
                if vowel_files:
                    # Verificar duración del primer archivo
                    try:
                        data, sr = sf.read(str(vowel_files[0]))
                        duration = len(data) / sr
                        print(f"  {vowel}/: {len(vowel_files)} archivos, ejemplo: {duration:.6f}s")
                    except:
                        print(f"  {vowel}/: {len(vowel_files)} archivos")
        
        # Verificar duraciones de algunos archivos
        print(f"\nVerificando duraciones de archivos generados (primeros 3):")
        all_files = []
        for vowel_dir in output_dir.iterdir():
            if vowel_dir.is_dir():
                all_files.extend(list(vowel_dir.glob("*.wav")))
        
        durations = []
        for file in all_files[:3]:  # Mostrar primeros 3
            try:
                data, sr = sf.read(str(file))
                duration = len(data) / sr
                durations.append(duration)
                print(f"  {file.parent.name}/{file.name}: {duration:.6f}s ({len(data)} muestras a {sr} Hz)")
            except Exception as e:
                print(f"  ❌ Error leyendo {file.name}: {e}")
        
        if durations:
            avg_duration = np.mean(durations)
            min_duration = np.min(durations)
            max_duration = np.max(durations)
            
            print(f"\nEstadísticas (primeros {len(durations)} archivos):")
            print(f"  Mínima: {min_duration:.6f}s")
            print(f"  Máxima: {max_duration:.6f}s")
            print(f"  Promedio: {avg_duration:.6f}s")
            print(f"  Desviación del objetivo ({args.duration}s): {abs(avg_duration - args.duration)*1000:.2f}ms")
    
    print(f"\n✅ Segmentos de {args.duration}s organizados por vocal en: {output_dir}")
    
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