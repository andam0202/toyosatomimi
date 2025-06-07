"""
pyannote-audio話者分離プロセッサ

pyannote-audioモデルを使用して話者の識別・分離を行う処理を提供
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from ..utils.audio_utils import AudioUtils
from ..utils.file_utils import FileUtils


class SpeakerSegment:
    """話者セグメント情報を表すクラス"""
    
    def __init__(self, start_time: float, end_time: float, speaker_id: str, confidence: float = 1.0):
        """
        話者セグメント初期化
        
        Args:
            start_time: 開始時間（秒）
            end_time: 終了時間（秒）
            speaker_id: 話者ID
            confidence: 信頼度（0.0-1.0）
        """
        self.start_time = start_time
        self.end_time = end_time
        self.speaker_id = speaker_id
        self.confidence = confidence
    
    @property
    def duration(self) -> float:
        """セグメントの長さ（秒）"""
        return self.end_time - self.start_time
    
    def __repr__(self) -> str:
        return f"SpeakerSegment(speaker={self.speaker_id}, {self.start_time:.2f}-{self.end_time:.2f}s, conf={self.confidence:.2f})"


class SpeakerProcessor:
    """pyannote-audio話者分離プロセッサクラス"""
    
    # 利用可能なモデル
    AVAILABLE_MODELS = {
        'pyannote/speaker-diarization-3.1': {
            'description': 'pyannote-audio v3.1 話者分離モデル',
            'language_support': 'multilingual',
            'quality': 'high',
            'speed': 'medium'
        },
        'pyannote/speaker-diarization': {
            'description': 'pyannote-audio 標準話者分離モデル',
            'language_support': 'multilingual', 
            'quality': 'standard',
            'speed': 'fast'
        }
    }
    
    def __init__(
        self,
        model_name: str = 'pyannote/speaker-diarization-3.1',
        device: str = 'auto',
        use_auth_token: bool = True
    ):
        """
        話者分離プロセッサを初期化
        
        Args:
            model_name: 使用するpyannoteモデル名
            device: 処理デバイス ('auto', 'cpu', 'cuda')
            use_auth_token: Hugging Face認証トークンを使用するか
        """
        self.model_name = model_name
        self.device = device
        self.use_auth_token = use_auth_token
        self.pipeline = None
        self._is_initialized = False
        
        # モデル名の検証
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"サポートされていないモデル: {model_name}")
        
        logging.info(f"話者分離プロセッサ初期化: モデル={model_name}, デバイス={device}")
    
    def _initialize_pipeline(self) -> None:
        """
        pyannote-audioパイプラインを初期化（遅延初期化）
        
        Note: 現在はモックバージョン。実際のpyannote-audio実装時に置き換える
        """
        if self._is_initialized:
            return
        
        try:
            # TODO: 実際のpyannote-audio初期化
            # from pyannote.audio import Pipeline
            # self.pipeline = Pipeline.from_pretrained(
            #     self.model_name,
            #     use_auth_token=self.use_auth_token
            # )
            
            # モックバージョン
            logging.warning("モックバージョン: 実際のpyannote-audioモデルは未実装")
            self.pipeline = f"mock_{self.model_name}"
            self._is_initialized = True
            
            logging.info(f"話者分離パイプライン初期化完了: {self.model_name}")
            
        except Exception as e:
            raise RuntimeError(f"話者分離パイプラインの初期化に失敗: {e}")
    
    def diarize(
        self,
        audio_path: str,
        min_duration: float = 1.0,
        max_speakers: Optional[int] = None
    ) -> List[SpeakerSegment]:
        """
        音声ファイルの話者分離を実行
        
        Args:
            audio_path: 音声ファイルパス
            min_duration: 最小セグメント長（秒）
            max_speakers: 最大話者数（Noneの場合は自動検出）
            
        Returns:
            List[SpeakerSegment]: 話者セグメントのリスト
            
        Raises:
            FileNotFoundError: 音声ファイルが見つからない場合
            RuntimeError: 話者分離処理に失敗した場合
        """
        audio_path = Path(audio_path)
        
        # 入力ファイルの検証
        if not AudioUtils.validate_audio_file(audio_path):
            raise FileNotFoundError(f"有効な音声ファイルが見つかりません: {audio_path}")
        
        logging.info(f"話者分離開始: {audio_path}")
        logging.info(f"モデル: {self.model_name}")
        logging.info(f"最小セグメント長: {min_duration}秒")
        
        try:
            # パイプライン初期化
            self._initialize_pipeline()
            
            # 音声情報取得
            audio_info = AudioUtils.get_audio_info(audio_path)
            duration = audio_info['duration']
            
            logging.info(f"音声長: {duration:.2f}秒")
            
            # 話者分離実行（現在はモック）
            segments = self._diarize_mock(audio_path, duration, min_duration, max_speakers)
            
            # 結果のフィルタリング
            filtered_segments = [
                seg for seg in segments 
                if seg.duration >= min_duration
            ]
            
            logging.info(f"話者分離完了: {len(filtered_segments)}個のセグメント検出")
            
            # 話者統計
            speakers = list(set(seg.speaker_id for seg in filtered_segments))
            for speaker in speakers:
                speaker_segments = [seg for seg in filtered_segments if seg.speaker_id == speaker]
                total_duration = sum(seg.duration for seg in speaker_segments)
                logging.info(f"話者{speaker}: {len(speaker_segments)}セグメント, 合計{total_duration:.2f}秒")
            
            return filtered_segments
            
        except Exception as e:
            logging.error(f"話者分離処理でエラー: {e}")
            raise RuntimeError(f"話者分離に失敗: {e}")
    
    def _diarize_mock(
        self,
        audio_path: Path,
        duration: float,
        min_duration: float,
        max_speakers: Optional[int]
    ) -> List[SpeakerSegment]:
        """
        話者分離のモック実装
        
        実際のpyannote-audio実装までの暫定処理
        
        Args:
            audio_path: 音声ファイルパス
            duration: 音声の長さ
            min_duration: 最小セグメント長
            max_speakers: 最大話者数
            
        Returns:
            List[SpeakerSegment]: モック話者セグメント
        """
        logging.warning("モック実装: 実際の話者分離は行われていません")
        
        # モック処理: 音声を時間で分割して複数話者に割り当て
        segments = []
        
        # 話者数を決定（最大3人、音声長に応じて調整）
        if max_speakers is not None:
            num_speakers = min(max_speakers, 3)
        else:
            num_speakers = min(int(duration / 30) + 1, 3)  # 30秒ごとに1人追加、最大3人
        
        speaker_ids = [f"SPEAKER_{i:02d}" for i in range(num_speakers)]
        
        # 時間を話者で分割（簡易的な実装）
        segment_length = 5.0  # 5秒ずつのセグメント
        current_time = 0.0
        speaker_index = 0
        
        while current_time < duration:
            end_time = min(current_time + segment_length, duration)
            
            # セグメント長が最小長以上の場合のみ追加
            if (end_time - current_time) >= min_duration:
                segment = SpeakerSegment(
                    start_time=current_time,
                    end_time=end_time,
                    speaker_id=speaker_ids[speaker_index],
                    confidence=0.8 + np.random.random() * 0.2  # 0.8-1.0の信頼度
                )
                segments.append(segment)
            
            current_time = end_time
            speaker_index = (speaker_index + 1) % num_speakers
        
        return segments
    
    def extract_speaker_audio(
        self,
        audio_path: str,
        segments: List[SpeakerSegment],
        output_dir: str,
        create_individual: bool = True,
        create_combined: bool = True
    ) -> Dict[str, List[str]]:
        """
        話者セグメントから音声ファイルを抽出
        
        Args:
            audio_path: 元音声ファイルパス
            segments: 話者セグメントリスト
            output_dir: 出力ディレクトリ
            create_individual: 個別セグメントファイルを作成するか
            create_combined: 結合ファイルを作成するか
            
        Returns:
            Dict[str, List[str]]: 話者IDごとの出力ファイルパスリスト
            
        Raises:
            FileNotFoundError: 音声ファイルが見つからない場合
            RuntimeError: 音声抽出処理に失敗した場合
        """
        audio_path = Path(audio_path)
        output_dir = Path(output_dir)
        
        # 入力ファイルの検証
        if not AudioUtils.validate_audio_file(audio_path):
            raise FileNotFoundError(f"有効な音声ファイルが見つかりません: {audio_path}")
        
        logging.info(f"話者音声抽出開始: {audio_path}")
        logging.info(f"出力ディレクトリ: {output_dir}")
        
        try:
            # 音声データ読み込み
            audio_data, sample_rate = AudioUtils.load_audio(audio_path)
            
            # 話者ごとにグループ化
            speaker_segments = {}
            for segment in segments:
                if segment.speaker_id not in speaker_segments:
                    speaker_segments[segment.speaker_id] = []
                speaker_segments[segment.speaker_id].append(segment)
            
            output_files = {}
            
            for speaker_id, speaker_segs in speaker_segments.items():
                logging.info(f"話者{speaker_id}の音声抽出: {len(speaker_segs)}セグメント")
                
                # 話者ディレクトリ作成
                speaker_dir = output_dir / f"speaker_{speaker_id}"
                FileUtils.ensure_directory(speaker_dir)
                
                output_files[speaker_id] = []
                extracted_segments = []
                
                # 個別セグメントファイル作成
                if create_individual:
                    for i, segment in enumerate(speaker_segs):
                        # 音声データを時間で切り出し
                        segment_audio = AudioUtils.split_audio_by_time(
                            audio_data, sample_rate,
                            segment.start_time, segment.end_time
                        )
                        
                        if len(segment_audio) > 0:
                            # フェード処理適用
                            segment_audio = AudioUtils.apply_fade(segment_audio, sample_rate)
                            
                            # ファイル保存
                            segment_file = speaker_dir / f"segment_{i+1:03d}.wav"
                            AudioUtils.save_audio(segment_audio, segment_file, sample_rate)
                            output_files[speaker_id].append(str(segment_file))
                            extracted_segments.append(segment_audio)
                
                # 結合ファイル作成
                if create_combined and extracted_segments:
                    combined_audio = AudioUtils.concatenate_audio(extracted_segments)
                    combined_audio = AudioUtils.normalize_audio(combined_audio)
                    
                    combined_file = speaker_dir / f"speaker_{speaker_id}_combined.wav"
                    AudioUtils.save_audio(combined_audio, combined_file, sample_rate)
                    output_files[speaker_id].append(str(combined_file))
                
                total_duration = sum(seg.duration for seg in speaker_segs)
                logging.info(f"話者{speaker_id}抽出完了: 合計{total_duration:.2f}秒")
            
            logging.info(f"全話者音声抽出完了: {len(speaker_segments)}人")
            return output_files
            
        except Exception as e:
            logging.error(f"話者音声抽出でエラー: {e}")
            raise RuntimeError(f"話者音声抽出に失敗: {e}")
    
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
            'use_auth_token': self.use_auth_token,
            'description': model_info.get('description', ''),
            'language_support': model_info.get('language_support', ''),
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
        # モデルごとの処理速度係数
        speed_factors = {
            'pyannote/speaker-diarization-3.1': 1.5,  # 音声長の1.5倍程度
            'pyannote/speaker-diarization': 1.2,      # 音声長の1.2倍程度
        }
        
        base_factor = speed_factors.get(self.model_name, 1.5)
        
        # デバイスによる補正
        if self.device == 'cpu':
            device_factor = 3.0  # CPUは3倍遅い
        else:
            device_factor = 1.0  # GPU使用
        
        estimated_time = audio_duration * base_factor * device_factor
        
        return estimated_time
    
    def analyze_speakers(self, segments: List[SpeakerSegment]) -> Dict[str, Any]:
        """
        話者分析結果を取得
        
        Args:
            segments: 話者セグメントリスト
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        if not segments:
            return {
                'num_speakers': 0,
                'total_duration': 0.0,
                'speakers': {}
            }
        
        # 話者ごとの統計
        speaker_stats = {}
        for segment in segments:
            if segment.speaker_id not in speaker_stats:
                speaker_stats[segment.speaker_id] = {
                    'segments': 0,
                    'total_duration': 0.0,
                    'avg_confidence': 0.0,
                    'min_confidence': 1.0,
                    'max_confidence': 0.0
                }
            
            stats = speaker_stats[segment.speaker_id]
            stats['segments'] += 1
            stats['total_duration'] += segment.duration
            stats['avg_confidence'] += segment.confidence
            stats['min_confidence'] = min(stats['min_confidence'], segment.confidence)
            stats['max_confidence'] = max(stats['max_confidence'], segment.confidence)
        
        # 平均信頼度計算
        for speaker_id, stats in speaker_stats.items():
            stats['avg_confidence'] /= stats['segments']
        
        total_duration = sum(seg.duration for seg in segments)
        
        return {
            'num_speakers': len(speaker_stats),
            'total_duration': total_duration,
            'num_segments': len(segments),
            'speakers': speaker_stats
        }