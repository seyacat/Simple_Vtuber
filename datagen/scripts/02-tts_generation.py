#!/usr/bin/env python3
"""
Script 02: Generar audio usando Edge TTS.
Genera 2000 muestras por vocal (A, E, I, O, U) con variaciones automáticas:
- Todas las voces en español disponibles (45+ voces)
- Volumen variado entre 80% y 100%
- Pitch con variaciones racionales (-20Hz a +20Hz)
- Procesamiento paralelo en lotes de 10
No requiere parámetros, ejecuta con configuración por defecto.
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
        
        # Configurar parámetros base (se variarán para generar 2000 muestras)
        self.rate = "+0%"  # Velocidad normal (fija)
        self.base_volume = "+0%"  # Volumen base
        self.base_pitch = "+0Hz"  # Tono base
        
        # Configurar variaciones para generar 2000 muestras por vocal
        self.samples_per_vocal = 2000
        self.volume_range = (80, 100)  # 80% a 100%
        self.pitch_variations = [-20, -10, 0, 10, 20]  # Variaciones en Hz
    
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
        
    async def text_to_wav_async(self, text, filename, sample_rate=16000, voice_name=None, pitch="+0Hz", volume="+0%"):
        """
        Convierte texto a archivo WAV usando Edge TTS (async).
        
        Args:
            text: Texto a sintetizar
            filename: Nombre del archivo de salida (sin extensión)
            sample_rate: Tasa de muestreo deseada (Hz)
            voice_name: Nombre de la voz a usar (None = usar la voz por defecto o rotar)
            pitch: Parámetro de tono (ej: "+0Hz", "+10Hz", "-10Hz")
            volume: Parámetro de volumen (ej: "+0%", "+10%", "-10%")
            
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
                volume=volume,
                pitch=pitch
            )
            
            # Configurar archivo de salida
            output_path = self.raw_audio_dir / f"{filename}.wav"
            
            # Guardar audio
            await communicate.save(str(output_path))
            
            # Edge TTS genera archivos a 24kHz, necesitamos verificar/convertir
            # La conversión a 16kHz se hará en el procesamiento de audio
            return output_path
            
        except Exception as e:
            print(f"  [ERROR] Error generando audio con voz {voice_name}: {e}")
            return None
    
    def text_to_wav(self, text, filename, sample_rate=16000, voice_name=None, pitch="+0Hz", volume="+0%"):
        """
        Versión síncrona de text_to_wav.
        
        Args:
            text: Texto a sintetizar
            filename: Nombre del archivo de salida (sin extensión)
            sample_rate: Tasa de muestreo deseada (Hz)
            voice_name: Nombre de la voz a usar
            pitch: Parámetro de tono
            volume: Parámetro de volumen
            
        Returns:
            Ruta al archivo generado o None si hay error
        """
        return asyncio.run(self.text_to_wav_async(text, filename, sample_rate, voice_name, pitch, volume))
    
    async def process_vocal_file_async(self, vocal, text_file_path, max_items=None):
        """
        Procesa un archivo de texto de una vocal (async) con procesamiento paralelo.
        Genera 2000 muestras por vocal con variaciones en voces, pitch y volumen.
        
        Args:
            vocal: Vocal ('A', 'E', 'I', 'O', 'U')
            text_file_path: Ruta al archivo de texto
            max_items: Máximo número de segmentos a procesar (None = todos, ignorado para 2000 muestras)
            
        Returns:
            Lista de archivos generados
        """
        print(f"\nProcesando vocal {vocal}: {text_file_path.name}")
        print(f"  Objetivo: {self.samples_per_vocal} muestras con variaciones en voces, pitch y volumen")
        
        # Leer archivo de texto
        with open(text_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Separar por puntos para obtener segmentos individuales
        segments = [s.strip() for s in content.split('.') if s.strip()]
        
        if not segments:
            print(f"  [ERROR] No hay segmentos en el archivo")
            return []
        
        # Usar solo el primer segmento (la vocal)
        segment = segments[0]
        print(f"  Segmento: '{segment}'")
        
        # Generar combinaciones de parámetros
        import random
        
        # Todas las voces disponibles
        voices = [v['ShortName'] for v in self.spanish_voices]
        
        # Generar variaciones de volumen (80% a 100%)
        volume_values = [f"+{v}%" for v in range(self.volume_range[0], self.volume_range[1] + 1, 2)]  # Cada 2%
        
        # Generar variaciones de pitch (Edge TTS requiere formato como "+20Hz", "-10Hz")
        pitch_values = []
        for p in self.pitch_variations:
            if p > 0:
                pitch_values.append(f"+{p}Hz")
            elif p < 0:
                pitch_values.append(f"{p}Hz")  # Ya incluye el signo negativo
            else:
                pitch_values.append("+0Hz")  # 0 necesita signo positivo
        
        print(f"  Voces disponibles: {len(voices)}")
        print(f"  Variaciones de volumen: {len(volume_values)} (de {self.volume_range[0]}% a {self.volume_range[1]}%)")
        print(f"  Variaciones de pitch: {len(pitch_values)}")
        
        # Calcular combinaciones totales
        total_combinations = len(voices) * len(volume_values) * len(pitch_values)
        print(f"  Combinaciones posibles: {total_combinations}")
        
        # Si hay menos combinaciones que muestras requeridas, repetiremos algunas
        if total_combinations < self.samples_per_vocal:
            print(f"  [WARN] Combinaciones insuficientes, se repetirán algunas para alcanzar {self.samples_per_vocal}")
        
        # Crear lista de todas las combinaciones posibles
        all_combinations = []
        for voice in voices:
            for volume in volume_values:
                for pitch in pitch_values:
                    all_combinations.append((voice, volume, pitch))
        
        # Mezclar combinaciones para diversidad
        random.shuffle(all_combinations)
        
        # Seleccionar o repetir combinaciones para alcanzar el objetivo
        selected_combinations = []
        for i in range(self.samples_per_vocal):
            combo_idx = i % len(all_combinations)
            selected_combinations.append(all_combinations[combo_idx])
        
        print(f"  Total muestras a generar: {len(selected_combinations)}")
        
        # Función para procesar una combinación
        async def process_combination(combo_index, voice, volume, pitch):
            # Crear nombre de archivo único
            safe_segment = segment.replace(' ', '_').replace('.', '')
            voice_short = voice.split('-')[-1].replace('Neural', '')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            
            # Nombre descriptivo con parámetros
            filename = f"{vocal}_{safe_segment}_{voice_short}_v{volume.replace('+', '').replace('%', '')}_p{pitch.replace('Hz', '')}_{timestamp}"
            
            task_index = combo_index + 1
            total_tasks = len(selected_combinations)
            
            print(f"  [{task_index}/{total_tasks}] Vocal: '{segment}' | Voz: {voice_short} | Vol: {volume} | Pitch: {pitch}")
            
            # Generar audio con parámetros específicos
            output_path = await self.text_to_wav_async(
                segment,
                filename,
                voice_name=voice,
                pitch=pitch,
                volume=volume
            )
            
            if output_path and output_path.exists():
                print(f"  [OK] [{task_index}/{total_tasks}] Archivo creado: {output_path.name}")
                return str(output_path)
            else:
                print(f"  [ERROR] [{task_index}/{total_tasks}] Error creando archivo")
                return None
        
        generated_files = []
        
        # Procesar en lotes de 10 (paralelo simultáneo)
        batch_size = 100
        
        # Procesar por lotes
        for batch_start in range(0, len(selected_combinations), batch_size):
            batch_end = min(batch_start + batch_size, len(selected_combinations))
            current_batch = selected_combinations[batch_start:batch_end]
            batch_number = (batch_start // batch_size) + 1
            total_batches = (len(selected_combinations) + batch_size - 1) // batch_size
            
            print(f"\n  --- Lote {batch_number}/{total_batches} ({len(current_batch)} muestras) ---")
            
            # Crear y ejecutar tareas para el lote actual simultáneamente
            tasks = []
            for i, (voice, volume, pitch) in enumerate(current_batch):
                combo_index = batch_start + i
                task = process_combination(combo_index, voice, volume, pitch)
                tasks.append(task)
            
            # Ejecutar todas las tareas del lote simultáneamente
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            for result in batch_results:
                    if isinstance(result, Exception):
                        print(f"  [ERROR] Error en tarea: {result}")
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
            max_items_per_vocal: Máximo de segmentos por vocal (ignorado en nuevo modo)
            test_mode: Si es True, genera menos muestras para prueba
            
        Returns:
            Diccionario con resultados
        """
        if test_mode:
            # En modo prueba, generar solo 10 muestras por vocal
            original_samples = self.samples_per_vocal
            self.samples_per_vocal = 10
            print("[WARN] MODO PRUEBA ACTIVADO (10 muestras por vocal)")
        
        print("\n" + "=" * 40)
        print("PROCESANDO TODAS LAS VOCALES CON EDGE TTS")
        print("=" * 40)
        print(f"Generando {self.samples_per_vocal} muestras por vocal")
        
        vocals = ['A', 'E', 'I', 'O', 'U']
        results = {}
        
        for vocal in vocals:
            text_file_path = self.base_dir / "processed" / vocal / f"{vocal}.txt"
            
            if not text_file_path.exists():
                print(f"[ERROR] Archivo no encontrado: {text_file_path}")
                results[vocal] = []
                continue
            
            print(f"\n{'=' * 8}")
            print(f"VOCAL: {vocal}")
            print(f"{'=' * 8}")
            
            # max_items_per_vocal es ignorado en el nuevo modo
            files = await self.process_vocal_file_async(vocal, text_file_path, None)
            
            results[vocal] = files
            print(f"  [OK] Vocal {vocal}: {len(files)} archivos generados")
        
        # Restaurar valor original si estábamos en modo prueba
        if test_mode:
            self.samples_per_vocal = original_samples
        
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
    print("GENERANDO 2000 MUESTRAS POR VOCAL CON VARIACIONES AUTOMÁTICAS")
    print("  • Todas las voces en español")
    print("  • Volumen: 80% a 100%")
    print("  • Pitch: variaciones racionales")
    
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
    print(f"\n[OK] Usando TODAS las voces en español ({len(generator.spanish_voices)} voces)")
    print(f"[OK] Generando {generator.samples_per_vocal} muestras por vocal")
    print(f"[OK] Rango de volumen: {generator.volume_range[0]}% a {generator.volume_range[1]}%")
    print(f"[OK] Variaciones de pitch: {generator.pitch_variations} Hz")
    
    # Procesar todas las vocales
    results = generator.process_all_vocals(
        max_items_per_vocal=args.max_items,
        test_mode=args.test
    )
    
    # Guardar metadata
    metadata = {
        'fecha_generacion': datetime.now().isoformat(),
        'configuracion_generacion': {
            'muestras_por_vocal': generator.samples_per_vocal,
            'uso_todas_las_voces': True,
            'total_voces_disponibles': len(generator.spanish_voices),
            'rango_volumen': f"{generator.volume_range[0]}% a {generator.volume_range[1]}%",
            'variaciones_pitch': generator.pitch_variations,
            'rate_fijo': generator.rate
        },
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
    
    print(f"\n[OK] Generación de audio con Edge TTS completada exitosamente")
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
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)