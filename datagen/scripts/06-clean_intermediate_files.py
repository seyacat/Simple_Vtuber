#!/usr/bin/env python3
"""
Script 06: Limpiar archivos intermedios del proceso de generación de audio.
Elimina directorios intermedios para dejar solo el dataset final organizado.
"""

import os
import sys
import shutil
from pathlib import Path

def clean_intermediate_files(base_dir="datagen", keep_final=True):
    """
    Elimina archivos y directorios intermedios del proceso.
    
    Args:
        base_dir: Directorio base del proyecto
        keep_final: Si es True, mantiene el dataset final (03s_segments)
        
    Returns:
        Diccionario con resultados de limpieza
    """
    base_path = Path(base_dir)
    
    # Directorios a eliminar (intermedios)
    dirs_to_remove = [
        "raw_audio",           # Audio generado por Windows TTS (viejo)
        "raw_audio_edge",      # Audio generado por Edge TTS
        "trimmed_audio",       # Audio recortado
        "filtered_audio",      # Audio filtrado
        "invalid_audio",       # Audio inválido (deletreado)
        "processed_audio_edge", # Procesamiento anterior
        "processed_audio_edge_fixed", # Procesamiento anterior
        "datagen",             # Directorio duplicado dentro de datagen/
    ]
    
    # Archivos a eliminar
    files_to_remove = [
        "combinaciones_metadata.json",
        "config_pipeline.json",
        "tts_generation_metadata.json",
        "edge_tts_generation_metadata.json",
        "processing_metadata.json",
    ]
    
    results = {
        'directorios_eliminados': [],
        'directorios_no_encontrados': [],
        'archivos_eliminados': [],
        'archivos_no_encontrados': [],
        'errores': []
    }
    
    print("=" * 60)
    print("LIMPIEZA DE ARCHIVOS INTERMEDIOS")
    print("=" * 60)
    
    # Eliminar directorios
    print("\nEliminando directorios intermedios:")
    for dir_name in dirs_to_remove:
        dir_path = base_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            try:
                shutil.rmtree(dir_path)
                results['directorios_eliminados'].append(dir_name)
                print(f"  ✅ Eliminado: {dir_name}/")
            except Exception as e:
                error_msg = f"{dir_name}: {e}"
                results['errores'].append(error_msg)
                print(f"  ❌ Error eliminando {dir_name}: {e}")
        else:
            results['directorios_no_encontrados'].append(dir_name)
    
    # Eliminar archivos
    print("\nEliminando archivos intermedios:")
    for file_name in files_to_remove:
        file_path = base_path / file_name
        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
                results['archivos_eliminados'].append(file_name)
                print(f"  ✅ Eliminado: {file_name}")
            except Exception as e:
                error_msg = f"{file_name}: {e}"
                results['errores'].append(error_msg)
                print(f"  ❌ Error eliminando {file_name}: {e}")
        else:
            results['archivos_no_encontrados'].append(file_name)
    
    # Verificar dataset final
    final_dataset = base_path / "03s_segments"
    if keep_final and final_dataset.exists():
        print(f"\n✅ Dataset final conservado: {final_dataset}")
        
        # Contar archivos en el dataset final
        total_files = 0
        vowel_counts = {}
        
        for vowel_dir in final_dataset.iterdir():
            if vowel_dir.is_dir():
                vowel_files = list(vowel_dir.glob("*.wav"))
                count = len(vowel_files)
                vowel_counts[vowel_dir.name] = count
                total_files += count
        
        print(f"  Archivos totales en dataset: {total_files}")
        if vowel_counts:
            print(f"  Distribución por vocal:")
            for vowel, count in sorted(vowel_counts.items()):
                print(f"    {vowel}: {count} archivos")
    elif keep_final:
        print(f"\n⚠️  Dataset final no encontrado: {final_dataset}")
    
    return results

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Limpiar archivos intermedios del proceso de audio')
    parser.add_argument('--base-dir', type=str, default='datagen',
                       help='Directorio base del proyecto (default: datagen)')
    parser.add_argument('--remove-final', action='store_true',
                       help='Eliminar también el dataset final (03s_segments)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Mostrar qué se eliminaría sin hacer cambios')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("=" * 60)
        print("SIMULACIÓN DE LIMPIEZA (DRY RUN)")
        print("=" * 60)
        print("\nSe eliminarían los siguientes directorios y archivos:")
        
        base_path = Path(args.base_dir)
        
        # Directorios a eliminar
        dirs_to_remove = [
            "raw_audio", "raw_audio_edge", "trimmed_audio",
            "filtered_audio", "invalid_audio", "processed_audio_edge",
            "processed_audio_edge_fixed", "datagen"
        ]
        
        for dir_name in dirs_to_remove:
            dir_path = base_path / dir_name
            if dir_path.exists():
                print(f"  📁 {dir_name}/ (existe)")
            else:
                print(f"  📁 {dir_name}/ (no existe)")
        
        # Archivos a eliminar
        files_to_remove = [
            "combinaciones_metadata.json", "config_pipeline.json",
            "tts_generation_metadata.json", "edge_tts_generation_metadata.json",
            "processing_metadata.json"
        ]
        
        for file_name in files_to_remove:
            file_path = base_path / file_name
            if file_path.exists():
                print(f"  📄 {file_name} (existe)")
            else:
                print(f"  📄 {file_name} (no existe)")
        
        # Dataset final
        final_dataset = base_path / "03s_segments"
        if args.remove_final:
            if final_dataset.exists():
                print(f"  🗑️  03s_segments/ (se eliminaría)")
            else:
                print(f"  🗑️  03s_segments/ (no existe)")
        else:
            if final_dataset.exists():
                print(f"  ✅ 03s_segments/ (se conservaría)")
            else:
                print(f"  ⚠️  03s_segments/ (no existe)")
        
        print(f"\n⚠️  Esta es una simulación. Use --dry-run false para ejecutar.")
        return 0
    
    # Ejecutar limpieza real
    results = clean_intermediate_files(
        base_dir=args.base_dir,
        keep_final=not args.remove_final
    )
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE LIMPIEZA")
    print("=" * 60)
    
    print(f"\nDirectorios eliminados: {len(results['directorios_eliminados'])}")
    for dir_name in results['directorios_eliminados']:
        print(f"  ✅ {dir_name}/")
    
    print(f"\nArchivos eliminados: {len(results['archivos_eliminados'])}")
    for file_name in results['archivos_eliminados']:
        print(f"  ✅ {file_name}")
    
    if results['directorios_no_encontrados']:
        print(f"\nDirectorios no encontrados: {len(results['directorios_no_encontrados'])}")
        for dir_name in results['directorios_no_encontrados'][:5]:  # Mostrar primeros 5
            print(f"  ⚠️  {dir_name}/")
    
    if results['archivos_no_encontrados']:
        print(f"\nArchivos no encontrados: {len(results['archivos_no_encontrados'])}")
        for file_name in results['archivos_no_encontrados'][:5]:  # Mostrar primeros 5
            print(f"  ⚠️  {file_name}")
    
    if results['errores']:
        print(f"\nErrores: {len(results['errores'])}")
        for error in results['errores'][:3]:  # Mostrar primeros 3 errores
            print(f"  ❌ {error}")
    
    print(f"\n✅ Limpieza completada")
    
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