"""
設定管理システム

アプリケーションの設定を管理し、ユーザー設定の永続化を提供
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from .file_utils import FileUtils


class ConfigManager:
    """設定管理クラス"""
    
    # デフォルト設定
    DEFAULT_CONFIG = {
        # Demucs設定
        'demucs': {
            'model': 'htdemucs',
            'device': 'auto',
            'output_format': 'wav'
        },
        
        # pyannote-audio設定
        'speaker_separation': {
            'min_duration': 1.0,
            'model': 'pyannote/speaker-diarization-3.1',
            'use_auth_token': True
        },
        
        # 音声処理設定
        'audio': {
            'sample_rate': 44100,
            'normalize_output': True,
            'apply_fade': True,
            'fade_duration': 0.01
        },
        
        # GUI設定
        'gui': {
            'window_width': 800,
            'window_height': 600,
            'remember_paths': True,
            'show_advanced_options': False
        },
        
        # 出力設定
        'output': {
            'create_individual_segments': True,
            'create_combined_files': True,
            'output_directory': None,  # Noneの場合は入力ファイルと同じ場所
            'organize_by_speaker': True
        },
        
        # ログ設定
        'logging': {
            'level': 'INFO',
            'file_logging': True,
            'console_logging': True,
            'max_log_files': 5
        },
        
        # その他
        'misc': {
            'check_updates': True,
            'send_analytics': False,
            'language': 'ja'
        }
    }
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        設定管理を初期化
        
        Args:
            config_file: 設定ファイルパス（Noneの場合はデフォルト位置）
        """
        if config_file is None:
            # デフォルトの設定ファイルパス
            self.config_file = self._get_default_config_path()
        else:
            self.config_file = Path(config_file)
        
        self._config = {}
        self._load_config()
    
    def _get_default_config_path(self) -> Path:
        """
        デフォルトの設定ファイルパスを取得
        
        Returns:
            Path: 設定ファイルパス
        """
        # ユーザーディレクトリの設定フォルダ
        if os.name == 'nt':  # Windows
            config_dir = Path.home() / 'AppData' / 'Local' / 'toyosatomimi'
        else:  # Linux/Mac
            config_dir = Path.home() / '.config' / 'toyosatomimi'
        
        return config_dir / 'config.json'
    
    def _load_config(self) -> None:
        """設定ファイルを読み込み"""
        try:
            if self.config_file.exists():
                self._config = FileUtils.read_json(self.config_file)
                logging.info(f"設定ファイル読み込み完了: {self.config_file}")
            else:
                logging.info("設定ファイルが見つかりません。デフォルト設定を使用します")
                
            # デフォルト設定でマージ
            self._config = self._merge_with_defaults(self._config)
            
        except Exception as e:
            logging.error(f"設定ファイル読み込みエラー: {e}")
            self._config = self.DEFAULT_CONFIG.copy()
    
    def _merge_with_defaults(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        ユーザー設定をデフォルト設定にマージ
        
        Args:
            user_config: ユーザー設定
            
        Returns:
            Dict[str, Any]: マージされた設定
        """
        def deep_merge(default: Dict, user: Dict) -> Dict:
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        return deep_merge(self.DEFAULT_CONFIG, user_config)
    
    def save_config(self) -> bool:
        """
        設定をファイルに保存
        
        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            success = FileUtils.write_json(self.config_file, self._config)
            if success:
                logging.info(f"設定ファイル保存完了: {self.config_file}")
            return success
        except Exception as e:
            logging.error(f"設定ファイル保存エラー: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key_path: 設定キーのパス（例: "demucs.model"）
            default: デフォルト値
            
        Returns:
            Any: 設定値
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        設定値を設定
        
        Args:
            key_path: 設定キーのパス（例: "demucs.model"）
            value: 設定値
        """
        keys = key_path.split('.')
        config = self._config
        
        # 最後のキー以外は辞書を作成
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        
        # 最後のキーに値を設定
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        設定セクション全体を取得
        
        Args:
            section: セクション名
            
        Returns:
            Dict[str, Any]: セクションの設定
        """
        return self._config.get(section, {}).copy()
    
    def set_section(self, section: str, config: Dict[str, Any]) -> None:
        """
        設定セクション全体を設定
        
        Args:
            section: セクション名
            config: セクションの設定
        """
        self._config[section] = config.copy()
    
    def reset_to_defaults(self) -> None:
        """設定をデフォルトにリセット"""
        self._config = self.DEFAULT_CONFIG.copy()
        logging.info("設定をデフォルトにリセットしました")
    
    def backup_config(self) -> Optional[Path]:
        """
        現在の設定をバックアップ
        
        Returns:
            Optional[Path]: バックアップファイルパス
        """
        if not self.config_file.exists():
            return None
        
        return FileUtils.backup_file(self.config_file)
    
    def validate_config(self) -> Dict[str, Any]:
        """
        設定の妥当性をチェック
        
        Returns:
            Dict[str, Any]: 検証結果
        """
        issues = []
        warnings = []
        
        # Demucs設定の検証
        demucs_model = self.get('demucs.model')
        if demucs_model not in ['htdemucs', 'htdemucs_ft', 'mdx_extra']:
            issues.append(f"無効なDemucsモデル: {demucs_model}")
        
        # 話者分離設定の検証
        min_duration = self.get('speaker_separation.min_duration')
        if not isinstance(min_duration, (int, float)) or min_duration <= 0:
            issues.append(f"無効な最小分離時間: {min_duration}")
        
        # 音声設定の検証
        sample_rate = self.get('audio.sample_rate')
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            issues.append(f"無効なサンプリングレート: {sample_rate}")
        
        # 出力ディレクトリの検証
        output_dir = self.get('output.output_directory')
        if output_dir is not None:
            output_path = Path(output_dir)
            if not output_path.exists():
                warnings.append(f"出力ディレクトリが存在しません: {output_dir}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        全設定を取得
        
        Returns:
            Dict[str, Any]: 全設定のコピー
        """
        return self._config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        設定を一括更新
        
        Args:
            updates: 更新する設定
        """
        self._config = self._merge_with_defaults(updates)
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """
        デフォルト設定を取得
        
        Returns:
            Dict[str, Any]: デフォルト設定のコピー
        """
        return cls.DEFAULT_CONFIG.copy()