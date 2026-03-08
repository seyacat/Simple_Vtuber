# Sistema de Generación de Dataset de Audio con TTS de Windows

Sistema completo para generar un dataset de audio sintético para entrenamiento de modelos de reconocimiento de vocales (A, E, I, O, U) usando Text-to-Speech (TTS) de Windows.

## 📋 Características

- ✅ Generación automática de todas las combinaciones consonante-vocal en español
- ✅ Síntesis de voz usando TTS de Windows (sin costos de API)
- ✅ Procesamiento automático para extraer segmentos de exactamente 0.3 segundos
- ✅ Organización en carpetas por vocal (A, E, I, O, U)
- ✅ Validación completa de calidad del dataset
- ✅ Reportes HTML detallados
- ✅ Modo prueba para verificación rápida

## 🏗️ Estructura del Proyecto

```
datagen/
├── raw_audio/          # Audios crudos generados por TTS
├── processed/          # Audios procesados de 0.3s
│   ├── A/             # Muestras para vocal A
│   ├── E/             # Muestras para vocal E
│   ├── I/             # Muestras para vocal I
│   ├── O/             # Muestras para vocal O
│   └── U/             # Muestras para vocal U
├── scripts/           # Scripts de generación
│   ├── generate_texts.py      # Genera combinaciones de textos
│   ├── tts_generation.py      # Sintetiza voz con TTS de Windows
│   ├── audio_processing.py    # Procesa y recorta audio
│   ├── validate_dataset.py    # Valida calidad del dataset
│   └── pipeline.py            # Script principal del pipeline
├── reports/           # Reportes de validación
└── README.md          # Este archivo
```

## 📊 Especificaciones del Dataset

- **Duración**: 0.3 segundos exactos (±10ms de tolerancia)
- **Sample rate**: 16000 Hz (compatible con `config.json` del proyecto principal)
- **Formato**: WAV 16-bit PCM mono
- **Vocales**: A, E, I, O, U
- **Consonantes**: Todas las consonantes españolas (b, c, d, f, g, h, j, k, l, m, n, ñ, p, q, r, s, t, v, w, x, y, z) + combinaciones especiales (ch, ll, rr)

## 🚀 Instalación Rápida

### 1. Instalar Dependencias

```powershell
# Instalar dependencias Python necesarias
pip install comtypes soundfile librosa numpy scipy
```

### 2. Verificar Voces de Windows

Asegúrate de que Windows tenga al menos una voz en español instalada:

1. Abre **Configuración de Windows** → **Hora e idioma** → **Voz**
2. En "Voces", verifica que haya una voz en español instalada
3. Si no hay, haz clic en "Agregar voces" y selecciona español

### 3. Verificar Instalación

```powershell
cd datagen/scripts
python test_tts.py
```

## 🛠️ Uso del Sistema

### Opción 1: Pipeline Completo (Recomendado)

Ejecuta todos los pasos automáticamente:

```powershell
# Pipeline completo (producción)
cd datagen/scripts
python pipeline.py

# Pipeline en modo prueba (solo 10 muestras)
python pipeline.py --test

# Pipeline con pasos específicos
python pipeline.py --steps generate_texts tts_generation
```

### Opción 2: Pasos Individuales

#### Paso 1: Generar Textos

```powershell
python generate_texts.py
```
**Salida**: `../combinaciones.json`, `../textos_individuales.txt`, `../textos_grupos.txt`

#### Paso 2: Generar Audio con TTS

```powershell
# Usar textos individuales (recomendado)
python tts_generation.py ../textos_individuales.txt

# Usar textos agrupados (más rápido)
python tts_generation.py ../textos_grupos.txt

# Modo prueba (solo 5 audios)
python tts_generation.py ../textos_individuales.txt 5
```
**Salida**: `../raw_audio/*.wav`, `../raw_audio/generation_metadata.json`

#### Paso 3: Procesar Audio

```powershell
python audio_processing.py
```
**Salida**: `../processed/{A,E,I,O,U}/*.wav`, `../processed/processing_metadata.json`

#### Paso 4: Validar Dataset

```powershell
python validate_dataset.py
```
**Salida**: `../reports/validation_report_*.html`, `../reports/validation_results_*.json`

## ⚙️ Parámetros del Pipeline

### pipeline.py

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--steps` | Pasos a ejecutar | Todos los pasos |
| `--test` | Modo prueba (límites reducidos) | False |
| `--base-dir` | Directorio base del dataset | "datagen" |
| `--use-groups` | Usar textos agrupados para TTS | False |

**Ejemplos**:
```powershell
# Solo generar textos y TTS
python pipeline.py --steps generate_texts tts_generation

# Pipeline completo en modo prueba
python pipeline.py --test

# Pipeline con textos agrupados
python pipeline.py --use-groups
```

### generate_texts.py

Genera 110 combinaciones únicas (22 consonantes × 5 vocales).

### tts_generation.py

| Parámetro | Descripción |
|-----------|-------------|
| `archivo_textos` | Ruta al archivo con textos (requerido) |
| `max_items` | Número máximo de textos a procesar (opcional) |

### audio_processing.py

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `input_dir` | Directorio con audios crudos | "../raw_audio" |
| `output_dir` | Directorio para audios procesados | "../processed" |
| `metadata_file` | Archivo JSON con metadata | "../raw_audio/generation_metadata.json" |

### validate_dataset.py

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `dataset_dir` | Directorio del dataset a validar | "../processed" |

## 🔧 Configuración Avanzada

### Ajustar Parámetros de Procesamiento

Edita `audio_processing.py` para modificar:

```python
# En la clase AudioProcessor:
target_duration=0.3,      # Duración objetivo en segundos
target_sr=16000,          # Sample rate objetivo
vad_threshold=0.01,       # Umbral para detección de voz
```

### Seleccionar Voz Específica

Edita `tts_generation.py` para usar una voz específica:

```python
# En WindowsTTSGenerator.__init__:
voice_name="Microsoft Helena Desktop"  # Nombre de voz específica
```

### Modificar Combinaciones de Textos

Edita `generate_texts.py` para cambiar las consonantes o vocales:

```python
CONSONANTES_ESPANOL = ['b', 'c', 'd', ...]  # Lista de consonantes
VOCALES = ['a', 'e', 'i', 'o', 'u']         # Lista de vocales
COMBINACIONES_ESPECIALES = ['ch', 'll', 'rr']  # Dígrafos
```

## 📈 Resultados Esperados

### Dataset de Producción
- **Total combinaciones**: 110 (22 consonantes × 5 vocales)
- **Muestras por vocal**: ~22 muestras (una por consonante)
- **Duración total**: ~33 segundos por vocal
- **Tamaño total**: ~5-10 MB

### Para Dataset Más Grande
Para más muestras por vocal, ejecuta múltiples veces o modifica los scripts para generar variaciones.

## 🐛 Solución de Problemas

### Problema: "comtypes no está instalado"
**Solución**:
```powershell
pip install comtypes
```

### Problema: "No se encontraron voces en español"
**Solución**:
1. Verifica que Windows tenga voces en español instaladas
2. Ejecuta `python test_tts.py` para listar voces disponibles
3. Instala voces desde Configuración de Windows → Hora e idioma → Voz

### Problema: "Error al generar audio"
**Solución**:
1. Verifica que el archivo de textos existe
2. Asegúrate de tener permisos de escritura en `datagen/raw_audio/`
3. Prueba con modo prueba primero: `python pipeline.py --test`

### Problema: "Archivos de 0.3s no se generan correctamente"
**Solución**:
1. Ajusta `vad_threshold` en `audio_processing.py`
2. Verifica que los audios crudos tengan suficiente volumen
3. Prueba con diferentes textos (más largos/cortos)

## 🔄 Integración con Proyecto Principal

El dataset generado es compatible con el pipeline existente:

### 1. Usar con `scripts/aumeta_dataset.py`
```powershell
# Copiar dataset procesado a la estructura esperada
cp -r datagen/processed/* dataset/
```

### 2. Usar con `extract_features_python.py`
```python
# El sample rate (16000 Hz) y formato son compatibles
```

### 3. Actualizar `config.json` si es necesario
```json
{
  "audio": {
    "sampleRate": 16000,
    "duration": 0.3,  # Actualizar si usas 0.3s en lugar de 0.1s
    "channels": 1
  }
}
```

## 📊 Métricas de Calidad

El sistema valida automáticamente:

- ✅ **Duración**: 0.3s ± 10ms
- ✅ **Sample rate**: 16000 Hz exactos
- ✅ **Formato**: WAV 16-bit PCM mono
- ✅ **Amplitud**: Sin clipping (< 1.0), señal suficiente (> 0.01)
- ✅ **Estructura**: Carpetas A, E, I, O, U correctamente organizadas

**Criterios de aceptación**:
- ≥ 80% de archivos válidos → Dataset de buena calidad
- ≥ 50% de archivos válidos → Dataset usable
- < 50% de archivos válidos → Requiere regeneración

## 🚀 Ejemplo de Ejecución Completa

```powershell
# 1. Navegar al directorio de scripts
cd d:/Vocals_Recognition_Model/datagen/scripts

# 2. Ejecutar pipeline en modo prueba
python pipeline.py --test

# 3. Verificar resultados
python validate_dataset.py

# 4. Si todo está bien, ejecutar pipeline completo
python pipeline.py

# 5. Revisar reporte de validación
start ../reports/validation_report_*.html
```

## 📝 Notas Importantes

1. **TTS de Windows** puede ser más lento que APIs en la nube, pero no tiene costos ni límites
2. **Calidad de audio** depende de las voces instaladas en Windows
3. **Modo prueba** es recomendado para verificar que todo funciona antes de generar el dataset completo
4. **Validación** genera reportes HTML detallados en `datagen/reports/`

## 📄 Licencia

Este sistema es parte del proyecto Vocal Recognition Model y sigue la misma licencia.

## 🤝 Contribuciones

Para reportar problemas o sugerir mejoras:
1. Verifica que el problema no esté listado en "Solución de Problemas"
2. Ejecuta en modo prueba para aislar el problema
3. Proporciona el archivo de reporte de validación generado

---

**¡Dataset listo para entrenamiento!** 🎉