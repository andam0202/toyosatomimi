# 音声分離アプリケーション

## 概要
このアプリケーションは、複数の話者が存在する音声データから、各話者の音声を分離するツールです。BGMや背景ノイズを除去し、個別の話者の音声を抽出します。

## 特徴
- BGMと音声の分離
- 複数話者の音声分離
- ドラッグ&ドロップ対応のGUIインターフェイス
- wav/mp3形式のサポート

## インストール要件
- Python 3.8-3.10
- 推奨: CUDA対応のGPU

## インストール方法
```bash
git clone https://github.com/yourusername/voice-separator.git
cd voice-separator
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install -r requirements.txt
```

## 使用方法
### コマンドライン
```bash
python -m src.main [オプション] <音声ファイルパス>
```

### GUI
```bash
python -m src.gui.main
```

## 開発
### テスト
```bash
pytest tests/
```

## ライセンス
MIT License

## 貢献
プルリクエストは歓迎します。大きな変更を行う前に、まずissueで議論してください。
