"""
Demucs BGM分離プロセッサ

Demucsモデルを使用してBGMとボーカルを分離する処理を提供
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import numpy as np

from ..utils.audio_utils import AudioUtils


class DemucsProcessor:
    """Demucs BGM分離プロセッサクラス"""
    
    # 利用可能なDemucsモデル
    AVAILABLE_MODELS = {
        'htdemucs': {
            'description': '標準品質、高速処理',
            'quality': 'standard',
            'speed': 'fast'
        },
        'htdemucs_ft': {
            'description': '高品質、中速処理', 
            'quality': 'high',
            'speed': 'medium'
        },
        'mdx_extra': {
            'description': '最高品質、低速処理',
            'quality': 'highest',
            'speed': 'slow'
        }
    }
    
    def __init__(self, model_name: str = 'htdemucs', device: str = 'auto'):
        """
        Demucsプロセッサを初期化
        
        Args:
            model_name: 使用するDemucsモデル名
            device: 処理デバイス ('auto', 'cpu', 'cuda')
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self._is_initialized = False
        
        # モデル名の検証
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"サポートされていないモデル: {model_name}")
        
        logging.info(f"Demucsプロセッサ初期化: モデル={model_name}, デバイス={device}")
    
    def _initialize_model(self) -> None:
        """
        Demucsモデルを初期化（遅延初期化）
        
        Note: 現在はモックバージョン。実際のDemucs実装時に置き換える
        """
        if self._is_initialized:
            return
        
        try:
            # TODO: 実際のDemucsモデル初期化
            # from demucs.api import load_model
            # self.model = load_model(self.model_name)
            
            # モックバージョン
            logging.warning("モックバージョン: 実際のDemucsモデルは未実装")
            self.model = f"mock_{self.model_name}"
            self._is_initialized = True
            
            logging.info(f"Demucsモデル初期化完了: {self.model_name}")
            
        except Exception as e:
            raise RuntimeError(f"Demucsモデルの初期化に失敗: {e}")
    
    def separate(
        self,
        input_path: str,
        output_dir: str,
        vocals_name: str = 'vocals.wav',
        bgm_name: str = 'bgm.wav'
    ) -> Tuple[str, str]:
        """
        BGMとボーカルを分離する
        
        Args:
            input_path: 入力音声ファイルパス
            output_dir: 出力ディレクトリ
            vocals_name: ボーカル出力ファイル名
            bgm_name: BGM出力ファイル名
            
        Returns:
            Tuple[str, str]: (ボーカルファイルパス, BGMファイルパス)
            
        Raises:
            FileNotFoundError: 入力ファイルが見つからない場合
            RuntimeError: 分離処理に失敗した場合
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        
        # 入力ファイルの検証
        if not AudioUtils.validate_audio_file(input_path):
            raise FileNotFoundError(f"有効な音声ファイルが見つかりません: {input_path}")
        
        # 出力ディレクトリの作成
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 出力パスの設定
        vocals_path = output_dir / vocals_name
        bgm_path = output_dir / bgm_name
        
        logging.info(f"BGM分離開始: {input_path}")
        logging.info(f"モデル: {self.model_name}")
        logging.info(f"出力ディレクトリ: {output_dir}")
        
        try:
            # モデル初期化
            self._initialize_model()
            
            # 音声ファイル読み込み
            audio_data, sample_rate = AudioUtils.load_audio(input_path)
            
            # BGM分離処理（現在はモック）
            vocals, bgm = self._separate_audio_mock(audio_data, sample_rate)
            
            # 結果を保存
            AudioUtils.save_audio(vocals, vocals_path, sample_rate)
            AudioUtils.save_audio(bgm, bgm_path, sample_rate)
            
            logging.info(f"BGM分離完了")
            logging.info(f"ボーカル: {vocals_path}")
            logging.info(f"BGM: {bgm_path}")
            
            return str(vocals_path), str(bgm_path)
            
        except Exception as e:
            logging.error(f"BGM分離処理でエラー: {e}")
            raise RuntimeError(f"BGM分離に失敗: {e}")
    
    def _separate_audio_mock(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        音声分離のモック実装
        
        実際のDemucs実装までの暫定処理
        
        Args:
            audio_data: 入力音声データ
            sample_rate: サンプリングレート
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (ボーカル, BGM)
        """
        logging.warning("モック実装: 実際の分離は行われていません")
        
        # モック処理: 元音声を少し減衰させたものをボーカルとして返す
        # BGMは元音声の高域を減衰させたもの
        
        # ボーカル（元音声の80%）
        vocals = audio_data * 0.8
        
        # BGM（元音声の30%、簡易的なローパスフィルタ）
        # 実際には周波数解析が必要だが、モックなので簡易的に処理
        bgm = audio_data * 0.3
        
        return vocals, bgm
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        使用中のモデル情報を取得
        
        Returns:
            Dict[str, Any]: モデル情報
        """
        model_info = self.AVAILABLE_MODELS.get(self.model_name, {})
        
        return {
            'model_name': self.model_name,
            'device': self.device,
            'description': model_info.get('description', ''),
            'quality': model_info.get('quality', ''),
            'speed': model_info.get('speed', ''),
            'is_initialized': self._is_initialized
        }
    
    @classmethod
    def list_available_models(cls) -> Dict[str, Dict[str, str]]:
        """
        利用可能なモデル一覧を取得
        
        Returns:
            Dict[str, Dict[str, str]]: モデル情報辞書
        """
        return cls.AVAILABLE_MODELS.copy()
    
    def estimate_processing_time(self, audio_duration: float) -> float:
        """
        処理時間を推定
        
        Args:
            audio_duration: 音声の長さ（秒）
            
        Returns:
            float: 推定処理時間（秒）
        """
        # モデルごとの処理速度係数（実測値に基づいて調整が必要）
        speed_factors = {
            'htdemucs': 2.0,      # 音声長の2倍程度
            'htdemucs_ft': 3.5,   # 音声長の3.5倍程度
            'mdx_extra': 5.0      # 音声長の5倍程度
        }
        
        base_factor = speed_factors.get(self.model_name, 3.0)
        
        # デバイスによる補正
        if self.device == 'cpu':
            device_factor = 2.0  # CPUは2倍遅い
        else:
            device_factor = 1.0  # GPU使用
        
        estimated_time = audio_duration * base_factor * device_factor
        
        return estimated_time