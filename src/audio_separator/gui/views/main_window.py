"""
メインウィンドウ

音声分離GUIアプリケーションのメインウィンドウ
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import logging

from ..components.file_selector import FileSelector
from ..components.parameter_panel import ParameterPanel
from ..components.progress_display import ProgressDisplay
from ..components.control_buttons import ControlButtons
from ..components.output_panel import OutputPanel
from ..components.preview_panel import PreviewPanel
from ..controllers.separation_controller import SeparationController
from ..models.gui_model import AudioSeparationModel


class MainWindow(tk.Tk):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        # モデルとコントローラー初期化
        self.model = AudioSeparationModel()
        self.controller = SeparationController(self.model, self)
        
        # ウィンドウ設定
        self._setup_window()
        
        # スタイル設定
        self._setup_styles()
        
        # UIコンポーネント作成
        self._create_components()
        
        # レイアウト設定
        self._setup_layout()
        
        # イベントバインド
        self._bind_events()
        
        # 設定読み込み
        self._load_settings()
        
        logging.info("MainWindow初期化完了")
    
    def _setup_window(self):
        """ウィンドウの基本設定"""
        # ウィンドウタイトル
        self.title("toyosatomimi - 音声分離アプリケーション")
        
        # ウィンドウサイズ
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        # アイコン設定（存在する場合）
        try:
            icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except:
            pass
        
        # 終了時のプロトコル
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # フォーカス設定
        self.focus_set()
    
    def _setup_styles(self):
        """スタイルテーマの設定"""
        style = ttk.Style()
        
        # 利用可能なテーマを確認
        available_themes = style.theme_names()
        
        # 推奨テーマを設定
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        else:
            style.theme_use(available_themes[0])
        
        # カスタムスタイル定義
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        
        # メインボタン用のスタイル
        style.configure('MainStart.TButton', 
                       font=('Arial', 14, 'bold'),
                       padding=(20, 10))
        
        # プログレスバーのスタイル
        style.configure('TProgressbar', thickness=20)
    
    def _create_components(self):
        """UIコンポーネントを作成"""
        # ステータスバー（最下部）
        self._create_status_bar()
        
        # メイン分離開始ボタン（ステータスバーの上）
        self.main_button_frame = ttk.Frame(self)
        self.main_button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(10, 5))
        
        self.main_start_button = ttk.Button(
            self.main_button_frame,
            text="🎯 音声分離を開始",
            command=self._on_main_start_click,
            style='MainStart.TButton'
        )
        self.main_start_button.pack(pady=5, ipadx=30, ipady=15)
        
        # メインフレーム（ボタンフレームの上に配置）
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左パネル（入力・設定）
        self.left_panel = ttk.Frame(self.main_frame)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 右パネル（結果・プレビュー）
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # ファイル選択コンポーネント
        self.file_selector = FileSelector(self.left_panel, self.controller)
        self.file_selector.pack(fill=tk.X, pady=(0, 10))
        
        # パラメータ調整パネル
        self.parameter_panel = ParameterPanel(self.left_panel, self.controller)
        self.parameter_panel.pack(fill=tk.X, pady=(0, 10))
        
        # 出力設定パネル
        self.output_panel = OutputPanel(self.left_panel, self.controller)
        self.output_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 実行制御ボタン
        self.control_buttons = ControlButtons(self.left_panel, self.controller)
        self.control_buttons.pack(fill=tk.X, pady=(0, 10))
        
        # 進捗表示
        self.progress_display = ProgressDisplay(self.left_panel, self.controller)
        self.progress_display.pack(fill=tk.X, pady=(0, 10))
        
        # プレビューパネル
        self.preview_panel = PreviewPanel(self.right_panel, self.controller)
        self.preview_panel.pack(fill=tk.BOTH, expand=True)
    
    def _setup_layout(self):
        """レイアウトを設定"""
        # メニューバー作成
        self._create_menu()
    
    def _create_menu(self):
        """メニューバーを作成"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="新しいプロジェクト", command=self.controller.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="プロジェクトを開く", command=self.controller.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="プロジェクトを保存", command=self.controller.save_project, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self._on_closing, accelerator="Ctrl+Q")
        
        # 処理メニュー
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="処理", menu=process_menu)
        process_menu.add_command(label="分離開始", command=self.controller.start_separation, accelerator="F5")
        process_menu.add_command(label="停止", command=self.controller.stop_separation, accelerator="Esc")
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="使用方法", command=self._show_help)
        help_menu.add_command(label="バージョン情報", command=self._show_about)
        
        # キーボードショートカット
        self.bind('<Control-n>', lambda e: self.controller.new_project())
        self.bind('<Control-o>', lambda e: self.controller.open_project())
        self.bind('<Control-s>', lambda e: self.controller.save_project())
        self.bind('<Control-q>', lambda e: self._on_closing())
        self.bind('<F5>', lambda e: self.controller.start_separation())
        self.bind('<Escape>', lambda e: self.controller.stop_separation())
    
    def _create_status_bar(self):
        """ステータスバーを作成"""
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 左側：一般ステータス
        self.status_label = ttk.Label(
            self.status_bar,
            text="準備完了",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 5))
        
        # 右側：GPU情報
        gpu_info = self._get_gpu_info()
        self.gpu_label = ttk.Label(
            self.status_bar,
            text=gpu_info,
            relief=tk.SUNKEN
        )
        self.gpu_label.pack(side=tk.RIGHT, padx=(5, 2))
    
    def _get_gpu_info(self) -> str:
        """GPU情報を取得"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                return f"GPU: {gpu_name}"
            else:
                return "GPU: 利用不可 (CPU動作)"
        except ImportError:
            return "GPU: PyTorch未検出"
        except Exception:
            return "GPU: 状態不明"
    
    def _bind_events(self):
        """イベントをバインド"""
        try:
            # ドラッグ&ドロップ設定（フォーカスイベント除外）
            self._setup_drag_drop()
        except Exception as e:
            logging.warning(f"イベントバインドエラー（継続可能）: {e}")
    
    def _setup_drag_drop(self):
        """ドラッグ&ドロップを設定"""
        try:
            # tkinterdnd2がインストールされており、メソッドが利用可能な場合のみ設定
            from tkinterdnd2 import DND_FILES
            
            # drop_target_registerメソッドが存在するかチェック
            if hasattr(self, 'drop_target_register'):
                self.drop_target_register(DND_FILES)
                self.dnd_bind('<<Drop>>', self._on_file_drop)
                logging.info("ドラッグ&ドロップ機能が有効です")
            else:
                logging.info("ドラッグ&ドロップは利用できません。ファイル選択ボタンを使用してください。")
            
        except ImportError:
            # tkinterdndが利用できない場合はスキップ
            logging.info("tkinterdnd2が利用できません。ファイル選択ボタンを使用してください。")
        except Exception as e:
            # その他のエラーも無視
            logging.info(f"ドラッグ&ドロップは無効です。ファイル選択ボタンを使用してください。")
    
    def _on_file_drop(self, event):
        """ファイルドロップ時の処理"""
        try:
            files = self.tk.splitlist(event.data)
            if files:
                file_path = Path(files[0])
                if file_path.suffix.lower() in ['.wav', '.mp3', '.flac', '.m4a', '.aac']:
                    self.file_selector.set_file(file_path)
                else:
                    messagebox.showerror("エラー", "対応していないファイル形式です。")
        except Exception as e:
            logging.error(f"ファイルドロップエラー: {e}")
    
    def _on_window_configure(self, event):
        """ウィンドウサイズ変更時の処理"""
        if event.widget == self:
            # 設定を自動保存（遅延実行）
            if hasattr(self, '_save_timer'):
                self.after_cancel(self._save_timer)
            self._save_timer = self.after(1000, self._auto_save_settings)
    
    def _on_main_start_click(self):
        """メイン分離開始ボタンクリック"""
        try:
            self.controller.start_separation()
            logging.info("メイン分離開始ボタンクリック")
        except Exception as e:
            logging.error(f"メイン分離開始ボタンエラー: {e}")
    
    def update_main_button_state(self, is_processing: bool, has_file: bool):
        """メイン分離開始ボタンの状態を更新"""
        try:
            if is_processing:
                self.main_start_button.config(
                    state=tk.DISABLED,
                    text="🔄 処理中..."
                )
            else:
                if has_file:
                    self.main_start_button.config(
                        state=tk.NORMAL,
                        text="🎯 音声分離を開始"
                    )
                else:
                    self.main_start_button.config(
                        state=tk.DISABLED,
                        text="📁 ファイルを選択してください"
                    )
        except Exception as e:
            logging.error(f"メインボタン状態更新エラー: {e}")
    
    def _auto_save_settings(self):
        """設定の自動保存"""
        try:
            settings = {
                'window': {
                    'geometry': self.geometry()
                }
            }
            
            # その他の設定も含める
            if hasattr(self, 'parameter_panel'):
                settings['parameters'] = self.parameter_panel.get_current_parameters()
            
            if hasattr(self, 'output_panel'):
                settings['output'] = self.output_panel.get_current_settings()
            
            self.controller.save_settings(settings)
            
        except Exception as e:
            logging.debug(f"自動設定保存エラー: {e}")
    
    def _load_settings(self):
        """設定を読み込み"""
        try:
            settings = self.controller.load_settings()
            if not settings:
                return
            
            # ウィンドウ設定
            if 'window' in settings and 'geometry' in settings['window']:
                self.geometry(settings['window']['geometry'])
            
            # パラメータ設定
            if 'parameters' in settings and hasattr(self, 'parameter_panel'):
                self.parameter_panel.set_parameters(settings['parameters'])
            
            # 出力設定
            if 'output' in settings and hasattr(self, 'output_panel'):
                self.output_panel.set_settings(settings['output'])
            
            logging.info("設定読み込み完了")
            
        except Exception as e:
            logging.error(f"設定読み込みエラー: {e}")
    
    def _show_help(self):
        """ヘルプを表示"""
        help_text = """
toyosatomimi - 音声分離アプリケーション

【使用方法】
1. 音声ファイルを選択またはドラッグ&ドロップ
2. 分離パラメータを調整（必要に応じて）
3. 出力設定を確認
4. 「分離開始」ボタンで処理開始

【対応形式】
入力: WAV, MP3, FLAC, M4A, AAC
出力: WAV, MP3, FLAC

【ショートカット】
Ctrl+N: 新しいプロジェクト
Ctrl+O: プロジェクトを開く
Ctrl+S: プロジェクトを保存
F5: 分離開始
Esc: 処理停止

【注意事項】
- GPU使用時は十分なVRAM容量を確保してください
- 長時間音声の処理には時間がかかります
- 処理中はコンピューターの他の作業を控えることを推奨
        """
        
        messagebox.showinfo("使用方法", help_text)
    
    def _show_about(self):
        """バージョン情報を表示"""
        about_text = """
toyosatomimi
音声分離アプリケーション

Version: 1.0.0
Author: toyosatomimi development team

使用技術:
- Demucs (BGM分離)
- pyannote-audio (話者分離)
- tkinter (GUI)

ライセンス:
このソフトウェアはMITライセンスの下で提供されています。
        """
        
        messagebox.showinfo("バージョン情報", about_text)
    
    def _on_closing(self):
        """ウィンドウクローズ時の処理"""
        try:
            # 処理中の確認
            if self.controller.is_processing():
                result = messagebox.askyesno(
                    "確認",
                    "処理中です。アプリケーションを終了しますか？\n処理は中断されます。"
                )
                if not result:
                    return
                
                # 処理を停止
                self.controller.stop_separation()
            
            # 設定を保存
            self._auto_save_settings()
            
            # ウィンドウを閉じる
            self.destroy()
            
            logging.info("アプリケーション終了")
            
        except Exception as e:
            logging.error(f"終了処理エラー: {e}")
            self.destroy()
    
    def update_status(self, message: str):
        """ステータスバーを更新"""
        try:
            self.status_label.config(text=message)
        except Exception as e:
            logging.error(f"ステータス更新エラー: {e}")


def main():
    """メイン実行関数"""
    try:
        # X11/XCBマルチスレッド対応（WSL環境用）
        import os
        import sys
        
        # WSL環境でのX11/XCB問題対応
        if 'DISPLAY' in os.environ:
            # OpenGL設定
            os.environ['LIBGL_ALWAYS_INDIRECT'] = '1'
            os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
            
            # XCBマルチスレッド問題対応
            try:
                # Xlib/XCBのスレッド初期化を強制
                import ctypes
                import ctypes.util
                
                # X11ライブラリをロード
                x11_lib = ctypes.util.find_library('X11')
                if x11_lib:
                    x11 = ctypes.CDLL(x11_lib)
                    # XInitThreadsを呼び出してマルチスレッド対応
                    if hasattr(x11, 'XInitThreads'):
                        x11.XInitThreads()
            except Exception:
                # ライブラリが見つからない場合は無視
                pass
            
            # 代替手段：環境変数でXCB問題を回避
            os.environ['XCB_SYNCHRONIZE'] = '1'
            os.environ['PYTHONPATH'] = os.environ.get('PYTHONPATH', '') + ':.'
        
        # ロギング設定（マルチスレッド対応）
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True  # 既存のログ設定を上書き
        )
        
        # tkinterインポート（テスト不要、直接実行）
        
        # アプリケーション実行
        app = MainWindow()
        app.mainloop()
        
    except Exception as e:
        logging.error(f"アプリケーション実行エラー: {e}")
        # GUIエラーメッセージ表示は条件付き
        try:
            from tkinter import messagebox
            messagebox.showerror("致命的エラー", f"アプリケーションの起動に失敗しました:\n{e}")
        except:
            print(f"❌ 致命的エラー: {e}")
            print("🖥️ Windows環境での実行を試してください")


if __name__ == "__main__":
    main()