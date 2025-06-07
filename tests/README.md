# テストディレクトリ

このディレクトリには音声分離機能のテストスクリプトが含まれています。

## 📁 ディレクトリ構造

```
tests/
├── README.md                    # このファイル
├── outputs/                     # テスト実行結果の出力先
│   └── latest/                  # 最新の実行結果（デフォルト出力先）
├── test_real_audio.py          # 実音声データでの統合テスト
├── test_integrated_separation.py # BGM分離+話者分離の統合テスト
├── test_speaker_simple.py      # pyannote-audio利用可能性チェック
└── test_speaker_tuning.py      # 話者分離パラメータ調整テスト
```

## 🧪 テストスクリプト

### 1. test_real_audio.py
実際の音声ファイルを使用した完全な音声分離テスト

```bash
# uvでの実行（推奨）
cd /path/to/toyosatomimi
uv run python tests/test_real_audio.py data/input/input_wav.wav

# 出力先指定
uv run python tests/test_real_audio.py data/input/input_wav.wav tests/outputs/my_test

# 従来方式（互換性）
source .venv/bin/activate
python tests/test_real_audio.py data/input/input_wav.wav
```

### 2. test_integrated_separation.py
BGM分離と話者分離の統合テスト

```bash
# uvでの実行（推奨）
uv run python tests/test_integrated_separation.py data/input/input_wav.wav tests/outputs/integrated_test

# 従来方式
source .venv/bin/activate
python tests/test_integrated_separation.py data/input/input_wav.wav tests/outputs/integrated_test
```

### 3. test_speaker_simple.py
pyannote-audio環境チェックと簡易話者分離テスト

```bash
# uvでの実行（推奨）
export HF_TOKEN='your_huggingface_token'
uv run python tests/test_speaker_simple.py

# 従来方式
HF_TOKEN='your_token' python tests/test_speaker_simple.py
```

### 4. test_speaker_tuning.py
異なるパラメータでの話者分離性能比較

```bash
# uvでの実行（推奨）
uv run python tests/test_speaker_tuning.py tests/outputs/latest/bgm_separated/vocals.wav tests/outputs/tuning_results

# 従来方式
python tests/test_speaker_tuning.py tests/outputs/latest/bgm_separated/vocals.wav tests/outputs/tuning_results
```

## 🔧 実行前の準備

1. **uv環境セットアップ**
```bash
cd /path/to/toyosatomimi
uv sync  # pyproject.tomlから依存関係をインストール
```

2. **認証トークン設定**（pyannote-audio使用時）
```bash
export HF_TOKEN='your_huggingface_token'
```

3. **環境に問題がある場合の再構築**
```bash
# 完全なクリーンアップと再構築
rm -rf .venv uv.lock
uv sync
```

## 📊 出力結果

すべてのテストは `tests/outputs/` 以下に結果を出力します：

```
tests/outputs/your_test_name/
├── bgm_separated/
│   ├── vocals.wav          # ボーカル音声（BGM除去済み）
│   └── bgm.wav            # BGM音声
└── speakers/
    ├── speaker_SPEAKER_00/ # 話者1
    │   ├── segment_001.wav # 個別セグメント
    │   ├── segment_002.wav
    │   └── speaker_SPEAKER_00_combined.wav  # 統合音声
    ├── speaker_SPEAKER_01/ # 話者2
    └── speaker_SPEAKER_02/ # 話者3
```

**実行例での結果**：
- 入力音声: 283.88秒
- 検出話者数: 3人
- 出力ファイル数: 58ファイル
- BGM分離: 完了（vocals.wav 26MB, bgm.wav 26MB）
- 話者分離: 55セグメント検出

## 🗂️ 旧出力フォルダの整理

ルートディレクトリにある `output_*` フォルダは開発過程で作成されたもので、今後は使用しません。
必要に応じて削除してください：

```bash
# 旧出力フォルダの確認
ls output_*

# 削除（必要に応じて）
rm -rf output_*
```