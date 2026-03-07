#!/usr/bin/env python3
"""
Script para generar textos para cada vocal con todas las combinaciones de consonantes.
Genera un archivo por vocal (A.txt, E.txt, I.txt, O.txt, U.txt) en sus respectivas carpetas.
"""

import os
import json
from pathlib import Path
from datetime import datetime

# Consonantes españolas (incluyendo ñ)
CONSONANTES_ESPANOL = [
    'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 
    'n', 'ñ', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z'
]

# Combinaciones especiales (dígrafos)
COMBINACIONES_ESPECIALES = ['ch', 'll', 'rr']

# Vocales
VOCALES = ['A', 'E', 'I', 'O', 'U']

def generar_combinaciones_por_vocal(vocal):
    """
    Genera todas las combinaciones para una vocal específica.
    
    Args:
        vocal: Vocal en mayúscula ('A', 'E', 'I', 'O', 'U')
    
    Returns:
        Lista de combinaciones para esa vocal
    """
    vocal_lower = vocal.lower()
    combinaciones = []
    
    # Vocal sola (sin consonante)
    combinaciones.append({
        'texto': vocal_lower,
        'consonante': '',
        'vocal': vocal,
        'tipo': 'vocal_sola',
        'direccion': 'vocal_sola'
    })
    
    # Combinaciones consonante + vocal (CV)
    for consonante in CONSONANTES_ESPANOL:
        texto = f"{consonante}{vocal_lower}"
        combinaciones.append({
            'texto': texto,
            'consonante': consonante,
            'vocal': vocal,
            'tipo': 'cv',
            'direccion': 'consonante_vocal'
        })
    
    # Combinaciones vocal + consonante (VC)
    for consonante in CONSONANTES_ESPANOL:
        texto = f"{vocal_lower}{consonante}"
        combinaciones.append({
            'texto': texto,
            'consonante': consonante,
            'vocal': vocal,
            'tipo': 'vc',
            'direccion': 'vocal_consonante'
        })
    
    # Combinaciones con dígrafos (CV)
    for especial in COMBINACIONES_ESPECIALES:
        texto = f"{especial}{vocal_lower}"
        combinaciones.append({
            'texto': texto,
            'consonante': especial,
            'vocal': vocal,
            'tipo': 'especial_cv',
            'direccion': 'consonante_vocal'
        })
    
    # Combinaciones con dígrafos (VC)
    for especial in COMBINACIONES_ESPECIALES:
        texto = f"{vocal_lower}{especial}"
        combinaciones.append({
            'texto': texto,
            'consonante': especial,
            'vocal': vocal,
            'tipo': 'especial_vc',
            'direccion': 'vocal_consonante'
        })
    
    return combinaciones

def generar_texto_formateado(combinaciones):
    """
    Formatea las combinaciones en un texto para TTS.
    Incluye silencios (puntos) entre combinaciones.
    
    Args:
        combinaciones: Lista de combinaciones
    
    Returns:
        Texto formateado para TTS
    """
    textos = [combo['texto'] for combo in combinaciones]
    # Unir con espacio y punto para separación
    texto_formateado = " . ".join(textos) + " . "
    return texto_formateado

def guardar_archivo_vocal(vocal, texto, output_dir):
    """
    Guarda el texto en un archivo en la carpeta de la vocal.
    
    Args:
        vocal: Vocal ('A', 'E', 'I', 'O', 'U')
        texto: Texto a guardar
        output_dir: Directorio base de salida
    
    Returns:
        Ruta al archivo guardado
    """
    # Crear carpeta de la vocal
    vocal_dir = output_dir / "processed" / vocal
    vocal_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar archivo de texto
    archivo_texto = vocal_dir / f"{vocal}.txt"
    with open(archivo_texto, 'w', encoding='utf-8') as f:
        f.write(texto)
    
    return archivo_texto

def guardar_metadata(combinaciones_por_vocal, output_dir):
    """
    Guarda metadata de todas las combinaciones en JSON.
    
    Args:
        combinaciones_por_vocal: Diccionario con combinaciones por vocal
        output_dir: Directorio base de salida
    
    Returns:
        Ruta al archivo JSON
    """
    metadata = {
        'fecha_generacion': datetime.now().isoformat(),
        'consonantes_utilizadas': CONSONANTES_ESPANOL + COMBINACIONES_ESPECIALES,
        'vocales_utilizadas': VOCALES,
        'total_consonantes': len(CONSONANTES_ESPANOL),
        'total_combinaciones_especiales': len(COMBINACIONES_ESPECIALES),
        'descripcion': 'Combinaciones consonante-vocal para generación de dataset de audio',
        'combinaciones_por_vocal': {}
    }
    
    for vocal in VOCALES:
        combinaciones = combinaciones_por_vocal.get(vocal, [])
        metadata['combinaciones_por_vocal'][vocal] = {
            'total_combinaciones': len(combinaciones),
            'cv_count': sum(1 for c in combinaciones if c['direccion'] == 'consonante_vocal'),
            'vc_count': sum(1 for c in combinaciones if c['direccion'] == 'vocal_consonante'),
            'archivo_texto': f"processed/{vocal}/{vocal}.txt"
        }
    
    archivo_json = output_dir / "combinaciones_metadata.json"
    with open(archivo_json, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return archivo_json

def main():
    """Función principal."""
    print("=" * 60)
    print("GENERADOR DE TEXTOS POR VOCAL")
    print("=" * 60)
    
    # Directorio base siempre relativo al proyecto
    # Asumimos que el script está en datagen/scripts/
    # y queremos generar en datagen/
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent  # datagen/
    project_root = base_dir.parent  # d:/Vocals_Recognition_Model/
    
    print(f"Directorio del script: {script_dir}")
    print(f"Directorio base (datagen): {base_dir}")
    
    # Crear directorios necesarios
    processed_dir = base_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar combinaciones para cada vocal
    print("\nGenerando combinaciones para cada vocal...")
    
    combinaciones_por_vocal = {}
    archivos_generados = []
    
    for vocal in VOCALES:
        print(f"\nVocal {vocal}:")
        
        # Generar combinaciones
        combinaciones = generar_combinaciones_por_vocal(vocal)
        combinaciones_por_vocal[vocal] = combinaciones
        
        print(f"  Combinaciones generadas: {len(combinaciones)}")
        
        # Contar por tipo
        cv_count = sum(1 for c in combinaciones if c['direccion'] == 'consonante_vocal')
        vc_count = sum(1 for c in combinaciones if c['direccion'] == 'vocal_consonante')
        print(f"    CV (consonante+vocal): {cv_count}")
        print(f"    VC (vocal+consonante): {vc_count}")
        
        # Formatear texto para TTS
        texto_formateado = generar_texto_formateado(combinaciones)
        
        # Guardar archivo en carpeta de la vocal
        archivo_vocal = guardar_archivo_vocal(vocal, texto_formateado, base_dir)
        archivos_generados.append(archivo_vocal)
        
        # Mostrar ruta relativa al proyecto
        ruta_relativa = archivo_vocal.relative_to(project_root)
        print(f"  Archivo guardado: {ruta_relativa}")
        
        # Mostrar ejemplo del texto
        palabras = texto_formateado.split()
        ejemplo = " ".join(palabras[:6]) + " ..."
        print(f"  Ejemplo: {ejemplo}")
    
    # Guardar metadata
    print("\nGuardando metadata...")
    archivo_metadata = guardar_metadata(combinaciones_por_vocal, base_dir)
    ruta_metadata_rel = archivo_metadata.relative_to(project_root)
    print(f"  Metadata guardada: {ruta_metadata_rel}")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    total_combinaciones = sum(len(combs) for combs in combinaciones_por_vocal.values())
    print(f"Consonantes españolas: {len(CONSONANTES_ESPANOL)}")
    print(f"Combinaciones especiales: {len(COMBINACIONES_ESPECIALES)}")
    print(f"Vocales: {len(VOCALES)}")
    print(f"Total combinaciones generadas: {total_combinaciones}")
    
    print("\nArchivos generados por vocal:")
    for vocal in VOCALES:
        archivo = base_dir / "processed" / vocal / f"{vocal}.txt"
        if archivo.exists():
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
                palabras = contenido.split()
                print(f"  {vocal}.txt: {len(palabras)} palabras, {len(contenido)} caracteres")
    
    print(f"\nMetadata: combinaciones_metadata.json")
    print(f"\nEstructura creada en {base_dir.name}/:")
    print(f"  processed/")
    for vocal in VOCALES:
        vocal_dir = base_dir / "processed" / vocal
        if vocal_dir.exists():
            archivos = list(vocal_dir.glob("*.txt"))
            print(f"    {vocal}/")
            for archivo in archivos:
                print(f"      {archivo.name}")
    
    print(f"  combinaciones_metadata.json")
    
    print(f"\n✅ Textos generados exitosamente en: {base_dir}/")
    
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