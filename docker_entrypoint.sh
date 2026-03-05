#!/bin/bash
# Script de entrada para Docker - Maneja extracción de características y entrenamiento

set -e

echo "========================================="
echo "Docker Pipeline - Extracción y Entrenamiento"
echo "========================================="

# Función para extraer características
extract_features() {
    echo ""
    echo "1. EXTRACCIÓN DE CARACTERÍSTICAS"
    echo "================================="
    
    # Verificar si ya existen características
    if [ -f "dataset/features.json" ]; then
        echo "✓ Características ya existen en dataset/features.json"
        echo "  Usando características existentes..."
        return 0
    fi
    
    # Verificar si hay archivos de audio
    audio_files=$(find dataset -name "*.wav" | wc -l)
    if [ "$audio_files" -eq 0 ]; then
        echo "✗ No se encontraron archivos .wav en dataset/"
        echo "  Por favor grabe audio primero con: node scripts/record.js"
        return 1
    fi
    
    echo "✓ Encontrados $audio_files archivos .wav"
    
    # Intentar extraer con Node.js primero
    echo "  Intentando extracción con Node.js..."
    if command -v node &> /dev/null && [ -f "scripts/extract_features.js" ]; then
        node scripts/extract_features.js
        
        if [ $? -eq 0 ] && [ -f "dataset/features.json" ]; then
            echo "✓ Extracción con Node.js completada exitosamente"
            echo "  Características guardadas en: dataset/features.json"
            return 0
        else
            echo "⚠  Extracción con Node.js falló, intentando con Python..."
        fi
    else
        echo "⚠  Node.js no disponible, intentando con Python..."
    fi
    
    # Intentar extraer con Python como alternativa
    echo "  Intentando extracción con Python..."
    if command -v python3 &> /dev/null && [ -f "extract_features_python.py" ]; then
        python3 extract_features_python.py
        
        if [ $? -eq 0 ] && [ -f "dataset/features_python.json" ]; then
            # Copiar características al nombre esperado
            cp dataset/features_python.json dataset/features.json
            echo "✓ Extracción con Python completada exitosamente"
            echo "  Características guardadas en: dataset/features.json"
            return 0
        else
            echo "✗ Error en la extracción con Python"
            return 1
        fi
    else
        echo "✗ Python no disponible para extracción"
        return 1
    fi
}

# Función para convertir a formato optimizado
convert_to_optimized() {
    echo ""
    echo "2. CONVERSIÓN A FORMATO OPTIMIZADO"
    echo "==================================="
    
    # Verificar si ya existe formato numpy
    if [ -f "dataset/numpy/features.npy" ]; then
        echo "✓ Formato numpy ya existe"
        return 0
    fi
    
    # Verificar si existen características
    if [ ! -f "dataset/features.json" ]; then
        echo "✗ No se encontró dataset/features.json"
        return 1
    fi
    
    echo "  Convirtiendo características a formato NumPy..."
    python3 convert_to_numpy.py
    
    if [ $? -eq 0 ]; then
        echo "✓ Conversión completada exitosamente"
        return 0
    else
        echo "✗ Error en la conversión"
        return 1
    fi
}

# Función para entrenamiento rápido
train_fast() {
    echo ""
    echo "3. ENTRENAMIENTO RÁPIDO CON GPU"
    echo "================================"
    
    # Verificar GPU
    if python3 -c "import tensorflow as tf; print('GPU disponible:', tf.config.list_physical_devices('GPU'))" | grep -q "GPU disponible: []"; then
        echo "⚠  ADVERTENCIA: No se detectó GPU"
        echo "   El entrenamiento será más lento en CPU"
    else
        echo "✓ GPU detectada - Entrenamiento acelerado"
    fi
    
    # Entrenar modelo
    echo "  Iniciando entrenamiento rápido..."
    
    MODEL_TYPE="fast"
    if [ "$1" == "lightning" ]; then
        MODEL_TYPE="lightning"
        echo "  Usando modelo lightning (máxima velocidad)"
    else
        echo "  Usando modelo fast (equilibrio velocidad/precisión)"
    fi
    
    python3 train_tensorflow_gpu.py --$MODEL_TYPE
    
    if [ $? -eq 0 ]; then
        echo "✓ Entrenamiento completado exitosamente"
        return 0
    else
        echo "✗ Error en el entrenamiento"
        return 1
    fi
}

# Función para pipeline completo
full_pipeline() {
    echo ""
    echo "PIPELINE COMPLETO"
    echo "================="
    
    extract_features
    if [ $? -ne 0 ]; then
        echo "✗ Pipeline detenido: Error en extracción de características"
        return 1
    fi
    
    convert_to_optimized
    if [ $? -ne 0 ]; then
        echo "⚠  Continuando sin conversión optimizada..."
    fi
    
    train_fast "$1"
    if [ $? -ne 0 ]; then
        echo "✗ Pipeline detenido: Error en entrenamiento"
        return 1
    fi
    
    echo ""
    echo "✅ PIPELINE COMPLETADO EXITOSAMENTE"
    echo "==================================="
    echo "Modelo guardado en: trained_python_fast/"
    echo "Logs de TensorBoard en: logs/tensorboard/fast_gpu"
    return 0
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: docker run [opciones] imagen [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  extract        Extraer características de audio"
    echo "  convert        Convertir características a formato optimizado"
    echo "  train [fast|lightning]  Entrenar modelo (default: fast)"
    echo "  pipeline [fast|lightning]  Pipeline completo (default: fast)"
    echo "  help           Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  docker run --gpus all -v \$(pwd):/app imagen pipeline"
    echo "  docker run --gpus all -v \$(pwd):/app imagen pipeline lightning"
    echo "  docker run -v \$(pwd):/app imagen extract"
    echo ""
    echo "Nota: Para GPU, use --gpus all flag"
}

# Procesar comando
COMMAND="${1:-pipeline}"
SUBCOMMAND="${2:-fast}"

case "$COMMAND" in
    extract)
        extract_features
        ;;
    convert)
        convert_to_optimized
        ;;
    train)
        train_fast "$SUBCOMMAND"
        ;;
    pipeline)
        full_pipeline "$SUBCOMMAND"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Comando no reconocido: $COMMAND"
        echo "Use 'help' para ver comandos disponibles"
        exit 1
        ;;
esac

exit $?