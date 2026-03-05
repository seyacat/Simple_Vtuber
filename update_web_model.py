#!/usr/bin/env python3
"""
Script para actualizar la aplicación web con el modelo TensorFlow.js convertido
"""

import os
import shutil
import json

def update_web_app(tfjs_model_dir, web_model_dir='public/models/vowel_model'):
    """
    Actualiza la aplicación web con el modelo TensorFlow.js convertido
    """
    print("=" * 60)
    print("ACTUALIZACIÓN DE MODELO PARA APLICACIÓN WEB")
    print("=" * 60)
    
    # Verificar que el modelo TensorFlow.js existe
    if not os.path.exists(tfjs_model_dir):
        print(f"❌ ERROR: No se encontró el modelo TensorFlow.js en: {tfjs_model_dir}")
        return False
    
    # Verificar archivos del modelo
    model_files = []
    for root, dirs, files in os.walk(tfjs_model_dir):
        for file in files:
            if file.endswith('.json') or file.endswith('.bin'):
                model_files.append(os.path.join(root, file))
    
    if not model_files:
        print(f"❌ ERROR: No se encontraron archivos .json o .bin en: {tfjs_model_dir}")
        return False
    
    print(f"✓ Modelo TensorFlow.js encontrado: {len(model_files)} archivos")
    
    # Crear directorio de destino
    os.makedirs(web_model_dir, exist_ok=True)
    print(f"✓ Directorio de destino creado: {web_model_dir}")
    
    # Copiar archivos del modelo
    print("\nCopiando archivos del modelo...")
    for file_path in model_files:
        rel_path = os.path.relpath(file_path, tfjs_model_dir)
        dest_path = os.path.join(web_model_dir, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(file_path, dest_path)
        print(f"  ✓ {rel_path} -> {os.path.relpath(dest_path, '.')}")
    
    # Encontrar archivo model.json principal
    model_json_path = None
    for file in os.listdir(tfjs_model_dir):
        if file == 'model.json' or file.endswith('.json'):
            full_path = os.path.join(tfjs_model_dir, file)
            # Verificar si es el archivo principal del modelo
            with open(full_path, 'r') as f:
                try:
                    content = json.load(f)
                    if 'modelTopology' in content or 'weightsManifest' in content:
                        model_json_path = file
                        break
                except:
                    continue
    
    if not model_json_path:
        # Buscar cualquier archivo .json
        for file in os.listdir(tfjs_model_dir):
            if file.endswith('.json'):
                model_json_path = file
                break
    
    if model_json_path:
        # Actualizar app_tfjs.js con la nueva ruta del modelo
        update_app_tfjs(web_model_dir, model_json_path)
    
    print("\n" + "=" * 60)
    print("✅ ACTUALIZACIÓN COMPLETADA")
    print("=" * 60)
    print(f"Modelo copiado a: {web_model_dir}")
    print("\nPara usar el nuevo modelo:")
    print(f"1. La aplicación web cargará automáticamente desde: {web_model_dir}/{model_json_path if model_json_path else 'model.json'}")
    print("2. Recargue la página web para usar el nuevo modelo")
    
    return True

def update_app_tfjs(model_dir, model_json_file):
    """Actualiza app_tfjs.js con la nueva ruta del modelo"""
    app_tfjs_path = 'app_tfjs.js'
    
    if not os.path.exists(app_tfjs_path):
        print(f"⚠  No se encontró {app_tfjs_path}, creando archivo de configuración...")
        create_model_config(model_dir, model_json_file)
        return
    
    print(f"\nActualizando {app_tfjs_path}...")
    
    # Leer el archivo
    with open(app_tfjs_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar y reemplazar la ruta del modelo
    old_path = "./trained/model.json"
    new_path = f"./{model_dir}/{model_json_file}"
    
    if old_path in content:
        new_content = content.replace(old_path, new_path)
        with open(app_tfjs_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ Ruta del modelo actualizada: {old_path} -> {new_path}")
    else:
        print("⚠  No se encontró la ruta del modelo original, agregando configuración...")
        create_model_config(model_dir, model_json_file)

def create_model_config(model_dir, model_json_file):
    """Crea un archivo de configuración para el modelo"""
    config = {
        "model": {
            "path": f"./{model_dir}/{model_json_file}",
            "inputShape": [13, 1, 1],
            "classes": ["A", "E", "I", "O", "U", "noise"],
            "description": "Modelo CNN entrenado para reconocimiento de vocales"
        },
        "training": {
            "date": "2026-03-04",
            "accuracy": 0.3763,
            "val_accuracy": 0.1709,
            "training_time": 6.65
        }
    }
    
    config_path = 'model_config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Archivo de configuración creado: {config_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Actualizar aplicación web con modelo TensorFlow.js')
    parser.add_argument('--input', '-i', default='trained_web/tfjs_model', 
                       help='Directorio del modelo TensorFlow.js (default: trained_web/tfjs_model)')
    parser.add_argument('--output', '-o', default='public/models/vowel_model',
                       help='Directorio de destino en la aplicación web (default: public/models/vowel_model)')
    
    args = parser.parse_args()
    
    success = update_web_app(args.input, args.output)
    
    if success:
        print("\n🎯 ¡Modelo listo para uso web!")
        print("Ejecute la aplicación web y recargue la página para usar el nuevo modelo.")
    else:
        print("\n❌ La actualización falló.")
        print("Verifique que el modelo TensorFlow.js se haya convertido correctamente.")
        exit(1)

if __name__ == "__main__":
    main()