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
# 基本実行（outputs/latestに出力）
cd /path/to/toyosatomimi
python tests/test_real_audio.py data/input/input_wav.wav

# 出力先指定
python tests/test_real_audio.py data/input/input_wav.wav tests/outputs/my_test
```

### 2. test_integrated_separation.py
BGM分離と話者分離の統合テスト

```bash
python tests/test_integrated_separation.py data/input/input_wav.wav tests/outputs/integrated_test
```

### 3. test_speaker_simple.py
pyannote-audio環境チェックと簡易話者分離テスト

```bash
HF_TOKEN='your_token' python tests/test_speaker_simple.py
```

### 4. test_speaker_tuning.py
異なるパラメータでの話者分離性能比較

```bash
python tests/test_speaker_tuning.py tests/outputs/latest/bgm_separated/vocals.wav tests/outputs/tuning_results
```

## 🔧 実行前の準備

1. **認証トークン設定**（pyannote-audio使用時）
```bash
export HF_TOKEN='your_huggingface_token'
```

2. **プロジェクトルートディレクトリで実行**
```bash
cd /path/to/toyosatomimi
python tests/test_real_audio.py data/input/input_wav.wav
```

## 📊 出力結果

すべてのテストは `tests/outputs/` 以下に結果を出力します：

- `bgm_separated/` - BGM分離結果（vocals.wav, bgm.wav）
- `speakers/` - 話者別音声ファイル
- ログファイル

## 🗂️ 旧出力フォルダの整理

ルートディレクトリにある `output_*` フォルダは開発過程で作成されたもので、今後は使用しません。
必要に応じて削除してください：

```bash
# 旧出力フォルダの確認
ls output_*

# 削除（必要に応じて）
rm -rf output_*
```