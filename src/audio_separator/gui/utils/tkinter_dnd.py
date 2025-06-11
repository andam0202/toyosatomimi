#!/usr/bin/env python3
"""
Tkinter ネイティブドラッグ&ドロップ実装
Windows の WM_DROPFILES メッセージを直接処理
"""

import tkinter as tk
from tkinter import messagebox
import logging
from pathlib import Path
from typing import Callable
import ctypes
from ctypes import wintypes
import sys

# Windows API 定数
WM_DROPFILES = 0x233
GWLP_WNDPROC = -4

class TkinterDragDrop:
    """Tkinter ウィジェット用ドラッグ&ドロップクラス"""
    
    def __init__(self, widget: tk.Widget, callback: Callable[[str], None]):
        self.widget = widget
        self.callback = callback
        self.hwnd = None
        self.original_wndproc = None
        self.new_wndproc = None
        
        # Widget が描画されるまで待機
        self.widget.after(100, self._setup_drop)
    
    def _setup_drop(self):
        """ドロップ機能を設定"""
        try:
            # ウィンドウハンドルを取得
            self.hwnd = self.widget.winfo_id()
            
            if self.hwnd:
                # DragAcceptFiles を有効化
                ctypes.windll.shell32.DragAcceptFiles(self.hwnd, True)
                
                # ウィンドウプロシージャをフック
                self._hook_wndproc()
                
                logging.info("tkinter ドラッグ&ドロップが有効になりました")
                return True
                
        except Exception as e:
            logging.warning(f"ドラッグ&ドロップ設定失敗: {e}")
            return False
    
    def _hook_wndproc(self):
        """ウィンドウプロシージャをフック"""
        try:
            # WndProc の型定義
            WNDPROC = ctypes.WINFUNCTYPE(
                ctypes.c_long,      # 戻り値 
                ctypes.c_void_p,    # hwnd
                ctypes.c_uint,      # uMsg
                ctypes.c_void_p,    # wParam
                ctypes.c_void_p     # lParam
            )
            
            def new_wndproc(hwnd, msg, wparam, lparam):
                if msg == WM_DROPFILES:
                    self._handle_dropped_files(wparam)
                    return 0
                # 元のプロシージャを呼び出し
                return ctypes.windll.user32.CallWindowProcW(
                    self.original_wndproc, hwnd, msg, wparam, lparam
                )
            
            # 新しいプロシージャを保存（ガベージコレクション防止）
            self.new_wndproc = WNDPROC(new_wndproc)
            
            # ウィンドウプロシージャを置き換え
            self.original_wndproc = ctypes.windll.user32.SetWindowLongPtrW(
                self.hwnd, GWLP_WNDPROC, self.new_wndproc
            )
            
        except Exception as e:
            logging.error(f"ウィンドウプロシージャフック失敗: {e}")
    
    def _handle_dropped_files(self, hdrop):
        """ドロップされたファイルを処理"""
        try:
            # ファイル数を取得
            file_count = ctypes.windll.shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
            
            if file_count > 0:
                # バッファサイズを取得
                buffer_size = ctypes.windll.shell32.DragQueryFileW(hdrop, 0, None, 0) + 1
                
                # ファイルパスを取得
                buffer = ctypes.create_unicode_buffer(buffer_size)
                ctypes.windll.shell32.DragQueryFileW(hdrop, 0, buffer, buffer_size)
                
                file_path = buffer.value
                if file_path:
                    # メインスレッドでコールバックを実行
                    self.widget.after(0, lambda: self.callback(file_path))
            
            # ドロップハンドルを解放
            ctypes.windll.shell32.DragFinish(hdrop)
            
        except Exception as e:
            logging.error(f"ドロップファイル処理エラー: {e}")
    
    def cleanup(self):
        """クリーンアップ"""
        if self.hwnd and self.original_wndproc:
            try:
                ctypes.windll.user32.SetWindowLongPtrW(
                    self.hwnd, GWLP_WNDPROC, self.original_wndproc
                )
                ctypes.windll.shell32.DragAcceptFiles(self.hwnd, False)
            except:
                pass

def setup_tkinter_drag_drop(widget: tk.Widget, callback: Callable[[str], None]) -> bool:
    """
    tkinter ウィジェットにドラッグ&ドロップを設定
    
    Args:
        widget: ドロップ対象のウィジェット
        callback: ファイルドロップ時のコールバック関数
    
    Returns:
        bool: 設定成功かどうか
    """
    try:
        if sys.platform != "win32":
            logging.warning("tkinter ドラッグ&ドロップはWindows専用です")
            return False
        
        dnd = TkinterDragDrop(widget, callback)
        
        # Widget に dnd オブジェクトを保存（ガベージコレクション防止）
        widget._dnd_handler = dnd
        
        return True
        
    except Exception as e:
        logging.error(f"tkinter ドラッグ&ドロップ設定失敗: {e}")
        return False

def test_drag_drop():
    """ドラッグ&ドロップのテスト"""
    
    def on_file_dropped(file_path):
        print(f"ファイルがドロップされました: {file_path}")
        label.config(text=f"ドロップされたファイル:\n{Path(file_path).name}")
    
    root = tk.Tk()
    root.title("ドラッグ&ドロップ テスト")
    root.geometry("400x300")
    
    label = tk.Label(
        root,
        text="ここにファイルをドラッグ&ドロップしてください",
        bg="lightblue",
        relief="solid",
        bd=2,
        font=("Arial", 12)
    )
    label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # ドラッグ&ドロップを設定
    success = setup_tkinter_drag_drop(label, on_file_dropped)
    
    if success:
        print("ドラッグ&ドロップが有効になりました")
    else:
        print("ドラッグ&ドロップの設定に失敗しました")
    
    root.mainloop()

if __name__ == "__main__":
    test_drag_drop()