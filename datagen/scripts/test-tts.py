#!/usr/bin/env python3
"""
Script simple para probar TTS de Windows.
Verifica que las dependencias estén instaladas y que el TTS funcione.
"""

import sys
import os

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas."""
    print("=== VERIFICACIÓN DE DEPENDENCIAS ===")
    
    dependencies = [
        ('comtypes', 'Síntesis de voz con Windows TTS'),
        ('soundfile', 'Lectura/escritura de archivos de audio'),
        ('librosa', 'Procesamiento de audio'),
        ('numpy', 'Cálculos numéricos'),
    ]
    
    missing = []
    for dep, desc in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep:20} - {desc}")
        except ImportError:
            print(f"❌ {dep:20} - {desc} - NO INSTALADO")
            missing.append(dep)
    
    return missing

def test_windows_tts():
    """Prueba básica de TTS de Windows."""
    print("\n=== PRUEBA DE TTS DE WINDOWS ===")
    
    try:
        import comtypes.client
        
        # Crear objeto de voz
        voice = comtypes.client.CreateObject("SAPI.SpVoice")
        
        # Listar voces disponibles
        voices = voice.GetVoices()
        print(f"Voces disponibles: {voices.Count}")
        
        spanish_voices = []
        for i in range(voices.Count):
            v = voices.Item(i)
            desc = v.GetDescription()
            print(f"  {i}: {desc}")
            
            # Buscar voces en español
            if 'spanish' in desc.lower() or 'español' in desc.lower() or 'es-' in desc.lower():
                spanish_voices.append((i, v))
        
        if spanish_voices:
            print(f"\n✅ Se encontraron {len(spanish_voices)} voces en español:")
            for i, v in spanish_voices:
                print(f"  - {v.GetDescription()}")
            
            # Probar con primera voz en español
            test_voice = spanish_voices[0][1]
            voice.Voice = test_voice
            
            # Probar síntesis
            test_text = "Hola, esto es una prueba del sistema."
            print(f"\n🔊 Probando síntesis: '{test_text}'")
            
            # Intentar hablar
            voice.Speak(test_text)
            print("✅ Síntesis de voz funcionando correctamente")
            
            return True
        else:
            print("\n⚠️  No se encontraron voces en español.")
            print("   Instale voces en español desde:")
            print("   Configuración de Windows > Hora e idioma > Voz")
            return False
            
    except Exception as e:
        print(f"\n❌ Error en TTS: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_processing():
    """Prueba básica de procesamiento de audio."""
    print("\n=== PRUEBA DE PROCESAMIENTO DE AUDIO ===")
    
    try:
        import numpy as np
        import soundfile as sf
        
        # Crear un audio de prueba simple
        test_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000))  # 440 Hz, 1 segundo
        test_audio = test_audio * 0.5  # Reducir amplitud
        
        # Guardar archivo de prueba
        test_file = "test_audio.wav"
        sf.write(test_file, test_audio, 16000, subtype='PCM_16')
        
        # Leer archivo
        audio, sr = sf.read(test_file)
        
        print(f"✅ Audio de prueba creado: {test_file}")
        print(f"   Muestras: {len(audio)}, Sample rate: {sr} Hz")
        print(f"   Duración: {len(audio)/sr:.3f} segundos")
        
        # Limpiar
        if os.path.exists(test_file):
            os.remove(test_file)
            print("✅ Archivo de prueba eliminado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento de audio: {e}")
        return False

def main():
    """Función principal."""
    print("=" * 60)
    print("PRUEBA DEL SISTEMA DE GENERACIÓN DE DATASET")
    print("=" * 60)
    
    # Verificar dependencias
    missing = check_dependencies()
    if missing:
        print(f"\n⚠️  Dependencias faltantes: {', '.join(missing)}")
        print("   Instalar con: pip install " + " ".join(missing))
        print("\nO instalar todas las dependencias:")
        print("   pip install -r ../requirements.txt")
    
    # Probar TTS
    tts_ok = test_windows_tts()
    
    # Probar procesamiento de audio
    audio_ok = test_audio_processing()
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE LA PRUEBA")
    print("=" * 60)
    
    if tts_ok and audio_ok:
        print("✅ ¡Sistema listo para generar dataset!")
        print("\nPróximos pasos:")
        print("1. Ejecutar pipeline en modo prueba:")
        print("   python pipeline.py --test")
        print("\n2. Si funciona, generar dataset completo:")
        print("   python pipeline.py")
        return 0
    else:
        print("⚠️  El sistema tiene problemas que resolver:")
        if not tts_ok:
            print("   - TTS de Windows no funciona correctamente")
        if not audio_ok:
            print("   - Procesamiento de audio tiene problemas")
        
        print("\nSolución de problemas:")
        print("1. Asegúrate de tener voces en español instaladas en Windows")
        print("2. Verifica que todas las dependencias estén instaladas")
        print("3. Ejecuta como administrador si hay problemas de permisos")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)