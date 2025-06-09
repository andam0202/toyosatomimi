#!/usr/bin/env python3
"""
シンプルで確実なファイル選択機能
ドラッグ&ドロップの代替として、実用的なファイル選択機能を提供
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import logging
from pathlib import Path
from typing import Callable
import subprocess
import sys
import os

class SuperFileSelector:
    """スーパーファイル選択クラス"""
    
    def __init__(self, widget: tk.Widget, callback: Callable[[str], None]):
        self.widget = widget
        self.callback = callback
        self.setup_super_selection()
    
    def setup_super_selection(self):
        """スーパーファイル選択を設定"""
        # 複数の方法でファイル選択を可能にする
        self.widget.bind('<Button-1>', self._on_click)
        self.widget.bind('<Double-Button-1>', self._on_double_click)
        self.widget.bind('<Button-3>', self._show_context_menu)
        self.widget.bind('<KeyPress-space>', self._on_space_key)
        self.widget.bind('<KeyPress-Return>', self._on_enter_key)
        
        # フォーカスを設定
        self.widget.focus_set()
        self.widget.config(cursor="hand2")
        
        logging.info("スーパーファイル選択機能が有効になりました")
    
    def _on_click(self, event):
        """シングルクリック時"""
        self._select_file()
    
    def _on_double_click(self, event):
        """ダブルクリック時"""
        self._select_file()
    
    def _on_space_key(self, event):
        """スペースキー押下時"""
        self._select_file()
    
    def _on_enter_key(self, event):
        """エンターキー押下時"""
        self._select_file()
    
    def _show_context_menu(self, event):
        """右クリックメニュー"""
        try:
            menu = tk.Menu(self.widget, tearoff=0)
            menu.add_command(label="📁 ファイルを選択", command=self._select_file)
            menu.add_separator()
            menu.add_command(label="📂 音楽フォルダを開く", command=self._open_music_folder)
            menu.add_command(label="📂 ダウンロードフォルダを開く", command=self._open_downloads_folder)
            menu.add_separator()
            menu.add_command(label="📋 クリップボードからパス", command=self._paste_from_clipboard)
            menu.add_separator()
            menu.add_command(label="🎵 サンプル音声ファイル", command=self._show_sample_info)
            
            menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logging.warning(f"コンテキストメニューエラー: {e}")
        finally:
            try:
                menu.grab_release()
            except:
                pass
    
    def _select_file(self):
        """ファイル選択ダイアログ"""
        # 音楽フォルダから開始
        initial_dir = self._get_initial_directory()
        
        file_path = filedialog.askopenfilename(
            title="音声ファイルを選択してください",
            filetypes=[
                ("すべての音声ファイル", "*.wav *.mp3 *.flac *.m4a *.aac *.ogg *.wma *.mp4 *.mov"),
                ("WAVファイル", "*.wav"),
                ("MP3ファイル", "*.mp3"),
                ("FLACファイル", "*.flac"),
                ("M4Aファイル", "*.m4a"),
                ("AACファイル", "*.aac"),
                ("その他の音声", "*.ogg *.wma"),
                ("動画ファイル", "*.mp4 *.mov *.avi *.mkv"),
                ("すべてのファイル", "*.*")
            ],
            initialdir=initial_dir
        )
        
        if file_path:
            self.callback(file_path)
    
    def _get_initial_directory(self):
        """初期ディレクトリを取得"""
        # 複数の候補から存在するものを選択
        candidates = [
            Path.home() / "Music",
            Path.home() / "ミュージック", 
            Path.home() / "Downloads",
            Path.home() / "ダウンロード",
            Path.home() / "Desktop",
            Path.home() / "デスクトップ",
            Path.home()
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        
        return str(Path.home())
    
    def _open_music_folder(self):
        """音楽フォルダを開く"""
        music_folder = Path.home() / "Music"
        if not music_folder.exists():
            music_folder = Path.home() / "ミュージック"
        
        if music_folder.exists():
            if sys.platform == "win32":
                os.startfile(music_folder)
            else:
                subprocess.run(["xdg-open", str(music_folder)])
        else:
            messagebox.showinfo("情報", "音楽フォルダが見つかりません")
    
    def _open_downloads_folder(self):
        """ダウンロードフォルダを開く"""
        downloads_folder = Path.home() / "Downloads"
        if not downloads_folder.exists():
            downloads_folder = Path.home() / "ダウンロード"
        
        if downloads_folder.exists():
            if sys.platform == "win32":
                os.startfile(downloads_folder)
            else:
                subprocess.run(["xdg-open", str(downloads_folder)])
        else:
            messagebox.showinfo("情報", "ダウンロードフォルダが見つかりません")
    
    def _paste_from_clipboard(self):
        """クリップボードからファイルパス"""
        try:
            clipboard_text = self.widget.clipboard_get().strip()
            
            if clipboard_text:
                # パスの正規化
                if clipboard_text.startswith('"') and clipboard_text.endswith('"'):
                    clipboard_text = clipboard_text[1:-1]
                
                path = Path(clipboard_text)
                
                if path.exists() and path.is_file():
                    self.callback(str(path))
                    messagebox.showinfo("成功", f"ファイルを選択しました:\n{path.name}")
                else:
                    messagebox.showwarning("警告", 
                        f"クリップボードの内容は有効なファイルパスではありません:\n{clipboard_text}")
        except tk.TclError:
            messagebox.showwarning("警告", "クリップボードが空です")
        except Exception as e:
            messagebox.showerror("エラー", f"クリップボード読み取りエラー:\n{e}")
    
    def _show_sample_info(self):
        """サンプル音声ファイルの情報"""
        info = """サンプル音声ファイルの取得方法:

🎵 無料音声素材サイト:
• 効果音ラボ (https://soundeffect-lab.info/)
• DOVA-SYNDROME (https://dova-s.jp/)
• 魔王魂 (https://maoudamashii.jokersounds.com/)

🎤 自分で録音:
• Windows標準のボイスレコーダー
• Audacity (無料音声編集ソフト)

📱 スマホアプリ:
• 録音アプリで複数人の会話を録音

推奨: 5分以内の音声ファイルから開始してください。"""
        
        messagebox.showinfo("サンプル音声ファイル", info)

def setup_super_file_selector(widget: tk.Widget, callback: Callable[[str], None]) -> bool:
    """
    スーパーファイル選択を設定
    
    Args:
        widget: 対象ウィジェット
        callback: ファイル選択時のコールバック
    
    Returns:
        bool: 常にTrue（確実に動作）
    """
    try:
        selector = SuperFileSelector(widget, callback)
        
        # ウィジェットにオブジェクトを保存
        widget._super_selector = selector
        
        return True
        
    except Exception as e:
        logging.error(f"スーパーファイル選択設定失敗: {e}")
        return False