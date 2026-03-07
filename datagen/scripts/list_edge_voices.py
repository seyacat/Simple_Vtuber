#!/usr/bin/env python3
"""
Script para listar voces disponibles en Edge TTS.
"""

import asyncio
import edge_tts

async def list_voices():
    """Lista todas las voces disponibles en Edge TTS."""
    voices = await edge_tts.list_voices()
    
    # Filtrar voces en español
    spanish_voices = [v for v in voices if 'Spanish' in v['Locale'] or 'es-' in v['Locale'].lower()]
    
    print("=" * 80)
    print(f"VOCES DISPONIBLES EN EDGE TTS (Total: {len(voices)})")
    print("=" * 80)
    
    print(f"\nVoces en español ({len(spanish_voices)}):")
    print("-" * 80)
    
    for i, voice in enumerate(spanish_voices):
        print(f"{i:3d}: {voice['ShortName']:30} | {voice['Locale']:15} | {voice['Gender']:8} | {voice['FriendlyName']}")
    
    # Mostrar algunas voces populares
    popular_spanish_voices = [
        "es-ES-AlvaroNeural",      # Masculino España
        "es-ES-ElviraNeural",      # Femenino España  
        "es-MX-DaliaNeural",       # Femenino México
        "es-MX-JorgeNeural",       # Masculino México
        "es-ES-AbrilNeural",       # Femenino España
        "es-ES-ArnauNeural",       # Masculino España
        "es-ES-EstrellaNeural",    # Femenino España
        "es-ES-TrianaNeural",      # Femenino España
        "es-ES-VeraNeural",        # Femenino España
    ]
    
    print(f"\nVoces populares recomendadas:")
    print("-" * 80)
    for voice_name in popular_spanish_voices:
        for voice in spanish_voices:
            if voice['ShortName'] == voice_name:
                print(f"  {voice['ShortName']:25} | {voice['Locale']:15} | {voice['Gender']:8} | {voice['FriendlyName']}")
                break
    
    return spanish_voices

if __name__ == "__main__":
    try:
        spanish_voices = asyncio.run(list_voices())
        print(f"\n✅ Total voces en español: {len(spanish_voices)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()