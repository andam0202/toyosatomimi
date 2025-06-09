"""
進捗表示コンポーネント

処理の進行状況を表示するUIコンポーネント
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
import logging


class ProgressDisplay(ttk.Frame):
    """進捗表示コンポーネント"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self._create_widgets()
        self._setup_layout()
        
        # 初期状態
        self.reset_progress()
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.LabelFrame(self, text="📊 進捗表示", padding=10)
        main_frame.pack(fill=tk.X)
        
        # 状態ラベル
        self.status_label = ttk.Label(
            main_frame,
            text="待機中",
            font=('Arial', 11, 'bold')
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100.0,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # 詳細情報フレーム
        detail_frame = ttk.Frame(main_frame)
        detail_frame.pack(fill=tk.X)
        
        # パーセンテージ表示
        self.percentage_label = ttk.Label(
            detail_frame,
            text="0%",
            font=('Arial', 10)
        )
        self.percentage_label.pack(side=tk.LEFT)
        
        # 残り時間表示
        self.time_label = ttk.Label(
            detail_frame,
            text="",
            font=('Arial', 10)
        )
        self.time_label.pack(side=tk.RIGHT)
        
        # 処理速度表示
        self.speed_label = ttk.Label(
            detail_frame,
            text="",
            font=('Arial', 10)
        )
        self.speed_label.pack(side=tk.RIGHT, padx=(0, 20))
    
    def _setup_layout(self):
        """レイアウトを設定"""
        pass
    
    def update_progress(self, percentage: float, status_message: str, 
                       time_remaining: Optional[float] = None,
                       processing_speed: Optional[float] = None):
        """進捗を更新"""
        try:
            # プログレスバーを更新
            self.progress_var.set(percentage)
            
            # ステータスメッセージを更新
            self.status_label.config(text=status_message)
            
            # パーセンテージを更新
            self.percentage_label.config(text=f"{percentage:.1f}%")
            
            # 残り時間を更新
            if time_remaining is not None:
                time_str = self._format_time(time_remaining)
                self.time_label.config(text=f"残り時間: {time_str}")
            else:
                self.time_label.config(text="")
            
            # 処理速度を更新
            if processing_speed is not None:
                self.speed_label.config(text=f"処理速度: {processing_speed:.1f}x")
            else:
                self.speed_label.config(text="")
            
            # 色分け
            if percentage >= 100.0:
                self.status_label.config(foreground='green')
            elif percentage > 0:
                self.status_label.config(foreground='blue')
            else:
                self.status_label.config(foreground='black')
            
            # 強制更新
            self.update_idletasks()
            
        except Exception as e:
            logging.error(f"進捗更新エラー: {e}")
    
    def set_error_state(self, error_message: str):
        """エラー状態を設定"""
        try:
            self.status_label.config(text=f"エラー: {error_message}", foreground='red')
            self.progress_var.set(0)
            self.percentage_label.config(text="0%")
            self.time_label.config(text="")
            self.speed_label.config(text="")
            
        except Exception as e:
            logging.error(f"エラー状態設定エラー: {e}")
    
    def set_cancelled_state(self):
        """キャンセル状態を設定"""
        try:
            self.status_label.config(text="処理がキャンセルされました", foreground='orange')
            self.time_label.config(text="")
            self.speed_label.config(text="")
            
        except Exception as e:
            logging.error(f"キャンセル状態設定エラー: {e}")
    
    def reset_progress(self):
        """進捗をリセット"""
        try:
            self.progress_var.set(0)
            self.status_label.config(text="待機中", foreground='black')
            self.percentage_label.config(text="0%")
            self.time_label.config(text="")
            self.speed_label.config(text="")
            
        except Exception as e:
            logging.error(f"進捗リセットエラー: {e}")
    
    def _format_time(self, seconds: float) -> str:
        """時間をフォーマット"""
        try:
            if seconds < 60:
                return f"{int(seconds)}秒"
            elif seconds < 3600:
                minutes = int(seconds // 60)
                secs = int(seconds % 60)
                return f"{minutes}分{secs:02d}秒"
            else:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                return f"{hours}時間{minutes:02d}分"
        except:
            return "計算中..."
    
    def pulse_mode(self, enable: bool = True):
        """パルスモード（不確定進捗）の切り替え"""
        try:
            if enable:
                self.progress_bar.config(mode='indeterminate')
                self.progress_bar.start(10)  # 10ms間隔でアニメーション
            else:
                self.progress_bar.stop()
                self.progress_bar.config(mode='determinate')
        except Exception as e:
            logging.error(f"パルスモード設定エラー: {e}")