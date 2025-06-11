"""
メインGUIウィンドウ

toyosatomimi音声分離アプリケーションのメインウィンドウを提供します。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.scrolledtext as scrolledtext
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import logging

from .components.file_selector import FileSelector
from .components.parameter_panel import ParameterPanel
from .components.output_panel import OutputPanel
from .components.progress_display import ProgressDisplay
from .components.log_display import LogDisplay
from .components.control_buttons import ControlButtons
from .components.preview_panel import PreviewPanel
from .models.gui_model import AudioSeparationModel
from .controllers.separation_controller import SeparationController


class MainWindow(tk.Tk):
    """メインGUIウィンドウクラス"""
    
    def __init__(self):
        super().__init__()
        
        # ウィンドウ設定
        self.title("toyosatomimi - 音声分離アプリケーション")
        self.geometry("1200x900")
        self.minsize(800, 600)
        
        # アイコン設定（将来実装）
        # self.iconbitmap("assets/icon.ico")
        
        # モデルとコントローラーの初期化
        self.model = AudioSeparationModel()
        self.controller = SeparationController(self.model, self)
        
        # UI要素の初期化
        self._create_menu()
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
        
        # ログハンドラー設定
        self._setup_logging()
        
        # ウィンドウクローズ時の処理
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        logging.info("toyosatomimi GUI起動完了")
    
    def _create_menu(self):
        """メニューバーを作成"""
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="ファイル(F)", menu=file_menu)
        file_menu.add_command(label="新しいプロジェクト", accelerator="Ctrl+N", command=self._new_project)
        file_menu.add_command(label="プロジェクトを開く", accelerator="Ctrl+O", command=self._open_project)
        file_menu.add_command(label="プロジェクトを保存", accelerator="Ctrl+S", command=self._save_project)
        file_menu.add_separator()
        file_menu.add_command(label="バッチ処理", accelerator="Ctrl+B", command=self._open_batch_window)
        file_menu.add_separator()
        file_menu.add_command(label="終了", accelerator="Alt+F4", command=self._on_closing)
        
        # 設定メニュー
        settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="設定(S)", menu=settings_menu)
        settings_menu.add_command(label="パラメータ設定", command=self._open_parameter_settings)
        settings_menu.add_command(label="出力設定", command=self._open_output_settings)
        settings_menu.add_command(label="環境設定", command=self._open_environment_settings)
        settings_menu.add_command(label="GPU設定", command=self._open_gpu_settings)
        settings_menu.add_command(label="プリセット管理", command=self._open_preset_manager)
        
        # ヘルプメニュー
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="ヘルプ(H)", menu=help_menu)
        help_menu.add_command(label="使用方法", command=self._show_help)
        help_menu.add_command(label="キーボードショートカット", command=self._show_shortcuts)
        help_menu.add_command(label="トラブルシューティング", command=self._show_troubleshooting)
        help_menu.add_separator()
        help_menu.add_command(label="バージョン情報", command=self._show_about)
    
    def _create_widgets(self):
        """UIウィジェットを作成"""
        # ファイル選択エリア
        self.file_selector = FileSelector(self, self.controller)
        
        # パラメータ調整パネル
        self.parameter_panel = ParameterPanel(self, self.controller)
        
        # 出力設定パネル
        self.output_panel = OutputPanel(self, self.controller)
        
        # 実行制御ボタン
        self.control_buttons = ControlButtons(self, self.controller)
        
        # 進捗表示
        self.progress_display = ProgressDisplay(self, self.controller)
        
        # ログ表示
        self.log_display = LogDisplay(self, self.controller)
        
        # プレビューパネル
        self.preview_panel = PreviewPanel(self, self.controller)
    
    def _setup_layout(self):
        """レイアウトを設定"""
        # メインフレーム
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ファイル選択エリア（上部）
        self.file_selector.pack(fill=tk.X, pady=(0, 10))
        
        # 中央エリア（パラメータと出力設定を横並び）
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(fill=tk.X, pady=(0, 10))
        
        # パラメータパネル（左側）
        self.parameter_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 出力設定パネル（右側）
        self.output_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 実行制御ボタン
        self.control_buttons.pack(fill=tk.X, pady=(0, 10))
        
        # 進捗表示
        self.progress_display.pack(fill=tk.X, pady=(0, 10))
        
        # 下部エリア（ログとプレビューをタブで切り替え）
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # ログタブ
        notebook.add(self.log_display, text="ログ")
        
        # プレビュータブ
        notebook.add(self.preview_panel, text="結果プレビュー")
    
    def _setup_bindings(self):
        """キーボードショートカットを設定"""
        self.bind('<Control-n>', lambda e: self._new_project())
        self.bind('<Control-o>', lambda e: self._open_project())
        self.bind('<Control-s>', lambda e: self._save_project())
        self.bind('<Control-b>', lambda e: self._open_batch_window())
        self.bind('<Control-r>', lambda e: self.controller.start_separation())
        self.bind('<Escape>', lambda e: self.controller.stop_separation())
        self.bind('<F1>', lambda e: self._show_help())
    
    def _setup_logging(self):
        """ログハンドラーを設定"""
        # GUIログハンドラーを作成
        gui_handler = self.log_display.get_log_handler()
        logging.getLogger().addHandler(gui_handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def _on_closing(self):
        """ウィンドウクローズ時の処理"""
        if self.controller.is_processing():
            result = messagebox.askyesno(
                "確認",
                "処理中です。本当に終了しますか？\\n処理は中断されます。"
            )
            if not result:
                return
            
            # 処理を停止
            self.controller.stop_separation()
        
        # 設定を保存
        self._save_current_settings()
        
        logging.info("toyosatomimi GUI終了")
        self.destroy()
    
    def _save_current_settings(self):
        """現在の設定を保存"""
        try:
            settings = {
                'parameters': self.parameter_panel.get_current_parameters(),
                'output': self.output_panel.get_current_settings(),
                'window': {
                    'geometry': self.geometry(),
                    'state': self.state()
                }
            }
            self.controller.save_settings(settings)
        except Exception as e:
            logging.error(f"設定保存エラー: {e}")
    
    # メニュー項目のイベントハンドラー
    def _new_project(self):
        """新しいプロジェクト"""
        self.controller.new_project()
    
    def _open_project(self):
        """プロジェクトを開く"""
        self.controller.open_project()
    
    def _save_project(self):
        """プロジェクトを保存"""
        self.controller.save_project()
    
    def _open_batch_window(self):
        """バッチ処理ウィンドウを開く"""
        from .windows.batch_window import BatchWindow
        BatchWindow(self, self.controller)
    
    def _open_parameter_settings(self):
        """パラメータ設定ダイアログを開く"""
        from .dialogs.parameter_dialog import ParameterDialog
        ParameterDialog(self, self.parameter_panel)
    
    def _open_output_settings(self):
        """出力設定ダイアログを開く"""
        from .dialogs.output_dialog import OutputDialog
        OutputDialog(self, self.output_panel)
    
    def _open_environment_settings(self):
        """環境設定ダイアログを開く"""
        from .dialogs.environment_dialog import EnvironmentDialog
        EnvironmentDialog(self, self.controller)
    
    def _open_gpu_settings(self):
        """GPU設定ダイアログを開く"""
        from .dialogs.gpu_dialog import GPUDialog
        GPUDialog(self, self.controller)
    
    def _open_preset_manager(self):
        """プリセット管理ダイアログを開く"""
        from .dialogs.preset_dialog import PresetDialog
        PresetDialog(self, self.parameter_panel)
    
    def _show_help(self):
        """ヘルプを表示"""
        from .dialogs.help_dialog import HelpDialog
        HelpDialog(self)
    
    def _show_shortcuts(self):
        """ショートカット一覧を表示"""
        shortcuts_text = """
キーボードショートカット:

ファイル操作:
  Ctrl+N    新しいプロジェクト
  Ctrl+O    プロジェクトを開く
  Ctrl+S    プロジェクトを保存
  Ctrl+B    バッチ処理

処理制御:
  Ctrl+R    分離開始
  Escape    処理停止

その他:
  F1        ヘルプ表示
  Alt+F4    アプリケーション終了
        """
        messagebox.showinfo("キーボードショートカット", shortcuts_text)
    
    def _show_troubleshooting(self):
        """トラブルシューティングを表示"""
        troubleshooting_text = """
よくある問題と解決策:

1. pyannote-audioエラー:
   - Hugging Face トークンを確認
   - モデルライセンスに同意
   - 環境変数 HF_TOKEN を設定

2. GPU関連エラー:
   - CUDA ドライバーを確認
   - GPU メモリ使用量を確認
   - CPU モードに切り替え

3. 音声ファイルエラー:
   - 対応形式を確認 (WAV, MP3, FLAC等)
   - ファイルの破損チェック
   - アクセス権限を確認

詳細なトラブルシューティングは
ドキュメントを参照してください。
        """
        messagebox.showinfo("トラブルシューティング", troubleshooting_text)
    
    def _show_about(self):
        """バージョン情報を表示"""
        about_text = """
toyosatomimi - 音声分離アプリケーション
バージョン: 0.1.0

複数の話者とBGMが含まれる音声ファイルから、
各話者の音声を個別に抽出するアプリケーション

技術:
- Demucs 4.0.1 (BGM分離)
- pyannote-audio 3.3.2 (話者分離)
- PyTorch 2.7.1+cu126 (GPU加速)

開発: Development Team
ライセンス: MIT License
        """
        messagebox.showinfo("バージョン情報", about_text)


def main():
    """GUI アプリケーションのメインエントリーポイント"""
    try:
        # ロギング設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # メインウィンドウを作成・実行
        app = MainWindow()
        app.mainloop()
        
    except Exception as e:
        # 起動時エラーの処理
        error_msg = f"アプリケーションの起動に失敗しました:\\n{e}"
        try:
            messagebox.showerror("起動エラー", error_msg)
        except:
            print(f"ERROR: {error_msg}")


if __name__ == "__main__":
    main()