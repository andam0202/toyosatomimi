"""
音声分離コントローラー

GUIとモデル間の制御ロジックを提供します。
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
import json
from tkinter import messagebox, filedialog

from ..models.gui_model import AudioSeparationModel, ProcessingProgress


class SeparationController:
    """音声分離コントローラー"""
    
    def __init__(self, model: AudioSeparationModel, view):
        self.model = model
        self.view = view
        
        # モデルのコールバックを設定
        self.model.add_progress_callback(self._on_progress_update)
        self.model.add_completion_callback(self._on_completion)
        
        logging.info("SeparationController初期化完了")
    
    def on_file_selected(self, file_path: Path, file_info: Dict[str, Any]):
        """ファイル選択時の処理"""
        try:
            # モデルに設定
            self.model.set_input_file(file_path, file_info)
            
            # UI状態を更新
            self._update_ui_state()
            
            logging.info(f"ファイル選択処理完了: {file_path}")
            
        except Exception as e:
            logging.error(f"ファイル選択処理エラー: {e}")
            messagebox.showerror("エラー", f"ファイル選択処理でエラー:\n{e}")
    
    def on_file_cleared(self):
        """ファイルクリア時の処理"""
        try:
            # モデルをリセット
            self.model.reset()
            
            # UI状態を更新
            self._update_ui_state()
            
            logging.info("ファイルクリア処理完了")
            
        except Exception as e:
            logging.error(f"ファイルクリア処理エラー: {e}")
    
    def on_parameters_changed(self, parameters: Dict[str, Any]):
        """パラメータ変更時の処理"""
        try:
            # モデルに設定
            self.model.set_separation_parameters(parameters)
            
            logging.debug("パラメータ更新完了")
            
        except Exception as e:
            logging.error(f"パラメータ更新エラー: {e}")
    
    def on_output_settings_changed(self, settings: Dict[str, Any]):
        """出力設定変更時の処理"""
        try:
            # モデルに設定
            self.model.set_output_settings(settings)
            
            logging.debug("出力設定更新完了")
            
        except Exception as e:
            logging.error(f"出力設定更新エラー: {e}")
    
    def start_separation(self):
        """音声分離を開始"""
        try:
            # 入力チェック
            if not self.model.input_file:
                messagebox.showerror("エラー", "音声ファイルを選択してください。")
                return
            
            # 出力ディレクトリチェック
            output_dir = self.model.output_settings.get('output_dir')
            if not output_dir:
                messagebox.showerror("エラー", "出力ディレクトリを設定してください。")
                return
            
            # 処理開始
            success = self.model.start_separation()
            if not success:
                messagebox.showerror("エラー", "処理の開始に失敗しました。")
                return
            
            # UI状態を更新
            self._update_ui_state()
            
            logging.info("音声分離開始")
            
        except Exception as e:
            logging.error(f"音声分離開始エラー: {e}")
            messagebox.showerror("エラー", f"処理開始でエラー:\n{e}")
    
    def stop_separation(self):
        """音声分離を停止"""
        try:
            if not self.model.is_processing():
                return
            
            # ユーザー確認
            result = messagebox.askyesno(
                "確認",
                "処理を停止しますか？\n進行中の処理は失われます。"
            )
            
            if result:
                self.model.stop_separation()
                logging.info("音声分離停止")
            
        except Exception as e:
            logging.error(f"音声分離停止エラー: {e}")
    
    def pause_separation(self):
        """音声分離を一時停止（将来実装）"""
        # TODO: 一時停止機能の実装
        messagebox.showinfo("情報", "一時停止機能は今後実装予定です。")
    
    def new_project(self):
        """新しいプロジェクト"""
        try:
            if self.model.is_processing():
                result = messagebox.askyesno(
                    "確認",
                    "処理中です。新しいプロジェクトを開始しますか？\n現在の処理は停止されます。"
                )
                if not result:
                    return
            
            # モデルをリセット
            self.model.reset()
            
            # UIをリセット
            if hasattr(self.view, 'file_selector'):
                self.view.file_selector._clear_selection()
            if hasattr(self.view, 'parameter_panel'):
                self.view.parameter_panel._reset_to_defaults()
            
            self._update_ui_state()
            
            logging.info("新しいプロジェクト開始")
            
        except Exception as e:
            logging.error(f"新しいプロジェクト開始エラー: {e}")
            messagebox.showerror("エラー", f"新しいプロジェクトの開始でエラー:\n{e}")
    
    def open_project(self):
        """プロジェクトを開く"""
        try:
            # プロジェクトファイル選択
            file_path = filedialog.askopenfilename(
                title="プロジェクトファイルを選択",
                filetypes=[
                    ("Project files", "*.json"),
                    ("All files", "*.*")
                ],
                defaultextension=".json"
            )
            
            if not file_path:
                return
            
            # プロジェクトファイル読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # プロジェクト復元
            self._restore_project(project_data)
            
            logging.info(f"プロジェクト読み込み完了: {file_path}")
            messagebox.showinfo("完了", "プロジェクトを読み込みました。")
            
        except Exception as e:
            logging.error(f"プロジェクト読み込みエラー: {e}")
            messagebox.showerror("エラー", f"プロジェクトの読み込みでエラー:\n{e}")
    
    def save_project(self):
        """プロジェクトを保存"""
        try:
            # 保存先選択
            file_path = filedialog.asksaveasfilename(
                title="プロジェクトファイルを保存",
                filetypes=[
                    ("Project files", "*.json"),
                    ("All files", "*.*")
                ],
                defaultextension=".json"
            )
            
            if not file_path:
                return
            
            # プロジェクトデータ作成
            project_data = self._create_project_data()
            
            # ファイル保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"プロジェクト保存完了: {file_path}")
            messagebox.showinfo("完了", "プロジェクトを保存しました。")
            
        except Exception as e:
            logging.error(f"プロジェクト保存エラー: {e}")
            messagebox.showerror("エラー", f"プロジェクトの保存でエラー:\n{e}")
    
    def save_settings(self, settings: Dict[str, Any]):
        """設定を保存"""
        try:
            # 設定ディレクトリを作成
            config_dir = Path.home() / '.toyosatomimi'
            config_dir.mkdir(exist_ok=True)
            
            # 設定ファイルに保存
            config_file = config_dir / 'gui_settings.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            logging.debug("設定保存完了")
            
        except Exception as e:
            logging.error(f"設定保存エラー: {e}")
    
    def load_settings(self) -> Optional[Dict[str, Any]]:
        """設定を読み込み"""
        try:
            config_file = Path.home() / '.toyosatomimi' / 'gui_settings.json'
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logging.debug("設定読み込み完了")
                return settings
            
        except Exception as e:
            logging.error(f"設定読み込みエラー: {e}")
        
        return None
    
    def is_processing(self) -> bool:
        """処理中かどうかをチェック"""
        return self.model.is_processing()
    
    def get_separation_results(self) -> Optional[Dict[str, Any]]:
        """分離結果を取得"""
        return self.model.get_separation_results()
    
    def _on_progress_update(self, progress: ProcessingProgress):
        """進捗更新時のコールバック"""
        try:
            # プログレスバーを更新
            if hasattr(self.view, 'progress_display'):
                self.view.progress_display.update_progress(
                    progress.percentage,
                    progress.message,
                    progress.time_remaining,
                    progress.processing_speed
                )
            
            # UI状態を更新
            self._update_ui_state()
            
        except Exception as e:
            logging.error(f"進捗更新エラー: {e}")
    
    def _on_completion(self, success: bool, error_message: Optional[str]):
        """処理完了時のコールバック"""
        try:
            if success:
                # 成功時の処理
                logging.info("音声分離処理完了")
                
                # 結果を表示
                results = self.model.get_separation_results()
                if results and results['output_files']:
                    file_count = sum(len(files) for files in results['output_files'].values())
                    messagebox.showinfo(
                        "処理完了",
                        f"音声分離が完了しました。\n\n"
                        f"話者数: {len(results['output_files'])}人\n"
                        f"出力ファイル数: {file_count}個\n\n"
                        f"結果は出力ディレクトリで確認できます。"
                    )
                
                # プレビューパネルを更新
                if hasattr(self.view, 'preview_panel'):
                    self.view.preview_panel.update_results(results)
            
            else:
                # エラー時の処理
                logging.error(f"音声分離処理エラー: {error_message}")
                messagebox.showerror(
                    "処理エラー",
                    f"音声分離処理でエラーが発生しました。\n\n{error_message}"
                )
            
            # UI状態を更新
            self._update_ui_state()
            
        except Exception as e:
            logging.error(f"完了処理エラー: {e}")
    
    def _update_ui_state(self):
        """UI状態を更新"""
        try:
            is_processing = self.model.is_processing()
            has_file = self.model.input_file is not None
            
            # 実行制御ボタンの状態更新
            if hasattr(self.view, 'control_buttons'):
                self.view.control_buttons.update_button_states(is_processing, has_file)
            
        except Exception as e:
            logging.error(f"UI状態更新エラー: {e}")
    
    def _create_project_data(self) -> Dict[str, Any]:
        """プロジェクトデータを作成"""
        project_data = {
            'version': '1.0',
            'input_file': str(self.model.input_file) if self.model.input_file else None,
            'file_info': self.model.file_info,
            'separation_params': self.model.separation_params,
            'output_settings': self.model.output_settings
        }
        
        # GUI設定も追加
        if hasattr(self.view, 'parameter_panel'):
            project_data['parameters'] = self.view.parameter_panel.get_current_parameters()
        
        if hasattr(self.view, 'output_panel'):
            project_data['output'] = self.view.output_panel.get_current_settings()
        
        return project_data
    
    def _restore_project(self, project_data: Dict[str, Any]):
        """プロジェクトを復元"""
        # 入力ファイル復元
        if project_data.get('input_file'):
            file_path = Path(project_data['input_file'])
            if file_path.exists():
                if hasattr(self.view, 'file_selector'):
                    self.view.file_selector.set_file(file_path)
        
        # パラメータ復元
        if project_data.get('parameters') and hasattr(self.view, 'parameter_panel'):
            self.view.parameter_panel.set_parameters(project_data['parameters'])
        
        # 出力設定復元
        if project_data.get('output') and hasattr(self.view, 'output_panel'):
            self.view.output_panel.set_settings(project_data['output'])