#!/usr/bin/env python3
"""
Pipeline principal para generación de dataset de audio.
Orquesta todo el proceso: generación de textos, TTS, procesamiento y validación.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class AudioDatasetPipeline:
    """Pipeline completo para generación de dataset de audio."""
    
    def __init__(self, base_dir: str = "datagen"):
        """
        Inicializa el pipeline.
        
        Args:
            base_dir: Directorio base para todos los archivos
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Directorios
        self.dirs = {
            'raw_audio': self.base_dir / "raw_audio",
            'processed': self.base_dir / "processed",
            'scripts': self.base_dir / "scripts",
            'reports': self.base_dir / "reports"
        }
        
        # Crear directorios
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Crear subdirectorios de vocales
        for vowel in ['A', 'E', 'I', 'O', 'U']:
            (self.dirs['processed'] / vowel).mkdir(exist_ok=True)
        
        # Archivos
        self.files = {
            'combinaciones': self.base_dir / "combinaciones.json",
            'textos_individuales': self.base_dir / "textos_individuales.txt",
            'textos_grupos': self.base_dir / "textos_grupos.txt",
            'tts_metadata': self.dirs['raw_audio'] / "generation_metadata.json",
            'processing_metadata': self.dirs['processed'] / "processing_metadata.json"
        }
        
        # Resultados del pipeline
        self.results = {
            'pipeline_start': datetime.now().isoformat(),
            'steps': {},
            'status': 'not_started',
            'errors': [],
            'warnings': []
        }
    
    def log_step(self, step_name: str, status: str, message: str = "", 
                details: Dict = None):
        """Registra un paso del pipeline."""
        self.results['steps'][step_name] = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'message': message,
            'details': details or {}
        }
        
        status_symbol = "✅" if status == 'success' else "❌" if status == 'error' else "⚠️"
        print(f"{status_symbol} [{step_name}] {message}")
    
    def step_generate_texts(self, max_combinations: Optional[int] = None) -> bool:
        """Paso 1: Generar textos con combinaciones consonante-vocal."""
        print("\n" + "=" * 60)
        print("PASO 1: GENERACIÓN DE TEXTOS")
        print("=" * 60)
        
        try:
            # Importar módulo de generación de textos
            sys.path.insert(0, str(self.dirs['scripts'].parent))
            from generate_texts import (
                CONSONANTES_ESPANOL, VOCALES, COMBINACIONES_ESPECIALES,
                generar_combinaciones_basicas, generar_combinaciones_especiales,
                generar_textos_con_silencios, guardar_combinaciones_json,
                guardar_lista_textos
            )
            
            print(f"Consonantes españolas: {len(CONSONANTES_ESPANOL)}")
            print(f"Vocales: {len(VOCALES)}")
            print(f"Combinaciones especiales: {len(COMBINACIONES_ESPECIALES)}")
            
            # Generar combinaciones
            combinaciones_basicas = generar_combinaciones_basicas()
            combinaciones_especiales = generar_combinaciones_especiales()
            todas_combinaciones = combinaciones_basicas + combinaciones_especiales
            
            if max_combinations:
                todas_combinaciones = todas_combinaciones[:max_combinations]
                print(f"Limitado a {max_combinations} combinaciones (modo prueba)")
            
            print(f"Total combinaciones generadas: {len(todas_combinaciones)}")
            
            # Generar textos formateados
            textos_individuales = generar_textos_con_silencios(
                todas_combinaciones, formato='individual'
            )
            textos_grupos = generar_textos_con_silencios(
                combinaciones_basicas, formato='grupo'
            )
            
            # Guardar resultados
            guardar_combinaciones_json(
                todas_combinaciones, 
                str(self.files['combinaciones'])
            )
            guardar_lista_textos(
                textos_individuales,
                str(self.files['textos_individuales'])
            )
            guardar_lista_textos(
                textos_grupos,
                str(self.files['textos_grupos'])
            )
            
            self.log_step(
                'generate_texts',
                'success',
                f"Generadas {len(todas_combinaciones)} combinaciones",
                {
                    'total_combinations': len(todas_combinaciones),
                    'individual_texts': len(textos_individuales),
                    'group_texts': len(textos_grupos)
                }
            )
            
            return True
            
        except Exception as e:
            self.log_step(
                'generate_texts',
                'error',
                f"Error al generar textos: {str(e)}"
            )
            self.results['errors'].append(f"generate_texts: {str(e)}")
            return False
    
    def step_tts_generation(self, max_items: Optional[int] = None, 
                          use_groups: bool = False) -> bool:
        """Paso 2: Generar audio usando TTS de Windows."""
        print("\n" + "=" * 60)
        print("PASO 2: GENERACIÓN DE AUDIO CON TTS")
        print("=" * 60)
        
        try:
            # Determinar archivo de textos a usar
            if use_groups:
                texts_file = self.files['textos_grupos']
                print("Usando textos agrupados por consonante")
            else:
                texts_file = self.files['textos_individuales']
                print("Usando textos individuales")
            
            if not texts_file.exists():
                self.log_step(
                    'tts_generation',
                    'error',
                    f"Archivo de textos no encontrado: {texts_file}"
                )
                return False
            
            # Importar módulo TTS
            sys.path.insert(0, str(self.dirs['scripts'].parent))
            from tts_generation import WindowsTTSGenerator
            
            print(f"Archivo de textos: {texts_file.name}")
            print(f"Directorio de salida: {self.dirs['raw_audio']}")
            
            if max_items:
                print(f"Límite: {max_items} textos (modo prueba)")
            
            # Inicializar generador TTS
            tts = WindowsTTSGenerator(output_dir=str(self.dirs['raw_audio']))
            
            # Procesar textos
            metadata_file = str(self.files['combinaciones']) if self.files['combinaciones'].exists() else None
            
            resultados = tts.process_text_list(
                texts_file=str(texts_file),
                metadata_file=metadata_file,
                max_items=max_items
            )
            
            if resultados:
                self.log_step(
                    'tts_generation',
                    'success',
                    f"Generados {len(resultados)} archivos de audio",
                    {
                        'audio_files_generated': len(resultados),
                        'output_dir': str(self.dirs['raw_audio'])
                    }
                )
                return True
            else:
                self.log_step(
                    'tts_generation',
                    'error',
                    "No se generaron archivos de audio"
                )
                return False
            
        except Exception as e:
            self.log_step(
                'tts_generation',
                'error',
                f"Error en generación TTS: {str(e)}"
            )
            self.results['errors'].append(f"tts_generation: {str(e)}")
            return False
    
    def step_audio_processing(self, max_files: Optional[int] = None) -> bool:
        """Paso 3: Procesar audio - extraer segmentos de 0.3 segundos."""
        print("\n" + "=" * 60)
        print("PASO 3: PROCESAMIENTO DE AUDIO")
        print("=" * 60)
        
        try:
            # Verificar que hay archivos de audio
            audio_files = list(self.dirs['raw_audio'].glob("*.wav"))
            if not audio_files:
                self.log_step(
                    'audio_processing',
                    'error',
                    "No se encontraron archivos de audio para procesar"
                )
                return False
            
            print(f"Archivos de audio encontrados: {len(audio_files)}")
            
            if max_files:
                audio_files = audio_files[:max_files]
                print(f"Limitado a {max_files} archivos (modo prueba)")
            
            # Importar módulo de procesamiento
            sys.path.insert(0, str(self.dirs['scripts'].parent))
            from audio_processing import AudioProcessor
            
            # Inicializar procesador
            processor = AudioProcessor(
                target_duration=0.3,
                target_sr=16000,
                vad_threshold=0.01
            )
            
            # Procesar archivos
            metadata_file = str(self.files['tts_metadata']) if self.files['tts_metadata'].exists() else None
            
            resultados = processor.process_batch(
                input_dir=str(self.dirs['raw_audio']),
                output_dir=str(self.dirs['processed']),
                metadata_file=metadata_file,
                max_files=max_files
            )
            
            if resultados:
                # Contar por vocal
                vowel_counts = {}
                for result in resultados:
                    vowel = result.get('vowel', 'unknown')
                    vowel_counts[vowel] = vowel_counts.get(vowel, 0) + 1
                
                self.log_step(
                    'audio_processing',
                    'success',
                    f"Procesados {len(resultados)} archivos",
                    {
                        'files_processed': len(resultados),
                        'vowel_distribution': vowel_counts,
                        'output_dir': str(self.dirs['processed'])
                    }
                )
                return True
            else:
                self.log_step(
                    'audio_processing',
                    'error',
                    "No se procesaron archivos exitosamente"
                )
                return False
            
        except Exception as e:
            self.log_step(
                'audio_processing',
                'error',
                f"Error en procesamiento de audio: {str(e)}"
            )
            self.results['errors'].append(f"audio_processing: {str(e)}")
            return False
    
    def step_validation(self) -> bool:
        """Paso 4: Validar calidad del dataset generado."""
        print("\n" + "=" * 60)
        print("PASO 4: VALIDACIÓN DEL DATASET")
        print("=" * 60)
        
        try:
            # Verificar que hay archivos procesados
            processed_files = []
            for vowel in ['A', 'E', 'I', 'O', 'U']:
                vowel_dir = self.dirs['processed'] / vowel
                if vowel_dir.exists():
                    processed_files.extend(list(vowel_dir.glob("*.wav")))
            
            if not processed_files:
                self.log_step(
                    'validation',
                    'error',
                    "No se encontraron archivos procesados para validar"
                )
                return False
            
            print(f"Archivos procesados encontrados: {len(processed_files)}")
            
            # Importar módulo de validación
            sys.path.insert(0, str(self.dirs['scripts'].parent))
            from validate_dataset import DatasetValidator
            
            # Inicializar validador
            validator = DatasetValidator(
                target_duration=0.3,
                target_sr=16000,
                tolerance=0.01
            )
            
            # Validar dataset
            results = validator.validate_directory(str(self.dirs['processed']))
            
            # Generar reporte
            report_path = validator.generate_report(str(self.dirs['reports']))
            
            # Evaluar resultados
            if results['total_files'] > 0:
                valid_percent = (results['valid_files'] / results['total_files']) * 100
                
                self.log_step(
                    'validation',
                    'success' if valid_percent >= 80 else 'warning',
                    f"Validación completada: {valid_percent:.1f}% válidos",
                    {
                        'total_files': results['total_files'],
                        'valid_files': results['valid_files'],
                        'invalid_files': results['invalid_files'],
                        'valid_percent': valid_percent,
                        'report_path': report_path
                    }
                )
                
                if valid_percent < 80:
                    self.results['warnings'].append(
                        f"Solo {valid_percent:.1f}% de archivos válidos (objetivo: 80%+)"
                    )
                
                return valid_percent >= 50  # Considerar éxito si al menos 50% válidos
            else:
                self.log_step(
                    'validation',
                    'error',
                    "No se validaron archivos"
                )
                return False
            
        except Exception as e:
            self.log_step(
                'validation',
                'error',
                f"Error en validación: {str(e)}"
            )
            self.results['errors'].append(f"validation: {str(e)}")
            return False
    
    def run_pipeline(self, steps: List[str] = None, test_mode: bool = False) -> bool:
        """
        Ejecuta el pipeline completo o pasos específicos.
        
        Args:
            steps: Lista de pasos a ejecutar (None = todos)
            test_mode: Modo prueba con límites reducidos
            
        Returns:
            True si el pipeline fue exitoso
        """
        print("=" * 60)
        print("PIPELINE DE GENERACIÓN DE DATASET DE AUDIO")
        print("=" * 60)
        print(f"Directorio base: {self.base_dir}")
        print(f"Modo prueba: {'Sí' if test_mode else 'No'}")
        print(f"Pasos a ejecutar: {steps or 'todos'}")
        print("=" * 60)
        
        # Definir pasos disponibles
        available_steps = {
            'generate_texts': self.step_generate_texts,
            'tts_generation': self.step_tts_generation,
            'audio_processing': self.step_audio_processing,
            'validation': self.step_validation
        }
        
        # Determinar qué pasos ejecutar
        if steps is None:
            steps_to_run = list(available_steps.keys())
        else:
            steps_to_run = [s for s in steps if s in available_steps]
        
        if not steps_to_run:
            print("❌ No hay pasos válidos para ejecutar")
            return False
        
        # Parámetros para modo prueba
        test_params = {
            'max_combinations': 10 if test_mode else None,
            'max_items': 5 if test_mode else None,
            'max_files': 5 if test_mode else None
        }
        
        # Ejecutar pasos en orden
        success = True
        for step_name in steps_to_run:
            step_func = available_steps[step_name]
            
            # Ejecutar paso con parámetros apropiados
            if step_name == 'generate_texts':
                step_success = step_func(test_params['max_combinations'])
            elif step_name == 'tts_generation':
                step_success = step_func(test_params['max_items'])
            elif step_name == 'audio_processing':
                step_success = step_func(test_params['max_files'])
            elif step_name == 'validation':
                step_success = step_func()
            else:
                step_success = step_func()
            
            if not step_success:
                success = False
                print(f"\n⚠️  Paso '{step_name}' falló. Continuando...")
                # Continuar con siguiente paso a menos que sea crítico
                if step_name in ['generate_texts', 'tts_generation']:
                    print(f"❌ Paso crítico '{step_name}' falló. Deteniendo pipeline.")
                    break
        
        # Finalizar pipeline
        self.results['pipeline_end'] = datetime.now().isoformat()
        self.results['status'] = 'success' if success else 'partial' if any(
            s['status'] == 'success' for s in self.results['steps'].values()
        ) else 'failed'
        
        # Guardar resultados
        results_file = self.dirs['reports'] / f"pipeline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # Mostrar resumen
        print("\n" + "=" * 60)
        print("RESUMEN DEL PIPELINE")
        print("=" * 60)
        
        for step_name, step_info in self.results['steps'].items():
            status_symbol = "✅" if step_info['status'] == 'success' else "❌" if step_info['status'] == 'error' else "⚠️"
            print(f"{status_symbol} {step_name}: {step_info['message']}")
        
        print(f"\n📊 Estado final: {self.results['status'].upper()}")
        print(f"📄 Resultados guardados en: {results_file}")
        
        if self.results['errors']:
            print(f"\n❌ Errores encontrados ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:  # Mostrar solo primeros 5
                print(f"  - {error}")
    
    if self.results['warnings']:
        print(f"\n⚠️  Advertencias ({len(self.results['warnings'])}):")
        for warning in self.results['warnings'][:5]:  # Mostrar solo primeros 5
            print(f"  - {warning}")
    
    # Mostrar estructura del dataset generado
    if self.dirs['processed'].exists():
        print(f"\n📁 Estructura del dataset generado:")
        print(f"  {self.base_dir}/")
        print(f"  ├── raw_audio/     # Audios crudos de TTS")
        print(f"  ├── processed/     # Audios procesados de 0.3s")
        
        for vowel in ['A', 'E', 'I', 'O', 'U']:
            vowel_dir = self.dirs['processed'] / vowel
            if vowel_dir.exists():
                file_count = len(list(vowel_dir.glob("*.wav")))
                print(f"  │   ├── {vowel}/      # {file_count} archivos")
        
        print(f"  ├── scripts/       # Scripts de generación")
        print(f"  └── reports/       # Reportes de validación")
    
    return success

def main():
"""Función principal del pipeline."""
parser = argparse.ArgumentParser(
    description='Pipeline para generación de dataset de audio con TTS de Windows'
)

parser.add_argument(
    '--steps',
    nargs='+',
    choices=['generate_texts', 'tts_generation', 'audio_processing', 'validation'],
    help='Pasos específicos a ejecutar (por defecto: todos)'
)

parser.add_argument(
    '--test',
    action='store_true',
    help='Ejecutar en modo prueba (límites reducidos)'
)

parser.add_argument(
    '--base-dir',
    default='datagen',
    help='Directorio base para el dataset (por defecto: datagen)'
)

parser.add_argument(
    '--use-groups',
    action='store_true',
    help='Usar textos agrupados en lugar de individuales para TTS'
)

args = parser.parse_args()

# Inicializar pipeline
pipeline = AudioDatasetPipeline(base_dir=args.base_dir)

# Configurar uso de grupos si se especificó
if args.use_groups:
    # Sobrescribir método para usar grupos
    original_tts_method = pipeline.step_tts_generation
    
    def tts_with_groups(max_items=None):
        return original_tts_method(max_items, use_groups=True)
    
    pipeline.step_tts_generation = tts_with_groups

# Ejecutar pipeline
success = pipeline.run_pipeline(steps=args.steps, test_mode=args.test)

# Código de salida
return 0 if success else 1

if __name__ == "__main__":
try:
    exit_code = main()
    sys.exit(exit_code)
except KeyboardInterrupt:
    print("\n\nPipeline cancelado por el usuario.")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error inesperado en el pipeline: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
