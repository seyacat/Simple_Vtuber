#!/usr/bin/env python3
"""
Script para convertir modelos Keras H5 a formato TensorFlow.js
Optimizado para Docker con manejo robusto de dependencias
"""

import os
import sys
import argparse
import subprocess

def install_tensorflowjs():
    """Instala tensorflowjs con versión compatible y sus dependencias"""
    print("Instalando dependencias para TensorFlow.js...")
    
    # Primero instalar h5py que es necesario para leer archivos .h5
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "h5py==3.9.0"
        ])
        print("✓ h5py 3.9.0 instalado")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Advertencia instalando h5py: {e}")
        # Continuar de todos modos, tal vez ya está instalado
    
    # Intentar con versión específica que funciona con TensorFlow 2.15
    print("Instalando tensorflowjs...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "tensorflowjs==4.22.0"
        ])
        print("✓ tensorflowjs 4.22.0 instalado")
        return True
    except subprocess.CalledProcessError:
        print("Intentando con versión más reciente...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "tensorflowjs"
            ])
            print("✓ tensorflowjs instalado (última versión)")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Error instalando tensorflowjs: {e}")
            return False

def check_and_install_tensorflow():
    """Verifica si TensorFlow está instalado y lo instala si es necesario"""
    try:
        import tensorflow as tf
        print(f"✓ TensorFlow {tf.__version__} ya está instalado")
        return True
    except ImportError:
        print("TensorFlow no encontrado, instalando...")
        try:
            # Instalar versión compatible
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "tensorflow==2.15.0"
            ])
            print("✓ TensorFlow 2.15.0 instalado")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Error instalando TensorFlow: {e}")
            return False

def convert_h5_to_tfjs(input_h5_path, output_dir):
    """
    Convierte un modelo H5 a formato TensorFlow.js
    """
    print(f"Convirtiendo: {input_h5_path} -> {output_dir}")
    
    # Verificar archivo de entrada
    if not os.path.exists(input_h5_path):
        print(f"ERROR: No se encontró: {input_h5_path}")
        return False
    
    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    
    # Intentar importar tensorflowjs
    try:
        import tensorflowjs as tfjs
        print("✓ TensorFlow.js importado")
    except ImportError:
        print("TensorFlow.js no encontrado, instalando...")
        if not install_tensorflowjs():
            return False
        try:
            import tensorflowjs as tfjs
            print("✓ TensorFlow.js importado después de instalación")
        except ImportError as e:
            print(f"✗ No se pudo importar tensorflowjs: {e}")
            return False
    
    # Verificar e instalar TensorFlow si es necesario
    if not check_and_install_tensorflow():
        return False
    
    # Importar tensorflow después de verificar/instalar
    try:
        import tensorflow as tf
        print("✓ TensorFlow importado")
    except ImportError as e:
        print(f"✗ Error importando TensorFlow después de instalación: {e}")
        return False
    
    try:
        # Deshabilitar mixed_float16 policy temporalmente para evitar errores de GPU
        original_policy = tf.keras.mixed_precision.global_policy()
        tf.keras.mixed_precision.set_global_policy('float32')
        
        # Cargar modelo
        print(f"Cargando modelo desde: {input_h5_path}")
        model = tf.keras.models.load_model(input_h5_path)
        print(f"✓ Modelo cargado: {model.input_shape} -> {model.output_shape}")
        
        # Restaurar política original
        tf.keras.mixed_precision.set_global_policy(original_policy)
        
        # Convertir a TensorFlow.js
        print(f"Convirtiendo a TensorFlow.js en: {output_dir}")
        tfjs.converters.save_keras_model(model, output_dir)
        
        # Verificar archivos generados
        file_count = 0
        for root, dirs, files in os.walk(output_dir):
            file_count += len(files)
        
        print(f"✓ Conversión completada: {file_count} archivos generados")
        
        # Mostrar estructura
        print("\nEstructura del modelo TensorFlow.js:")
        for root, dirs, files in os.walk(output_dir):
            level = root.replace(output_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error durante la conversión: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Convertir modelo Keras (.keras o .h5) a TensorFlow.js')
    parser.add_argument('--input', '-i', required=True, help='Ruta al archivo model.keras o model.h5')
    parser.add_argument('--output', '-o', required=True, help='Directorio de salida')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CONVERSIÓN A TENSORFLOW.JS PARA WEB")
    print("=" * 60)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print("=" * 60)
    
    success = convert_h5_to_tfjs(args.input, args.output)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ CONVERSIÓN EXITOSA")
        print("=" * 60)
        print(f"Modelo TensorFlow.js disponible en:")
        print(f"  {args.output}")
        print("\nPara usar en la aplicación web:")
        print(f"1. Copiar '{args.output}/' a 'public/models/vowel_model/'")
        print(f"2. Actualizar app_tfjs.js para cargar el nuevo modelo")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ CONVERSIÓN FALLIDA")
        print("=" * 60)
        print("Sugerencias:")
        print("1. Verificar que tensorflowjs esté instalado")
        print("2. Verificar compatibilidad de versiones")
        print("3. Intentar manualmente: tensorflowjs_converter --input_format=keras model.keras output_dir/")
        sys.exit(1)

if __name__ == "__main__":
    main()