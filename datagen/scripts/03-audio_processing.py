#!/usr/bin/env python3
"""
Script para procesar archivos de audio:
1. Detectar actividad vocal (VAD)
2. Extraer segmentos de exactamente 0.3 segundos
3. Normalizar y convertir a 16000 Hz
4. Organizar en carpetas por vocal
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

try:
    import soundfile as sf
    import librosa
except ImportError:
    print("ERROR: soundfile o librosa no están instalados.")
    print("Instalar con: pip install soundfile librosa")
    sys.exit(1)

class AudioProcessor:
    """Procesador de audio para extraer segmentos de 0.3 segundos."""
    
    def __init__(self, target_duration=0.3, target_sr=16000, vad_threshold=0.01):
        """
        Inicializa el procesador de audio.
        
        Args:
            target_duration: Duración objetivo en segundos (0.3)
            target_sr: Tasa de muestreo objetivo (16000 Hz)
            vad_threshold: Umbral para detección de actividad vocal
        """
        self.target_duration = target_duration
        self.target_sr = target_sr
        self.vad_threshold = vad_threshold
        
        # Calcular número de muestras objetivo
        self.target_samples = int(target_duration * target_sr)
        
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Carga un archivo de audio.
        
        Args:
            audio_path: Ruta al archivo de audio
            
        Returns:
            Tupla (audio_data, sample_rate)
        """
        try:
            # Cargar audio
            audio, sr = librosa.load(audio_path, sr=None, mono=True)
            return audio, sr
        except Exception as e:
            print(f"  ❌ Error al cargar {audio_path}: {e}")
            return None, None
    
    def detect_voice_activity(self, audio: np.ndarray, sr: int) -> List[Tuple[int, int]]:
        """
        Detecta segmentos con actividad vocal usando energía RMS.
        
        Args:
            audio: Señal de audio
            sr: Tasa de muestreo
            
        Returns:
            Lista de tuplas (inicio_muestra, fin_muestra) para cada segmento
        """
        if audio is None or len(audio) == 0:
            return []
        
        # Calcular energía RMS en ventanas
        frame_length = int(0.025 * sr)  # 25ms
        hop_length = int(0.010 * sr)    # 10ms
        
        # Calcular RMS
        rms = librosa.feature.rms(
            y=audio, 
            frame_length=frame_length, 
            hop_length=hop_length
        )[0]
        
        # Normalizar RMS
        if rms.max() > 0:
            rms_normalized = rms / rms.max()
        else:
            rms_normalized = rms
        
        # Aplicar umbral
        voice_active = rms_normalized > self.vad_threshold
        
        # Encontrar segmentos activos
        segments = []
        in_segment = False
        start_idx = 0
        
        for i, active in enumerate(voice_active):
            if active and not in_segment:
                # Inicio de segmento
                in_segment = True
                start_idx = i
            elif not active and in_segment:
                # Fin de segmento
                in_segment = False
                end_idx = i
                
                # Convertir índices de frames a muestras
                start_sample = start_idx * hop_length
                end_sample = end_idx * hop_length
                
                # Asegurar que el segmento tenga al menos 0.1s
                segment_duration = (end_sample - start_sample) / sr
                if segment_duration >= 0.1:
                    segments.append((start_sample, end_sample))
        
        # Manejar segmento que termina al final del audio
        if in_segment:
            end_sample = len(audio)
            segment_duration = (end_sample - start_idx * hop_length) / sr
            if segment_duration >= 0.1:
                segments.append((start_idx * hop_length, end_sample))
        
        return segments
    
    def extract_best_segment(self, audio: np.ndarray, sr: int, 
                           segments: List[Tuple[int, int]]) -> Optional[np.ndarray]:
        """
        Extrae el mejor segmento de 0.3 segundos.
        
        Args:
            audio: Señal de audio
            sr: Tasa de muestreo
            segments: Segmentos detectados
            
        Returns:
            Segmento de audio de 0.3 segundos o None
        """
        if not segments:
            return None
        
        # Calcular energía de cada segmento
        segment_energies = []
        for start, end in segments:
            segment = audio[start:end]
            if len(segment) > 0:
                energy = np.sqrt(np.mean(segment**2))
                segment_energies.append((energy, start, end))
        
        if not segment_energies:
            return None
        
        # Seleccionar segmento con mayor energía
        segment_energies.sort(reverse=True)
        best_energy, best_start, best_end = segment_energies[0]
        
        # Calcular centro del segmento
        segment_center = (best_start + best_end) // 2
        
        # Calcular ventana de 0.3 segundos centrada
        half_samples = self.target_samples // 2
        target_start = segment_center - half_samples
        target_end = segment_center + half_samples
        
        # Ajustar si se sale de los límites del audio
        if target_start < 0:
            target_start = 0
            target_end = self.target_samples
        elif target_end > len(audio):
            target_end = len(audio)
            target_start = max(0, target_end - self.target_samples)
        
        # Extraer segmento
        segment = audio[target_start:target_end]
        
        # Asegurar longitud exacta
        if len(segment) < self.target_samples:
            # Rellenar con ceros si es necesario
            padding = self.target_samples - len(segment)
            segment = np.pad(segment, (0, padding), mode='constant')
        elif len(segment) > self.target_samples:
            # Recortar si es necesario
            segment = segment[:self.target_samples]
        
        return segment
    
    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normaliza el audio a amplitud máxima de 0.9.
        
        Args:
            audio: Señal de audio
            
        Returns:
            Audio normalizado
        """
        if len(audio) == 0:
            return audio
        
        # Encontrar valor máximo absoluto
        max_val = np.max(np.abs(audio))
        
        if max_val > 0:
            # Normalizar a 0.9 para evitar clipping
            normalized = audio * (0.9 / max_val)
            return normalized
        else:
            return audio
    
    def resample_audio(self, audio: np.ndarray, original_sr: int) -> np.ndarray:
        """
        Re-muestrea el audio a la tasa de muestreo objetivo.
        
        Args:
            audio: Señal de audio
            original_sr: Tasa de muestreo original
            
        Returns:
            Audio re-muestreado
        """
        if original_sr == self.target_sr:
            return audio
        
        # Re-muestrear usando librosa
        resampled = librosa.resample(
            y=audio, 
            orig_sr=original_sr, 
            target_sr=self.target_sr
        )
        
        return resampled
    
    def process_audio_file(self, input_path: str, output_dir: str, 
                          metadata: dict = None) -> Optional[dict]:
        """
        Procesa un archivo de audio completo.
        
        Args:
            input_path: Ruta al archivo de audio de entrada
            output_dir: Directorio base de salida
            metadata: Metadata del archivo (para determinar vocal)
            
        Returns:
            Metadata del archivo procesado o None si hay error
        """
        print(f"Procesando: {Path(input_path).name}")
        
        # Cargar audio
        audio, sr = self.load_audio(input_path)
        if audio is None:
            return None
        
        # Detectar actividad vocal
        segments = self.detect_voice_activity(audio, sr)
        
        if not segments:
            print(f"  ⚠️  No se detectó actividad vocal")
            return None
        
        # Extraer mejor segmento
        segment = self.extract_best_segment(audio, sr, segments)
        
        if segment is None:
            print(f"  ⚠️  No se pudo extraer segmento válido")
            return None
        
        # Normalizar
        segment = self.normalize_audio(segment)
        
        # Re-muestrear si es necesario
        if sr != self.target_sr:
            segment = self.resample_audio(segment, sr)
        
        # Determinar vocal para organización
        input_filename = Path(input_path).name
        vowel = self._determine_vowel(metadata, input_filename)
        
        # Crear directorio de salida para la vocal
        vowel_dir = Path(output_dir) / vowel
        vowel_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar nombre de archivo único
        # Usar microsegundos para evitar colisiones
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Incluir milisegundos
        # Extraer texto del nombre original (ej: "A_a_20260307_103004.wav" -> "a")
        original_text = 'unknown'
        if '_' in input_filename:
            parts = input_filename.split('_')
            if len(parts) >= 2:
                original_text = parts[1]  # El texto después de la vocal
        
        filename = f"{vowel}_{original_text}_{timestamp}.wav"
        output_path = vowel_dir / filename
        
        # Guardar archivo
        try:
            sf.write(str(output_path), segment, self.target_sr, subtype='PCM_16')
            
            # Calcular duración real
            duration = len(segment) / self.target_sr
            
            print(f"  ✅ Guardado: {filename} ({duration:.3f}s)")
            
            # Crear metadata del archivo procesado
            result_metadata = {
                'input_file': Path(input_path).name,
                'output_file': filename,
                'vowel': vowel,
                'consonant': consonant,
                'original_duration': len(audio) / sr,
                'processed_duration': duration,
                'sample_rate': self.target_sr,
                'output_path': str(output_path),
                'timestamp': datetime.now().isoformat(),
                'segments_detected': len(segments)
            }
            
            if metadata:
                result_metadata.update(metadata)
            
            return result_metadata
            
        except Exception as e:
            print(f"  ❌ Error al guardar: {e}")
            return None
    
    def _determine_vowel(self, metadata: dict, filename: str = "") -> str:
        """
        Determina la vocal a partir de la metadata o nombre de archivo.
        
        Args:
            metadata: Metadata del archivo
            filename: Nombre del archivo original
            
        Returns:
            Letra de la vocal (A, E, I, O, U) o 'unknown'
        """
        # Primero intentar desde metadata
        if metadata:
            vowel = metadata.get('vocal', '').upper()
            
            # Si es un grupo, usar primera vocal del grupo
            if vowel == 'GRUPO' and 'combinaciones_incluidas' in metadata:
                first_combo = metadata['combinaciones_incluidas'][0]
                # Extraer vocal del primer carácter (ej: "ba" -> "a")
                if len(first_combo) >= 2:
                    vowel = first_combo[-1].upper()
        
        # Si no se encontró en metadata, intentar desde el nombre del archivo
        if not vowel or vowel not in ['A', 'E', 'I', 'O', 'U']:
            # Buscar vocal en el nombre del archivo (ej: "A_a_20260307_103004.wav" -> "A")
            if filename:
                # El formato es: {vocal}_{texto}_{timestamp}.wav
                parts = filename.split('_')
                if parts and parts[0] in ['A', 'E', 'I', 'O', 'U']:
                    vowel = parts[0]
        
        # Validar que sea una vocal válida
        valid_vowels = ['A', 'E', 'I', 'O', 'U']
        if vowel in valid_vowels:
            return vowel
        else:
            return 'unknown'
    
    def process_batch(self, input_dir: str, output_dir: str, 
                     metadata_file: str = None, max_files: int = None) -> List[dict]:
        """
        Procesa un lote de archivos de audio.
        
        Args:
            input_dir: Directorio con archivos de audio de entrada
            output_dir: Directorio base de salida
            metadata_file: Archivo JSON con metadata (opcional)
            max_files: Número máximo de archivos a procesar
            
        Returns:
            Lista de metadata de archivos procesados
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"❌ Directorio de entrada no existe: {input_dir}")
            return []
        
        # Cargar metadata si está disponible
        metadata_dict = {}
        if metadata_file and Path(metadata_file).exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_data = json.load(f)
            
            # Crear diccionario por nombre de archivo
            if 'files' in metadata_data:
                for file_meta in metadata_data['files']:
                    filename = file_meta.get('filename', '')
                    if filename:
                        metadata_dict[filename] = file_meta
        
        # Listar archivos de audio
        audio_files = list(input_path.glob("*.wav"))
        if not audio_files:
            print(f"❌ No se encontraron archivos WAV en: {input_dir}")
            return []
        
        if max_files:
            audio_files = audio_files[:max_files]
        
        print(f"Procesando {len(audio_files)} archivos de audio...")
        
        # Procesar cada archivo
        results = []
        for i, audio_file in enumerate(audio_files, 1):
            print(f"\n[{i}/{len(audio_files)}]")
            
            # Obtener metadata para este archivo
            file_metadata = metadata_dict.get(audio_file.name, {})
            
            # Procesar archivo
            result = self.process_audio_file(
                input_path=str(audio_file),
                output_dir=output_dir,
                metadata=file_metadata
            )
            
            if result:
                results.append(result)
        
        # Guardar metadata de procesamiento
        if results:
            output_metadata = {
                'processing_date': datetime.now().isoformat(),
                'total_files_processed': len(audio_files),
                'successful_processing': len(results),
                'target_duration': self.target_duration,
                'target_sample_rate': self.target_sr,
                'processed_files': results
            }
            
            metadata_output = Path(output_dir) / "processing_metadata.json"
            with open(metadata_output, 'w', encoding='utf-8') as f:
                json.dump(output_metadata, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Metadata guardada en: {metadata_output}")
        
        return results

def main():
    """Función principal."""
    print("=" * 60)
    print("PROCESADOR DE AUDIO - EXTRACCIÓN DE SEGMENTOS 0.3s")
    print("=" * 60)
    
    # Configuración por defecto
    input_dir = "datagen/raw_audio"
    output_dir = "datagen/processed"
    metadata_file = "datagen/raw_audio/generation_metadata.json"
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    if len(sys.argv) > 3:
        metadata_file = sys.argv[3]
    
    # Verificar directorio de entrada
    if not Path(input_dir).exists():
        print(f"❌ Directorio de entrada no existe: {input_dir}")
        print("\nSugerencias:")
        print("1. Primero ejecuta generate_texts.py para crear textos")
        print("2. Luego ejecuta tts_generation.py para generar audio")
        print("3. Finalmente ejecuta este script para procesar el audio")
        return 1
    
    # Inicializar procesador
    print("\nInicializando procesador de audio...")
    processor = AudioProcessor(
        target_duration=0.3,
        target_sr=16000,
        vad_threshold=0.01
    )
    
    # Procesar lote de archivos
    print(f"\nProcesando archivos desde: {input_dir}")
    print(f"Guardando resultados en: {output_dir}")
    
    results = processor.process_batch(
        input_dir=input_dir,
        output_dir=output_dir,
        metadata_file=metadata_file,
        max_files=None  # Procesar todos
    )
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL PROCESAMIENTO")
    print("=" * 60)
    
    if results:
        # Contar por vocal
        vowel_counts = {}
        for result in results:
            vowel = result.get('vowel', 'unknown')
            vowel_counts[vowel] = vowel_counts.get(vowel, 0) + 1
        
        print(f"Archivos procesados exitosamente: {len(results)}")
        print("\nDistribución por vocal:")
        for vowel in ['A', 'E', 'I', 'O', 'U', 'unknown']:
            count = vowel_counts.get(vowel, 0)
            if count > 0:
                print(f"  {vowel}: {count} archivos")
        
        # Verificar duraciones
        durations = [r.get('processed_duration', 0) for r in results]
        if durations:
            avg_duration = np.mean(durations)
            min_duration = np.min(durations)
            max_duration = np.max(durations)
            
            print(f"\nEstadísticas de duración:")
            print(f"  Mínima: {min_duration:.3f}s")
            print(f"  Máxima: {max_duration:.3f}s")
            print(f"  Promedio: {avg_duration:.3f}s")
            
            # Verificar que las duraciones estén cerca de 0.3s
            tolerance = 0.01  # 10ms
            within_tolerance = sum(1 for d in durations if abs(d - 0.3) <= tolerance)
            print(f"  Dentro de tolerancia (±{tolerance}s): {within_tolerance}/{len(durations)}")
        
        print(f"\n✅ Procesamiento completado exitosamente")
        print(f"   Archivos procesados: {len(results)}")
        print(f"   Directorio de salida: {output_dir}")
        
        # Mostrar estructura de directorios creada
        print("\nEstructura de directorios creada:")
        output_path = Path(output_dir)
        if output_path.exists():
            for vowel_dir in output_path.iterdir():
                if vowel_dir.is_dir():
                    vowel_files = list(vowel_dir.glob("*.wav"))
                    print(f"  {vowel_dir.name}/: {len(vowel_files)} archivos")
    else:
        print("❌ No se procesó ningún archivo exitosamente")
        return 1
    
    return 0

def main():
    """Función principal."""
    print("=" * 60)
    print("PROCESADOR DE AUDIO - EXTRACCIÓN DE SEGMENTOS 0.3s")
    print("=" * 60)
    
    # Configuración por defecto
    input_dir = "datagen/raw_audio"
    output_dir = "datagen/processed"
    metadata_file = "datagen/raw_audio/generation_metadata.json"
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    if len(sys.argv) > 3:
        metadata_file = sys.argv[3]
    
    # Verificar directorio de entrada
    if not Path(input_dir).exists():
        print(f"❌ Directorio de entrada no existe: {input_dir}")
        print("\nSugerencias:")
        print("1. Primero ejecuta generate_texts.py para crear textos")
        print("2. Luego ejecuta tts_generation.py para generar audio")
        print("3. Finalmente ejecuta este script para procesar el audio")
        return 1
    
    # Inicializar procesador
    print("\nInicializando procesador de audio...")
    processor = AudioProcessor(
        target_duration=0.3,
        target_sr=16000,
        vad_threshold=0.01
    )
    
    # Procesar lote de archivos
    print(f"\nProcesando archivos desde: {input_dir}")
    print(f"Guardando resultados en: {output_dir}")
    
    results = processor.process_batch(
        input_dir=input_dir,
        output_dir=output_dir,
        metadata_file=metadata_file,
        max_files=None  # Procesar todos
    )
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL PROCESAMIENTO")
    print("=" * 60)
    
    if results:
        # Contar por vocal
        vowel_counts = {}
        for result in results:
            vowel = result.get('vowel', 'unknown')
            vowel_counts[vowel] = vowel_counts.get(vowel, 0) + 1
        
        print(f"Archivos procesados exitosamente: {len(results)}")
        print("\nDistribución por vocal:")
        for vowel in ['A', 'E', 'I', 'O', 'U', 'unknown']:
            count = vowel_counts.get(vowel, 0)
            if count > 0:
                print(f"  {vowel}: {count} archivos")
        
        # Verificar duraciones
        durations = [r.get('processed_duration', 0) for r in results]
        if durations:
            avg_duration = np.mean(durations)
            min_duration = np.min(durations)
            max_duration = np.max(durations)
            
            print(f"\nEstadísticas de duración:")
            print(f"  Mínima: {min_duration:.3f}s")
            print(f"  Máxima: {max_duration:.3f}s")
            print(f"  Promedio: {avg_duration:.3f}s")
            
            # Verificar que las duraciones estén cerca de 0.3s
            tolerance = 0.01  # 10ms
            within_tolerance = sum(1 for d in durations if abs(d - 0.3) <= tolerance)
            print(f"  Dentro de tolerancia (±{tolerance}s): {within_tolerance}/{len(durations)}")
        
        print(f"\n✅ Procesamiento completado exitosamente")
        print(f"   Archivos procesados: {len(results)}")
        print(f"   Directorio de salida: {output_dir}")
        
        # Mostrar estructura de directorios creada
        print("\nEstructura de directorios creada:")
        output_path = Path(output_dir)
        if output_path.exists():
            for vowel_dir in output_path.iterdir():
                if vowel_dir.is_dir():
                    vowel_files = list(vowel_dir.glob("*.wav"))
                    print(f"  {vowel_dir.name}/: {len(vowel_files)} archivos")
    else:
        print("❌ No se procesó ningún archivo exitosamente")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nProcesamiento cancelado por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)