#!/usr/bin/env python3
"""
Script para filtrar y eliminar archivos de audio demasiado largos.
Audio muy largo (> 0.3s para sílabas simples) probablemente está deletreado.
"""

import os
import sys
from pathlib import Path
import shutil

try:
    import soundfile as sf
except ImportError:
    print("ERROR: soundfile no está instalado.")
    print("Instalar con: pip install soundfile")
    sys.exit(1)

def analyze_audio_duration(input_path, max_duration=0.3):
    """
    Analiza la duración de un archivo de audio.
    
    Args:
        input_path: Ruta al archivo de audio
        max_duration: Duración máxima permitida para sílabas (segundos)
        
    Returns:
        Tupla (duración, es_válido, razón)
    """
    try:
        # Cargar audio
        audio_data, sample_rate = sf.read(str(input_path))
        
        # Calcular duración
        duration = len(audio_data) / sample_rate
        
        # Determinar si es válido
        if duration > max_duration:
            return duration, False, f"Demasiado largo ({duration:.3f}s > {max_duration}s)"
        else:
            return duration, True, f"OK ({duration:.3f}s)"
            
    except Exception as e:
        return 0, False, f"Error: {e}"

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Filtrar archivos de audio demasiado largos')
    parser.add_argument('--input-dir', type=str, default='trimmed_audio',
                       help='Directorio con archivos de audio recortados (relativo a datagen/)')
    parser.add_argument('--output-dir', type=str, default='filtered_audio',
                       help='Directorio para archivos filtrados (relativo a datagen/)')
    parser.add_argument('--max-duration', type=float, default=0.4,
                       help='Duración máxima permitida para sílabas (default: 0.4s)')
    parser.add_argument('--move-invalid', type=str, default='invalid_audio',
                       help='Directorio para archivos inválidos (opcional, relativo a datagen/)')
    parser.add_argument('--test', action='store_true',
                       help='Modo prueba (procesa solo 10 archivos)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("FILTRADO DE AUDIO DEMASIADO LARGO")
    print("=" * 60)
    
    # Obtener directorio base (datagen/) relativo al script
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent  # datagen/
    
    # Configurar directorios relativos a datagen/
    input_dir = base_dir / args.input_dir
    output_dir = base_dir / args.output_dir
    invalid_dir = base_dir / args.move_invalid if args.move_invalid else None
    
    if not input_dir.exists():
        print(f"❌ Directorio de entrada no existe: {input_dir}")
        print(f"   Ejecuta primero: python trim_silence.py")
        return 1
    
    # Crear directorios
    output_dir.mkdir(parents=True, exist_ok=True)
    if invalid_dir:
        invalid_dir.mkdir(parents=True, exist_ok=True)
    
    # Encontrar archivos de audio
    audio_files = list(input_dir.glob("*.wav"))
    
    if not audio_files:
        print(f"❌ No se encontraron archivos .wav en {input_dir}")
        return 1
    
    print(f"Archivos encontrados: {len(audio_files)}")
    print(f"Directorio de entrada: {input_dir}")
    print(f"Directorio de salida (válidos): {output_dir}")
    if invalid_dir:
        print(f"Directorio para inválidos: {invalid_dir}")
    print(f"Duración máxima permitida: {args.max_duration}s")
    
    if args.test:
        audio_files = audio_files[:10]
        print(f"⚠️  MODO PRUEBA: Procesando solo {len(audio_files)} archivos")
    
    print("\n" + "-" * 60)
    
    # Analizar y filtrar archivos
    valid_count = 0
    invalid_count = 0
    
    for i, input_file in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] Analizando: {input_file.name}")
        
        # Analizar audio
        duration, is_valid, reason = analyze_audio_duration(input_file, args.max_duration)
        
        if is_valid:
            # Copiar a directorio de válidos
            output_file = output_dir / input_file.name
            shutil.copy2(input_file, output_file)
            print(f"  ✅ VÁLIDO: {reason}")
            valid_count += 1
        else:
            print(f"  ❌ INVÁLIDO: {reason}")
            
            if invalid_dir:
                # Mover a directorio de inválidos
                invalid_file = invalid_dir / input_file.name
                shutil.move(input_file, invalid_file)
            invalid_count += 1
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE FILTRADO")
    print("=" * 60)
    
    print(f"Archivos analizados: {len(audio_files)}")
    print(f"Archivos válidos: {valid_count}")
    print(f"Archivos inválidos (demasiado largos): {invalid_count}")
    
    if valid_count > 0:
        print(f"\n✅ Archivos válidos guardados en: {output_dir}")
    
    if invalid_count > 0 and invalid_dir:
        print(f"🗑️  Archivos inválidos movidos a: {invalid_dir}")
    
    # Mostrar ejemplos de archivos inválidos
    if invalid_count > 0:
        print(f"\nEjemplos de archivos inválidos (demasiado largos):")
        invalid_files = list(invalid_dir.glob("*.wav"))[:5] if invalid_dir else []
        for file in invalid_files:
            try:
                data, sr = sf.read(str(file))
                duration = len(data) / sr
                print(f"  {file.name}: {duration:.3f}s")
            except:
                pass
    
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