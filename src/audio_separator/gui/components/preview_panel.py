"""
プレビューパネル

分離結果の表示とプレビューを提供するUIコンポーネント
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import subprocess
import platform


class PreviewPanel(ttk.Frame):
    """プレビューパネル"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # 現在の結果データ
        self.current_results = None
        
        self._create_widgets()
        self._setup_layout()
        
        # 初期状態
        self._show_initial_state()
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.LabelFrame(self, text="📺 結果プレビュー", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 結果表示エリア
        self.result_notebook = ttk.Notebook(main_frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 概要タブ
        self.overview_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.overview_frame, text="📊 概要")
        
        # ファイル一覧タブ
        self.files_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.files_frame, text="📁 ファイル一覧")
        
        # 分析タブ
        self.analysis_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.analysis_frame, text="🔍 分析結果")
        
        # 概要タブのコンテンツ
        self._create_overview_tab()
        
        # ファイル一覧タブのコンテンツ
        self._create_files_tab()
        
        # 分析タブのコンテンツ
        self._create_analysis_tab()
        
        # アクションボタン
        self._create_action_buttons(main_frame)
    
    def _create_overview_tab(self):
        """概要タブのコンテンツを作成"""
        # スクロール可能フレーム
        canvas = tk.Canvas(self.overview_frame)
        scrollbar = ttk.Scrollbar(self.overview_frame, orient="vertical", command=canvas.yview)
        self.overview_content = ttk.Frame(canvas)
        
        self.overview_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.overview_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 概要情報ラベル
        self.overview_labels = {}
        
        # 入力ファイル情報
        input_frame = ttk.LabelFrame(self.overview_content, text="📥 入力ファイル", padding=5)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.overview_labels['input_file'] = ttk.Label(input_frame, text="")
        self.overview_labels['input_file'].pack(anchor=tk.W)
        
        self.overview_labels['input_duration'] = ttk.Label(input_frame, text="")
        self.overview_labels['input_duration'].pack(anchor=tk.W)
        
        self.overview_labels['input_size'] = ttk.Label(input_frame, text="")
        self.overview_labels['input_size'].pack(anchor=tk.W)
        
        # 処理結果情報
        result_frame = ttk.LabelFrame(self.overview_content, text="📤 処理結果", padding=5)
        result_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.overview_labels['speakers_count'] = ttk.Label(result_frame, text="")
        self.overview_labels['speakers_count'].pack(anchor=tk.W)
        
        self.overview_labels['output_files'] = ttk.Label(result_frame, text="")
        self.overview_labels['output_files'].pack(anchor=tk.W)
        
        self.overview_labels['total_size'] = ttk.Label(result_frame, text="")
        self.overview_labels['total_size'].pack(anchor=tk.W)
        
        # 処理時間情報
        time_frame = ttk.LabelFrame(self.overview_content, text="⏱️ 処理時間", padding=5)
        time_frame.pack(fill=tk.X)
        
        self.overview_labels['processing_time'] = ttk.Label(time_frame, text="")
        self.overview_labels['processing_time'].pack(anchor=tk.W)
        
        self.overview_labels['processing_speed'] = ttk.Label(time_frame, text="")
        self.overview_labels['processing_speed'].pack(anchor=tk.W)
    
    def _create_files_tab(self):
        """ファイル一覧タブのコンテンツを作成"""
        # ツリービュー
        tree_frame = ttk.Frame(self.files_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # ツリービューとスクロールバー
        self.files_tree = ttk.Treeview(
            tree_frame,
            columns=('size', 'duration', 'type'),
            show='tree headings'
        )
        
        # 列の設定
        self.files_tree.heading('#0', text='ファイル名')
        self.files_tree.heading('size', text='サイズ')
        self.files_tree.heading('duration', text='長さ')
        self.files_tree.heading('type', text='種類')
        
        self.files_tree.column('#0', width=300)
        self.files_tree.column('size', width=100)
        self.files_tree.column('duration', width=100)
        self.files_tree.column('type', width=100)
        
        # スクロールバー
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.files_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        # ダブルクリックでファイルを開く
        self.files_tree.bind('<Double-1>', self._on_file_double_click)
        
        # 右クリックメニュー
        self._create_file_context_menu()
    
    def _create_analysis_tab(self):
        """分析タブのコンテンツを作成"""
        # スクロール可能テキストエリア
        text_frame = ttk.Frame(self.analysis_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.analysis_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Courier', 10)
        )
        
        analysis_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=analysis_scrollbar.set)
        
        self.analysis_text.pack(side="left", fill="both", expand=True)
        analysis_scrollbar.pack(side="right", fill="y")
    
    def _create_action_buttons(self, parent):
        """アクションボタンを作成"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 出力フォルダを開くボタン
        self.open_folder_button = ttk.Button(
            button_frame,
            text="📁 出力フォルダを開く",
            command=self._open_output_folder,
            state=tk.DISABLED
        )
        self.open_folder_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # レポート保存ボタン
        self.save_report_button = ttk.Button(
            button_frame,
            text="📊 レポート保存",
            command=self._save_report,
            state=tk.DISABLED
        )
        self.save_report_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 結果クリアボタン
        self.clear_button = ttk.Button(
            button_frame,
            text="🗑️ 結果クリア",
            command=self._clear_results,
            state=tk.DISABLED
        )
        self.clear_button.pack(side=tk.RIGHT)
    
    def _create_file_context_menu(self):
        """ファイル右クリックメニューを作成"""
        self.file_context_menu = tk.Menu(self, tearoff=0)
        self.file_context_menu.add_command(label="ファイルを開く", command=self._open_selected_file)
        self.file_context_menu.add_command(label="フォルダで表示", command=self._show_in_folder)
        self.file_context_menu.add_separator()
        self.file_context_menu.add_command(label="パスをコピー", command=self._copy_file_path)
        
        self.files_tree.bind('<Button-3>', self._show_file_context_menu)
    
    def _setup_layout(self):
        """レイアウトを設定"""
        pass
    
    def _show_initial_state(self):
        """初期状態を表示"""
        # 概要タブ
        for label in self.overview_labels.values():
            label.config(text="")
        
        # 待機メッセージ
        welcome_text = """
toyosatomimi 音声分離アプリケーション

📝 使用手順:
1. 音声ファイルを選択
2. 分離パラメータを調整
3. 出力設定を確認
4. 分離開始ボタンをクリック

分離処理が完了すると、ここに結果が表示されます。

🎵 対応ファイル形式:
- WAV, MP3, FLAC, M4A, AAC

🔧 主な機能:
- BGM分離 (Demucs)
- 話者分離 (pyannote-audio)
- GPU加速対応
        """
        
        # 概要タブに初期メッセージを表示
        ttk.Label(
            self.overview_content,
            text=welcome_text,
            justify=tk.LEFT,
            font=('Arial', 10)
        ).pack(anchor=tk.W, pady=20)
    
    def update_results(self, results: Optional[Dict[str, Any]]):
        """結果を更新"""
        self.current_results = results
        
        if not results:
            self._clear_display()
            return
        
        try:
            # 概要タブを更新
            self._update_overview(results)
            
            # ファイル一覧タブを更新
            self._update_files_list(results)
            
            # 分析タブを更新
            self._update_analysis(results)
            
            # ボタン状態を更新
            self._update_button_states(True)
            
            logging.info("プレビュー更新完了")
            
        except Exception as e:
            logging.error(f"プレビュー更新エラー: {e}")
            messagebox.showerror("エラー", f"結果表示でエラー:\n{e}")
    
    def _update_overview(self, results: Dict[str, Any]):
        """概要タブを更新"""
        # 既存のウィジェットをクリア
        for widget in self.overview_content.winfo_children():
            widget.destroy()
        
        # 新しいコンテンツを作成
        self._create_overview_tab()
        
        # 入力ファイル情報
        input_file = results.get('input_file', '')
        self.overview_labels['input_file'].config(text=f"ファイル: {Path(input_file).name}")
        
        duration = results.get('duration', 0)
        self.overview_labels['input_duration'].config(text=f"長さ: {self._format_duration(duration)}")
        
        file_size = results.get('file_size', 0)
        self.overview_labels['input_size'].config(text=f"サイズ: {self._format_size(file_size)}")
        
        # 処理結果情報
        output_files = results.get('output_files', {})
        speakers_count = len(output_files)
        self.overview_labels['speakers_count'].config(text=f"検出話者数: {speakers_count}人")
        
        total_files = sum(len(files) for files in output_files.values())
        self.overview_labels['output_files'].config(text=f"出力ファイル数: {total_files}個")
        
        total_size = results.get('total_output_size', 0)
        self.overview_labels['total_size'].config(text=f"出力総サイズ: {self._format_size(total_size)}")
        
        # 処理時間情報
        processing_time = results.get('processing_time', 0)
        self.overview_labels['processing_time'].config(text=f"処理時間: {self._format_duration(processing_time)}")
        
        if duration > 0 and processing_time > 0:
            speed_ratio = duration / processing_time
            self.overview_labels['processing_speed'].config(text=f"処理速度: {speed_ratio:.1f}x リアルタイム")
        else:
            self.overview_labels['processing_speed'].config(text="処理速度: 計算不可")
    
    def _update_files_list(self, results: Dict[str, Any]):
        """ファイル一覧タブを更新"""
        # 既存のアイテムをクリア
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        output_files = results.get('output_files', {})
        
        for speaker_id, files in output_files.items():
            # 話者ノードを追加
            speaker_node = self.files_tree.insert(
                '',
                'end',
                text=f"🎤 {speaker_id}",
                values=('', '', '話者'),
                open=True
            )
            
            for file_path in files:
                file_path = Path(file_path)
                
                # ファイル情報を取得
                file_size = 0
                try:
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                except:
                    pass
                
                # ファイルタイプを判定
                if 'combined' in file_path.name:
                    file_type = "統合音声"
                    icon = "🎵"
                else:
                    file_type = "セグメント"
                    icon = "📄"
                
                # ファイルノードを追加
                self.files_tree.insert(
                    speaker_node,
                    'end',
                    text=f"{icon} {file_path.name}",
                    values=(
                        self._format_size(file_size),
                        "",  # 音声長は後で実装
                        file_type
                    )
                )
        
        # BGM分離ファイルも追加
        bgm_files = results.get('bgm_files', [])
        if bgm_files:
            bgm_node = self.files_tree.insert(
                '',
                'end',
                text="🎼 BGM分離",
                values=('', '', 'BGM'),
                open=True
            )
            
            for file_path in bgm_files:
                file_path = Path(file_path)
                
                file_size = 0
                try:
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                except:
                    pass
                
                if 'vocals' in file_path.name:
                    icon = "🎤"
                    file_type = "ボーカル"
                else:
                    icon = "🎼"
                    file_type = "BGM"
                
                self.files_tree.insert(
                    bgm_node,
                    'end',
                    text=f"{icon} {file_path.name}",
                    values=(
                        self._format_size(file_size),
                        "",
                        file_type
                    )
                )
    
    def _update_analysis(self, results: Dict[str, Any]):
        """分析タブを更新"""
        # テキストエリアを有効化
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)
        
        # 分析情報を作成
        analysis_text = self._generate_analysis_report(results)
        
        # テキストを挿入
        self.analysis_text.insert(tk.END, analysis_text)
        
        # テキストエリアを無効化
        self.analysis_text.config(state=tk.DISABLED)
    
    def _generate_analysis_report(self, results: Dict[str, Any]) -> str:
        """分析レポートを生成"""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append("toyosatomimi 音声分離 - 分析レポート")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # 入力ファイル情報
        report_lines.append("📥 入力ファイル情報")
        report_lines.append("-" * 30)
        report_lines.append(f"ファイル名: {Path(results.get('input_file', '')).name}")
        report_lines.append(f"ファイルサイズ: {self._format_size(results.get('file_size', 0))}")
        report_lines.append(f"音声長: {self._format_duration(results.get('duration', 0))}")
        report_lines.append("")
        
        # 処理パラメータ
        params = results.get('parameters', {})
        if params:
            report_lines.append("⚙️ 処理パラメータ")
            report_lines.append("-" * 30)
            for key, value in params.items():
                report_lines.append(f"{key}: {value}")
            report_lines.append("")
        
        # 検出結果
        output_files = results.get('output_files', {})
        report_lines.append("🎤 話者検出結果")
        report_lines.append("-" * 30)
        report_lines.append(f"検出話者数: {len(output_files)}人")
        
        for speaker_id, files in output_files.items():
            report_lines.append(f"\n{speaker_id}:")
            for file_path in files:
                file_size = 0
                try:
                    file_size = Path(file_path).stat().st_size
                except:
                    pass
                report_lines.append(f"  - {Path(file_path).name} ({self._format_size(file_size)})")
        
        report_lines.append("")
        
        # 処理時間情報
        report_lines.append("⏱️ パフォーマンス")
        report_lines.append("-" * 30)
        processing_time = results.get('processing_time', 0)
        report_lines.append(f"処理時間: {self._format_duration(processing_time)}")
        
        duration = results.get('duration', 0)
        if duration > 0 and processing_time > 0:
            speed_ratio = duration / processing_time
            report_lines.append(f"処理速度: {speed_ratio:.2f}x リアルタイム")
        
        # GPU情報
        gpu_info = results.get('gpu_info', '')
        if gpu_info:
            report_lines.append(f"GPU使用: {gpu_info}")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def _format_duration(self, seconds: float) -> str:
        """時間をフォーマット"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}分{secs:.1f}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}時間{minutes}分{secs:.1f}秒"
    
    def _format_size(self, bytes_size: int) -> str:
        """ファイルサイズをフォーマット"""
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"
    
    def _update_button_states(self, has_results: bool):
        """ボタン状態を更新"""
        state = tk.NORMAL if has_results else tk.DISABLED
        
        self.open_folder_button.config(state=state)
        self.save_report_button.config(state=state)
        self.clear_button.config(state=state)
    
    def _clear_display(self):
        """表示をクリア"""
        # 概要タブをクリア
        for widget in self.overview_content.winfo_children():
            widget.destroy()
        
        # ファイル一覧をクリア
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # 分析テキストをクリア
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.config(state=tk.DISABLED)
        
        # 初期状態を表示
        self._show_initial_state()
        
        # ボタン状態を更新
        self._update_button_states(False)
    
    def _clear_results(self):
        """結果をクリア"""
        self.current_results = None
        self._clear_display()
        logging.info("プレビュー結果クリア")
    
    def _open_output_folder(self):
        """出力フォルダを開く"""
        if not self.current_results:
            return
        
        output_dir = self.current_results.get('output_directory', '')
        if output_dir and Path(output_dir).exists():
            self._open_path_in_explorer(output_dir)
        else:
            messagebox.showerror("エラー", "出力フォルダが見つかりません。")
    
    def _save_report(self):
        """レポートを保存"""
        if not self.current_results:
            return
        
        try:
            from tkinter import filedialog
            
            # 保存先選択
            file_path = filedialog.asksaveasfilename(
                title="レポートを保存",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if file_path:
                # レポート生成
                report_content = self._generate_analysis_report(self.current_results)
                
                # ファイル保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                messagebox.showinfo("完了", f"レポートを保存しました:\n{file_path}")
                logging.info(f"レポート保存: {file_path}")
        
        except Exception as e:
            logging.error(f"レポート保存エラー: {e}")
            messagebox.showerror("エラー", f"レポート保存でエラー:\n{e}")
    
    def _on_file_double_click(self, event):
        """ファイルダブルクリック"""
        self._open_selected_file()
    
    def _show_file_context_menu(self, event):
        """ファイル右クリックメニュー表示"""
        try:
            self.file_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            logging.error(f"コンテキストメニューエラー: {e}")
    
    def _open_selected_file(self):
        """選択されたファイルを開く"""
        selection = self.files_tree.selection()
        if not selection:
            return
        
        try:
            item = selection[0]
            file_name = self.files_tree.item(item, 'text')
            
            # アイコンを除去してファイル名を取得
            clean_name = file_name.split(' ', 1)[-1] if ' ' in file_name else file_name
            
            # ファイルパスを構築
            if self.current_results:
                output_dir = Path(self.current_results.get('output_directory', ''))
                file_path = self._find_file_in_results(clean_name)
                
                if file_path and file_path.exists():
                    self._open_path_in_explorer(str(file_path))
                else:
                    messagebox.showerror("エラー", "ファイルが見つかりません。")
        
        except Exception as e:
            logging.error(f"ファイル開くエラー: {e}")
            messagebox.showerror("エラー", f"ファイルを開けませんでした:\n{e}")
    
    def _show_in_folder(self):
        """フォルダで表示"""
        selection = self.files_tree.selection()
        if not selection:
            return
        
        try:
            item = selection[0]
            file_name = self.files_tree.item(item, 'text')
            
            clean_name = file_name.split(' ', 1)[-1] if ' ' in file_name else file_name
            file_path = self._find_file_in_results(clean_name)
            
            if file_path and file_path.exists():
                self._show_file_in_explorer(str(file_path))
            else:
                messagebox.showerror("エラー", "ファイルが見つかりません。")
        
        except Exception as e:
            logging.error(f"フォルダ表示エラー: {e}")
    
    def _copy_file_path(self):
        """ファイルパスをコピー"""
        selection = self.files_tree.selection()
        if not selection:
            return
        
        try:
            item = selection[0]
            file_name = self.files_tree.item(item, 'text')
            
            clean_name = file_name.split(' ', 1)[-1] if ' ' in file_name else file_name
            file_path = self._find_file_in_results(clean_name)
            
            if file_path:
                # クリップボードにコピー
                self.clipboard_clear()
                self.clipboard_append(str(file_path))
                messagebox.showinfo("完了", "ファイルパスをクリップボードにコピーしました。")
        
        except Exception as e:
            logging.error(f"パスコピーエラー: {e}")
    
    def _find_file_in_results(self, file_name: str) -> Optional[Path]:
        """結果からファイルを検索"""
        if not self.current_results:
            return None
        
        # 全ての出力ファイルから検索
        output_files = self.current_results.get('output_files', {})
        for files in output_files.values():
            for file_path in files:
                if Path(file_path).name == file_name:
                    return Path(file_path)
        
        # BGMファイルからも検索
        bgm_files = self.current_results.get('bgm_files', [])
        for file_path in bgm_files:
            if Path(file_path).name == file_name:
                return Path(file_path)
        
        return None
    
    def _open_path_in_explorer(self, path: str):
        """パスをエクスプローラーで開く"""
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.Popen(['explorer', path])
            elif system == "Darwin":  # macOS
                subprocess.Popen(['open', path])
            else:  # Linux
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            logging.error(f"エクスプローラー起動エラー: {e}")
            messagebox.showerror("エラー", f"フォルダを開けませんでした:\n{e}")
    
    def _show_file_in_explorer(self, file_path: str):
        """ファイルをエクスプローラーで表示"""
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.Popen(['explorer', '/select,', file_path])
            elif system == "Darwin":  # macOS
                subprocess.Popen(['open', '-R', file_path])
            else:  # Linux
                # Linuxでは親ディレクトリを開く
                subprocess.Popen(['xdg-open', str(Path(file_path).parent)])
        except Exception as e:
            logging.error(f"ファイル表示エラー: {e}")
            # フォールバック：親ディレクトリを開く
            self._open_path_in_explorer(str(Path(file_path).parent))