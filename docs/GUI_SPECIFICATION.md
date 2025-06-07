# GUI仕様書 - toyosatomimi 音声分離アプリケーション

## 概要

toyosatomimi音声分離アプリケーションのGUI（グラフィカルユーザーインターフェース）の詳細仕様書です。
ユーザーが直感的に操作でき、高度な音声分離機能を利用できるデスクトップアプリケーションを目指します。

**技術基盤**: Python Tkinter + カスタムウィジェット
**対象OS**: Windows, Linux (WSL2), macOS
**Python要件**: 3.10+

---

## 1. 全体レイアウト設計

### 1.1 メインウィンドウ構成
```
┌─────────────────────────────────────────────────────────────┐
│ [toyosatomimi - 音声分離アプリケーション]               [\_][□][×] │
├─────────────────────────────────────────────────────────────┤
│ ファイル(F)  設定(S)  ヘルプ(H)                              │
├─────────────────────────────────────────────────────────────┤
│ ┌─ファイル選択─────────────────────────────────────────────┐ │
│ │ 📁 ファイルをドラッグ&ドロップまたはクリックして選択      │ │
│ │ 選択済み: input_gakumas.wav (272.47秒, 48kHz, ステレオ) │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─パラメータ設定───────┐ ┌─出力設定─────────┐ │
│ │ 🎚️ クラスタリング閾値  │ │ 📂 出力ディレクトリ │ │
│ │ [====●====] 0.3      │ │ C:/Users/.../output │ │
│ │ 🎚️ セグメンテーション │ │ 📁 出力形式         │ │
│ │ onset [===●=] 0.2    │ │ ☑ 統合ファイル      │ │
│ │ offset[===●=] 0.2    │ │ ☑ 個別セグメント   │ │
│ │ 👥 強制話者数: [2]   │ │ 🎵 音声形式         │ │
│ │ ☑ 重複発話除去       │ │ ● WAV ○ MP3 ○ FLAC │ │
│ │ ☑ 音声前処理         │ │ サンプリングレート   │ │
│ │ 最小セグメント: 0.5s │ │ [44100Hz ▼]        │ │
│ └─────────────────────┘ └─────────────────┘ │
│ ┌─実行制御─────────────────────────────────────────────────┐ │
│ │ [🎯 分離開始] [⏸️ 一時停止] [⏹️ 停止] [💾 設定保存]      │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─進捗表示─────────────────────────────────────────────────┐ │
│ │ 🔄 BGM分離中... ████████████████████████████████████ 67%  │ │
│ │ 残り時間: 約1分23秒 | 処理速度: 6.2x                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─ログ表示─────────────────────────────────────────────────┐ │
│ │ [INFO] 音声ファイル読み込み完了: input_gakumas.wav       │ │
│ │ [INFO] パイプライン初期化完了 (デバイス: cuda)           │ │
│ │ [INFO] BGM分離開始...                                   │ │
│ │ [WARN] GPU使用率が高くなっています                       │ │
│ │ [▼詳細] [🔄更新] [💾保存] [❌クリア]                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─結果プレビュー───────────────────────────────────────────┐ │
│ │ 話者1 (64.75秒) [▶️再生] [📊波形] speaker01_combined.wav  │ │
│ │ 話者2 (56.60秒) [▶️再生] [📊波形] speaker02_combined.wav  │ │
│ │ BGM (272.47秒)  [▶️再生] [📊波形] bgm.wav                │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 ウィンドウサイズ
- **初期サイズ**: 1200x900px
- **最小サイズ**: 800x600px
- **リサイズ**: 可能（レスポンシブレイアウト）

---

## 2. 基本機能

### 2.1 ドラッグ&ドロップファイル選択

**機能説明**: ユーザーが音声ファイルを簡単に選択できる直感的なインターフェース

**対応形式**: WAV, MP3, FLAC, M4A, AAC, OGG

**UI仕様**:
```python
# ファイル選択エリア
class FileDropArea(tk.Frame):
    def __init__(self):
        # ドロップエリアの視覚的表示
        self.drop_label = "📁 ファイルをドラッグ&ドロップまたはクリックして選択"
        self.selected_label = "選択済み: {filename} ({duration}秒, {sample_rate}Hz, {channels})"
        
    def validate_file(self, file_path):
        # AudioUtils.validate_audio_file()を使用
        # ファイル情報表示（時間、品質など）
```

**動作**:
1. ファイルドロップ時の視覚フィードバック（ハイライト）
2. 無効ファイル時のエラーメッセージ表示
3. ファイル情報の自動表示（時間、サンプリングレート、チャンネル数）

### 2.2 進捗バー表示

**機能説明**: 処理の進行状況をリアルタイムで表示

**UI仕様**:
```python
class ProgressDisplay(tk.Frame):
    def __init__(self):
        self.progress_bar = ttk.Progressbar(mode='determinate')
        self.status_label = tk.Label()  # "BGM分離中..."
        self.time_label = tk.Label()    # "残り時間: 約1分23秒"
        self.speed_label = tk.Label()   # "処理速度: 6.2x"
        
    def update_progress(self, percentage, status, time_remaining, speed):
        # プログレスバーと表示の更新
```

**表示内容**:
- **段階別進捗**: BGM分離(0-50%) → 話者分離(50-90%) → 音声抽出(90-100%)
- **残り時間予測**: 処理速度ベースの動的計算
- **処理速度**: リアルタイム vs 音声時間の比率

### 2.3 リアルタイムログ表示

**機能説明**: 処理状況の詳細をユーザーに表示

**UI仕様**:
```python
class LogDisplay(tk.Frame):
    def __init__(self):
        self.log_text = scrolledtext.ScrolledText()
        self.log_levels = ['DEBUG', 'INFO', 'WARN', 'ERROR']
        self.auto_scroll = tk.BooleanVar(value=True)
        
    def add_log(self, level, message, timestamp=None):
        # レベル別の色分け表示
        # 自動スクロール機能
```

**ログレベル**:
- **INFO**: 一般的な処理状況（青色）
- **WARN**: 注意が必要な状況（オレンジ色）
- **ERROR**: エラー発生（赤色）
- **DEBUG**: 詳細な技術情報（グレー色）

### 2.4 音声プレビュー再生

**機能説明**: 分離結果をアプリ内で確認できる再生機能

**UI仕様**:
```python
class AudioPlayer(tk.Frame):
    def __init__(self):
        self.play_button = tk.Button()      # ▶️/⏸️
        self.stop_button = tk.Button()      # ⏹️
        self.position_scale = tk.Scale()    # 再生位置
        self.volume_scale = tk.Scale()      # 音量
        self.time_label = tk.Label()        # "01:23 / 04:32"
        
    def play_audio(self, file_path):
        # pygame/pydub等を使用した音声再生
```

**機能**:
- **再生/一時停止/停止**: 基本的な音声制御
- **位置調整**: シークバーによる任意位置へのジャンプ
- **音量調整**: 音量スライダー
- **波形表示**: 簡易的な音声波形の視覚化

---

## 3. パラメータ調整機能

### 3.1 調整可能パラメータ

**UI仕様**:
```python
class ParameterPanel(tk.Frame):
    def __init__(self):
        # スライダー + 数値入力のコンビネーション
        self.clustering_threshold = ParameterSlider(0.1, 0.9, 0.3)
        self.segmentation_onset = ParameterSlider(0.1, 0.9, 0.2)
        self.segmentation_offset = ParameterSlider(0.1, 0.9, 0.2)
        self.force_num_speakers = tk.Spinbox(from_=0, to=10)
        self.overlap_removal = tk.BooleanVar(value=True)
        self.audio_preprocessing = tk.BooleanVar(value=True)
        self.min_segment_duration = ParameterSlider(0.1, 3.0, 0.5)
```

**パラメータ詳細**:

1. **クラスタリング閾値** (0.1-0.9)
   - デフォルト: 0.3
   - 説明: "低いほど細かく話者を分離"
   - ツールチップ: 詳細な説明表示

2. **セグメンテーション感度** 
   - onset (0.1-0.9, デフォルト: 0.2)
   - offset (0.1-0.9, デフォルト: 0.2)
   - 説明: "低いほど短いセグメントも検出"

3. **強制話者数** (0-10)
   - デフォルト: 0 (自動検出)
   - 説明: "指定した人数に強制分離"

4. **重複発話除去** (チェックボックス)
   - デフォルト: ON
   - 説明: "同時発話部分を自動除去"

5. **音声前処理** (チェックボックス)
   - デフォルト: ON
   - 説明: "ノイズ除去と話者特徴強調"

6. **最小セグメント長** (0.1-3.0秒)
   - デフォルト: 0.5秒
   - 説明: "これより短いセグメントは除外"

### 3.2 プリセット機能

**UI仕様**:
```python
class PresetManager(tk.Frame):
    def __init__(self):
        self.preset_combo = ttk.Combobox()  # プリセット選択
        self.save_button = tk.Button()      # 現在設定を保存
        self.delete_button = tk.Button()    # プリセット削除
        
    presets = {
        "標準設定": {"clustering": 0.3, "onset": 0.2, ...},
        "高精度分離": {"clustering": 0.2, "onset": 0.1, ...},
        "高速処理": {"clustering": 0.5, "onset": 0.4, ...},
        "2人会話": {"clustering": 0.3, "force_speakers": 2, ...}
    }
```

---

## 4. 出力設定機能

### 4.1 ファイル命名規則

**新しい命名規則**:
```
元ファイル: input_gakumas.wav
出力構造:
📁 output_gakumas_20250607_204523/
  📁 speaker_01_gakumas/
    🎵 gakumas_speaker01_combined.wav          # 統合ファイル
    🎵 gakumas_speaker01_seg001_0m15s-0m23s.wav # 個別セグメント
    🎵 gakumas_speaker01_seg002_0m31s-0m45s.wav
    📄 speaker01_segments.txt                   # セグメント情報
  📁 speaker_02_gakumas/
    🎵 gakumas_speaker02_combined.wav
    🎵 gakumas_speaker02_seg001_0m18s-0m25s.wav
    📄 speaker02_segments.txt
  📁 bgm_gakumas/
    🎵 gakumas_bgm.wav                         # BGM
    🎵 gakumas_vocals.wav                      # ボーカル
  📄 separation_report.json                     # 分離結果レポート
```

**実装仕様**:
```python
class OutputNaming:
    def generate_filename(self, base_name, speaker_id, segment_idx=None, 
                         start_time=None, end_time=None):
        if segment_idx is not None:
            # セグメントファイル名
            start_str = self.format_time(start_time)  # "0m15s"
            end_str = self.format_time(end_time)      # "0m23s"
            return f"{base_name}_speaker{speaker_id:02d}_seg{segment_idx:03d}_{start_str}-{end_str}.wav"
        else:
            # 統合ファイル名
            return f"{base_name}_speaker{speaker_id:02d}_combined.wav"
```

### 4.2 出力形式選択

**UI仕様**:
```python
class OutputFormatPanel(tk.Frame):
    def __init__(self):
        # 出力内容選択
        self.create_combined = tk.BooleanVar(value=True)
        self.create_individual = tk.BooleanVar(value=True)
        self.create_bgm = tk.BooleanVar(value=True)
        
        # 音声形式選択
        self.audio_format = tk.StringVar(value="wav")  # wav/mp3/flac
        self.sample_rate = tk.StringVar(value="44100")  # 22050/44100/48000
        self.bit_depth = tk.StringVar(value="16")       # 16/24/32
        
        # 追加出力
        self.create_report = tk.BooleanVar(value=True)
        self.create_segment_info = tk.BooleanVar(value=True)
```

**出力オプション**:
1. **統合ファイル**: 話者ごとの全セグメント結合ファイル
2. **個別セグメント**: セグメントごとの個別ファイル
3. **BGM分離**: BGMとボーカル分離ファイル
4. **分離レポート**: JSON形式の詳細情報
5. **セグメント情報**: テキスト形式のタイムスタンプ情報

### 4.3 音声品質設定

**音声形式別設定**:
```python
format_settings = {
    "wav": {
        "sample_rates": [22050, 44100, 48000, 96000],
        "bit_depths": [16, 24, 32],
        "default_quality": "high"
    },
    "mp3": {
        "bitrates": [128, 192, 256, 320],
        "quality": ["standard", "high", "extreme"],
        "default_bitrate": 256
    },
    "flac": {
        "compression": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "bit_depths": [16, 24],
        "default_compression": 5
    }
}
```

---

## 5. 詳細機能

### 5.1 バッチ処理

**機能説明**: 複数ファイルの一括処理

**UI仕様**:
```python
class BatchProcessor(tk.Toplevel):
    def __init__(self):
        self.file_list = ttk.Treeview()      # ファイルリスト表示
        self.add_files_button = tk.Button()  # ファイル追加
        self.remove_file_button = tk.Button() # ファイル削除
        self.start_batch_button = tk.Button() # バッチ開始
        self.overall_progress = ttk.Progressbar() # 全体進捗
        
    def process_queue(self):
        # キューに基づく順次処理
        # 各ファイルの個別進捗表示
```

**バッチ処理ウィンドウ**:
```
┌─バッチ処理─────────────────────────────────────────────┐
│ ファイル一覧:                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ ✓ input_gakumas.wav    (完了)     4分32秒          │ │
│ │ 🔄 conversation.wav    (処理中)   2分15秒   [67%]  │ │
│ │ ⏳ meeting_record.wav  (待機中)   15分43秒         │ │
│ │ ❌ invalid_file.wav    (エラー)   -               │ │
│ └────────────────────────────────────────────────────┘ │
│ [📁追加] [❌削除] [⏸️一時停止] [⏹️停止]                │
│ 全体進捗: ████████████████▒▒▒▒▒▒▒▒ 2/4 ファイル完了   │
│ 残り時間: 約8分32秒                                   │
└───────────────────────────────────────────────────────┘
```

### 5.2 設定保存/読み込み

**機能説明**: ユーザー設定の永続化

**設定ファイル構造** (JSON):
```json
{
  "version": "1.0",
  "last_updated": "2025-06-07T20:45:00Z",
  "parameters": {
    "clustering_threshold": 0.3,
    "segmentation_onset": 0.2,
    "segmentation_offset": 0.2,
    "force_num_speakers": null,
    "overlap_removal": true,
    "audio_preprocessing": true,
    "min_segment_duration": 0.5
  },
  "output_settings": {
    "create_combined": true,
    "create_individual": true,
    "create_bgm": true,
    "audio_format": "wav",
    "sample_rate": 44100,
    "bit_depth": 16
  },
  "ui_settings": {
    "window_size": [1200, 900],
    "window_position": [100, 100],
    "log_level": "INFO",
    "auto_save_settings": true
  },
  "presets": {
    "user_preset_1": { ... },
    "user_preset_2": { ... }
  }
}
```

### 5.3 エクスポート設定

**多様な出力形式サポート**:

**音声形式**:
- **WAV**: 非圧縮、最高品質 (デフォルト)
- **MP3**: 圧縮、汎用性高い
- **FLAC**: 可逆圧縮、高品質+ファイルサイズ削減

**メタデータ付加**:
```python
metadata = {
    "title": f"Speaker {speaker_id:02d}",
    "artist": "toyosatomimi Audio Separator",
    "album": f"Separated from {original_filename}",
    "date": datetime.now().strftime("%Y-%m-%d"),
    "comment": f"Segment {seg_start:.1f}s-{seg_end:.1f}s",
    "genre": "Speech"
}
```

### 5.4 エラー処理と詳細情報表示

**エラー種別と対応**:

**レベル1: 軽微なエラー**
- GPU使用率警告
- 音声品質注意
- セグメント数警告
→ 処理継続、警告表示

**レベル2: 重大なエラー**
- pyannote-audio利用不可
- CUDA エラー
- メモリ不足
→ フォールバック処理、詳細情報表示

**レベル3: 致命的エラー**
- ファイル読み込み失敗
- 出力先書き込み不可
- 予期しない例外
→ 処理停止、詳細エラー情報とログ出力

**エラー詳細ダイアログ**:
```
┌─エラー詳細─────────────────────────────────────────────┐
│ ❌ pyannote-audioモデルの読み込みに失敗しました          │
│                                                       │
│ 原因: Hugging Face認証トークンが無効です                │
│                                                       │
│ 対処法:                                               │
│ 1. 環境変数HF_TOKENを確認してください                   │
│ 2. https://huggingface.co/settings/tokens で          │
│    新しいトークンを生成してください                     │
│ 3. モデルライセンスに同意していることを確認してください   │
│                                                       │
│ 📋 詳細ログ:                                          │
│ [ERROR] Failed to load pyannote model: 401 Unauthorized│
│ [INFO] フォールバック: 簡易話者分離を使用します          │
│                                                       │
│ [📋クリップボードにコピー] [💾ログ保存] [❌閉じる]      │
└───────────────────────────────────────────────────────┘
```

---

## 6. メニューバー機能

### 6.1 ファイルメニュー
- **新しいプロジェクト** (Ctrl+N)
- **プロジェクトを開く** (Ctrl+O)
- **プロジェクトを保存** (Ctrl+S)
- **最近使用したファイル**
- **バッチ処理** (Ctrl+B)
- **終了** (Alt+F4)

### 6.2 設定メニュー
- **パラメータ設定**
- **出力設定** 
- **環境設定**
- **GPU設定**
- **プリセット管理**

### 6.3 ヘルプメニュー
- **使用方法**
- **キーボードショートカット**
- **トラブルシューティング**
- **バージョン情報**
- **ライセンス情報**

---

## 7. 技術実装仕様

### 7.1 GUI技術スタック

**メインフレームワーク**: Python Tkinter
```python
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.scrolledtext as scrolledtext
```

**追加ライブラリ**:
- **tkinterdnd2**: ドラッグ&ドロップ機能
- **pygame**: 音声再生
- **matplotlib**: 波形表示
- **PIL (Pillow)**: アイコン・画像処理
- **threading**: 非同期処理

### 7.2 アーキテクチャ設計

**MVCパターン**:
```python
# Model: データ・ビジネスロジック
class AudioSeparationModel:
    def __init__(self):
        self.demucs_processor = DemucsProcessor()
        self.speaker_processor = SpeakerProcessor()
        
# View: ユーザーインターフェース
class MainWindow(tk.Tk):
    def __init__(self):
        self.parameter_panel = ParameterPanel()
        self.progress_display = ProgressDisplay()
        
# Controller: View-Model間の制御
class AudioSeparationController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
```

### 7.3 非同期処理設計

**処理フロー**:
```python
class ProcessingThread(threading.Thread):
    def run(self):
        try:
            # 1. BGM分離 (0-50%)
            self.update_progress(0, "BGM分離開始...")
            bgm_result = self.model.separate_bgm()
            self.update_progress(50, "BGM分離完了")
            
            # 2. 話者分離 (50-90%)
            self.update_progress(50, "話者分離開始...")
            speaker_result = self.model.separate_speakers()
            self.update_progress(90, "話者分離完了")
            
            # 3. 音声抽出 (90-100%)
            self.update_progress(90, "音声抽出開始...")
            output_files = self.model.extract_audio()
            self.update_progress(100, "処理完了")
            
        except Exception as e:
            self.handle_error(e)
```

### 7.4 設定管理

**設定ファイル場所**:
- Windows: `%APPDATA%/toyosatomimi/config.json`
- Linux: `~/.config/toyosatomimi/config.json`
- macOS: `~/Library/Application Support/toyosatomimi/config.json`

---

## 8. ユーザビリティ

### 8.1 キーボードショートカット
- **Ctrl+O**: ファイルを開く
- **Ctrl+S**: 設定を保存
- **Ctrl+B**: バッチ処理
- **Space**: 音声再生/一時停止
- **Ctrl+R**: 処理開始
- **Esc**: 処理キャンセル
- **F1**: ヘルプ表示

### 8.2 ツールチップ
すべてのパラメータとボタンに説明的なツールチップを表示

### 8.3 状況に応じたUI
- **ファイル未選択時**: パラメータ設定を無効化
- **処理中**: 不要なボタンを無効化
- **エラー時**: 詳細情報と対処法を表示

### 8.4 アクセシビリティ
- **高コントラスト対応**
- **フォントサイズ調整**
- **キーボードナビゲーション**

---

## 9. 今後の拡張機能

### 9.1 将来実装予定
- **リアルタイム音声分離**
- **クラウド処理対応**
- **AI音声品質向上**
- **多言語対応**
- **プラグインシステム**

### 9.2 プロ版機能
- **商用利用ライセンス**
- **バッチAPIサーバー**
- **カスタムモデル学習**
- **企業向けサポート**

---

## 10. 実装優先度

### フェーズ1: 基本GUI (優先度: 高)
- [x] パラメータ調整機能の実装完了
- [ ] メインウィンドウレイアウト
- [ ] ファイル選択機能
- [ ] 基本的な実行制御

### フェーズ2: 中核機能 (優先度: 高)
- [ ] 進捗表示
- [ ] ログ表示
- [ ] 音声プレビュー
- [ ] 出力設定

### フェーズ3: 高度機能 (優先度: 中)
- [ ] バッチ処理
- [ ] 設定保存/読み込み
- [ ] エラー処理強化
- [ ] プリセット機能

### フェーズ4: 詳細機能 (優先度: 低)
- [ ] 波形表示
- [ ] 詳細統計情報
- [ ] 出力品質最適化
- [ ] アクセシビリティ向上

---

**作成日**: 2025年6月7日  
**最終更新**: 2025年6月7日  
**バージョン**: 1.0  
**ステータス**: ドラフト完成