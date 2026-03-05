#!/usr/bin/env node

/**
 * Script Node.js para convertir modelos TensorFlow a formato web
 * Proporciona guías y opciones para conversión
 */

const fs = require('fs-extra');
const path = require('path');
const { execSync, spawn } = require('child_process');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

console.log('='.repeat(60));
console.log('CONVERSOR DE MODELOS TENSORFLOW A WEB');
console.log('='.repeat(60));

/**
 * Verificar si tensorflowjs_converter está disponible
 */
function checkPythonConverter() {
    try {
        execSync('tensorflowjs_converter --version', { stdio: 'pipe' });
        console.log('✓ tensorflowjs_converter (Python) disponible');
        return true;
    } catch (error) {
        console.log('✗ tensorflowjs_converter no encontrado');
        return false;
    }
}

/**
 * Verificar si @tensorflow/tfjs-node está disponible para conversión H5
 */
function checkTFJSNode() {
    try {
        require('@tensorflow/tfjs-node');
        console.log('✓ @tensorflow/tfjs-node disponible');
        return true;
    } catch (error) {
        console.log('✗ @tensorflow/tfjs-node no disponible');
        return false;
    }
}

/**
 * Mostrar opciones de conversión
 */
function showConversionOptions() {
    console.log('\nOPCIONES DE CONVERSIÓN DISPONIBLES:');
    console.log('1. Usar tensorflowjs_converter (Python) - RECOMENDADO');
    console.log('   Comando: tensorflowjs_converter --input_format=keras model.h5 output_dir/');
    console.log('   Requiere: pip install tensorflowjs');
    
    console.log('\n2. Usar script Python existente');
    console.log('   Comando: python convert_to_tfjs.py --input model.h5 --output output_dir');
    console.log('   Archivo: convert_to_tfjs.py');
    
    console.log('\n3. Usar Docker (ya configurado)');
    console.log('   Comando: docker-compose up convert-tfjs');
    console.log('   Configuración: docker-compose.yml');
    
    console.log('\n4. Conversión manual para modelos simples');
    console.log('   - Guardar modelo como SavedModel en Python');
    console.log('   - Usar tf.saved_model.save(model, "saved_model")');
    console.log('   - Luego convertir con opción 1 o 2');
}

/**
 * Generar script Python para conversión
 */
function generatePythonScript(inputPath, outputDir) {
    const scriptContent = `#!/usr/bin/env python3
import tensorflow as tf
import tensorflowjs as tfjs
import os
import sys

def convert_model(input_path, output_dir):
    print(f"Convirtiendo: {input_path} -> {output_dir}")
    
    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    
    # Cargar modelo
    print("Cargando modelo...")
    model = tf.keras.models.load_model(input_path)
    print(f"Modelo cargado: {model.input_shape} -> {model.output_shape}")
    
    # Convertir a TensorFlow.js
    print("Convirtiendo a TensorFlow.js...")
    tfjs.converters.save_keras_model(model, output_dir)
    
    print(f"Conversión completada en: {output_dir}")
    
    # Listar archivos generados
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            print(f"  {file} ({size} bytes)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python convert_simple.py <input_model.h5> <output_dir>")
        sys.exit(1)
    
    convert_model(sys.argv[1], sys.argv[2])
`;
    
    const scriptPath = path.join(process.cwd(), 'convert_simple.py');
    fs.writeFileSync(scriptPath, scriptContent);
    console.log(`\nScript Python generado: ${scriptPath}`);
    console.log(`Ejecutar: python ${scriptPath} "${inputPath}" "${outputDir}"`);
    
    return scriptPath;
}

/**
 * Crear estructura de directorios para modelo web
 */
function createWebModelStructure(modelName, outputDir) {
    const structure = {
        'model.json': `{
  "format": "layers-model",
  "generatedBy": "TensorFlow.js Converter",
  "convertedBy": "Node.js Script",
  "modelTopology": {},
  "weightsManifest": []
}`,
        'metadata.json': `{
  "modelName": "${modelName}",
  "description": "Modelo convertido para uso web",
  "inputShape": "unknown",
  "outputShape": "unknown",
  "conversionDate": "${new Date().toISOString()}",
  "originalFormat": "keras/h5"
}`
    };
    
    // Crear directorio
    fs.ensureDirSync(outputDir);
    
    // Escribir archivos
    for (const [filename, content] of Object.entries(structure)) {
        const filepath = path.join(outputDir, filename);
        fs.writeFileSync(filepath, content);
        console.log(`  Creado: ${filename}`);
    }
    
    console.log(`\nEstructura básica creada en: ${outputDir}`);
    console.log('NOTA: Esta es una estructura de ejemplo. Para un modelo real,');
    console.log('      usa tensorflowjs_converter para conversión completa.');
}

/**
 * Función principal
 */
async function main() {
    const argv = yargs(hideBin(process.argv))
        .option('input', {
            alias: 'i',
            type: 'string',
            description: 'Ruta al modelo de entrada (.h5)'
        })
        .option('output', {
            alias: 'o',
            type: 'string',
            description: 'Directorio de salida',
            default: 'trained_web/tfjs_model'
        })
        .option('method', {
            alias: 'm',
            type: 'string',
            description: 'Método de conversión (python, docker, manual)',
            default: 'python'
        })
        .option('check', {
            type: 'boolean',
            description: 'Solo verificar dependencias',
            default: false
        })
        .help()
        .alias('help', 'h')
        .argv;
    
    // Verificar dependencias
    console.log('\nVERIFICANDO DEPENDENCIAS:');
    const hasPythonConverter = checkPythonConverter();
    const hasTFJSNode = checkTFJSNode();
    
    if (argv.check) {
        showConversionOptions();
        process.exit(0);
    }
    
    // Si no hay entrada, mostrar ayuda
    if (!argv.input) {
        console.log('\nUSO:');
        console.log('  node scripts/convert_model.js --input model.h5 --output output_dir');
        console.log('  node scripts/convert_model.js --check (verificar dependencias)');
        console.log('\nEJEMPLOS:');
        console.log('  node scripts/convert_model.js --input trained_python_fast/model.h5 --output trained_web/tfjs_model');
        console.log('  npm run convert-h5 (usando package.json scripts)');
        
        showConversionOptions();
        process.exit(0);
    }
    
    // Verificar archivo de entrada
    const inputPath = path.resolve(argv.input);
    const outputDir = path.resolve(argv.output);
    
    if (!fs.existsSync(inputPath)) {
        console.error(`\nERROR: Archivo de entrada no encontrado: ${inputPath}`);
        process.exit(1);
    }
    
    console.log(`\nCONFIGURACIÓN:`);
    console.log(`  Input:  ${inputPath}`);
    console.log(`  Output: ${outputDir}`);
    console.log(`  Método: ${argv.method}`);
    
    // Procesar según método
    switch (argv.method) {
        case 'python':
            if (hasPythonConverter) {
                console.log('\nEJECUTANDO CONVERSIÓN CON tensorflowjs_converter...');
                const command = `tensorflowjs_converter --input_format=keras "${inputPath}" "${outputDir}"`;
                console.log(`Comando: ${command}`);
                
                try {
                    execSync(command, { stdio: 'inherit' });
                    console.log(`\n✅ CONVERSIÓN COMPLETADA`);
                    console.log(`Modelo disponible en: ${outputDir}`);
                } catch (error) {
                    console.error(`\n❌ ERROR EN CONVERSIÓN: ${error.message}`);
                    console.log('\nIntentando generar script Python alternativo...');
                    generatePythonScript(inputPath, outputDir);
                }
            } else {
                console.log('\n❌ tensorflowjs_converter no disponible');
                console.log('Instalar con: pip install tensorflowjs');
                console.log('\nGenerando script Python alternativo...');
                generatePythonScript(inputPath, outputDir);
            }
            break;
            
        case 'docker':
            console.log('\nEJECUTANDO CONVERSIÓN CON DOCKER...');
            console.log('Nota: Asegúrate de que Docker esté corriendo');
            console.log('Comando: docker-compose up convert-tfjs');
            
            try {
                execSync('docker-compose up convert-tfjs', { stdio: 'inherit' });
            } catch (error) {
                console.error(`\n❌ ERROR CON DOCKER: ${error.message}`);
                console.log('Verifica que docker-compose.yml esté configurado correctamente');
            }
            break;
            
        case 'manual':
            console.log('\nCREANDO ESTRUCTURA MANUAL PARA MODELO WEB...');
            const modelName = path.basename(inputPath, '.h5');
            createWebModelStructure(modelName, outputDir);
            console.log('\n⚠️  Esta es solo una estructura básica.');
            console.log('   Para conversión real del modelo, usa:');
            console.log('   1. tensorflowjs_converter (recomendado)');
            console.log('   2. El script Python convert_to_tfjs.py');
            break;
            
        default:
            console.error(`\n❌ Método no válido: ${argv.method}`);
            console.log('Métodos disponibles: python, docker, manual');
            process.exit(1);
    }
    
    // Mostrar instrucciones finales
    console.log('\n' + '='.repeat(60));
    console.log('INSTRUCCIONES PARA USO EN WEB:');
    console.log('='.repeat(60));
    console.log('1. En app_tfjs.js, actualiza la ruta del modelo:');
    console.log(`   const model = await tf.loadLayersModel('${path.relative(process.cwd(), outputDir)}/model.json');`);
    console.log('\n2. Asegúrate de que el modelo esté accesible desde el navegador:');
    console.log('   - Copia el directorio a public/models/');
    console.log('   - O configura un servidor estático');
    console.log('\n3. Para probar el modelo convertido:');
    console.log('   npm run test (usa scripts/test_model.js)');
    console.log('='.repeat(60));
}

// Ejecutar
if (require.main === module) {
    main().catch(error => {
        console.error('ERROR FATAL:', error);
        process.exit(1);
    });
}

module.exports = {
    checkPythonConverter,
    checkTFJSNode,
    showConversionOptions,
    generatePythonScript,
    createWebModelStructure
};