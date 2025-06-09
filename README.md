# toyosatomimi 🎵

**高性能音声分離アプリケーション** - 複数話者とBGMが混在する音声から、各話者の音声を個別に抽出

[![Build Status](https://github.com/user/toyosatomimi/workflows/Build%20Windows%20Release/badge.svg)](https://github.com/user/toyosatomimi/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 主な機能

- 🎼 **BGM分離**: Demucsを使用した高品質な音源分離
- 🎤 **話者分離**: pyannote-audioによる話者識別・分離
- ⚡ **GPU加速**: CUDA対応による高速処理
- 🖥️ **直感的GUI**: 使いやすいグラフィカルインターフェース
- 📊 **詳細分析**: 処理結果の可視化とレポート生成
- 🔧 **高度設定**: パラメータの細かい調整が可能

## 🚀 Windows版ダウンロード

### 📦 リリース版（推奨）

最新の安定版をダウンロード:
- [**toyosatomimi-windows-portable.zip**](https://github.com/user/toyosatomimi/releases/latest) - ポータブル版（推奨）
- [**toyosatomimi.exe**](https://github.com/user/toyosatomimi/releases/latest) - スタンドアロン実行ファイル

### ⚙️ システム要件

- **OS**: Windows 10/11 (64-bit)
- **メモリ**: 8GB RAM以上推奨
- **ストレージ**: 2GB以上の空き容量
- **GPU**: NVIDIA GPU（オプション、処理高速化）

## 📱 使用方法

### Windows版（GUI）

1. **アプリケーション起動**
   ```
   toyosatomimi.exe をダブルクリック
   ```

2. **音声ファイル選択**
   - ファイル選択ボタンをクリック
   - または音声ファイルをドラッグ&ドロップ

3. **設定調整**（オプション）
   - BGM分離の有効/無効
   - 話者分離のパラメータ調整
   - 出力形式・保存先の設定

4. **分離実行**
   - 「分離開始」ボタンをクリック
   - 進捗状況をリアルタイム表示

5. **結果確認**
   - プレビューパネルで結果を確認
   - 出力フォルダから分離された音声ファイルを取得

### 対応ファイル形式

- **入力**: WAV, MP3, FLAC, M4A, AAC
- **出力**: WAV, MP3, FLAC

## 🛠️ 開発者向け

### 環境セットアップ

```bash
# uvのインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトのクローン
git clone https://github.com/user/toyosatomimi.git
cd toyosatomimi

# 依存関係のインストール
uv sync

# CUDA版PyTorch（GPU使用時）
uv pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### GUI起動（開発環境）

#### Windows環境（推奨）
```powershell
# PowerShell で実行
cd C:\Users\mao0202\Documents\GitHub\toyosatomimi
uv run python -m src.audio_separator.gui
```

**注意**: このGUIアプリケーションはWindows環境での使用を前提として開発されています。WSL環境では表示関連の問題が発生する可能性があるため、Windows PowerShell での実行を推奨します。

### テスト実行

```bash
# 基本インポートテスト
uv run python -c "
import sys; sys.path.insert(0, 'src')
from audio_separator.gui.models.gui_model import AudioSeparationModel
print('✅ Import successful')
"

# 実音声テスト
uv run python tests/test_real_audio.py data/input/sample.wav
```

### ビルド（実行ファイル作成）

```bash
# Nuitkaを追加（推奨）
uv add --dev nuitka

# 実行ファイルビルド
uv run python nuitka_build.py --build

# 実行ファイル確認
./dist/toyosatomimi.exe
```

## 🧪 テスト・開発フロー

### 開発フロー

```bash
# 1. 基本テスト（コア機能）
uv run python tests/test_real_audio.py data/input/sample.wav

# 2. GUI起動・テスト（Windows PowerShell）
uv run python -m src.audio_separator.gui

# 3. リリースビルド（GitHub Actions）
git tag v1.0.0
git push origin v1.0.0
```

### GUI テストフロー

1. **開発** → コード実装・基本テスト
2. **GUI確認** → Windows環境でGUI動作確認
3. **自動ビルド** → GitHub Actionsでビルド
4. **リリース** → GitHub Releasesで配布

## 📖 技術仕様

### アーキテクチャ

- **フレームワーク**: tkinter（Python標準GUI）
- **パターン**: MVC（Model-View-Controller）
- **BGM分離**: Demucs (htdemucs)
- **話者分離**: pyannote-audio v3.1
- **音声処理**: librosa, soundfile
- **GPU加速**: PyTorch CUDA

### 処理フロー

```
音声入力 → BGM分離 → 話者分離 → ファイル出力
   ↓         ↓         ↓         ↓
 ファイル選択  ボーカル抽出  話者識別   結果保存
```

## ⚠️ 注意事項

### ライセンス制限

- **pyannote-audio**: 学術・研究用途に制限あり
- **商用利用**: 別途ライセンス契約が必要
- **Hugging Face**: モデル利用前に利用規約への同意が必須

### パフォーマンス

- **処理時間**: GPU使用時 約1/6倍速、CPU使用時 約1.5倍時間
- **メモリ使用量**: 長時間音声では大量のメモリを使用
- **推奨**: 5分未満の音声ファイルから開始

## 🤝 コントリビューション

プルリクエストや Issue の報告を歓迎します：

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🙏 謝辞

- [Demucs](https://github.com/facebookresearch/demucs) - 高品質音源分離
- [pyannote-audio](https://github.com/pyannote/pyannote-audio) - 話者分離
- [uv](https://github.com/astral-sh/uv) - 高速Pythonパッケージ管理