"""
ファイル選択コンポーネント

ドラッグ&ドロップとファイル選択ダイアログを提供するUIコンポーネント
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional, Callable
import logging

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    logging.info("tkinterdnd2が利用できません。ネイティブドラッグ&ドロップを試行します。")

from ...utils.audio_utils import AudioUtils
from ..utils.native_dnd import setup_drag_drop, create_drop_indicator
from ..utils.tkinter_dnd import setup_tkinter_drag_drop
from ..utils.simple_dnd import setup_super_file_selector


class FileSelector(ttk.Frame):
    """ファイル選択コンポーネント"""
    
    # サポートされているファイル形式
    SUPPORTED_FORMATS = {
        '.wav': 'WAV Files',
        '.mp3': 'MP3 Files', 
        '.flac': 'FLAC Files',
        '.m4a': 'M4A Files',
        '.aac': 'AAC Files',
        '.ogg': 'OGG Files'
    }
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_file: Optional[Path] = None
        self.file_info: Optional[dict] = None
        
        self._create_widgets()
        self._setup_layout()
        self._setup_dnd()
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.LabelFrame(self, text="📁 ファイル選択", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ドロップエリア
        self.drop_frame = tk.Frame(
            main_frame, 
            height=100,
            relief=tk.RAISED,
            bd=2,
            bg='#f0f0f0'
        )
        self.drop_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ドロップエリアのラベル
        self.drop_label = tk.Label(
            self.drop_frame,
            text="📁 ファイルをドラッグ&ドロップまたはクリックして選択",
            font=('Arial', 12),
            bg='#f0f0f0',
            fg='#666666',
            cursor='hand2'
        )
        self.drop_label.pack(expand=True)
        
        # クリックイベント
        self.drop_label.bind('<Button-1>', self._on_click_select)
        self.drop_frame.bind('<Button-1>', self._on_click_select)
        
        # ファイル情報表示
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X)
        
        # ファイル情報ラベル
        self.info_label = ttk.Label(
            info_frame,
            text="ファイルが選択されていません",
            font=('Arial', 10)
        )
        self.info_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # クリアボタン
        self.clear_button = ttk.Button(
            info_frame,
            text="❌ クリア",
            command=self._clear_selection,
            state=tk.DISABLED
        )
        self.clear_button.pack(side=tk.RIGHT, padx=(10, 0))
    
    def _setup_layout(self):
        """レイアウトを設定"""
        # ドロップエリアのサイズを固定
        self.drop_frame.pack_propagate(False)
    
    def _setup_dnd(self):
        """ファイル選択機能を設定"""
        success = False
        
        # スーパーファイル選択を設定（メイン機能）
        try:
            def file_drop_callback(file_path: str):
                """ファイル選択コールバック"""
                self._handle_file_selection(Path(file_path))
            
            # スーパーファイル選択を設定
            success = setup_super_file_selector(self.drop_frame, file_drop_callback)
            
            if success:
                # ドロップエリアのテキストを更新
                self.drop_label.config(
                    text="📁 クリック・ダブルクリック・右クリックで選択\n🎵 複数の便利機能で簡単ファイル選択",
                    bg='lightcoral',
                    relief='solid',
                    bd=2,
                    font=('Arial', 11, 'bold'),
                    cursor='hand2'
                )
                logging.info("スーパーファイル選択機能が有効になりました")
                
        except Exception as e:
            logging.warning(f"スーパーファイル選択設定失敗: {e}")
        
        # フォールバック: クリック選択のみ
        if not success:
            self.drop_label.config(
                text="📁 クリックしてファイルを選択",
                bg='lightgray',
                cursor='hand2'
            )
            logging.info("基本ファイル選択機能が有効です")
    
    def _on_click_select(self, event=None):
        """クリックでファイル選択"""
        # ファイル選択ダイアログの設定
        filetypes = []
        for ext, desc in self.SUPPORTED_FORMATS.items():
            filetypes.append((desc, f'*{ext}'))
        filetypes.append(('All supported', ' '.join(f'*{ext}' for ext in self.SUPPORTED_FORMATS.keys())))
        filetypes.append(('All files', '*.*'))
        
        # ファイル選択ダイアログを表示
        file_path = filedialog.askopenfilename(
            title="音声ファイルを選択",
            filetypes=filetypes,
            initialdir=Path.home()
        )
        
        if file_path:
            self._process_file(Path(file_path))
    
    def _on_drop(self, event):
        """ドロップ時の処理"""
        files = event.data.split()
        if files:
            # 最初のファイルを処理
            file_path = Path(files[0].strip('{}'))
            self._process_file(file_path)
        
        # ドラッグ効果をリセット
        self._reset_drop_visual()
    
    def _on_drag_enter(self, event):
        """ドラッグエンター時の視覚効果"""
        self.drop_frame.config(bg='#e6f3ff', relief=tk.SUNKEN)
        self.drop_label.config(
            bg='#e6f3ff',
            text="📁 ファイルをドロップしてください",
            fg='#0066cc'
        )
    
    def _on_drag_leave(self, event):
        """ドラッグリーブ時の視覚効果をリセット"""
        self._reset_drop_visual()
    
    def _reset_drop_visual(self):
        """ドロップエリアの視覚効果をリセット"""
        self.drop_frame.config(bg='#f0f0f0', relief=tk.RAISED)
        if not self.selected_file:
            self.drop_label.config(
                bg='#f0f0f0',
                text="📁 ファイルをドラッグ&ドロップまたはクリックして選択",
                fg='#666666'
            )
    
    def _process_file(self, file_path: Path):
        """ファイルを処理"""
        try:
            # ファイル存在チェック
            if not file_path.exists():
                messagebox.showerror("エラー", f"ファイルが見つかりません:\\n{file_path}")
                return
            
            # ファイル形式チェック
            if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
                messagebox.showerror(
                    "エラー", 
                    f"サポートされていないファイル形式です:\\n{file_path.suffix}\\n\\n"
                    f"対応形式: {', '.join(self.SUPPORTED_FORMATS.keys())}"
                )
                return
            
            # 音声ファイルの検証
            if not AudioUtils.validate_audio_file(file_path):
                messagebox.showerror("エラー", "無効な音声ファイルです。")
                return
            
            # ファイル情報を取得
            try:
                self.file_info = AudioUtils.get_audio_info(file_path)
            except Exception as e:
                messagebox.showerror("エラー", f"ファイル情報の取得に失敗:\\n{e}")
                return
            
            # ファイル選択を更新
            self.selected_file = file_path
            self._update_display()
            
            # コントローラーに通知
            self.controller.on_file_selected(file_path, self.file_info)
            
            logging.info(f"ファイル選択: {file_path}")
            
        except Exception as e:
            logging.error(f"ファイル処理エラー: {e}")
            messagebox.showerror("エラー", f"ファイルの処理中にエラーが発生しました:\\n{e}")
    
    def _update_display(self):
        """表示を更新"""
        if self.selected_file and self.file_info:
            # ファイル名
            filename = self.selected_file.name
            
            # ファイル情報
            duration = self.file_info['duration']
            sample_rate = self.file_info['sample_rate']
            channels = self.file_info['channels']
            file_size = self.file_info['file_size']
            
            # 時間の表示形式
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            time_str = f"{minutes}:{seconds:02d}"
            
            # チャンネル表示
            channel_str = "ステレオ" if channels == 2 else f"{channels}ch"
            
            # ファイルサイズ表示
            if file_size > 1024 * 1024:
                size_str = f"{file_size / 1024 / 1024:.1f}MB"
            else:
                size_str = f"{file_size / 1024:.1f}KB"
            
            # 表示テキスト
            info_text = (
                f"選択済み: {filename} "
                f"({time_str}, {sample_rate}Hz, {channel_str}, {size_str})"
            )
            
            # ラベルを更新
            self.drop_label.config(
                text=f"✅ {filename}",
                fg='#006600'
            )
            self.info_label.config(text=info_text)
            self.clear_button.config(state=tk.NORMAL)
            
        else:
            # 選択なし状態
            self.drop_label.config(
                text="📁 ファイルをドラッグ&ドロップまたはクリックして選択",
                fg='#666666'
            )
            self.info_label.config(text="ファイルが選択されていません")
            self.clear_button.config(state=tk.DISABLED)
    
    def _clear_selection(self):
        """選択をクリア"""
        self.selected_file = None
        self.file_info = None
        self._update_display()
        self._reset_drop_visual()
        
        # コントローラーに通知
        self.controller.on_file_cleared()
        
        logging.info("ファイル選択をクリア")
    
    def get_selected_file(self) -> Optional[Path]:
        """選択されたファイルを取得"""
        return self.selected_file
    
    def get_file_info(self) -> Optional[dict]:
        """ファイル情報を取得"""
        return self.file_info
    
    def set_file(self, file_path: Path):
        """外部からファイルを設定"""
        self._process_file(file_path)
    
    def is_file_selected(self) -> bool:
        """ファイルが選択されているかチェック"""
        return self.selected_file is not None