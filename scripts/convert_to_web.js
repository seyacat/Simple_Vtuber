#!/usr/bin/env node

/**
 * Script Node.js para convertir modelos TensorFlow a formato web
 * Soporta:
 * - Modelos Keras H5 (.h5) a TensorFlow.js
 * - Modelos SavedModel a TensorFlow.js
 * - Conversión a formato compatible con navegador
 */

const fs = require('fs-extra');
const path = require('path');
const { execSync } = require('child_process');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

// Verificar si TensorFlow.js está disponible
let tf;
let tfconv;
try {
    tf = require('@tensorflow/tfjs');
    tfconv = require('@tensorflow/tfjs-converter');
    console.log('✓ TensorFlow.js y tfjs-converter cargados');
} catch (error) {
    console.error('Error: @tensorflow/tfjs-converter no está instalado');
    console.error('Instalar con: npm install @tensorflow/tfjs-converter');
    process.exit(1);
}

/**
 * Instalar dependencias necesarias
 */
async function installDependencies() {
    console.log('Verificando dependencias...');
    
    try {
        // Verificar si tensorflowjs_converter está disponible
        execSync('tensorflowjs_converter --version', { stdio: 'pipe' });
        console.log('✓ tensorflowjs_converter disponible');
        return true;
    } catch (error) {
        console.log('tensorflowjs_converter no encontrado, intentando instalar...');
        
        try {
            // Intentar instalar tensorflowjs globalmente
            execSync('npm install -g @tensorflow/tfjs-converter', { stdio: 'inherit' });
            console.log('✓ @tensorflow/tfjs-converter instalado globalmente');
            return true;
        } catch (installError) {
            console.error('✗ Error instalando tensorflowjs_converter:', installError.message);
            console.error('Instalar manualmente: pip install tensorflowjs');
            return false;
        }
    }
}

/**
 * Convertir modelo H5 a TensorFlow.js usando Python tensorflowjs_converter
 * @param {string} inputPath - Ruta al archivo .h5
 * @param {string} outputDir - Directorio de salida
 * @returns {boolean} - True si la conversión fue exitosa
 */
function convertH5WithPython(inputPath, outputDir) {
    console.log(`Convirtiendo modelo H5: ${inputPath} -> ${outputDir}`);
    
    try {
        // Crear directorio de salida
        fs.ensureDirSync(outputDir);
        
        // Ejecutar tensorflowjs_converter
        const command = `tensorflowjs_converter --input_format=keras "${inputPath}" "${outputDir}"`;
        console.log(`Ejecutando: ${command}`);
        
        execSync(command, { stdio: 'inherit' });
        
        // Verificar archivos generados
        const files = fs.readdirSync(outputDir);
        console.log(`✓ Conversión completada: ${files.length} archivos generados`);
        
        // Mostrar estructura
        console.log('\nEstructura del modelo TensorFlow.js:');
        files.forEach(file => {
            const filePath = path.join(outputDir, file);
            const stats = fs.statSync(filePath);
            if (stats.isFile()) {
                console.log(`  📄 ${file} (${(stats.size / 1024).toFixed(2)} KB)`);
            } else {
                console.log(`  📁 ${file}/`);
            }
        });
        
        return true;
    } catch (error) {
        console.error(`✗ Error en conversión H5: ${error.message}`);
        return false;
    }
}

/**
 * Convertir SavedModel a TensorFlow.js usando Python tensorflowjs_converter
 * @param {string} inputDir - Directorio del SavedModel
 * @param {string} outputDir - Directorio de salida
 * @returns {boolean} - True si la conversión fue exitosa
 */
function convertSavedModelWithPython(inputDir, outputDir) {
    console.log(`Convirtiendo SavedModel: ${inputDir} -> ${outputDir}`);
    
    try {
        // Verificar que es un SavedModel válido
        const savedModelPb = path.join(inputDir, 'saved_model.pb');
        if (!fs.existsSync(savedModelPb)) {
            console.error(`✗ No es un SavedModel válido: ${savedModelPb} no encontrado`);
            return false;
        }
        
        // Crear directorio de salida
        fs.ensureDirSync(outputDir);
        
        // Ejecutar tensorflowjs_converter para SavedModel
        const command = `tensorflowjs_converter --input_format=tf_saved_model "${inputDir}" "${outputDir}"`;
        console.log(`Ejecutando: ${command}`);
        
        execSync(command, { stdio: 'inherit' });
        
        // Verificar archivos generados
        const files = fs.readdirSync(outputDir);
        console.log(`✓ Conversión completada: ${files.length} archivos generados`);
        
        return true;
    } catch (error) {
        console.error(`✗ Error en conversión SavedModel: ${error.message}`);
        return false;
    }
}

/**
 * Convertir usando la API de TensorFlow.js (Node.js puro)
 * @param {string} inputPath - Ruta al modelo
 * @param {string} outputDir - Directorio de salida
 * @param {string} format - Formato de entrada (keras, tf_saved_model)
 * @returns {boolean} - True si la conversión fue exitosa
 */
async function convertWithTFJS(inputPath, outputDir, format = 'keras') {
    console.log(`Convirtiendo con TensorFlow.js API: ${inputPath} -> ${outputDir}`);
    
    try {
        // Crear directorio de salida
        await fs.ensureDir(outputDir);
        
        // Nota: La API de conversión de TensorFlow.js en Node.js es limitada
        // En la práctica, tensorflowjs_converter (Python) es más robusto
        console.log('⚠️  La conversión directa con TensorFlow.js API puede ser limitada');
        console.log('   Considera usar tensorflowjs_converter (Python) para mejor compatibilidad');
        
        // Para modelos Keras H5, podríamos cargar y guardar
        if (format === 'keras' && inputPath.endsWith('.h5')) {
            console.log('⚠️  La carga directa de .h5 en Node.js requiere tensorflowjs-node-gpu');
            console.log('   Usando método Python como fallback...');
            return convertH5WithPython(inputPath, outputDir);
        }
        
        return false;
    } catch (error) {
        console.error(`✗ Error en conversión TF.js API: ${error.message}`);
        return false;
    }
}

/**
 * Copiar modelo convertido a directorio público para web
 * @param {string} sourceDir - Directorio del modelo convertido
 * @param {string} targetDir - Directorio público destino
 */
function copyToPublic(sourceDir, targetDir) {
    console.log(`Copiando modelo a directorio público: ${sourceDir} -> ${targetDir}`);
    
    try {
        // Crear directorio destino
        fs.ensureDirSync(targetDir);
        
        // Copiar archivos
        fs.copySync(sourceDir, targetDir, { overwrite: true });
        
        // Verificar copia
        const sourceFiles = fs.readdirSync(sourceDir);
        const targetFiles = fs.readdirSync(targetDir);
        
        console.log(`✓ Copia completada: ${sourceFiles.length} archivos copiados`);
        
        // Crear archivo de metadatos
        const metadata = {
            convertedAt: new Date().toISOString(),
            source: sourceDir,
            target: targetDir,
            files: targetFiles
        };
        
        const metadataPath = path.join(targetDir, 'conversion_metadata.json');
        fs.writeJsonSync(metadataPath, metadata, { spaces: 2 });
        
        console.log(`✓ Metadatos guardados en: ${metadataPath}`);
        
        return true;
    } catch (error) {
        console.error(`✗ Error copiando a público: ${error.message}`);
        return false;
    }
}

/**
 * Validar modelo convertido
 * @param {string} modelDir - Directorio del modelo convertido
 * @returns {boolean} - True si el modelo es válido
 */
async function validateConvertedModel(modelDir) {
    console.log(`Validando modelo convertido en: ${modelDir}`);
    
    try {
        // Verificar archivos esenciales
        const modelJsonPath = path.join(modelDir, 'model.json');
        if (!fs.existsSync(modelJsonPath)) {
            console.error(`✗ model.json no encontrado en: ${modelDir}`);
            return false;
        }
        
        // Intentar cargar el modelo con TensorFlow.js
        console.log('Intentando cargar modelo con TensorFlow.js...');
        const model = await tf.loadLayersModel(`file://${modelJsonPath}`);
        
        console.log(`✓ Modelo cargado exitosamente`);
        console.log(`  Input shape: ${JSON.stringify(model.inputs[0].shape)}`);
        console.log(`  Output shape: ${JSON.stringify(model.outputs[0].shape)}`);
        console.log(`  Layers: ${model.layers.length}`);
        
        // Liberar memoria
        model.dispose();
        
        return true;
    } catch (error) {
        console.error(`✗ Error validando modelo: ${error.message}`);
        return false;
    }
}

/**
 * Función principal
 */
async function main() {
    const argv = yargs(hideBin(process.argv))
        .option('input', {
            alias: 'i',
            type: 'string',
            description: 'Ruta al modelo de entrada (.h5 o directorio SavedModel)',
            demandOption: true
        })
        .option('output', {
            alias: 'o',
            type: 'string',
            description: 'Directorio de salida para el modelo TensorFlow.js',
            demandOption: true
        })
        .option('format', {
            alias: 'f',
            type: 'string',
            description: 'Formato de entrada (keras, saved_model, auto)',
            default: 'auto',
            choices: ['keras', 'saved_model', 'auto']
        })
        .option('to-public', {
            type: 'string',
            description: 'También copiar a directorio público (ej: public/models/)'
        })
        .option('validate', {
            type: 'boolean',
            description: 'Validar modelo después de conversión',
            default: true
        })
        .help()
        .alias('help', 'h')
        .argv;
    
    console.log('='.repeat(60));
    console.log('CONVERSIÓN DE MODELO TENSORFLOW A WEB (Node.js)');
    console.log('='.repeat(60));
    
    // Verificar entrada
    const inputPath = path.resolve(argv.input);
    const outputDir = path.resolve(argv.output);
    
    if (!fs.existsSync(inputPath)) {
        console.error(`✗ Ruta de entrada no existe: ${inputPath}`);
        process.exit(1);
    }
    
    console.log(`Input:  ${inputPath}`);
    console.log(`Output: ${outputDir}`);
    console.log(`Format: ${argv.format}`);
    console.log('='.repeat(60));
    
    // Determinar formato automáticamente si es 'auto'
    let format = argv.format;
    if (format === 'auto') {
        if (inputPath.endsWith('.h5')) {
            format = 'keras';
            console.log(`Formato detectado: keras (.h5)`);
        } else if (fs.existsSync(path.join(inputPath, 'saved_model.pb'))) {
            format = 'saved_model';
            console.log(`Formato detectado: saved_model`);
        } else {
            console.error('✗ No se pudo detectar el formato del modelo');
            console.error('   Especifica manualmente con --format keras o --format saved_model');
            process.exit(1);
        }
    }
    
    // Instalar/verificar dependencias
    const depsOk = await installDependencies();
    if (!depsOk) {
        console.error('✗ Dependencias insuficientes para conversión');
        process.exit(1);
    }
    
    // Realizar conversión según formato
    let success = false;
    
    if (format === 'keras') {
        success = convertH5WithPython(inputPath, outputDir);
    } else if (format === 'saved_model') {
        success = convertSavedModelWithPython(inputPath, outputDir);
    } else {
        console.error(`✗ Formato no soportado: ${format}`);
        process.exit(1);
    }
    
    if (!success) {
        console.error('✗ La conversión falló');
        process.exit(1);
    }
    
    // Validar modelo convertido
    if (argv.validate) {
        const valid = await validateConvertedModel(outputDir);
        if (!valid) {
            console.warn('⚠️  El modelo convertido podría tener problemas');
        }
    }
    
    // Copiar a directorio público si se especificó
    if (argv.toPublic) {
        const publicDir = path.resolve(argv.toPublic);
        copyToPublic(outputDir, publicDir);
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ CONVERSIÓN COMPLETADA EXITOSAMENTE');
    console.log('='.repeat(60));
    console.log(`Modelo TensorFlow.js disponible en:`);
    console.log(`  ${outputDir}`);
    console.log('\nPara usar en la aplicación web:');
    console.log(`1. Referenciar en app_tfjs.js:`);
    console.log(`   const model = await tf.loadLayersModel('${path.basename(outputDir)}/model.json');`);
    console.log(`2. O servir desde: http://localhost/models/${path.basename(outputDir)}/`);
    console.log('='.repeat(60));
}

// Ejecutar script
if (require.main === module) {
    main().catch(error => {
        console.error('✗ Error fatal:', error);
        process.exit(1);
    });
}

module.exports = {
    convertH5WithPython,
    convertSavedModelWithPython,
    convertWithTFJS,
    copyToPublic,
    validateConvertedModel
};