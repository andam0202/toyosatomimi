# 音声分離アプリケーション

複数話者とBGMが混在する音声から、各話者の音声を個別に抽出するPythonアプリケーション

## 概要

このアプリケーションは以下の2段階で音声を分離します：

1. **BGM分離**: Demucsを使用して音楽とボーカルを分離
2. **話者分離**: pyannote-audioを使用して複数の話者を識別・分離

## 特徴

- 🎵 高品質なBGM除去（Demucs）
- 🗣️ 正確な話者分離（pyannote-audio）
- 💻 直感的なGUIインターフェース
- 📁 ドラッグアンドドロップ対応
- ⚙️ 柔軟なパラメータ設定
- 📊 リアルタイム進行状況表示

## インストール

### 1. 環境準備
```bash
# Python 3.8以上が必要
python --version

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 2. 依存関係のインストール
```bash
# 自動セットアップ
python setup.py

# または手動インストール
pip install -r requirements.txt
```

### 3. pyannote-audio設定
初回使用時にHugging Faceトークンが必要な場合があります：
1. [Hugging Face](https://huggingface.co/settings/tokens)でトークンを取得
2. アプリケーション起動時に入力

## 使用方法

### 基本的な使い方

1. **アプリケーション起動**
```bash
python audio_separator.py
```

2. **ファイル選択**
   - ドラッグアンドドロップで音声ファイルを投入
   - または「参照」ボタンでファイル選択

3. **出力先設定**
   - 出力ディレクトリを指定
   - 未指定の場合は入力ファイルと同じ場所

4. **パラメータ調整**
   - **Demucsモデル**: 分離品質を選択
     - `htdemucs`: 標準品質、高速
     - `htdemucs_ft`: 高品質
     - `mdx_extra`: 最高品質、低速
   - **最小話者分離時間**: 短いセグメントを除外（推奨: 1.0秒）

5. **処理実行**
   - 「処理開始」ボタンをクリック
   - ログで進行状況を確認

### 対応ファイル形式

- **入力**: WAV, MP3, FLAC, M4A, AAC
- **出力**: WAV（44.1kHz）

## 出力構造

処理完了後、以下のファイルが生成されます：

```
output_directory/
├── vocals.wav                    # BGM除去済み音声
├── bgm.wav                      # 分離されたBGM
├── speaker_SPEAKER_00/          # 話者1のフォルダ
│   ├── segment_001.wav          # セグメント1
│   ├── segment_002.wav          # セグメント2
│   └── speaker_SPEAKER_00_combined.wav  # 結合音声
├── speaker_SPEAKER_01/          # 話者2のフォルダ
│   └── ...
└── speaker_SPEAKER_XX/          # 話者Nのフォルダ
    └── ...
```

## システム要件

### 最小要件
- Python 3.8以上
- RAM: 4GB以上
- ストレージ: 2GB以上の空き容量

### 推奨環境
- Python 3.9-3.11
- CUDA対応GPU（大幅な高速化）
- RAM: 8GB以上
- SSD推奨

### GPU設定
CUDA対応GPUがある場合、自動的に検出・使用されます：
```bash
# CUDA確認
python -c "import torch; print(torch.cuda.is_available())"
```

## トラブルシューティング

### よくある問題

**1. モジュールが見つからない**
```bash
pip install --upgrade -r requirements.txt
```

**2. pyannote-audioのエラー**
- Hugging Faceトークンを確認
- インターネット接続を確認

**3. メモリ不足**
- より短い音声ファイルで試行
- 他のアプリケーションを終了

**4. GPU認識しない**
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### パフォーマンス最適化

- **CPU使用時**: htdemucsモデルを推奨
- **GPU使用時**: htdemucs_ftまたはmdx_extraモデル
- **メモリ節約**: 最小話者分離時間を長めに設定

## 技術仕様

### 使用ライブラリ
- **Demucs**: 音楽分離（Facebook Research）
- **pyannote-audio**: 話者分離（CNRS/IRIT）
- **Tkinter**: GUI フレームワーク
- **librosa**: 音声処理
- **torch**: 深層学習フレームワーク

### 処理フロー
```
入力音声 → Demucs → ボーカル抽出 → pyannote → 話者分離 → 個別音声出力
         ↓
        BGM出力
```

## ライセンス

このプロジェクトで使用される主要ライブラリのライセンス：
- Demucs: MIT License
- pyannote-audio: MIT License

## 制限事項

- 同時話者数の上限なし（実用的には10人程度まで）
- ファイルサイズ: メモリに依存
- 処理時間: ファイル長の2-5倍程度

## 更新履歴

- v1.0.0: 初期リリース
  - BGM分離機能
  - 話者分離機能
  - GUI実装