# CLAUDE.md

このファイルは、このリポジトリでコードを扱う際のClaude Code (claude.ai/code) への指針を提供します。

## プロジェクト概要

このPython音声分離アプリケーション（音声分離アプリケーション）は、複数の話者とBGMが含まれる音声ファイルから、各話者の音声を個別に抽出します。アプリケーションは以下の2段階の処理を行います：

1. **BGM分離**: Demucsを使用してボーカルとBGMを分離
2. **話者分離**: pyannote-audioを使用して各話者を識別・分離

## 主要コンポーネント（想定構造）

- **main.py**: アプリケーションのエントリーポイント
- **src/audio_separator/**: コア処理モジュール
  - `processors/`: 音声処理クラス（DemucsProcessor、SpeakerProcessor）
  - `gui/`: Tkinterを使用したGUIコンポーネント
  - `utils/`: 音声、ファイル処理、設定のユーティリティ関数
- **scripts/**: インストールとセットアップスクリプト
- **config/**: 設定ファイル
- **tests/**: テストモジュール

## 開発用コマンド

このプロジェクトではuvを使用してPython環境を管理します：

```bash
# 仮想環境の作成とアクティベート
uv venv
source .venv/bin/activate  # Linux/Mac/WSL
# .venv\Scripts\activate   # Windows

# 依存関係のインストール（requirements.txtがある場合）
uv pip install -r requirements.txt

# アプリケーションの実行
python main.py

# テストの実行
python -m pytest tests/
# または
python tests/test_processors.py

# パッケージの追加
uv add package_name

# 開発用パッケージの追加
uv add --dev package_name
```

## 音声処理アーキテクチャ

アプリケーションは以下の処理フローに従います：
```
入力音声 → Demucs（BGM分離） → ボーカル抽出 → pyannote-audio（話者分離） → 個別話者音声ファイル
        ↓
       BGM出力
```

## 出力構造

アプリケーションは整理された出力を生成します：
```
output_directory/
├── vocals.wav                    # BGM除去済み音声
├── bgm.wav                      # 分離されたBGM
├── speaker_SPEAKER_00/          # 話者1のフォルダ
│   ├── segment_001.wav          # 個別セグメント
│   └── speaker_SPEAKER_00_combined.wav  # 結合音声
└── speaker_SPEAKER_XX/          # 追加の話者
```

## 主要ライブラリと依存関係

- **Demucs**: 音楽音源分離（Facebook Research）
- **pyannote-audio**: 話者分離・ダイアライゼーション
- **Tkinter**: GUIフレームワーク
- **librosa**: 音声処理ユーティリティ
- **PyTorch**: 深層学習フレームワーク

## 開発環境

- 主要開発環境：Windows 10 + WSL2
- CPUとGPU（CUDA）の両方に対応
- GUIはドラッグアンドドロップ機能をサポート
- 入力対応形式：WAV, MP3, FLAC, M4A, AAC
- デフォルト出力：WAVファイル（44.1kHz）

## 設定

アプリケーションは以下の方法で設定をサポートします：
- 環境変数（AUDIO_SEPARATOR_*）
- 設定ファイル（config/default_config.json）
- GUI設定（~/.audio_separator/config.jsonに保存）

## 重要な技術的注意事項

- CUDA対応デバイスでのGPUアクセラレーション利用可能
- メモリ要件：4GB以上のRAM（8GB以上推奨）
- 処理時間：通常、音声ファイル長の2-5倍
- 同時話者数制限なし（実用的な上限は約10人）