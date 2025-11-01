# FFmpeg Video Composition Script
# Combine two videos: UE Render Frames + Frustum Visualization

param(
    [string]$BaseDir = "D:\ue5\projects\first\Saved\Screenshots\end\Horse_and_Car",  # Base directory containing render frames
    [int]$Fps = 1,
    [string]$OutputName = "combined_video.mp4"
)

# Path setup
$renderFramesDir = $BaseDir
$frustumOutputDir = "$BaseDir\output"  # Frustum visualization output subdirectory
$outputVideo = "$BaseDir\$OutputName"

Write-Host "=== FFmpeg Video Composition Script ===" -ForegroundColor Cyan
Write-Host "Render frames dir: $renderFramesDir" -ForegroundColor Yellow
Write-Host "Frustum frames dir: $frustumOutputDir" -ForegroundColor Yellow
Write-Host "Output video: $outputVideo" -ForegroundColor Green

# Check directories exist
if (-Not (Test-Path $renderFramesDir)) {
    Write-Host "[ERROR] Render frames directory not found: $renderFramesDir" -ForegroundColor Red
    exit 1
}

if (-Not (Test-Path $frustumOutputDir)) {
    Write-Host "[ERROR] Frustum frames directory not found: $frustumOutputDir" -ForegroundColor Red
    exit 1
}

# Temporary video files
$tempVideo1 = "$BaseDir\temp_render.mp4"
$tempVideo2 = "$BaseDir\temp_frustum.mp4"

Write-Host "`n--- Step 1: Generate render frames video ---" -ForegroundColor Cyan

# Detect starting frame number from render frames directory
$firstFrame = Get-ChildItem -Path $renderFramesDir -Filter "frame_*.png" | 
              Sort-Object Name | 
              Select-Object -First 1

if ($null -eq $firstFrame) {
    Write-Host "[ERROR] No frame_*.png files found in $renderFramesDir" -ForegroundColor Red
    exit 1
}

# Extract starting frame number from filename
$startNumber = [int]($firstFrame.Name -replace 'frame_(\d+)\.png', '$1')
Write-Host "Detected start frame number: $startNumber" -ForegroundColor Cyan

# Generate render frames video with H.264 encoding
ffmpeg -y -framerate $Fps `
    -start_number $startNumber `
    -i "$renderFramesDir\frame_%04d.png" `
    -c:v libx264 -pix_fmt yuv420p -crf 18 `
    $tempVideo1

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to generate render video!" -ForegroundColor Red
    exit 1
}

Write-Host "`n--- Step 2: Generate frustum frames video ---" -ForegroundColor Cyan

# Detect starting frame number from frustum output directory
# Frustum frames are directly in output subdirectory, named as frame_XXXX.png
$firstFrustumFrame = Get-ChildItem -Path $frustumOutputDir -Filter "frame_*.png" | 
                     Sort-Object Name | 
                     Select-Object -First 1

if ($null -eq $firstFrustumFrame) {
    Write-Host "[ERROR] No frame_*.png files found in $frustumOutputDir" -ForegroundColor Red
    exit 1
}

$frustumStartNumber = [int]($firstFrustumFrame.Name -replace 'frame_(\d+)\.png', '$1')
Write-Host "Detected frustum start frame number: $frustumStartNumber" -ForegroundColor Cyan

# Generate frustum video (same encoding as render video)
ffmpeg -y -framerate $Fps `
    -start_number $frustumStartNumber `
    -i "$frustumOutputDir\frame_%04d.png" `
    -c:v libx264 -pix_fmt yuv420p -crf 18 `
    $tempVideo2

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to generate frustum video!" -ForegroundColor Red
    exit 1
}

Write-Host "`n--- Step 3: Stack videos horizontally ---" -ForegroundColor Cyan
# Scale both videos to 480p height and stack them side-by-side
ffmpeg -y -i $tempVideo1 -i $tempVideo2 `
    -filter_complex "[0:v]scale=-1:480[v0];[1:v]scale=-1:480[v1];[v0][v1]hstack=inputs=2[v]" `
    -map "[v]" `
    -c:v libx264 -pix_fmt yuv420p -crf 18 `
    $outputVideo

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Video created: $outputVideo" -ForegroundColor Green
    
    # Cleanup temporary video files
    Write-Host "`n--- Cleaning up temporary files ---" -ForegroundColor Cyan
    Remove-Item $tempVideo1 -ErrorAction SilentlyContinue
    Remove-Item $tempVideo2 -ErrorAction SilentlyContinue
    Write-Host "[SUCCESS] Temporary files removed" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Failed to stack videos!" -ForegroundColor Red
    Write-Host "Temp video 1: $tempVideo1" -ForegroundColor Yellow
    Write-Host "Temp video 2: $tempVideo2" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan