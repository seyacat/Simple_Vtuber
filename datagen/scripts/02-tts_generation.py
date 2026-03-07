#!/usr/bin/env python3
"""
Script 02: Generar audio usando Edge TTS.
Lee los archivos de texto por vocal (A.txt, E.txt, etc.) y genera archivos de audio.
Usa Edge TTS que tiene muchas más voces en español que Windows TTS.
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("ERROR: edge-tts no está instalado. Instalar con: pip install edge-tts")
    sys.exit(1)

class EdgeTTSGenerator:
    """Generador de audio usando Edge TTS."""
    
    def __init__(self, base_dir="datagen", voice_name="es-ES-ElviraNeural"):
        """
        Inicializa el generador Edge TTS.
        
        Args:
            base_dir: Directorio base del proyecto
            voice_name: Nombre de la voz a usar (ej: "es-ES-ElviraNeural")
        """
        self.base_dir = Path(base_dir)
        self.raw_audio_dir = self.base_dir / "raw_audio_edge"
        self.raw_audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar voz
        self.voice_name = voice_name
        print(f"Voz seleccionada: {self.voice_name}")
        
        # Configurar parámetros
        self.rate = "+0%"  # Velocidad normal
        self.volume = "+0%"  # Volumen normal
        
    async def text_to_wav_async(self, text, filename, sample_rate=16000):
        """
        Convierte texto a archivo WAV usando Edge TTS (async).
        
        Args:
            text: Texto a sintetizar
            filename: Nombre del archivo de salida (sin extensión)
            sample_rate: Tasa de muestreo deseada (Hz)
            
        Returns:
            Ruta al archivo generado o None si hay error
        """
        try:
            # Crear communicator
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice_name,
                rate=self.rate,
                volume=self.volume
            )
            
            # Configurar archivo de salida
            output_path = self.raw_audio_dir / f"{filename}.wav"
            
            # Guardar audio
            await communicate.save(str(output_path))
            
            # Edge TTS genera archivos a 24kHz, necesitamos verificar/convertir
            # La conversión a 16kHz se hará en el procesamiento de audio
            return output_path
            
        except Exception as e:
            print(f"  ❌ Error generando audio: {e}")
            return None
    
    def text_to_wav(self, text, filename, sample_rate=16000):
        """
        Versión síncrona de text_to_wav.
        
        Args:
            text: Texto a sintetizar
            filename: Nombre del archivo de salida (sin extensión)
            sample_rate: Tasa de muestreo deseada (Hz)
            
        Returns:
            Ruta al archivo generado o None si hay error
        """
        return asyncio.run(self.text_to_wav_async(text, filename, sample_rate))
    
    async def process_vocal_file_async(self, vocal, text_file_path, max_items=None):
        """
        Procesa un archivo de texto de una vocal (async).
        
        Args:
            vocal: Vocal ('A', 'E', 'I', 'O', 'U')
            text_file_path: Ruta al archivo de texto
            max_items: Máximo número de segmentos a procesar (None = todos)
            
        Returns:
            Lista de archivos generados
        """
        print(f"\nProcesando vocal {vocal}: {text_file_path.name}")
        
        # Leer archivo de texto
        with open(text_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Separar por puntos para obtener segmentos individuales
        segments = [s.strip() for s in content.split('.') if s.strip()]
        
        if max_items:
            segments = segments[:max_items]
            print(f"  (Limitado a {max_items} segmentos)")
        
        print(f"  Segmentos a procesar: {len(segments)}")
        
        generated_files = []
        
        for i, segment in enumerate(segments, 1):
            # Crear nombre de archivo seguro
            safe_segment = segment.replace(' ', '_').replace('.', '')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{vocal}_{safe_segment}_{timestamp}"
            
            print(f"  [{i}/{len(segments)}] Segmento: '{segment}'")
            print(f"  Generando: '{segment}...' -> {filename}.wav")
            
            # Generar audio
            output_path = await self.text_to_wav_async(segment, filename)
            
            if output_path and output_path.exists():
                print(f"  ✅ Archivo creado: {output_path.name}")
                generated_files.append(str(output_path))
            else:
                print(f"  ❌ Error creando archivo para: {segment}")
            
            # Pequeña pausa para evitar sobrecargar el servicio
            if i < len(segments):
                await asyncio.sleep(0.1)
        
        return generated_files
    
    def process_vocal_file(self, vocal, text_file_path, max_items=None):
        """
        Versión síncrona de process_vocal_file.
        
        Args:
            vocal: Vocal ('A', 'E', 'I', 'O', 'U')
            text_file_path: Ruta al archivo de texto
            max_items: Máximo número de segmentos a procesar (None = todos)
            
        Returns:
            Lista de archivos generados
        """
        return asyncio.run(self.process_vocal_file_async(vocal, text_file_path, max_items))
    
    async def process_all_vocals_async(self, max_items_per_vocal=None, test_mode=False):
        """
        Procesa todas las vocales (async).
        
        Args:
            max_items_per_vocal: Máximo de segmentos por vocal
            test_mode: Si es True, procesa solo 5 segmentos por vocal
            
        Returns:
            Diccionario con resultados
        """
        if test_mode:
            max_items_per_vocal = 5
            print("⚠️  MODO PRUEBA ACTIVADO (5 segmentos por vocal)")
        
        print("\n" + "=" * 40)
        print("PROCESANDO TODAS LAS VOCALES CON EDGE TTS")
        print("=" * 40)
        
        vocals = ['A', 'E', 'I', 'O', 'U']
        results = {}
        
        for vocal in vocals:
            text_file_path = self.base_dir / "processed" / vocal / f"{vocal}.txt"
            
            if not text_file_path.exists():
                print(f"❌ Archivo no encontrado: {text_file_path}")
                results[vocal] = []
                continue
            
            print(f"\n{'=' * 8}")
            print(f"VOCAL: {vocal}")
            print(f"{'=' * 8}")
            
            files = await self.process_vocal_file_async(
                vocal, text_file_path, max_items_per_vocal
            )
            
            results[vocal] = files
            print(f"  ✅ Vocal {vocal}: {len(files)} archivos generados")
        
        return results
    
    def process_all_vocals(self, max_items_per_vocal=None, test_mode=False):
        """
        Versión síncrona de process_all_vocals.
        
        Args:
            max_items_per_vocal: Máximo de segmentos por vocal
            test_mode: Si es True, procesa solo 5 segmentos por vocal
            
        Returns:
            Diccionario con resultados
        """
        return asyncio.run(self.process_all_vocals_async(max_items_per_vocal, test_mode))

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generar audio usando Edge TTS')
    parser.add_argument('--test', action='store_true', help='Modo prueba (5 segmentos por vocal)')
    parser.add_argument('--voice', type=str, default='es-ES-ElviraNeural', 
                       help='Nombre de la voz Edge TTS (ej: es-ES-ElviraNeural)')
    parser.add_argument('--max-items', type=int, default=None,
                       help='Máximo número de segmentos por vocal')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SCRIPT 02: GENERACIÓN DE AUDIO CON EDGE TTS")
    print("=" * 60)
    
    # Inicializar generador
    generator = EdgeTTSGenerator(voice_name=args.voice)
    
    # Procesar todas las vocales
    results = generator.process_all_vocals(
        max_items_per_vocal=args.max_items,
        test_mode=args.test
    )
    
    # Guardar metadata
    metadata = {
        'fecha_generacion': datetime.now().isoformat(),
        'voz_utilizada': args.voice,
        'modo_prueba': args.test,
        'total_archivos_generados': sum(len(files) for files in results.values()),
        'archivos_por_vocal': {vocal: len(files) for vocal, files in results.items()},
        'directorio_salida': str(generator.raw_audio_dir)
    }
    
    metadata_path = generator.raw_audio_dir / "edge_tts_generation_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE GENERACIÓN EDGE TTS")
    print("=" * 60)
    
    total_files = 0
    for vocal, files in results.items():
        print(f"  {vocal}: {len(files)} archivos")
        total_files += len(files)
    
    print(f"\n  TOTAL: {total_files} archivos generados")
    print(f"  Metadata guardada en: {metadata_path.relative_to(generator.base_dir)}")
    print(f"  Audios guardados en: {generator.raw_audio_dir.relative_to(generator.base_dir)}/")
    
    print(f"\n✅ Generación de audio con Edge TTS completada exitosamente")
    print(f"   Total archivos generados: {total_files}")
    print(f"   Directorio: {generator.raw_audio_dir}")
    
    if total_files > 0:
        print(f"\nPrimeros archivos generados:")
        for vocal in ['A', 'E', 'I', 'O', 'U']:
            if results.get(vocal):
                first_file = Path(results[vocal][0]).name
                print(f"  {vocal}: {first_file}")
    
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