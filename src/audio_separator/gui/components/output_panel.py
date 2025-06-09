"""
出力設定パネル

音声分離の出力設定を管理するUIコンポーネント
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, Any
import logging


class OutputPanel(ttk.Frame):
    """出力設定パネル"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # 出力設定
        self.settings = {
            'output_dir': Path.cwd() / 'output',
            'create_combined': True,
            'create_individual': True,
            'create_bgm': True,
            'audio_format': 'wav',
            'sample_rate': 44100,
            'bit_depth': 16,
            'naming_style': 'detailed',
            'create_report': True
        }
        
        self._create_widgets()
        self._setup_layout()
        
        # 初期設定をコントローラーに通知
        self.controller.on_output_settings_changed(self.settings)
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.LabelFrame(self, text="📂 出力設定", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 出力ディレクトリ選択
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dir_frame, text="📁 出力ディレクトリ:").pack(anchor=tk.W)
        
        dir_select_frame = ttk.Frame(dir_frame)
        dir_select_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.dir_var = tk.StringVar(value=str(self.settings['output_dir']))
        self.dir_entry = ttk.Entry(dir_select_frame, textvariable=self.dir_var, state='readonly')
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            dir_select_frame,
            text="📁",
            command=self._select_output_dir,
            width=3
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 出力内容選択
        content_frame = ttk.LabelFrame(main_frame, text="📋 出力内容", padding=5)
        content_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.combined_var = tk.BooleanVar(value=self.settings['create_combined'])
        self.combined_var.trace('w', self._on_setting_change)
        ttk.Checkbutton(
            content_frame,
            text="🎵 統合ファイル (話者ごとの結合音声)",
            variable=self.combined_var
        ).pack(anchor=tk.W, pady=(0, 2))
        
        self.individual_var = tk.BooleanVar(value=self.settings['create_individual'])
        self.individual_var.trace('w', self._on_setting_change)
        ttk.Checkbutton(
            content_frame,
            text="📁 個別セグメント (セグメントごとの音声ファイル)",
            variable=self.individual_var
        ).pack(anchor=tk.W, pady=(0, 2))
        
        self.bgm_var = tk.BooleanVar(value=self.settings['create_bgm'])
        self.bgm_var.trace('w', self._on_setting_change)
        ttk.Checkbutton(
            content_frame,
            text="🎼 BGM分離ファイル (BGM + ボーカル)",
            variable=self.bgm_var
        ).pack(anchor=tk.W, pady=(0, 2))
        
        self.report_var = tk.BooleanVar(value=self.settings['create_report'])
        self.report_var.trace('w', self._on_setting_change)
        ttk.Checkbutton(
            content_frame,
            text="📊 分離レポート (JSON形式の詳細情報)",
            variable=self.report_var
        ).pack(anchor=tk.W)
        
        # 音声形式設定
        format_frame = ttk.LabelFrame(main_frame, text="🎵 音声形式", padding=5)
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        # フォーマット選択
        format_select_frame = ttk.Frame(format_frame)
        format_select_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(format_select_frame, text="形式:").pack(side=tk.LEFT)
        
        self.format_var = tk.StringVar(value=self.settings['audio_format'])
        self.format_var.trace('w', self._on_setting_change)
        
        format_combo = ttk.Combobox(
            format_select_frame,
            textvariable=self.format_var,
            values=['wav', 'mp3', 'flac'],
            state='readonly',
            width=10
        )
        format_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # サンプリングレート
        sr_frame = ttk.Frame(format_frame)
        sr_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(sr_frame, text="サンプリングレート:").pack(side=tk.LEFT)
        
        self.sr_var = tk.IntVar(value=self.settings['sample_rate'])
        self.sr_var.trace('w', self._on_setting_change)
        
        sr_combo = ttk.Combobox(
            sr_frame,
            textvariable=self.sr_var,
            values=[22050, 44100, 48000, 96000],
            state='readonly',
            width=10
        )
        sr_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(sr_frame, text="Hz").pack(side=tk.LEFT, padx=(5, 0))
        
        # ファイル命名規則
        naming_frame = ttk.LabelFrame(main_frame, text="📝 ファイル命名", padding=5)
        naming_frame.pack(fill=tk.X)
        
        self.naming_var = tk.StringVar(value=self.settings['naming_style'])
        self.naming_var.trace('w', self._on_setting_change)
        
        ttk.Radiobutton(
            naming_frame,
            text="📄 簡易 (segment_001.wav)",
            variable=self.naming_var,
            value='simple'
        ).pack(anchor=tk.W, pady=(0, 2))
        
        ttk.Radiobutton(
            naming_frame,
            text="📋 詳細 (filename_speaker01_seg001_0m15s-0m23s.wav)",
            variable=self.naming_var,
            value='detailed'
        ).pack(anchor=tk.W)
    
    def _setup_layout(self):
        """レイアウトを設定"""
        pass
    
    def _select_output_dir(self):
        """出力ディレクトリを選択"""
        dir_path = filedialog.askdirectory(
            title="出力ディレクトリを選択",
            initialdir=self.settings['output_dir']
        )
        
        if dir_path:
            self.settings['output_dir'] = Path(dir_path)
            self.dir_var.set(str(dir_path))
            self._notify_change()
            logging.info(f"出力ディレクトリ選択: {dir_path}")
    
    def _on_setting_change(self, *args):
        """設定変更時のコールバック"""
        # 設定を更新
        self.settings.update({
            'create_combined': self.combined_var.get(),
            'create_individual': self.individual_var.get(),
            'create_bgm': self.bgm_var.get(),
            'audio_format': self.format_var.get(),
            'sample_rate': self.sr_var.get(),
            'naming_style': self.naming_var.get(),
            'create_report': self.report_var.get()
        })
        
        self._notify_change()
    
    def _notify_change(self):
        """変更をコントローラーに通知"""
        self.controller.on_output_settings_changed(self.settings)
        logging.debug("出力設定変更通知")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """現在の設定を取得"""
        return self.settings.copy()
    
    def set_settings(self, settings: Dict[str, Any]):
        """設定を適用"""
        self.settings.update(settings)
        
        # UIを更新
        if 'output_dir' in settings:
            self.dir_var.set(str(settings['output_dir']))
        
        if 'create_combined' in settings:
            self.combined_var.set(settings['create_combined'])
        
        if 'create_individual' in settings:
            self.individual_var.set(settings['create_individual'])
        
        if 'create_bgm' in settings:
            self.bgm_var.set(settings['create_bgm'])
        
        if 'audio_format' in settings:
            self.format_var.set(settings['audio_format'])
        
        if 'sample_rate' in settings:
            self.sr_var.set(settings['sample_rate'])
        
        if 'naming_style' in settings:
            self.naming_var.set(settings['naming_style'])
        
        if 'create_report' in settings:
            self.report_var.set(settings['create_report'])
        
        self._notify_change()
    
    def validate_settings(self) -> bool:
        """設定の妥当性をチェック"""
        # 出力ディレクトリの存在確認
        output_dir = Path(self.settings['output_dir'])
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror(
                "エラー",
                f"出力ディレクトリの作成に失敗:\n{output_dir}\n\n{e}"
            )
            return False
        
        # 出力内容の確認
        if not any([
            self.settings['create_combined'],
            self.settings['create_individual'],
            self.settings['create_bgm']
        ]):
            messagebox.showerror(
                "エラー",
                "少なくとも1つの出力内容を選択してください。"
            )
            return False
        
        return True
    
    def get_output_directory(self) -> Path:
        """出力ディレクトリを取得"""
        return Path(self.settings['output_dir'])
    
    def is_combined_enabled(self) -> bool:
        """統合ファイル出力が有効かチェック"""
        return self.settings['create_combined']
    
    def is_individual_enabled(self) -> bool:
        """個別セグメント出力が有効かチェック"""
        return self.settings['create_individual']
    
    def get_naming_style(self) -> str:
        """ファイル命名スタイルを取得"""
        return self.settings['naming_style']