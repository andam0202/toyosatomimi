"""
Demucs BGM分離プロセッサ

Demucsモデルを使用してBGMとボーカルを分離する処理を提供
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, Callable
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
        """
        if self._is_initialized:
            return
        
        try:
            # 実際のDemucsを試行、失敗時はシンプル分離にフォールバック
            try:
                import demucs
                logging.info(f"Demucs v{demucs.__version__} 検出")
                self.model = f"demucs_{self.model_name}"
                self._demucs_available = True
            except Exception as demucs_error:
                logging.warning(f"Demucs利用不可: {demucs_error}")
                logging.info("シンプルBGM分離にフォールバック")
                self.model = f"simple_{self.model_name}"
                self._demucs_available = False
            
            self._is_initialized = True
            logging.info(f"BGM分離モデル初期化完了: {self.model}")
            
        except Exception as e:
            raise RuntimeError(f"BGM分離モデルの初期化に失敗: {e}")
    
    def separate(
        self,
        input_path: str,
        output_dir: str,
        vocals_name: str = 'vocals.wav',
        bgm_name: str = 'bgm.wav',
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Tuple[str, str]:
        """
        BGMとボーカルを分離する
        
        Args:
            input_path: 入力音声ファイルパス
            output_dir: 出力ディレクトリ
            vocals_name: ボーカル出力ファイル名
            bgm_name: BGM出力ファイル名
            progress_callback: 進捗コールバック関数 (進捗率, メッセージ)
            
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
            # 進捗報告
            if progress_callback:
                progress_callback(0.1, "モデル初期化中...")
            
            # モデル初期化
            self._initialize_model()
            
            # 進捗報告
            if progress_callback:
                progress_callback(0.3, "音声ファイル読み込み中...")
            
            # 音声ファイル読み込み
            audio_data, sample_rate = AudioUtils.load_audio(input_path)
            
            # 進捗報告
            if progress_callback:
                progress_callback(0.5, "BGM分離処理中...")
            
            # BGM分離処理
            if hasattr(self, '_demucs_available') and self._demucs_available:
                vocals, bgm = self._separate_audio_demucs(audio_data, sample_rate)
            else:
                vocals, bgm = self._separate_audio_simple(audio_data, sample_rate)
            
            # 進捗報告
            if progress_callback:
                progress_callback(0.8, "音声ファイル保存中...")
            
            # 結果を保存
            AudioUtils.save_audio(vocals, vocals_path, sample_rate)
            AudioUtils.save_audio(bgm, bgm_path, sample_rate)
            
            # 進捗報告
            if progress_callback:
                progress_callback(1.0, "BGM分離完了")
            
            logging.info(f"BGM分離完了")
            logging.info(f"ボーカル: {vocals_path}")
            logging.info(f"BGM: {bgm_path}")
            
            return str(vocals_path), str(bgm_path)
            
        except Exception as e:
            logging.error(f"BGM分離処理でエラー: {e}")
            raise RuntimeError(f"BGM分離に失敗: {e}")
    
    def _separate_audio_demucs(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Demucsを使用した音声分離
        
        Args:
            audio_data: 入力音声データ
            sample_rate: サンプリングレート
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (ボーカル, BGM)
        """
        logging.info("実際のDemucsによる音声分離実行中...")
        
        try:
            import torch
            from demucs import pretrained
            
            # モデル読み込み
            if not hasattr(self, '_demucs_model') or self._demucs_model is None:
                logging.info(f"Demucsモデル '{self.model_name}' を読み込み中...")
                self._demucs_model = pretrained.get_model(self.model_name)
                
                # デバイス設定（設定に基づく）
                if self.device == 'cuda':
                    # GPU強制使用
                    if torch.cuda.is_available():
                        device = 'cuda'
                        logging.info("GPU使用を強制しています")
                    else:
                        logging.warning("GPU強制指定されましたが、CUDAが利用できません。CPUで実行します")
                        device = 'cpu'
                elif self.device == 'cpu':
                    # CPU強制使用
                    device = 'cpu'
                    logging.info("CPU使用を強制しています")
                else:
                    # auto: GPU優先、フォールバックCPU
                    device = 'cuda' if torch.cuda.is_available() else 'cpu'
                    logging.info(f"自動デバイス選択: {device}")
                
                self._demucs_model = self._demucs_model.to(device)
                self._demucs_model.eval()
                
                logging.info(f"Demucsモデル読み込み完了 (デバイス: {device})")
            
            # 音声データをPyTorchテンソルに変換
            # audio_dataがモノラルの場合はステレオに変換
            if len(audio_data.shape) == 1:
                # モノラル -> ステレオ
                stereo_audio = np.stack([audio_data, audio_data])
            else:
                stereo_audio = audio_data
            
            # [channels, samples] -> [1, channels, samples] (バッチ次元追加)
            audio_tensor = torch.from_numpy(stereo_audio).float().unsqueeze(0)
            
            # テンソルを同じデバイスに移動
            device = next(self._demucs_model.parameters()).device
            audio_tensor = audio_tensor.to(device)
            
            logging.info(f"入力テンソル形状: {audio_tensor.shape}, デバイス: {device}")
            
            # Demucsで分離実行
            with torch.no_grad():
                from demucs.apply import apply_model
                separated = apply_model(self._demucs_model, audio_tensor)
            
            logging.info(f"分離結果テンソル形状: {separated.shape}")
            
            # separated shape: [1, 4, channels, samples]
            # 4つのソース: drums, bass, other, vocals
            separated = separated.squeeze(0)  # バッチ次元を削除
            
            # ボーカル（インデックス3）とその他を分離
            vocals_tensor = separated[3]  # vocals
            
            # BGM = drums + bass + other
            bgm_tensor = separated[0] + separated[1] + separated[2]  # drums + bass + other
            
            # テンソルをCPUに移動してからnumpy配列に変換してモノラルに
            vocals = vocals_tensor.mean(dim=0).cpu().numpy()  # ステレオ -> モノラル
            bgm = bgm_tensor.mean(dim=0).cpu().numpy()  # ステレオ -> モノラル
            
            logging.info("実際のDemucs分離完了")
            return vocals, bgm
            
        except Exception as e:
            logging.error(f"Demucs分離でエラー: {e}")
            logging.info("シンプル分離にフォールバック")
            return self._separate_audio_simple(audio_data, sample_rate)
    
    def _separate_audio_simple(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        シンプルな音声分離実装
        
        Args:
            audio_data: 入力音声データ
            sample_rate: サンプリングレート
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (ボーカル, BGM)
        """
        logging.info("シンプル分離法による音声分離実行中...")
        
        # ステレオの場合はセンター抜き法でボーカル抽出
        if len(audio_data.shape) > 1:
            # ステレオ音声の場合
            left = audio_data[0] if audio_data.shape[0] == 2 else audio_data
            right = audio_data[1] if audio_data.shape[0] == 2 else audio_data
            
            # センター抜き法：L-Rでセンター成分（ボーカル）を強調
            vocals = (left - right) * 2.0
            
            # BGM：L+Rでサイド成分を取得し、ローパスフィルタ適用
            center = (left + right) / 2
            bgm = self._apply_lowpass_filter(center, sample_rate, cutoff_freq=4000)
        else:
            # モノラル音声の場合は周波数フィルタのみ
            # ハイパスフィルタでボーカル域を強調
            vocals = self._apply_highpass_filter(audio_data, sample_rate, cutoff_freq=200)
            
            # ローパスフィルタでBGM域を強調
            bgm = self._apply_lowpass_filter(audio_data, sample_rate, cutoff_freq=4000) * 0.7
        
        # 正規化
        vocals = AudioUtils.normalize_audio(vocals, 0.8)
        bgm = AudioUtils.normalize_audio(bgm, 0.8)
        
        return vocals, bgm
    
    def _apply_lowpass_filter(self, audio: np.ndarray, sample_rate: int, cutoff_freq: int = 4000) -> np.ndarray:
        """ローパスフィルタ適用"""
        try:
            from scipy import signal
            nyquist = sample_rate / 2
            normalized_cutoff = cutoff_freq / nyquist
            b, a = signal.butter(4, normalized_cutoff, btype='low')
            return signal.filtfilt(b, a, audio)
        except ImportError:
            # scipyがない場合は単純な減衰
            return audio * 0.7
    
    def _apply_highpass_filter(self, audio: np.ndarray, sample_rate: int, cutoff_freq: int = 200) -> np.ndarray:
        """ハイパスフィルタ適用"""
        try:
            from scipy import signal
            nyquist = sample_rate / 2
            normalized_cutoff = cutoff_freq / nyquist
            b, a = signal.butter(4, normalized_cutoff, btype='high')
            return signal.filtfilt(b, a, audio)
        except ImportError:
            # scipyがない場合は元音声をそのまま返す
            return audio
    
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