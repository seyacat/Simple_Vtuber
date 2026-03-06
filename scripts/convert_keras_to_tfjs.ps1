$currentPath = (Get-Location).Path
$outputDir = "$currentPath\trained_web\tfjs_model"

if (Test-Path $outputDir) {
    Remove-Item -Path $outputDir -Recurse -Force
}

Write-Host "CONVERSION A TENSORFLOW.JS"
Write-Host "Input:  $currentPath\trained_python_fast\model.keras"
Write-Host "Output: $outputDir"

# Para archivos .keras, necesitamos usar --input_format=keras_saved_model
docker run --rm -v "${currentPath}:/app" --entrypoint tensorflowjs_converter simple_vtuber-convert-tfjs --input_format=keras_saved_model /app/trained_python_fast/model.keras /app/trained_web/tfjs_model

if ($LASTEXITCODE -eq 0) {
    Write-Host "CONVERSION EXITOSA"
} else {
    Write-Host "CONVERSION FALLIDA"
    exit 1
}