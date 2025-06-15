"""
実行制御ボタン

音声分離処理の開始・停止・一時停止を制御するUIコンポーネント
"""

import tkinter as tk
from tkinter import ttk
import logging


class ControlButtons(ttk.Frame):
    """実行制御ボタン"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self._create_widgets()
        self._setup_layout()
        
        # 初期状態設定
        self.update_button_states(is_processing=False, has_file=False)
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.LabelFrame(self, text="⚙️ 処理制御", padding=10)
        main_frame.pack(fill=tk.X)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        # 一時停止ボタン
        self.pause_button = ttk.Button(
            button_frame,
            text="⏸️ 一時停止",
            command=self._on_pause_click
        )
        self.pause_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 停止ボタン
        self.stop_button = ttk.Button(
            button_frame,
            text="⏹️ 停止",
            command=self._on_stop_click
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 設定保存ボタン
        self.save_button = ttk.Button(
            button_frame,
            text="💾 設定保存",
            command=self._on_save_click
        )
        self.save_button.pack(side=tk.LEFT)
        
        # ステータス表示
        self.status_label = ttk.Label(
            main_frame,
            text="待機中",
            font=('Arial', 10)
        )
        self.status_label.pack(pady=(10, 0))
    
    def _setup_layout(self):
        """レイアウトを設定"""
        pass
    
    def _on_pause_click(self):
        """一時停止ボタンクリック"""
        try:
            self.controller.pause_separation()
            logging.info("一時停止ボタンクリック")
        except Exception as e:
            logging.error(f"一時停止ボタンエラー: {e}")
    
    def _on_stop_click(self):
        """停止ボタンクリック"""
        try:
            self.controller.stop_separation()
            logging.info("停止ボタンクリック")
        except Exception as e:
            logging.error(f"停止ボタンエラー: {e}")
    
    def _on_save_click(self):
        """設定保存ボタンクリック"""
        try:
            # 現在の設定を取得して保存
            settings = {}
            
            # パラメータパネルから設定取得
            if hasattr(self.controller.view, 'parameter_panel'):
                settings['parameters'] = self.controller.view.parameter_panel.get_current_parameters()
            
            # 出力パネルから設定取得
            if hasattr(self.controller.view, 'output_panel'):
                settings['output'] = self.controller.view.output_panel.get_current_settings()
            
            # ウィンドウ設定
            settings['window'] = {
                'geometry': self.controller.view.geometry()
            }
            
            self.controller.save_settings(settings)
            
            # 状態表示を一時的に更新
            original_text = self.status_label.cget('text')
            self.status_label.config(text="設定を保存しました", foreground='green')
            self.after(2000, lambda: self.status_label.config(text=original_text, foreground='black'))
            
            logging.info("設定保存ボタンクリック")
            
        except Exception as e:
            logging.error(f"設定保存ボタンエラー: {e}")
            self.status_label.config(text="設定保存エラー", foreground='red')
            self.after(2000, lambda: self.status_label.config(text="待機中", foreground='black'))
    
    def update_button_states(self, is_processing: bool, has_file: bool):
        """ボタンの状態を更新"""
        try:
            if is_processing:
                # 処理中
                self.pause_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.NORMAL)
                self.save_button.config(state=tk.DISABLED)
                self.status_label.config(text="処理中...", foreground='blue')
                
            else:
                # 待機中
                self.pause_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.DISABLED)
                self.save_button.config(state=tk.NORMAL)
                
                if has_file:
                    self.status_label.config(text="実行準備完了", foreground='green')
                else:
                    self.status_label.config(text="ファイルを選択してください", foreground='orange')
        
        except Exception as e:
            logging.error(f"ボタン状態更新エラー: {e}")
    
    def set_status_message(self, message: str, color: str = 'black'):
        """ステータスメッセージを設定"""
        try:
            self.status_label.config(text=message, foreground=color)
        except Exception as e:
            logging.error(f"ステータス設定エラー: {e}")