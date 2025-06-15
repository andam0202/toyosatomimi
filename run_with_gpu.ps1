# GPU強制使用でアプリケーションを起動

Write-Host "=== GPU強制使用設定 ===" -ForegroundColor Green

# 環境変数設定
$env:CUDA_VISIBLE_DEVICES="0"
$env:TORCH_CUDA_ARCH_LIST="8.6"
$env:PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
$env:FORCE_GPU="1"

# Hugging Face token確認
if (-not $env:HF_TOKEN) {
    Write-Host "⚠️ HF_TOKEN環境変数が設定されていません" -ForegroundColor Yellow
    Write-Host "以下で設定してください: `$env:HF_TOKEN='your_token_here'" -ForegroundColor Yellow
}

# GPU環境確認
Write-Host "GPU環境確認中..." -ForegroundColor Cyan
$gpuCheck = uv run python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU数: {torch.cuda.device_count()}')" 2>&1
Write-Host $gpuCheck

if ($gpuCheck -match "CUDA: True") {
    Write-Host "✅ GPU利用可能 - アプリケーションを起動します" -ForegroundColor Green
    uv run python -m src.audio_separator.gui
} else {
    Write-Host "❌ GPU利用不可 - CUDA版PyTorchをインストールしてください" -ForegroundColor Red
    Write-Host "インストールコマンド:" -ForegroundColor Yellow
    Write-Host "uv pip install torch==2.4.0+cu121 torchvision==0.19.0+cu121 torchaudio==2.4.0+cu121 --index-url https://download.pytorch.org/whl/cu121"
}