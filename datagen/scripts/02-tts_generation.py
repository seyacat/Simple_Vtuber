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
    
    def __init__(self, base_dir="datagen", voice_name=None, use_all_spanish_voices=False):
        """
        Inicializa el generador Edge TTS.
        
        Args:
            base_dir: Directorio base del proyecto
            voice_name: Nombre de la voz a usar (ej: "es-ES-ElviraNeural")
            use_all_spanish_voices: Si es True, usa todas las voces en español disponibles
        """
        self.base_dir = Path(base_dir)
        self.raw_audio_dir = self.base_dir / "raw_audio_edge"
        self.raw_audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Obtener voces disponibles
        self.spanish_voices = self._get_spanish_voices()
        
        # Configurar voz/voces
        self.use_all_spanish_voices = use_all_spanish_voices
        if use_all_spanish_voices:
            print(f"Usando TODAS las voces en español: {len(self.spanish_voices)} voces")
            self.voice_name = None  # Se rotará entre voces
        else:
            self.voice_name = voice_name or "es-ES-ElviraNeural"
            print(f"Voz seleccionada: {self.voice_name}")
        
        # Configurar parámetros
        self.rate = "+0%"  # Velocidad normal
        self.volume = "+0%"  # Volumen normal
    
    def _get_spanish_voices(self):
        """Obtiene todas las voces en español disponibles en Edge TTS."""
        try:
            import edge_tts
            # edge_tts.list_voices() es async, necesitamos ejecutarlo en un event loop
            async def get_voices_async():
                voices = await edge_tts.list_voices()
                spanish_voices = [
                    voice for voice in voices
                    if voice['Locale'].startswith('es-') and 'Neural' in voice['ShortName']
                ]
                # Ordenar por nombre
                spanish_voices.sort(key=lambda x: x['ShortName'])
                return spanish_voices
            
            # Ejecutar el async function
            return asyncio.run(get_voices_async())
        except Exception as e:
            print(f"Error obteniendo voces: {e}")
            # Voces por defecto si falla
            return [
                {'ShortName': 'es-ES-AlvaroNeural', 'Locale': 'es-ES', 'Gender': 'Male'},
                {'ShortName': 'es-ES-ElviraNeural', 'Locale': 'es-ES', 'Gender': 'Female'},
                {'ShortName': 'es-MX-DaliaNeural', 'Locale': 'es-MX', 'Gender': 'Female'},
                {'ShortName': 'es-MX-JorgeNeural', 'Locale': 'es-MX', 'Gender': 'Male'},
                {'ShortName': 'es-AR-ElenaNeural', 'Locale': 'es-AR', 'Gender': 'Female'},
                {'ShortName': 'es-AR-TomasNeural', 'Locale': 'es-AR', 'Gender': 'Male'},
                {'ShortName': 'es-CL-CatalinaNeural', 'Locale': 'es-CL', 'Gender': 'Female'},
                {'ShortName': 'es-CL-LorenzoNeural', 'Locale': 'es-CL', 'Gender': 'Male'},
                {'ShortName': 'es-CO-GonzaloNeural', 'Locale': 'es-CO', 'Gender': 'Male'},
                {'ShortName': 'es-CO-SalomeNeural', 'Locale': 'es-CO', 'Gender': 'Female'},
            ]
        
    async def text_to_wav_async(self, text, filename, sample_rate=16000, voice_name=None):
        """
        Convierte texto a archivo WAV usando Edge TTS (async).
        
        Args:
            text: Texto a sintetizar
            filename: Nombre del archivo de salida (sin extensión)
            sample_rate: Tasa de muestreo deseada (Hz)
            voice_name: Nombre de la voz a usar (None = usar la voz por defecto o rotar)
            
        Returns:
            Ruta al archivo generado o None si hay error
        """
        try:
            # Determinar qué voz usar
            if voice_name is None:
                if self.use_all_spanish_voices:
                    # Rotar entre voces - usar la primera disponible
                    voice_name = self.spanish_voices[0]['ShortName']
                else:
                    voice_name = self.voice_name
            
            # Crear communicator
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_name,
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
            print(f"  ❌ Error generando audio con voz {voice_name}: {e}")
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
        Procesa un archivo de texto de una vocal (async) con procesamiento paralelo.
        Si use_all_spanish_voices es True, genera CADA segmento con TODAS las voces.
        
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
        
        # Si estamos usando todas las voces, mostrar información
        if self.use_all_spanish_voices:
            print(f"  Generando CADA segmento con TODAS las {len(self.spanish_voices)} voces en español")
            print(f"  Total de archivos a generar: {len(segments) * len(self.spanish_voices)}")
        
        # Función para procesar un segmento con una voz específica
        async def process_segment_with_voice(segment, segment_index, total_segments, voice_index, total_voices):
            # Crear nombre de archivo único con milisegundos
            safe_segment = segment.replace(' ', '_').replace('.', '')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Incluye milisegundos
            
            # Determinar qué voz usar
            voice_name = None
            if self.use_all_spanish_voices and voice_index is not None:
                voice_idx = voice_index % len(self.spanish_voices)
                voice_name = self.spanish_voices[voice_idx]['ShortName']
                filename = f"{vocal}_{safe_segment}_{voice_idx:03d}_{timestamp}"
                voice_info = f" (voz: {voice_name.split('-')[-1]})"
            else:
                filename = f"{vocal}_{safe_segment}_{timestamp}"
                voice_info = ""
            
            task_index = segment_index * total_voices + voice_index + 1
            total_tasks = total_segments * total_voices
            
            print(f"  [{task_index}/{total_tasks}] Segmento: '{segment}'{voice_info}")
            print(f"  Generando: '{segment}...' -> {filename}.wav")
            
            # Generar audio
            output_path = await self.text_to_wav_async(segment, filename, voice_name=voice_name)
            
            if output_path and output_path.exists():
                print(f"  ✅ [{task_index}/{total_tasks}] Archivo creado: {output_path.name}")
                return str(output_path)
            else:
                print(f"  ❌ [{task_index}/{total_tasks}] Error creando archivo para: {segment}")
                return None
        
        generated_files = []
        
        if self.use_all_spanish_voices:
            # Generar CADA segmento con TODAS las voces
            total_segments = len(segments)
            total_voices = len(self.spanish_voices)
            total_tasks = total_segments * total_voices
            
            # Procesar en lotes de 10 (paralelo simultáneo)
            batch_size = 10
            
            # Crear lista de todas las tareas (segmento × voz)
            all_tasks = []
            for segment_index, segment in enumerate(segments):
                for voice_index in range(total_voices):
                    all_tasks.append((segment, segment_index, voice_index))
            
            # Procesar por lotes
            for batch_start in range(0, len(all_tasks), batch_size):
                batch_end = min(batch_start + batch_size, len(all_tasks))
                current_batch = all_tasks[batch_start:batch_end]
                batch_number = (batch_start // batch_size) + 1
                total_batches = (len(all_tasks) + batch_size - 1) // batch_size
                
                print(f"\n  --- Lote {batch_number}/{total_batches} ({len(current_batch)} tareas) ---")
                
                # Crear y ejecutar tareas para el lote actual simultáneamente
                tasks = []
                for segment, segment_index, voice_index in current_batch:
                    task = process_segment_with_voice(
                        segment, segment_index, total_segments, voice_index, total_voices
                    )
                    tasks.append(task)
                
                # Ejecutar todas las tareas del lote simultáneamente
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Procesar resultados
                for result in batch_results:
                    if isinstance(result, Exception):
                        print(f"  ❌ Error en tarea: {result}")
                    elif result is not None:
                        generated_files.append(result)
        else:
            # Modo original: un segmento, una voz
            total_segments = len(segments)
            
            # Procesar en lotes de 10 (paralelo simultáneo)
            batch_size = 10
            
            # Procesar por lotes
            for batch_start in range(0, total_segments, batch_size):
                batch_end = min(batch_start + batch_size, total_segments)
                current_batch = segments[batch_start:batch_end]
                batch_number = (batch_start // batch_size) + 1
                total_batches = (total_segments + batch_size - 1) // batch_size
                
                print(f"\n  --- Lote {batch_number}/{total_batches} ({len(current_batch)} segmentos) ---")
                
                # Crear y ejecutar tareas para el lote actual simultáneamente
                tasks = []
                for i, segment in enumerate(current_batch, 1):
                    global_index = batch_start + i
                    task = process_segment_with_voice(
                        segment, global_index - 1, total_segments, None, 1
                    )
                    tasks.append(task)
                
                # Ejecutar todas las tareas del lote simultáneamente
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Procesar resultados
                for result in batch_results:
                    if isinstance(result, Exception):
                        print(f"  ❌ Error en tarea: {result}")
                    elif result is not None:
                        generated_files.append(result)
        
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
    parser.add_argument('--max-items', type=int, default=None,
                       help='Máximo número de segmentos por vocal')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SCRIPT 02: GENERACIÓN DE AUDIO CON EDGE TTS")
    print("=" * 60)
    
    # Obtener directorio base (datagen/) relativo al script
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent  # datagen/
    
    # Inicializar generador - SIEMPRE usa todas las voces
    generator = EdgeTTSGenerator(
        base_dir=base_dir,
        voice_name=None,  # No se usa cuando use_all_spanish_voices=True
        use_all_spanish_voices=True
    )
    
    # Mostrar información de voces
    print(f"✅ Usando TODAS las voces en español ({len(generator.spanish_voices)} voces)")
    print("  Las voces se distribuirán entre los segmentos de forma rotativa")
    
    # Procesar todas las vocales
    results = generator.process_all_vocals(
        max_items_per_vocal=args.max_items,
        test_mode=args.test
    )
    
    # Guardar metadata
    metadata = {
        'fecha_generacion': datetime.now().isoformat(),
        'uso_todas_las_voces': True,
        'total_voces_disponibles': len(generator.spanish_voices),
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