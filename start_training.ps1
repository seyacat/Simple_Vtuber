# Script PowerShell para inicio rápido de entrenamiento Docker en Windows

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "ENTRENAMIENTO TENSORFLOW DOCKER - WINDOWS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Docker
Write-Host "Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker instalado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker no está instalado" -ForegroundColor Red
    Write-Host "  Descargar Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Verificar Docker Compose
Write-Host "Verificando Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose instalado: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠  Docker Compose no encontrado, probando 'docker compose'..." -ForegroundColor Yellow
    try {
        $composeVersion = docker compose version
        Write-Host "✓ Docker Compose (nativo) instalado" -ForegroundColor Green
        $dockerComposeCmd = "docker compose"
    } catch {
        Write-Host "✗ Docker Compose no está disponible" -ForegroundColor Red
        Write-Host "  Instalar Docker Compose o actualizar Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
}

# Verificar GPU NVIDIA (opcional)
Write-Host "Verificando GPU NVIDIA..." -ForegroundColor Yellow
try {
    $nvidiaSmi = nvidia-smi
    Write-Host "✓ GPU NVIDIA detectada" -ForegroundColor Green
    
    # Verificar NVIDIA Container Toolkit
    Write-Host "Verificando NVIDIA Container Toolkit..." -ForegroundColor Yellow
    try {
        docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi > $null 2>&1
        Write-Host "✓ NVIDIA Container Toolkit funcionando" -ForegroundColor Green
        $gpuAvailable = $true
    } catch {
        Write-Host "⚠  NVIDIA Container Toolkit no configurado correctamente" -ForegroundColor Yellow
        Write-Host "  GPU acceleration puede no funcionar" -ForegroundColor Yellow
        $gpuAvailable = $false
    }
} catch {
    Write-Host "⚠  No se detectó GPU NVIDIA" -ForegroundColor Yellow
    Write-Host "  El entrenamiento usará CPU (más lento)" -ForegroundColor Yellow
    $gpuAvailable = $false
}

# Construir imagen Docker
Write-Host ""
Write-Host "Construyendo imagen Docker..." -ForegroundColor Cyan
try {
    if ($dockerComposeCmd) {
        Invoke-Expression "$dockerComposeCmd build"
    } else {
        docker-compose build
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Imagen Docker construida exitosamente" -ForegroundColor Green
    } else {
        Write-Host "✗ Error construyendo imagen Docker" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
    exit 1
}

# Convertir características a formato optimizado
Write-Host ""
Write-Host "Preparando datos para entrenamiento rápido..." -ForegroundColor Cyan
if (Test-Path "dataset\features.json") {
    Write-Host "✓ Características ya extraídas" -ForegroundColor Green
    
    # Verificar si ya está convertido a numpy
    if (-not (Test-Path "dataset\numpy\features.npy")) {
        Write-Host "Convirtiendo a formato optimizado..." -ForegroundColor Yellow
        try {
            python convert_to_numpy.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Conversión completada" -ForegroundColor Green
            }
        } catch {
            Write-Host "⚠  No se pudo convertir, continuando..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "✓ Datos ya convertidos a formato optimizado" -ForegroundColor Green
    }
} else {
    Write-Host "⚠  No se encontraron características extraídas" -ForegroundColor Yellow
    Write-Host "  Se extraerán automáticamente durante el entrenamiento" -ForegroundColor Yellow
}

# Mostrar opciones
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "OPCIONES DE ENTRENAMIENTO" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Pipeline completo con GPU (RECOMENDADO si tiene GPU)" -ForegroundColor White
Write-Host "2. Pipeline completo con CPU" -ForegroundColor White
Write-Host "3. Solo extraer características" -ForegroundColor White
Write-Host "4. Solo entrenar (asume características ya extraídas)" -ForegroundColor White
Write-Host "5. TensorBoard para monitoreo" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Seleccione opción (1-5)"

switch ($choice) {
    "1" {
        if ($gpuAvailable) {
            Write-Host "Iniciando pipeline completo con GPU..." -ForegroundColor Green
            if ($dockerComposeCmd) {
                Invoke-Expression "$dockerComposeCmd up pipeline-gpu"
            } else {
                docker-compose up pipeline-gpu
            }
        } else {
            Write-Host "⚠  GPU no disponible, usando CPU en su lugar" -ForegroundColor Yellow
            Write-Host "Iniciando pipeline completo con CPU..." -ForegroundColor Green
            if ($dockerComposeCmd) {
                Invoke-Expression "$dockerComposeCmd up pipeline-lightning"
            } else {
                docker-compose up pipeline-lightning
            }
        }
    }
    "2" {
        Write-Host "Iniciando pipeline completo con CPU..." -ForegroundColor Green
        if ($dockerComposeCmd) {
            Invoke-Expression "$dockerComposeCmd up pipeline-lightning"
        } else {
            docker-compose up pipeline-lightning
        }
    }
    "3" {
        Write-Host "Extrayendo características..." -ForegroundColor Green
        if ($dockerComposeCmd) {
            Invoke-Expression "$dockerComposeCmd up extract-features"
        } else {
            docker-compose up extract-features
        }
    }
    "4" {
        Write-Host "Iniciando solo entrenamiento..." -ForegroundColor Green
        if ($gpuAvailable) {
            if ($dockerComposeCmd) {
                Invoke-Expression "$dockerComposeCmd up train-only"
            } else {
                docker-compose up train-only
            }
        } else {
            Write-Host "⚠  GPU no disponible, entrenamiento será más lento" -ForegroundColor Yellow
            if ($dockerComposeCmd) {
                Invoke-Expression "$dockerComposeCmd up train-only"
            } else {
                docker-compose up train-only
            }
        }
    }
    "5" {
        Write-Host "Iniciando TensorBoard..." -ForegroundColor Green
        Write-Host "Abrir en navegador: http://localhost:6006" -ForegroundColor Yellow
        if ($dockerComposeCmd) {
            Invoke-Expression "$dockerComposeCmd up tensorboard"
        } else {
            docker-compose up tensorboard
        }
    }
    default {
        Write-Host "Opción no válida" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "INSTRUCCIONES ADICIONALES" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Comandos manuales:" -ForegroundColor White
Write-Host ""
Write-Host "• Pipeline completo con GPU:" -ForegroundColor Gray
Write-Host "  docker-compose up pipeline-gpu" -ForegroundColor DarkGray
Write-Host ""
Write-Host "• Pipeline con modelo lightning (máxima velocidad):" -ForegroundColor Gray
Write-Host "  docker-compose up pipeline-lightning" -ForegroundColor DarkGray
Write-Host ""
Write-Host "• Solo extraer características:" -ForegroundColor Gray
Write-Host "  docker-compose up extract-features" -ForegroundColor DarkGray
WriteHost ""
Write-Host "• TensorBoard:" -ForegroundColor Gray
Write-Host "  docker-compose up tensorboard" -ForegroundColor DarkGray
Write-Host "  Luego abrir: http://localhost:6006" -ForegroundColor DarkGray
Write-Host ""
Write-Host "• Detener todos los contenedores:" -ForegroundColor Gray
Write-Host "  docker-compose down" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Modelos guardados en: trained_python_fast\" -ForegroundColor Yellow
Write-Host "Logs en: logs\tensorboard\fast_gpu\" -ForegroundColor Yellow