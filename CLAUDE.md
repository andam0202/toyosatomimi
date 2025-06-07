# CLAUDE.md

このファイルは、このリポジトリでコードを扱う際のClaude Code (claude.ai/code) への指針を提供します。
Claude Codeは以降日本語で出力をしてください。

## プロジェクト概要

toyosatomimi（音声分離アプリケーション）は、複数の話者とBGMが含まれる音声ファイルから、各話者の音声を個別に抽出するPythonアプリケーションです。

**主要機能:**
1. **BGM分離**: Demucs（htdemucs）を使用してボーカルとBGMを分離
2. **話者分離**: pyannote-audio v3.1を使用して各話者を識別・分離
3. **GPU加速**: CUDA対応による高速処理
4. **フォールバック機能**: pyannote-audioが利用できない場合の簡易分離

## プロジェクト構造

```
toyosatomimi/
├── src/audio_separator/           # コア処理モジュール
│   ├── __init__.py
│   ├── main.py                   # メインアプリケーション
│   ├── processors/               # 音声処理プロセッサ
│   │   ├── __init__.py
│   │   ├── demucs_processor.py   # BGM分離（Demucs）
│   │   └── speaker_processor.py  # 話者分離（pyannote-audio）
│   └── utils/                    # ユーティリティ
│       ├── __init__.py
│       ├── audio_utils.py        # 音声処理ユーティリティ
│       ├── config_manager.py     # 設定管理
│       └── file_utils.py         # ファイル操作
├── tests/                        # テストディレクトリ
│   ├── README.md                 # テスト実行ガイド
│   ├── outputs/                  # テスト出力先（デフォルト）
│   │   └── latest/              # 最新の実行結果
│   ├── test_real_audio.py        # 実音声統合テスト
│   ├── test_integrated_separation.py # BGM+話者分離統合テスト
│   ├── test_speaker_simple.py    # pyannote-audio環境チェック
│   └── test_speaker_tuning.py    # 話者分離パラメータ調整
├── data/input/                   # 入力音声ファイル
├── config/                       # 設定ファイル
├── pyproject.toml               # Python依存関係定義
└── DEVELOPMENT_PLAN.md          # 開発計画書（5フェーズ）
```

## 開発環境セットアップ

### 必要な環境
- **Python**: 3.10+
- **GPU**: NVIDIA GPU（CUDA 12.1対応）推奨
- **メモリ**: 8GB以上のRAM（GPU: 6GB VRAM推奨）
- **OS**: Linux/Windows（WSL2推奨）

### 依存関係インストール

```bash
# 仮想環境のアクティベート
source .venv/bin/activate

# 主要パッケージのインストール
pip install pyannote.audio  # 話者分離
pip install demucs          # BGM分離

# その他の依存関係
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121  # CUDA対応PyTorch
pip install librosa soundfile scipy  # 音声処理
```

### Hugging Face認証設定（pyannote-audio用）

```bash
# 環境変数設定
export HF_TOKEN='your_huggingface_token_here'

# モデルライセンス同意が必要:
# https://huggingface.co/pyannote/speaker-diarization-3.1
```

## テスト実行

### 基本テスト

```bash
# プロジェクトルートで実行
cd /path/to/toyosatomimi

# 環境チェック（pyannote-audio利用可能性）
source .venv/bin/activate
export HF_TOKEN='your_token'
python tests/test_speaker_simple.py

# 実音声ファイルでの統合テスト（推奨）
python tests/test_real_audio.py data/input/input_wav.wav

# 出力先指定
python tests/test_real_audio.py data/input/input_wav.wav tests/outputs/my_test
```

### 出力ディレクトリ

全てのテストはデフォルトで `tests/outputs/latest/` に出力されます：

```
tests/outputs/latest/
├── bgm_separated/           # BGM分離結果
│   ├── vocals.wav          # ボーカル音声（BGM除去済み）
│   └── bgm.wav            # BGM音声
└── speakers/              # 話者別音声
    ├── speaker_SPEAKER_00/ # 話者1
    │   ├── segment_001.wav # 個別セグメント
    │   ├── segment_002.wav
    │   └── speaker_SPEAKER_00_combined.wav  # 統合音声
    ├── speaker_SPEAKER_01/ # 話者2
    └── speaker_SPEAKER_02/ # 話者3
```

## 処理フロー

```
入力音声（混合） 
    ↓
1. BGM分離（Demucs htdemucs）
    ├── vocals.wav（ボーカル）
    └── bgm.wav（BGM）
    ↓
2. 話者分離（pyannote-audio）
    ├── セグメント検出
    └── 話者識別
    ↓
3. 音声抽出
    ├── speaker_SPEAKER_00/
    ├── speaker_SPEAKER_01/
    └── speaker_SPEAKER_XX/
```

## 技術的詳細

### BGM分離（DemucsProcessor）
- **モデル**: `htdemucs`（高品質音源分離）
- **GPU加速**: CUDA対応で大幅な高速化
- **処理時間**: 283秒音声を約37秒で処理（RTX 2060）
- **出力**: 44.1kHz WAVファイル

### 話者分離（SpeakerProcessor）
- **モデル**: `pyannote/speaker-diarization-3.1`
- **最小セグメント長**: 1.0秒（調整可能）
- **フォールバック**: pyannote-audio利用不可時は簡易分離
- **出力**: 話者別セグメント + 統合音声

### パフォーマンス
- **GPU処理**: CUDA利用で6-10倍高速化
- **メモリ使用量**: 283秒音声で約89MB出力
- **同時話者数**: 実用的上限は10人程度

## 既知の問題と解決策

### 1. pyannote-audio インポートエラー
```bash
# 症状: ModuleNotFoundError: No module named 'pyannote'
# 解決: 仮想環境内に再インストール
pip uninstall -y pyannote.audio
pip install pyannote.audio
```

### 2. CUDA メモリエラー
```bash
# GPU メモリ不足時はCPUフォールバック
# 長時間音声は分割処理を推奨
```

### 3. NumPy 互換性
```bash
# NumPy 2.x系との非互換
pip install "numpy<2.0"
```

## 開発フェーズ

現在のプロジェクトは **フェーズ2（コア機能実装）** 完了済み：

- ✅ フェーズ1: プロジェクト基盤
- ✅ フェーズ2: コア機能実装（BGM分離 + 話者分離）
- 🚧 フェーズ3: GUI実装（未実装）
- 🚧 フェーズ4: 最適化・高度機能（未実装）
- 🚧 フェーズ5: デプロイメント（未実装）

## 重要な注意事項

### Hugging Face利用規約
- pyannote-audioモデルは学術・研究用途に制限
- 商用利用には別途ライセンス契約が必要
- モデル利用前にHugging Face上で利用規約への同意が必須

### GPU要件
- **推奨**: NVIDIA RTX 2060以上（6GB VRAM）
- **最小**: GTX 1060（3GB VRAM）
- CPU-onlyでも動作可能（処理時間は6-10倍長い）

### ファイル形式
- **入力対応**: WAV, MP3, FLAC, M4A, AAC
- **出力形式**: WAV（44.1kHz, 16-bit）
- **推奨入力**: WAV形式（圧縮による音質劣化なし）