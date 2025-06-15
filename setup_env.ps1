# GPU と Hugging Face 環境設定スクリプト
# PowerShell で実行してください

Write-Host "=== GPU & Hugging Face 環境設定 ===" -ForegroundColor Green

# ===== Hugging Face Token 設定 =====
# トークンを取得後、以下のコメントアウトを外して実行
# $env:HF_TOKEN="your_huggingface_token_here"
# [System.Environment]::SetEnvironmentVariable("HF_TOKEN", "your_huggingface_token_here", "User")

# ===== GPU 強制使用設定 =====
$env:CUDA_VISIBLE_DEVICES="0"
$env:TORCH_CUDA_ARCH_LIST="8.6"  # RTX 30シリーズの場合（RTX 40xx系なら8.9）

# PyTorch CUDA設定
$env:PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"

Write-Host "環境変数設定完了" -ForegroundColor Green
Write-Host ""

# ===== GPU環境テスト =====
Write-Host "=== GPU環境テスト ===" -ForegroundColor Cyan
Write-Host "GPU診断スクリプトを実行中..."

try {
    $result = uv run python gpu_diagnostic.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ GPU診断完了" -ForegroundColor Green
        Write-Host $result
    } else {
        Write-Host "⚠️ GPU診断でエラーが発生しました:" -ForegroundColor Yellow
        Write-Host $result
    }
} catch {
    Write-Host "❌ GPU診断スクリプトの実行に失敗しました" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 次の手順 ===" -ForegroundColor Yellow
Write-Host "1. https://huggingface.co/settings/tokens でアクセストークンを作成"
Write-Host "2. 以下のモデルにアクセス権限を付与:"
Write-Host "   - https://huggingface.co/pyannote/speaker-diarization-3.1"
Write-Host "   - https://huggingface.co/pyannote/segmentation-3.0"
Write-Host "3. 上記のHF_TOKEN設定行のコメントアウトを外してトークンを設定"
Write-Host "4. このスクリプトを再実行"
Write-Host "5. uv run python -m src.audio_separator.gui でGUI起動"
Write-Host ""
Write-Host "💡 ヒント:"
Write-Host "  - GPU強制使用: アプリのパラメータで force_gpu=True に設定"
Write-Host "  - VRAM不足の場合: CPU処理に切り替え可能"