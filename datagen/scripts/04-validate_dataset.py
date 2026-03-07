#!/usr/bin/env python3
"""
Script para validar la calidad del dataset generado.
Verifica duraciones, sample rates, formato y estructura.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

try:
    import soundfile as sf
    import librosa
except ImportError:
    print("ERROR: soundfile o librosa no están instalados.")
    print("Instalar con: pip install soundfile librosa")
    sys.exit(1)

class DatasetValidator:
    """Validador de dataset de audio."""
    
    def __init__(self, target_duration=0.3, target_sr=16000, tolerance=0.01):
        """
        Inicializa el validador.
        
        Args:
            target_duration: Duración objetivo en segundos (0.3)
            target_sr: Tasa de muestreo objetivo (16000 Hz)
            tolerance: Tolerancia para duración en segundos (0.01 = 10ms)
        """
        self.target_duration = target_duration
        self.target_sr = target_sr
        self.tolerance = tolerance
        
        # Calcular muestras objetivo
        self.target_samples = int(target_duration * target_sr)
        
        # Resultados de validación
        self.results = {
            'validation_date': datetime.now().isoformat(),
            'target_duration': target_duration,
            'target_sample_rate': target_sr,
            'tolerance': tolerance,
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'by_vowel': {},
            'errors': [],
            'warnings': []
        }
    
    def validate_audio_file(self, file_path: str) -> Dict:
        """
        Valida un archivo de audio individual.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            Diccionario con resultados de validación
        """
        result = {
            'file_path': str(file_path),
            'filename': Path(file_path).name,
            'valid': True,
            'errors': [],
            'warnings': [],
            'duration': None,
            'sample_rate': None,
            'channels': None,
            'format': None,
            'max_amplitude': None
        }
        
        try:
            # Leer metadata del archivo
            info = sf.info(file_path)
            result['sample_rate'] = info.samplerate
            result['channels'] = info.channels
            result['format'] = info.subtype
            
            # Verificar sample rate
            if info.samplerate != self.target_sr:
                result['valid'] = False
                result['errors'].append(
                    f"Sample rate incorrecto: {info.samplerate} Hz (esperado: {self.target_sr} Hz)"
                )
            
            # Verificar canales (debe ser mono)
            if info.channels != 1:
                result['warnings'].append(
                    f"Archivo no es mono: {info.channels} canales"
                )
            
            # Cargar audio para verificar duración y amplitud
            audio, sr = librosa.load(file_path, sr=None, mono=True)
            duration = len(audio) / sr
            result['duration'] = duration
            
            # Verificar duración
            if abs(duration - self.target_duration) > self.tolerance:
                result['valid'] = False
                result['errors'].append(
                    f"Duración fuera de tolerancia: {duration:.3f}s (esperado: {self.target_duration}s ± {self.tolerance}s)"
                )
            
            # Verificar amplitud (no clipping)
            max_amp = np.max(np.abs(audio))
            result['max_amplitude'] = float(max_amp)
            
            if max_amp > 1.0:
                result['errors'].append(
                    f"Clipping detectado: amplitud máxima = {max_amp:.3f} (> 1.0)"
                )
            elif max_amp < 0.01:
                result['warnings'].append(
                    f"Señal muy débil: amplitud máxima = {max_amp:.3f}"
                )
            
            # Verificar silencio (energía muy baja)
            rms = np.sqrt(np.mean(audio**2))
            if rms < 0.001:
                result['warnings'].append(
                    f"Posible archivo silencioso: RMS = {rms:.6f}"
                )
            
            # Verificar que no sea todo ceros
            if np.all(audio == 0):
                result['valid'] = False
                result['errors'].append("Archivo contiene solo silencio (todos ceros)")
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Error al leer archivo: {str(e)}")
        
        return result
    
    def validate_directory(self, dataset_dir: str) -> Dict:
        """
        Valida todo un directorio de dataset.
        
        Args:
            dataset_dir: Directorio raíz del dataset
            
        Returns:
            Diccionario con resultados de validación
        """
        dataset_path = Path(dataset_dir)
        
        if not dataset_path.exists():
            self.results['errors'].append(f"Directorio no existe: {dataset_dir}")
            return self.results
        
        print(f"Validando dataset en: {dataset_dir}")
        
        # Buscar subdirectorios de vocales
        vowel_dirs = []
        for item in dataset_path.iterdir():
            if item.is_dir() and item.name in ['A', 'E', 'I', 'O', 'U']:
                vowel_dirs.append(item)
        
        if not vowel_dirs:
            # Buscar archivos WAV directamente
            audio_files = list(dataset_path.glob("*.wav"))
            if audio_files:
                vowel_dirs = [dataset_path]
            else:
                self.results['errors'].append("No se encontraron directorios de vocales (A, E, I, O, U) ni archivos WAV")
                return self.results
        
        # Validar cada directorio de vocal
        for vowel_dir in vowel_dirs:
            vowel = vowel_dir.name if vowel_dir != dataset_path else 'root'
            print(f"\nValidando vocal '{vowel}':")
            
            # Buscar archivos WAV
            audio_files = list(vowel_dir.glob("*.wav"))
            if not audio_files:
                print(f"  ⚠️  No se encontraron archivos WAV en {vowel}")
                continue
            
            print(f"  Encontrados {len(audio_files)} archivos")
            
            # Inicializar estadísticas para esta vocal
            vowel_stats = {
                'total_files': len(audio_files),
                'valid_files': 0,
                'invalid_files': 0,
                'total_errors': 0,
                'total_warnings': 0,
                'durations': [],
                'file_results': []
            }
            
            # Validar cada archivo
            for i, audio_file in enumerate(audio_files, 1):
                print(f"  [{i}/{len(audio_files)}] Validando: {audio_file.name}", end='\r')
                
                result = self.validate_audio_file(str(audio_file))
                vowel_stats['file_results'].append(result)
                
                if result['valid']:
                    vowel_stats['valid_files'] += 1
                else:
                    vowel_stats['invalid_files'] += 1
                
                vowel_stats['total_errors'] += len(result['errors'])
                vowel_stats['total_warnings'] += len(result['warnings'])
                
                if result['duration'] is not None:
                    vowel_stats['durations'].append(result['duration'])
            
            print(f"  [{len(audio_files)}/{len(audio_files)}] Completado")
            
            # Actualizar resultados generales
            self.results['total_files'] += vowel_stats['total_files']
            self.results['valid_files'] += vowel_stats['valid_files']
            self.results['invalid_files'] += vowel_stats['invalid_files']
            self.results['by_vowel'][vowel] = vowel_stats
            
            # Mostrar resumen para esta vocal
            if vowel_stats['durations']:
                avg_duration = np.mean(vowel_stats['durations'])
                min_duration = np.min(vowel_stats['durations'])
                max_duration = np.max(vowel_stats['durations'])
                
                print(f"    ✅ Válidos: {vowel_stats['valid_files']}/{vowel_stats['total_files']}")
                print(f"    ❌ Inválidos: {vowel_stats['invalid_files']}/{vowel_stats['total_files']}")
                print(f"    ⚠️  Advertencias: {vowel_stats['total_warnings']}")
                print(f"    ⏱️  Duración: {min_duration:.3f}s - {max_duration:.3f}s (avg: {avg_duration:.3f}s)")
        
        return self.results
    
    def generate_report(self, output_dir: str = "datagen") -> str:
        """
        Genera un reporte de validación.
        
        Args:
            output_dir: Directorio donde guardar el reporte
            
        Returns:
            Ruta al archivo de reporte
        """
        # Crear directorio si no existe
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Calcular porcentajes
        if self.results['total_files'] > 0:
            valid_percent = (self.results['valid_files'] / self.results['total_files']) * 100
            invalid_percent = (self.results['invalid_files'] / self.results['total_files']) * 100
        else:
            valid_percent = invalid_percent = 0
        
        # Generar reporte HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_path / f"validation_report_{timestamp}.html"
        
        html_content = self._generate_html_report(valid_percent, invalid_percent)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # También guardar JSON con resultados completos
        json_path = output_path / f"validation_results_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Reporte HTML guardado en: {report_path}")
        print(f"✅ Resultados JSON guardados en: {json_path}")
        
        return str(report_path)
    
    def _generate_html_report(self, valid_percent: float, invalid_percent: float) -> str:
        """Genera contenido HTML para el reporte."""
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Validación - Dataset de Audio</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .vowel-section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background: #f8f9fa; }}
        .valid {{ color: #27ae60; font-weight: bold; }}
        .invalid {{ color: #e74c3c; font-weight: bold; }}
        .warning {{ color: #f39c12; }}
        .error {{ color: #c0392b; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .progress-bar {{ height: 20px; background: #bdc3c7; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .progress-valid {{ height: 100%; background: #27ae60; width: {valid_percent}%; }}
        .progress-invalid {{ height: 100%; background: #e74c3c; width: {invalid_percent}%; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Reporte de Validación - Dataset de Audio</h1>
        <p>Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>📈 Resumen General</h2>
        <p>Total archivos: {self.results['total_files']}</p>
        <p class="valid">Archivos válidos: {self.results['valid_files']} ({valid_percent:.1f}%)</p>
        <p class="invalid">Archivos inválidos: {self.results['invalid_files']} ({invalid_percent:.1f}%)</p>
        
        <div class="progress-bar">
            <div class="progress-valid" title="{valid_percent:.1f}% válidos"></div>
            <div class="progress-invalid" title="{invalid_percent:.1f}% inválidos"></div>
        </div>
        
        <p>Duración objetivo: {self.target_duration}s ± {self.tolerance}s</p>
        <p>Sample rate objetivo: {self.target_sr} Hz</p>
    </div>
"""
        
        # Sección por vocal
        for vowel, stats in self.results['by_vowel'].items():
            if stats['total_files'] > 0:
                vowel_valid_percent = (stats['valid_files'] / stats['total_files']) * 100
                
                html += f"""
    <div class="vowel-section">
        <h3>🗣️ Vocal '{vowel.upper()}'</h3>
        <p>Archivos: {stats['valid_files']}/{stats['total_files']} válidos ({vowel_valid_percent:.1f}%)</p>
        <p>Errores: {stats['total_errors']} | Advertencias: {stats['total_warnings']}</p>
"""
                
                if stats['durations']:
                    avg_duration = np.mean(stats['durations'])
                    min_duration = np.min(stats['durations'])
                    max_duration = np.max(stats['durations'])
                    
                    html += f"""
        <p>Duración: {min_duration:.3f}s - {max_duration:.3f}s (promedio: {avg_duration:.3f}s)</p>
"""
                
                # Tabla de archivos problemáticos
                problematic_files = [f for f in stats['file_results'] if not f['valid'] or f['warnings']]
                if problematic_files:
                    html += """
        <h4>📋 Archivos con problemas:</h4>
        <table>
            <tr>
                <th>Archivo</th>
                <th>Estado</th>
                <th>Problemas</th>
            </tr>
"""
                    
                    for file_result in problematic_files[:10]:  # Mostrar solo primeros 10
                        status = "✅ Válido" if file_result['valid'] else "❌ Inválido"
                        problems = []
                        problems.extend(file_result['errors'])
                        problems.extend(file_result['warnings'])
                        
                        html += f"""
            <tr>
                <td>{file_result['filename']}</td>
                <td>{status}</td>
                <td>{'<br>'.join(problems)}</td>
            </tr>
"""
                    
                    html += """
        </table>
"""
                    
                    if len(problematic_files) > 10:
                        html += f"""
        <p>... y {len(problematic_files) - 10} archivos más con problemas.</p>
"""
                
                html += """
    </div>
"""
        
        # Recomendaciones
        html += """
    <div class="vowel-section">
        <h3>💡 Recomendaciones</h3>
"""
        
        if self.results['invalid_files'] > 0:
            html += """
        <p class="warning">⚠️ Se encontraron archivos inválidos. Considera:</p>
        <ul>
            <li>Regenerar los archivos problemáticos</li>
            <li>Ajustar parámetros de generación de TTS</li>
            <li>Verificar que las voces en español estén instaladas correctamente</li>
        </ul>
"""
        
        if self.results['total_files'] < 50:
            html += f"""
        <p class="warning">⚠️ Dataset pequeño ({self.results['total_files']} archivos). Para mejor entrenamiento:</p>
        <ul>
            <li>Generar más muestras (objetivo: 50+ por vocal)</li>
            <li>Considerar augmentación de datos</li>
        </ul>
"""
        
        if any(stats['total_warnings'] > stats['total_files'] * 0.5 for stats in self.results['by_vowel'].values()):
            html += """
        <p class="warning">⚠️ Muchas advertencias detectadas. Verifica:</p>
        <ul>
            <li>Calidad de audio (señales muy débiles)</li>
            <li>Proceso de normalización</li>
            <li>Detección de actividad vocal</li>
        </ul>
"""
        
        html += """
    </div>
    
    <div class="vowel-section">
        <h3>📊 Estadísticas Detalladas</h3>
        <table>
            <tr>
                <th>Vocal</th>
                <th>Total</th>
                <th>Válidos</th>
                <th>Inválidos</th>
                <th>% Válidos</th>
                <th>Errores</th>
                <th>Advertencias</th>
            </tr>
"""
        
        for vowel, stats in self.results['by_vowel'].items():
            if stats['total_files'] > 0:
                vowel_valid_percent = (stats['valid_files'] / stats['total_files']) * 100
                html += f"""
            <tr>
                <td>{vowel.upper()}</td>
                <td>{stats['total_files']}</td>
                <td class="valid">{stats['valid_files']}</td>
                <td class="invalid">{stats['invalid_files']}</td>
                <td>{vowel_valid_percent:.1f}%</td>
                <td>{stats['total_errors']}</td>
                <td>{stats['total_warnings']}</td>
            </tr>
"""
        
        html += f"""
            <tr style="font-weight: bold; background: #f1f1f1;">
                <td>TOTAL</td>
                <td>{self.results['total_files']}</td>
                <td class="valid">{self.results['valid_files']}</td>
                <td class="invalid">{self.results['invalid_files']}</td>
                <td>{valid_percent:.1f}%</td>
                <td>{sum(s['total_errors'] for s in self.results['by_vowel'].values())}</td>
                <td>{sum(s['total_warnings'] for s in self.results['by_vowel'].values())}</td>
            </tr>
        </table>
    </div>
    
    <div class="vowel-section">
        <h3>🔧 Configuración Usada</h3>
        <ul>
            <li>Duración objetivo: {self.target_duration} segundos</li>
            <li>Tolerancia: ±{self.tolerance} segundos</li>
            <li>Sample rate objetivo: {self.target_sr} Hz</li>
            <li>Fecha de validación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
    </div>
</body>
</html>
"""
        
        return html

def main():
    """Función principal."""
    print("=" * 60)
    print("VALIDADOR DE DATASET DE AUDIO")
    print("=" * 60)
    
    # Configuración por defecto
    dataset_dir = "datagen/processed"
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        dataset_dir = sys.argv[1]
    
    # Verificar directorio
    if not Path(dataset_dir).exists():
        print(f"❌ Directorio del dataset no existe: {dataset_dir}")
        print("\nSugerencias:")
        print("1. Primero ejecuta el pipeline completo para generar el dataset")
        print("2. O especifica la ruta correcta al dataset procesado")
        return 1
    
    # Inicializar validador
    print("\nInicializando validador...")
    validator = DatasetValidator(
        target_duration=0.3,
        target_sr=16000,
        tolerance=0.01
    )
    
    # Validar dataset
    print(f"\nValidando dataset en: {dataset_dir}")
    results = validator.validate_directory(dataset_dir)
    
    # Generar reporte
    print("\nGenerando reporte de validación...")
    report_path = validator.generate_report()
    
    # Mostrar resumen en consola
    print("\n" + "=" * 60)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    if results['total_files'] > 0:
        valid_percent = (results['valid_files'] / results['total_files']) * 100
        
        print(f"📊 Archivos totales: {results['total_files']}")
        print(f"✅ Archivos válidos: {results['valid_files']} ({valid_percent:.1f}%)")
        print(f"❌ Archivos inválidos: {results['invalid_files']}")
        
        print("\n🗣️ Distribución por vocal:")
        for vowel, stats in results['by_vowel'].items():
            if stats['total_files'] > 0:
                vowel_valid = (stats['valid_files'] / stats['total_files']) * 100
                print(f"  {vowel.upper()}: {stats['valid_files']}/{stats['total_files']} ({vowel_valid:.1f}%)")
        
        # Recomendaciones basadas en resultados
        print("\n💡 Recomendaciones:")
        
        if valid_percent < 90:
            print("  ⚠️  Menos del 90% de archivos válidos. Considera regenerar el dataset.")
        
        if results['total_files'] < 50:
            print(f"  ⚠️  Dataset pequeño ({results['total_files']} archivos). Objetivo: 50+ por vocal.")
        
        # Verificar balance
        vowel_counts = {v: s['total_files'] for v, s in results['by_vowel'].items()
                       if v in ['A', 'E', 'I', 'O', 'U']}
        if vowel_counts:
            min_count = min(vowel_counts.values())
            max_count = max(vowel_counts.values())
            if max_count > min_count * 2:
                print(f"  ⚠️  Dataset desbalanceado. Mayor diferencia: {max_count}/{min_count}")
        
        print(f"\n📄 Reporte detallado generado en: {report_path}")
        
        if valid_percent >= 95:
            print("\n🎉 ¡Dataset de alta calidad! Listo para entrenamiento.")
        elif valid_percent >= 80:
            print("\n👍 Dataset aceptable. Puede usarse para entrenamiento.")
        else:
            print("\n⚠️  Dataset con problemas. Se recomienda mejorar antes de entrenar.")
    
    else:
        print("❌ No se encontraron archivos para validar.")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nValidación cancelada por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)