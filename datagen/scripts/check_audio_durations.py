#!/usr/bin/env python3
"""
Script para verificar duraciones de archivos de audio generados.
"""

import os
import sys
from pathlib import Path

try:
    import soundfile as sf
except ImportError:
    print("ERROR: soundfile no está instalado. Instalar con: pip install soundfile")
    sys.exit(1)

def check_audio_duration(audio_path):
    """Verifica la duración de un archivo de audio."""
    try:
        data, samplerate = sf.read(str(audio_path))
        duration = len(data) / samplerate
        return duration, samplerate, len(data)
    except Exception as e:
        print(f"  ❌ Error leyendo {audio_path.name}: {e}")
        return None, None, None

def main():
    """Función principal."""
    base_dir = Path("datagen")
    
    # Verificar archivos de Edge TTS
    edge_dir = base_dir / "raw_audio_edge"
    
    if not edge_dir.exists():
        print(f"❌ Directorio no encontrado: {edge_dir}")
        return
    
    print("=" * 80)
    print("VERIFICACIÓN DE DURACIONES DE AUDIO (EDGE TTS)")
    print("=" * 80)
    
    audio_files = list(edge_dir.glob("*.wav"))
    
    if not audio_files:
        print("No se encontraron archivos .wav")
        return
    
    print(f"Archivos encontrados: {len(audio_files)}")
    print("-" * 80)
    
    # Clasificar por vocal
    vocals = ['A', 'E', 'I', 'O', 'U']
    files_by_vocal = {v: [] for v in vocals}
    
    for file in audio_files:
        for v in vocals:
            if file.name.startswith(f"{v}_"):
                files_by_vocal[v].append(file)
                break
    
    # Verificar cada vocal
    for vocal in vocals:
        files = files_by_vocal[vocal]
        if not files:
            continue
        
        print(f"\n{vocal}: {len(files)} archivos")
        print("-" * 40)
        
        for file in sorted(files):
            duration, sr, samples = check_audio_duration(file)
            if duration is not None:
                status = "✅" if duration < 1.0 else "⚠️ "
                print(f"  {status} {file.name:40} | {duration:.3f}s | {sr} Hz | {samples} muestras")
                
                # Verificar si es muy largo (posible deletreo)
                if duration > 2.0:
                    print(f"    ⚠️  POSIBLE DELETREO: {duration:.2f}s > 2.0s")
    
    # Resumen estadístico
    print("\n" + "=" * 80)
    print("RESUMEN ESTADÍSTICO")
    print("=" * 80)
    
    all_durations = []
    for file in audio_files:
        duration, sr, _ = check_audio_duration(file)
        if duration is not None:
            all_durations.append(duration)
    
    if all_durations:
        avg_duration = sum(all_durations) / len(all_durations)
        max_duration = max(all_durations)
        min_duration = min(all_durations)
        
        print(f"Total archivos: {len(all_durations)}")
        print(f"Duración promedio: {avg_duration:.3f}s")
        print(f"Duración mínima: {min_duration:.3f}s")
        print(f"Duración máxima: {max_duration:.3f}s")
        
        # Contar archivos sospechosos (> 1.5s)
        suspicious = [d for d in all_durations if d > 1.5]
        print(f"Archivos sospechosos (>1.5s): {len(suspicious)}")
        
        if suspicious:
            print("\nArchivos con posible deletreo:")
            for file in audio_files:
                duration, sr, _ = check_audio_duration(file)
                if duration and duration > 1.5:
                    print(f"  {file.name}: {duration:.3f}s")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()