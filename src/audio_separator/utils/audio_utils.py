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
            
            # 形状チェック：ステレオの場合は転置
            if len(audio_data.shape) == 2 and audio_data.shape[0] == 2:
                # [2, samples] -> [samples, 2] for soundfile
                audio_data = audio_data.T
            
            # soundfileで保存（拡張子から自動形式判定）
            sf.write(str(output_path), audio_data, sample_rate)
            
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
    def light_enhance_for_diarization(audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        BGM分離済み音声用の軽微な前処理
        
        Args:
            audio_data: 音声データ (モノラル)
            sample_rate: サンプリングレート
            
        Returns:
            np.ndarray: 軽微に処理された音声データ
        """
        try:
            # BGM分離済み音声なので軽微な処理のみ
            processed_audio = audio_data.copy()
            
            # 1. 軽微なノイズゲーティング（閾値を低く設定）
            rms = np.sqrt(np.mean(processed_audio**2))
            noise_gate_threshold = rms * 0.05  # 非常に低い閾値
            processed_audio[np.abs(processed_audio) < noise_gate_threshold] *= 0.5
            
            # 2. 軽微な正規化（ダイナミックレンジ保持）
            max_val = np.max(np.abs(processed_audio))
            if max_val > 0:
                target_level = 0.7  # 控えめな正規化
                processed_audio = processed_audio * (target_level / max_val)
            
            return processed_audio
            
        except Exception as e:
            logging.warning(f"軽微な前処理でエラー: {e}")
            return audio_data
    
    @staticmethod
    def enhance_speech_for_diarization(audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        話者分離用の音声品質向上処理
        
        Args:
            audio_data: 音声データ
            sample_rate: サンプリングレート
            
        Returns:
            np.ndarray: 処理済み音声データ
        """
        try:
            # ステレオからモノラルに変換（必要に応じて）
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=0)
            
            # ノイズ除去（改良版）
            enhanced = AudioUtils._advanced_noise_reduction(audio_data, sample_rate)
            
            # 音声帯域の強調（話者識別に重要な周波数帯域）
            enhanced = AudioUtils._enhance_speaker_features(enhanced, sample_rate)
            
            # 動的レンジ圧縮（話者の声質差を明確化）
            enhanced = AudioUtils._dynamic_range_compression(enhanced)
            
            # 正規化（クリッピング防止）
            enhanced = AudioUtils.normalize_audio(enhanced, 0.85)
            
            return enhanced
            
        except Exception as e:
            logging.warning(f"音声前処理エラー: {e}")
            # エラー時は正規化のみ
            return AudioUtils.normalize_audio(audio_data, 0.8)
    
    @staticmethod
    def _simple_noise_reduction(audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """簡易ノイズ除去"""
        try:
            from scipy import signal
            # 高域ノイズを軽減するローパスフィルタ
            nyquist = sample_rate / 2
            cutoff = 8000  # 8kHz以上をカット
            if cutoff < nyquist:
                normalized_cutoff = cutoff / nyquist
                b, a = signal.butter(4, normalized_cutoff, btype='low')
                return signal.filtfilt(b, a, audio)
            return audio
        except ImportError:
            return audio
    
    @staticmethod
    def _enhance_speech_band(audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """音声帯域強調"""
        try:
            from scipy import signal
            nyquist = sample_rate / 2
            # 音声帯域（300Hz-4000Hz）を強調
            low_cutoff = 300 / nyquist
            high_cutoff = 4000 / nyquist
            if low_cutoff < 1.0 and high_cutoff < 1.0:
                b, a = signal.butter(4, [low_cutoff, high_cutoff], btype='band')
                enhanced = signal.filtfilt(b, a, audio)
                # 元音声とミックス（7:3）
                return 0.7 * audio + 0.3 * enhanced
            return audio
        except ImportError:
            return audio
    
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
    
    @staticmethod
    def _advanced_noise_reduction(audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """改良版ノイズ除去"""
        try:
            import scipy.signal as signal
            
            # スペクトル減算による高度なノイズ除去
            # 短時間フーリエ変換
            nperseg = min(2048, len(audio) // 8)
            f, t, Zxx = signal.stft(audio, sample_rate, nperseg=nperseg)
            
            # ノイズレベル推定（最初の0.5秒から）
            noise_frames = int(0.5 * sample_rate / (nperseg // 4))
            noise_spectrum = np.mean(np.abs(Zxx[:, :noise_frames]), axis=1, keepdims=True)
            
            # スペクトル減算
            magnitude = np.abs(Zxx)
            phase = np.angle(Zxx)
            
            # ノイズ減算（保守的に）
            enhanced_magnitude = magnitude - 0.5 * noise_spectrum
            enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
            
            # 逆変換
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            _, enhanced = signal.istft(enhanced_stft, sample_rate, nperseg=nperseg)
            
            return enhanced[:len(audio)]
            
        except Exception:
            # エラー時は簡易ハイパスフィルタ
            return AudioUtils._simple_noise_reduction(audio, sample_rate)
    
    @staticmethod
    def _enhance_speaker_features(audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """話者特徴の強調"""
        try:
            import scipy.signal as signal
            
            # 話者識別に重要な周波数帯域を強調
            # 基本周波数帯域（80-300Hz）を軽く強調
            sos_low = signal.butter(4, [80, 300], btype='band', fs=sample_rate, output='sos')
            low_enhanced = signal.sosfilt(sos_low, audio) * 0.3
            
            # 音声認識に重要な帯域（300-3400Hz）を強調
            sos_mid = signal.butter(4, [300, 3400], btype='band', fs=sample_rate, output='sos')
            mid_enhanced = signal.sosfilt(sos_mid, audio) * 1.2
            
            # 高周波成分（3400-8000Hz）を適度に強調
            sos_high = signal.butter(4, [3400, 8000], btype='band', fs=sample_rate, output='sos')
            high_enhanced = signal.sosfilt(sos_high, audio) * 0.8
            
            # 合成
            enhanced = audio + low_enhanced + mid_enhanced + high_enhanced
            
            return enhanced
            
        except Exception:
            # エラー時は元の音声を返す
            return audio
    
    @staticmethod
    def _dynamic_range_compression(audio: np.ndarray) -> np.ndarray:
        """動的レンジ圧縮（話者の声質差を明確化）"""
        try:
            # 簡易コンプレッサー
            threshold = 0.3
            ratio = 4.0
            
            # 絶対値で処理
            abs_audio = np.abs(audio)
            sign = np.sign(audio)
            
            # 閾値を超える部分を圧縮
            mask = abs_audio > threshold
            compressed = abs_audio.copy()
            compressed[mask] = threshold + (abs_audio[mask] - threshold) / ratio
            
            # 符号を復元
            result = compressed * sign
            
            # 小音量部分の増幅（話者の細かい特徴を強調）
            quiet_mask = abs_audio < 0.1
            result[quiet_mask] *= 1.5
            
            return result
            
        except Exception:
            return audio