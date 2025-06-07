"""
音声処理ユーティリティ関数

音声ファイルの読み込み、保存、変換などの基本的な音声処理機能を提供
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Union, List
import numpy as np
import librosa
import soundfile as sf


class AudioUtils:
    """音声処理ユーティリティクラス"""
    
    # サポートされている音声形式
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg'}
    
    # デフォルトのサンプリングレート
    DEFAULT_SAMPLE_RATE = 44100
    
    @staticmethod
    def load_audio(
        file_path: Union[str, Path], 
        sample_rate: Optional[int] = None,
        mono: bool = True
    ) -> Tuple[np.ndarray, int]:
        """
        音声ファイルを読み込む
        
        Args:
            file_path: 音声ファイルのパス
            sample_rate: 目標サンプリングレート（Noneの場合は元のレートを維持）
            mono: モノラルに変換するかどうか
            
        Returns:
            Tuple[np.ndarray, int]: (音声データ, サンプリングレート)
            
        Raises:
            FileNotFoundError: ファイルが見つからない場合
            ValueError: サポートされていない形式の場合
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"音声ファイルが見つかりません: {file_path}")
            
        if file_path.suffix.lower() not in AudioUtils.SUPPORTED_FORMATS:
            raise ValueError(f"サポートされていない音声形式: {file_path.suffix}")
        
        try:
            # librosaで音声を読み込み
            audio_data, sr = librosa.load(
                str(file_path),
                sr=sample_rate,
                mono=mono
            )
            
            logging.info(f"音声ファイル読み込み完了: {file_path}")
            logging.info(f"サンプリングレート: {sr}Hz, 長さ: {len(audio_data)/sr:.2f}秒")
            
            return audio_data, sr
            
        except Exception as e:
            raise ValueError(f"音声ファイルの読み込みに失敗: {e}")
    
    @staticmethod
    def save_audio(
        audio_data: np.ndarray,
        output_path: Union[str, Path],
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        format: str = 'wav'
    ) -> None:
        """
        音声データをファイルに保存する
        
        Args:
            audio_data: 音声データ
            output_path: 出力ファイルパス
            sample_rate: サンプリングレート
            format: 出力形式
            
        Raises:
            ValueError: 無効なデータまたは形式の場合
        """
        output_path = Path(output_path)
        
        # 出力ディレクトリを作成
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 音声データの正規化（クリッピング防止）
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # soundfileで保存
            sf.write(str(output_path), audio_data, sample_rate, format=format)
            
            logging.info(f"音声ファイル保存完了: {output_path}")
            
        except Exception as e:
            raise ValueError(f"音声ファイルの保存に失敗: {e}")
    
    @staticmethod
    def get_audio_info(file_path: Union[str, Path]) -> dict:
        """
        音声ファイルの情報を取得する
        
        Args:
            file_path: 音声ファイルのパス
            
        Returns:
            dict: 音声ファイルの情報
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"音声ファイルが見つかりません: {file_path}")
        
        try:
            # ファイル情報を取得（メタデータのみ）
            info = sf.info(str(file_path))
            
            return {
                'duration': info.duration,
                'sample_rate': info.samplerate,
                'channels': info.channels,
                'format': info.format,
                'subtype': info.subtype,
                'file_size': file_path.stat().st_size,
                'file_path': str(file_path)
            }
            
        except Exception as e:
            raise ValueError(f"音声ファイル情報の取得に失敗: {e}")
    
    @staticmethod
    def normalize_audio(audio_data: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
        """
        音声データを正規化する
        
        Args:
            audio_data: 音声データ
            target_peak: 目標ピーク値
            
        Returns:
            np.ndarray: 正規化された音声データ
        """
        if len(audio_data) == 0:
            return audio_data
        
        # 現在のピーク値を取得
        current_peak = np.max(np.abs(audio_data))
        
        if current_peak == 0:
            return audio_data
        
        # 正規化
        normalized = audio_data * (target_peak / current_peak)
        
        return normalized
    
    @staticmethod
    def split_audio_by_time(
        audio_data: np.ndarray,
        sample_rate: int,
        start_time: float,
        end_time: float
    ) -> np.ndarray:
        """
        時間指定で音声データを切り出す
        
        Args:
            audio_data: 音声データ
            sample_rate: サンプリングレート
            start_time: 開始時間（秒）
            end_time: 終了時間（秒）
            
        Returns:
            np.ndarray: 切り出された音声データ
        """
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)
        
        # 範囲チェック
        start_sample = max(0, start_sample)
        end_sample = min(len(audio_data), end_sample)
        
        if start_sample >= end_sample:
            return np.array([])
        
        return audio_data[start_sample:end_sample]
    
    @staticmethod
    def validate_audio_file(file_path: Union[str, Path]) -> bool:
        """
        音声ファイルの有効性を検証する
        
        Args:
            file_path: 音声ファイルのパス
            
        Returns:
            bool: 有効な音声ファイルかどうか
        """
        try:
            file_path = Path(file_path)
            
            # ファイル存在チェック
            if not file_path.exists():
                return False
            
            # 拡張子チェック
            if file_path.suffix.lower() not in AudioUtils.SUPPORTED_FORMATS:
                return False
            
            # ファイル読み込みテスト
            info = sf.info(str(file_path))
            
            # 基本的な妥当性チェック
            if info.duration <= 0 or info.samplerate <= 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def create_silence(duration: float, sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
        """
        無音の音声データを作成する
        
        Args:
            duration: 長さ（秒）
            sample_rate: サンプリングレート
            
        Returns:
            np.ndarray: 無音の音声データ
        """
        num_samples = int(duration * sample_rate)
        return np.zeros(num_samples, dtype=np.float32)
    
    @staticmethod
    def concatenate_audio(audio_segments: List[np.ndarray]) -> np.ndarray:
        """
        複数の音声データを結合する
        
        Args:
            audio_segments: 音声データのリスト
            
        Returns:
            np.ndarray: 結合された音声データ
        """
        if not audio_segments:
            return np.array([])
        
        # すべてのセグメントを結合
        return np.concatenate(audio_segments)
    
    @staticmethod
    def apply_fade(
        audio_data: np.ndarray,
        sample_rate: int,
        fade_in_duration: float = 0.01,
        fade_out_duration: float = 0.01
    ) -> np.ndarray:
        """
        フェードイン・フェードアウトを適用する
        
        Args:
            audio_data: 音声データ
            sample_rate: サンプリングレート
            fade_in_duration: フェードイン時間（秒）
            fade_out_duration: フェードアウト時間（秒）
            
        Returns:
            np.ndarray: フェード処理された音声データ
        """
        if len(audio_data) == 0:
            return audio_data
        
        audio_copy = audio_data.copy()
        
        # フェードイン
        fade_in_samples = int(fade_in_duration * sample_rate)
        if fade_in_samples > 0 and fade_in_samples < len(audio_copy):
            fade_in_curve = np.linspace(0, 1, fade_in_samples)
            audio_copy[:fade_in_samples] *= fade_in_curve
        
        # フェードアウト
        fade_out_samples = int(fade_out_duration * sample_rate)
        if fade_out_samples > 0 and fade_out_samples < len(audio_copy):
            fade_out_curve = np.linspace(1, 0, fade_out_samples)
            audio_copy[-fade_out_samples:] *= fade_out_curve
        
        return audio_copy