"""
パラメータ調整パネル

話者分離のパラメータを調整するUIコンポーネント
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable
import logging


class ParameterSlider(ttk.Frame):
    """パラメータスライダーウィジェット"""
    
    def __init__(self, parent, label: str, min_val: float, max_val: float, 
                 default_val: float, resolution: float = 0.1, 
                 tooltip: str = "", callback: Callable = None):
        super().__init__(parent)
        
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.resolution = resolution
        self.callback = callback
        
        # 変数
        self.var = tk.DoubleVar(value=default_val)
        self.var.trace('w', self._on_change)
        
        self._create_widgets(tooltip)
    
    def _create_widgets(self, tooltip: str):
        """ウィジェットを作成"""
        # ラベル
        label_frame = ttk.Frame(self)
        label_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.label_widget = ttk.Label(label_frame, text=self.label)
        self.label_widget.pack(side=tk.LEFT)
        
        # 値表示
        self.value_label = ttk.Label(label_frame, text=f"{self.var.get():.1f}")
        self.value_label.pack(side=tk.RIGHT)
        
        # スライダー
        self.scale = ttk.Scale(
            self,
            from_=self.min_val,
            to=self.max_val,
            variable=self.var,
            orient=tk.HORIZONTAL,
            length=200
        )
        self.scale.pack(fill=tk.X)
        
        # ツールチップ
        if tooltip:
            self._create_tooltip(tooltip)
    
    def _create_tooltip(self, text: str):
        """ツールチップを作成"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(
                tooltip,
                text=text,
                background="lightyellow",
                relief="solid",
                borderwidth=1,
                font=("Arial", 9)
            )
            label.pack()
            
            # 3秒後に閉じる
            tooltip.after(3000, tooltip.destroy)
        
        self.label_widget.bind('<Button-1>', show_tooltip)
    
    def _on_change(self, *args):
        """値変更時のコールバック"""
        value = round(self.var.get(), 1)
        self.value_label.config(text=f"{value:.1f}")
        
        if self.callback:
            self.callback(self.label, value)
    
    def get_value(self) -> float:
        """現在の値を取得"""
        return round(self.var.get(), 1)
    
    def set_value(self, value: float):
        """値を設定"""
        self.var.set(value)


class ParameterPanel(ttk.Frame):
    """パラメータ調整パネル"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # パラメータ値を保存する辞書
        self.parameters = {}
        
        # デフォルト値
        self.defaults = {
            'clustering_threshold': 0.3,
            'segmentation_onset': 0.2,
            'segmentation_offset': 0.2,
            'force_num_speakers': 0,  # 0 = 自動
            'min_segment_duration': 0.5,
            'overlap_removal': True,
            'audio_preprocessing': True
        }
        
        # 現在の値をデフォルトで初期化
        self.parameters.update(self.defaults)
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.LabelFrame(self, text="🎚️ パラメータ設定", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # スクロール可能フレーム
        canvas = tk.Canvas(main_frame, height=300)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # クラスタリング閾値
        self.clustering_slider = ParameterSlider(
            scrollable_frame,
            label="🎯 クラスタリング閾値",
            min_val=0.1,
            max_val=0.9,
            default_val=self.defaults['clustering_threshold'],
            resolution=0.1,
            tooltip="話者の分離精度を調整\\n低いほど細かく分離\\n高いほど統合的に分離",
            callback=self._on_parameter_change
        )
        self.clustering_slider.pack(fill=tk.X, pady=(0, 10))
        
        # セグメンテーション感度
        seg_frame = ttk.LabelFrame(scrollable_frame, text="🎵 セグメンテーション感度", padding=5)
        seg_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.onset_slider = ParameterSlider(
            seg_frame,
            label="開始感度 (onset)",
            min_val=0.1,
            max_val=0.9,
            default_val=self.defaults['segmentation_onset'],
            resolution=0.1,
            tooltip="音声セグメントの開始点検出感度\\n低いほど細かく検出",
            callback=self._on_parameter_change
        )
        self.onset_slider.pack(fill=tk.X, pady=(0, 5))
        
        self.offset_slider = ParameterSlider(
            seg_frame,
            label="終了感度 (offset)",
            min_val=0.1,
            max_val=0.9,
            default_val=self.defaults['segmentation_offset'],
            resolution=0.1,
            tooltip="音声セグメントの終了点検出感度\\n低いほど細かく検出",
            callback=self._on_parameter_change
        )
        self.offset_slider.pack(fill=tk.X)
        
        # 話者数設定
        speaker_frame = ttk.Frame(scrollable_frame)
        speaker_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(speaker_frame, text="👥 強制話者数:").pack(side=tk.LEFT)
        
        self.speaker_var = tk.IntVar(value=self.defaults['force_num_speakers'])
        self.speaker_var.trace('w', self._on_speaker_change)
        
        self.speaker_spinbox = tk.Spinbox(
            speaker_frame,
            from_=0,
            to=10,
            width=5,
            textvariable=self.speaker_var
        )
        self.speaker_spinbox.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(speaker_frame, text="(0=自動検出)").pack(side=tk.LEFT, padx=(5, 0))
        
        # 最小セグメント長
        self.min_duration_slider = ParameterSlider(
            scrollable_frame,
            label="⏱️ 最小セグメント長 (秒)",
            min_val=0.1,
            max_val=3.0,
            default_val=self.defaults['min_segment_duration'],
            resolution=0.1,
            tooltip="これより短いセグメントは除外されます",
            callback=self._on_parameter_change
        )
        self.min_duration_slider.pack(fill=tk.X, pady=(0, 10))
        
        # チェックボックス設定
        checkbox_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ 処理オプション", padding=5)
        checkbox_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 重複発話除去
        self.overlap_var = tk.BooleanVar(value=self.defaults['overlap_removal'])
        self.overlap_var.trace('w', self._on_checkbox_change)
        
        overlap_check = ttk.Checkbutton(
            checkbox_frame,
            text="🚫 重複発話除去",
            variable=self.overlap_var
        )
        overlap_check.pack(anchor=tk.W, pady=(0, 5))
        
        # 音声前処理
        self.preprocessing_var = tk.BooleanVar(value=self.defaults['audio_preprocessing'])
        self.preprocessing_var.trace('w', self._on_checkbox_change)
        
        preprocessing_check = ttk.Checkbutton(
            checkbox_frame,
            text="🎛️ 音声前処理",
            variable=self.preprocessing_var
        )
        preprocessing_check.pack(anchor=tk.W)
        
        # プリセット機能
        preset_frame = ttk.LabelFrame(scrollable_frame, text="📋 プリセット", padding=5)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        # プリセット選択
        preset_select_frame = ttk.Frame(preset_frame)
        preset_select_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(preset_select_frame, text="選択:").pack(side=tk.LEFT)
        
        self.preset_var = tk.StringVar(value="カスタム")
        self.preset_combo = ttk.Combobox(
            preset_select_frame,
            textvariable=self.preset_var,
            values=["標準設定", "高精度分離", "高速処理", "2人会話", "カスタム"],
            state="readonly",
            width=15
        )
        self.preset_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.preset_combo.bind('<<ComboboxSelected>>', self._on_preset_change)
        
        # プリセットボタン
        button_frame = ttk.Frame(preset_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="💾 保存",
            command=self._save_preset,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="🔄 リセット",
            command=self._reset_to_defaults,
            width=8
        ).pack(side=tk.LEFT)
        
        # スクロールバーを配置
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _setup_layout(self):
        """レイアウトを設定"""
        pass
    
    def _on_parameter_change(self, param_name: str, value: float):
        """パラメータ変更時のコールバック"""
        # パラメータ名を内部名に変換
        param_map = {
            "🎯 クラスタリング閾値": "clustering_threshold",
            "開始感度 (onset)": "segmentation_onset", 
            "終了感度 (offset)": "segmentation_offset",
            "⏱️ 最小セグメント長 (秒)": "min_segment_duration"
        }
        
        internal_name = param_map.get(param_name, param_name)
        self.parameters[internal_name] = value
        
        # プリセットをカスタムに変更（preset_varが初期化されている場合のみ）
        if hasattr(self, 'preset_var'):
            self.preset_var.set("カスタム")
        
        # コントローラーに通知
        self.controller.on_parameters_changed(self.parameters)
        
        logging.debug(f"パラメータ変更: {internal_name} = {value}")
    
    def _on_speaker_change(self, *args):
        """話者数変更時のコールバック"""
        value = self.speaker_var.get()
        self.parameters['force_num_speakers'] = value if value > 0 else None
        
        # プリセットをカスタムに変更（preset_varが初期化されている場合のみ）
        if hasattr(self, 'preset_var'):
            self.preset_var.set("カスタム")
        
        # コントローラーに通知
        self.controller.on_parameters_changed(self.parameters)
        
        logging.debug(f"強制話者数変更: {value}")
    
    def _on_checkbox_change(self, *args):
        """チェックボックス変更時のコールバック"""
        self.parameters['overlap_removal'] = self.overlap_var.get()
        self.parameters['audio_preprocessing'] = self.preprocessing_var.get()
        
        # プリセットをカスタムに変更（preset_varが初期化されている場合のみ）
        if hasattr(self, 'preset_var'):
            self.preset_var.set("カスタム")
        
        # コントローラーに通知
        self.controller.on_parameters_changed(self.parameters)
        
        logging.debug(f"オプション変更: overlap={self.overlap_var.get()}, preprocessing={self.preprocessing_var.get()}")
    
    def _on_preset_change(self, event=None):
        """プリセット変更時のコールバック"""
        preset_name = self.preset_var.get()
        
        if preset_name == "カスタム":
            return
        
        # プリセット定義
        presets = {
            "標準設定": {
                'clustering_threshold': 0.3,
                'segmentation_onset': 0.2,
                'segmentation_offset': 0.2,
                'force_num_speakers': None,
                'min_segment_duration': 0.5,
                'overlap_removal': True,
                'audio_preprocessing': True
            },
            "高精度分離": {
                'clustering_threshold': 0.2,
                'segmentation_onset': 0.1,
                'segmentation_offset': 0.1,
                'force_num_speakers': None,
                'min_segment_duration': 0.3,
                'overlap_removal': True,
                'audio_preprocessing': True
            },
            "高速処理": {
                'clustering_threshold': 0.5,
                'segmentation_onset': 0.4,
                'segmentation_offset': 0.4,
                'force_num_speakers': None,
                'min_segment_duration': 1.0,
                'overlap_removal': False,
                'audio_preprocessing': False
            },
            "2人会話": {
                'clustering_threshold': 0.3,
                'segmentation_onset': 0.2,
                'segmentation_offset': 0.2,
                'force_num_speakers': 2,
                'min_segment_duration': 0.5,
                'overlap_removal': True,
                'audio_preprocessing': True
            }
        }
        
        if preset_name in presets:
            self._apply_preset(presets[preset_name])
            logging.info(f"プリセット適用: {preset_name}")
    
    def _apply_preset(self, preset_params: Dict[str, Any]):
        """プリセットを適用"""
        # パラメータを更新
        self.parameters.update(preset_params)
        
        # UIを更新
        self.clustering_slider.set_value(preset_params['clustering_threshold'])
        self.onset_slider.set_value(preset_params['segmentation_onset'])
        self.offset_slider.set_value(preset_params['segmentation_offset'])
        self.min_duration_slider.set_value(preset_params['min_segment_duration'])
        
        self.speaker_var.set(preset_params['force_num_speakers'] or 0)
        self.overlap_var.set(preset_params['overlap_removal'])
        self.preprocessing_var.set(preset_params['audio_preprocessing'])
        
        # コントローラーに通知
        self.controller.on_parameters_changed(self.parameters)
    
    def _save_preset(self):
        """現在の設定をプリセットとして保存"""
        # TODO: プリセット保存ダイアログの実装
        from tkinter import simpledialog
        
        name = simpledialog.askstring("プリセット保存", "プリセット名を入力してください:")
        if name:
            # TODO: 実際の保存処理
            logging.info(f"プリセット保存: {name}")
            messagebox.showinfo("保存完了", f"プリセット '{name}' を保存しました。")
    
    def _reset_to_defaults(self):
        """デフォルト値にリセット"""
        self._apply_preset(self.defaults)
        self.preset_var.set("標準設定")
        logging.info("パラメータをデフォルト値にリセット")
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """現在のパラメータを取得"""
        return self.parameters.copy()
    
    def set_parameters(self, params: Dict[str, Any]):
        """パラメータを設定"""
        self._apply_preset(params)
        self.preset_var.set("カスタム")
    
    def get_separation_params(self) -> Dict[str, Any]:
        """話者分離用のパラメータを取得"""
        return {
            'clustering_threshold': self.parameters['clustering_threshold'],
            'segmentation_onset': self.parameters['segmentation_onset'],
            'segmentation_offset': self.parameters['segmentation_offset'],
            'force_num_speakers': self.parameters['force_num_speakers'],
            'min_duration': self.parameters['min_segment_duration']
        }
    
    def is_overlap_removal_enabled(self) -> bool:
        """重複除去が有効かチェック"""
        return self.parameters['overlap_removal']
    
    def is_preprocessing_enabled(self) -> bool:
        """音声前処理が有効かチェック"""
        return self.parameters['audio_preprocessing']