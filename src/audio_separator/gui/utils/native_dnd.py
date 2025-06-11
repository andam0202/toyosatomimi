#!/usr/bin/env python3
"""
シンプルドラッグ&ドロップ実装
クリック選択を中心とした実用的なファイル選択機能
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import logging
from pathlib import Path
from typing import Optional, Callable
import subprocess
import sys

# 簡易実装のため、Windows APIは使用しない
SIMPLE_DND_AVAILABLE = True

class EnhancedFileSelector:
    """拡張ファイル選択クラス"""
    
    def __init__(self, widget: tk.Widget, callback: Callable[[str], None]):
        self.widget = widget
        self.callback = callback
        self.setup_enhanced_selection()
    
    def setup_enhanced_selection(self):
        """拡張ファイル選択を設定"""
        # ダブルクリックでファイル選択
        self.widget.bind('<Double-Button-1>', self._on_double_click)
        
        # 右クリックでコンテキストメニュー
        self.widget.bind('<Button-3>', self._show_context_menu)
        
        # キーボードショートカット（スペースキー）
        self.widget.bind('<KeyPress-space>', self._on_space_key)
        self.widget.focus_set()  # フォーカスを設定してキーイベントを受信
        
        logging.info("拡張ファイル選択機能が有効になりました")
    
    def _on_double_click(self, event):
        """ダブルクリック時のファイル選択"""
        self._select_file()
    
    def _on_space_key(self, event):
        """スペースキー押下時のファイル選択"""
        self._select_file()
    
    def _show_context_menu(self, event):
        """右クリックメニューを表示"""
        try:
            context_menu = tk.Menu(self.widget, tearoff=0)
            context_menu.add_command(label="📁 ファイルを選択", command=self._select_file)
            context_menu.add_separator()
            context_menu.add_command(label="📋 クリップボードからパス", command=self._paste_from_clipboard)
            context_menu.add_separator()
            context_menu.add_command(label="🔍 最近のファイル", command=self._show_recent_files)
            
            context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logging.warning(f"コンテキストメニューエラー: {e}")
        finally:
            context_menu.grab_release()
    
    def _select_file(self):
        """ファイル選択ダイアログを表示"""
        file_path = filedialog.askopenfilename(
            title="音声ファイルを選択",
            filetypes=[
                ("音声ファイル", "*.wav *.mp3 *.flac *.m4a *.aac *.ogg *.wma"),
                ("WAVファイル", "*.wav"),
                ("MP3ファイル", "*.mp3"),
                ("FLACファイル", "*.flac"),
                ("M4Aファイル", "*.m4a"),
                ("すべてのファイル", "*.*")
            ],
            initialdir=str(Path.home() / "Music")  # 音楽フォルダから開始
        )
        
        if file_path:
            self.callback(file_path)
    
    def _paste_from_clipboard(self):
        """クリップボードからファイルパスを取得"""
        try:
            clipboard_text = self.widget.clipboard_get()
            if clipboard_text:
                path = Path(clipboard_text.strip())
                if path.exists() and path.is_file():
                    self.callback(str(path))
                else:
                    messagebox.showwarning("警告", "クリップボードの内容は有効なファイルパスではありません")
        except Exception as e:
            messagebox.showwarning("警告", "クリップボードからの読み取りに失敗しました")
    
    def _show_recent_files(self):
        """最近のファイルを表示（簡易実装）"""
        messagebox.showinfo("最近のファイル", "この機能は将来のバージョンで実装予定です")

class SimpleDragDropArea:
    """シンプルなドラッグ&ドロップエリア"""
    
    def __init__(self, parent: tk.Widget, callback: Callable[[str], None]):
        self.parent = parent
        self.callback = callback
        self.setup_visual_feedback()
    
    def setup_visual_feedback(self):
        """視覚的フィードバックを設定"""
        # クリック時のファイル選択として動作
        self.parent.bind('<Button-1>', self._on_click)
        self.parent.bind('<Enter>', self._on_enter)
        self.parent.bind('<Leave>', self._on_leave)
        
        # 初期スタイル保存
        self.original_bg = self.parent.cget('bg') if hasattr(self.parent, 'cget') else None
    
    def _on_click(self, event):
        """クリック時のファイル選択"""
        file_path = filedialog.askopenfilename(
            title="音声ファイルを選択",
            filetypes=[
                ("音声ファイル", "*.wav *.mp3 *.flac *.m4a *.aac"),
                ("WAVファイル", "*.wav"),
                ("MP3ファイル", "*.mp3"),
                ("FLACファイル", "*.flac"),
                ("M4Aファイル", "*.m4a"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            self.callback(file_path)
    
    def _on_enter(self, event):
        """マウスオーバー時のスタイル変更"""
        try:
            if hasattr(self.parent, 'config'):
                self.parent.config(bg='lightblue')
        except:
            pass
    
    def _on_leave(self, event):
        """マウスアウト時のスタイル復元"""
        try:
            if hasattr(self.parent, 'config') and self.original_bg:
                self.parent.config(bg=self.original_bg)
        except:
            pass

def setup_drag_drop(widget: tk.Widget, callback: Callable[[str], None]) -> tuple[bool, object]:
    """
    拡張ファイル選択を設定
    
    Args:
        widget: ドロップ対象のウィジェット
        callback: ファイルドロップ時のコールバック関数
    
    Returns:
        tuple[bool, object]: (設定成功かどうか, 選択オブジェクト)
    """
    try:
        # 拡張ファイル選択を設定
        enhanced_selector = EnhancedFileSelector(widget, callback)
        return True, enhanced_selector
        
    except Exception as e:
        logging.error(f"ファイル選択機能設定失敗: {e}")
        
        # 最終フォールバック: 簡易版
        try:
            simple_dnd = SimpleDragDropArea(widget, callback)
            return True, simple_dnd
        except Exception as e2:
            logging.error(f"簡易ファイル選択も失敗: {e2}")
            return False, None

def create_drop_indicator(parent: tk.Widget, text: str = "ファイルをドラッグ&ドロップ\nまたはクリックして選択") -> tk.Label:
    """
    ドロップインジケーターラベルを作成
    
    Args:
        parent: 親ウィジェット
        text: 表示テキスト
    
    Returns:
        tk.Label: ドロップインジケーター
    """
    indicator = tk.Label(
        parent,
        text=text,
        bg='lightgray',
        fg='darkblue',
        font=('Arial', 12),
        relief='dashed',
        bd=2,
        justify='center'
    )
    
    return indicator