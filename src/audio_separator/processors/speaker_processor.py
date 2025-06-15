"""
pyannote-audio話者分離プロセッサ

pyannote-audioモデルを使用して話者の識別・分離を行う処理を提供
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Callable
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
    
    def _get_auth_token(self):
        """Hugging Face認証トークンを取得"""
        import os
        
        # 環境変数から取得
        token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
        
        if token:
            logging.info("✅ Hugging Face tokenが環境変数から取得されました")
            return token
        elif self.use_auth_token:
            logging.info("🔑 Hugging Face tokenが設定されていますが、環境変数が見つかりません")
            return True  # huggingface_hubのデフォルトトークン使用を試行
        else:
            logging.warning("❌ Hugging Face tokenが設定されていません")
            return None
    
    def _initialize_pipeline(self) -> None:
        """
        pyannote-audioパイプラインを初期化（遅延初期化）
        """
        if self._is_initialized:
            return
        
        try:
            # 実際のpyannote-audioを試行、失敗時は簡易話者分離にフォールバック
            try:
                from pyannote.audio import Pipeline
                import torch
                
                logging.info(f"pyannote-audioパイプライン '{self.model_name}' を読み込み中...")
                
                # デバイス設定（設定に基づく）
                if self.device == 'cuda':
                    # GPU強制使用
                    if torch.cuda.is_available():
                        device = torch.device('cuda')
                        logging.info("pyannote-audio: GPU使用を強制しています")
                    else:
                        logging.warning("pyannote-audio: GPU強制指定されましたが、CUDAが利用できません。CPUで実行します")
                        device = torch.device('cpu')
                elif self.device == 'cpu':
                    # CPU強制使用
                    device = torch.device('cpu')
                    logging.info("pyannote-audio: CPU使用を強制しています")
                else:
                    # auto: GPU優先、フォールバックCPU
                    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    logging.info(f"pyannote-audio: 自動デバイス選択: {device}")
                
                # Hugging Face token設定の確認・自動設定
                auth_token = self._get_auth_token()
                
                # パイプライン初期化
                self.pipeline = Pipeline.from_pretrained(
                    self.model_name,
                    use_auth_token=auth_token
                )
                
                # パイプラインの詳細パラメータ調整
                # より精密な話者分離のためのパラメータ設定
                if hasattr(self.pipeline, '_segmentation'):
                    # セグメンテーション感度調整（より細かい分離）
                    if hasattr(self.pipeline._segmentation, 'onset'):
                        self.pipeline._segmentation.onset = 0.3  # デフォルト0.5から下げる
                    if hasattr(self.pipeline._segmentation, 'offset'):
                        self.pipeline._segmentation.offset = 0.3  # デフォルト0.5から下げる
                
                if hasattr(self.pipeline, '_clustering'):
                    # クラスタリング閾値調整（話者をより細かく分離）
                    if hasattr(self.pipeline._clustering, 'threshold'):
                        self.pipeline._clustering.threshold = 0.5  # デフォルト0.7から下げる
                
                # 重複発話制御の設定
                if hasattr(self.pipeline, 'instantiate'):
                    # 重複発話検出を無効化（重なりを避ける）
                    try:
                        # pyannote v3.1では重複部分を自動で処理する設定
                        self.pipeline.instantiate({
                            'segmentation': {
                                'min_duration_on': 0.0,
                                'min_duration_off': 0.0
                            },
                            'clustering': {
                                'method': 'centroid',
                                'min_cluster_size': 2,
                                'threshold': 0.5
                            }
                        })
                    except Exception as e:
                        logging.info(f"パイプライン詳細設定をスキップ: {e}")
                
                # 重複発話を避けるための後処理フラグ
                self._remove_overlapping_segments = True
                
                # デバイスに移動
                self.pipeline = self.pipeline.to(device)
                self._device = device
                self._pyannote_available = True
                
                logging.info(f"pyannote-audioパイプライン初期化完了 (デバイス: {device})")
                
            except Exception as pyannote_error:
                logging.warning(f"pyannote-audio利用不可: {pyannote_error}")
                logging.info("簡易話者分離にフォールバック")
                self.pipeline = f"simple_{self.model_name}"
                self._pyannote_available = False
            
            self._is_initialized = True
            
        except Exception as e:
            raise RuntimeError(f"話者分離パイプラインの初期化に失敗: {e}")
    
    def _initialize_pipeline_with_params(
        self, 
        clustering_threshold: float,
        segmentation_onset: float,
        segmentation_offset: float
    ) -> None:
        """
        パラメータを動的に設定してパイプラインを初期化
        """
        # 基本初期化
        self._initialize_pipeline()
        
        if hasattr(self, '_pyannote_available') and self._pyannote_available:
            try:
                # パラメータを動的に更新
                if hasattr(self.pipeline, '_segmentation'):
                    if hasattr(self.pipeline._segmentation, 'onset'):
                        self.pipeline._segmentation.onset = segmentation_onset
                    if hasattr(self.pipeline._segmentation, 'offset'):
                        self.pipeline._segmentation.offset = segmentation_offset
                
                if hasattr(self.pipeline, '_clustering'):
                    if hasattr(self.pipeline._clustering, 'threshold'):
                        self.pipeline._clustering.threshold = clustering_threshold
                
                logging.info(f"パイプラインパラメータ更新完了: clustering={clustering_threshold}, onset={segmentation_onset}, offset={segmentation_offset}")
                
            except Exception as e:
                logging.warning(f"パラメータ設定エラー: {e}")
    
    def diarize(
        self,
        audio_path: str,
        min_duration: float = 0.5,  # より短いセグメントも検出
        max_speakers: Optional[int] = None,
        clustering_threshold: float = 0.5,  # より細かく分離
        segmentation_onset: float = 0.3,  # セグメンテーション開始感度
        segmentation_offset: float = 0.3,  # セグメンテーション終了感度
        force_num_speakers: Optional[int] = None  # 強制的に指定した話者数に分離
    ) -> List[SpeakerSegment]:
        """
        音声ファイルの話者分離を実行
        
        Args:
            audio_path: 音声ファイルパス
            min_duration: 最小セグメント長（秒）
            max_speakers: 最大話者数（Noneの場合は自動検出）
            clustering_threshold: クラスタリング閾値（0.1-1.0、低いほど細かく分離）
            segmentation_onset: セグメンテーション開始感度（0.1-0.9、低いほど細かく検出）
            segmentation_offset: セグメンテーション終了感度（0.1-0.9、低いほど細かく検出）
            force_num_speakers: 強制的に指定した話者数に分離（Noneの場合は自動検出）
            
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
            # パイプライン初期化（パラメータ更新）
            self._initialize_pipeline_with_params(clustering_threshold, segmentation_onset, segmentation_offset)
            
            # 音声情報取得
            audio_info = AudioUtils.get_audio_info(audio_path)
            duration = audio_info['duration']
            
            logging.info(f"音声長: {duration:.2f}秒")
            logging.info(f"クラスタリング閾値: {clustering_threshold}")
            logging.info(f"セグメンテーション感度: onset={segmentation_onset}, offset={segmentation_offset}")
            if force_num_speakers:
                logging.info(f"強制話者数: {force_num_speakers}人")
            
            # BGM分離後音声の品質を確認
            audio_info = AudioUtils.get_audio_info(audio_path)
            logging.info(f"話者分離入力音声品質: {audio_info}")
            
            # BGM分離後の音声に最適化された前処理を適用
            if hasattr(self, '_pyannote_available') and self._pyannote_available:
                logging.info("BGM分離済み音声用の軽微な前処理実行中...")
                
                # 元音声を読み込み
                audio_data, sample_rate = AudioUtils.load_audio(audio_path)
                
                # BGM分離後音声用の軽微な処理（ノイズ除去のみ）
                enhanced_audio = AudioUtils.light_enhance_for_diarization(audio_data, sample_rate)
                
                # 一時ファイルに保存
                temp_enhanced_path = audio_path.parent / f"temp_light_enhanced_{audio_path.name}"
                AudioUtils.save_audio(enhanced_audio, temp_enhanced_path, sample_rate)
                
                # 処理後の音声パスを更新
                audio_path_for_processing = temp_enhanced_path
                logging.info("軽微な前処理完了")
            else:
                audio_path_for_processing = audio_path
            
            # 話者分離実行
            if hasattr(self, '_pyannote_available') and self._pyannote_available:
                segments = self._diarize_pyannote(audio_path_for_processing, duration, min_duration, max_speakers, clustering_threshold, force_num_speakers)
                
                # 一時ファイル削除
                if audio_path_for_processing != audio_path:
                    try:
                        audio_path_for_processing.unlink()
                        logging.info("一時ファイル削除完了")
                    except Exception:
                        pass
            else:
                segments = self._diarize_simple(audio_path, duration, min_duration, max_speakers, force_num_speakers)
            
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
    
    def _diarize_pyannote(
        self,
        audio_path: Path,
        duration: float,
        min_duration: float,
        max_speakers: Optional[int],
        clustering_threshold: float = 0.7,
        force_num_speakers: Optional[int] = None
    ) -> List[SpeakerSegment]:
        """
        pyannote-audioを使用した実際の話者分離
        
        Args:
            audio_path: 音声ファイルパス
            duration: 音声の長さ
            min_duration: 最小セグメント長
            max_speakers: 最大話者数
            
        Returns:
            List[SpeakerSegment]: 話者セグメント
        """
        logging.info("実際のpyannote-audioによる話者分離実行中...")
        
        try:
            # PyTorchのWarningを一時的に抑制
            import warnings
            warnings.filterwarnings("ignore", message="std(): degrees of freedom is <= 0")
            # pyannote-audioパイプライン実行
            # v3.1では直接パラメータを渡すことができないため、標準実行
            diarization = self.pipeline(str(audio_path))
            
            # 結果をSpeakerSegmentに変換
            segments = []
            for turn, track, speaker in diarization.itertracks(yield_label=True):
                # セグメント長チェック
                segment_duration = turn.end - turn.start
                if segment_duration >= min_duration:
                    segment = SpeakerSegment(
                        start_time=turn.start,
                        end_time=turn.end,
                        speaker_id=speaker,
                        confidence=1.0  # pyannoteは信頼度を直接提供しないため1.0とする
                    )
                    segments.append(segment)
            
            # 話者数制限処理（強制話者数を優先）
            target_speakers = force_num_speakers if force_num_speakers is not None else max_speakers
            
            if target_speakers is not None:
                unique_speakers = len(set(seg.speaker_id for seg in segments))
                if force_num_speakers is not None:
                    logging.info(f"検出された話者数: {unique_speakers}人, 強制話者数: {force_num_speakers}人")
                else:
                    logging.info(f"検出された話者数: {unique_speakers}人, 最大話者数: {max_speakers}人")
                
                if unique_speakers > target_speakers:
                    # 検出された話者数が多い場合、上位N人に制限
                    if force_num_speakers is not None:
                        logging.info(f"話者数を{unique_speakers}人から{force_num_speakers}人に制限します")
                    else:
                        logging.info(f"話者数を{unique_speakers}人から{max_speakers}人に制限します")
                    
                    # 話者ごとの総発話時間を計算
                    speaker_durations = {}
                    for segment in segments:
                        if segment.speaker_id not in speaker_durations:
                            speaker_durations[segment.speaker_id] = 0.0
                        speaker_durations[segment.speaker_id] += segment.duration
                    
                    # 発話時間の長い順にソート
                    top_speakers = sorted(
                        speaker_durations.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:target_speakers]
                    
                    top_speaker_ids = [speaker_id for speaker_id, _ in top_speakers]
                    
                    # 上位話者のセグメントのみを保持
                    segments = [seg for seg in segments if seg.speaker_id in top_speaker_ids]
                    
                    if force_num_speakers is not None:
                        logging.info(f"強制話者数制限適用完了: {len(top_speaker_ids)}人の話者を保持")
                    else:
                        logging.info(f"最大話者数制限適用完了: {len(top_speaker_ids)}人の話者を保持")
                
                elif force_num_speakers is not None and unique_speakers == 1 and force_num_speakers > 1:
                    # 1つの話者しか検出されなかった場合の分割処理
                    logging.info(f"話者数が{unique_speakers}人のため、{force_num_speakers}人に強制分割します")
                    segments = self._force_split_speakers(segments, force_num_speakers)
            
            # 重複セグメント除去処理
            if hasattr(self, '_remove_overlapping_segments') and self._remove_overlapping_segments:
                segments = self._remove_overlapping_speech(segments)
            
            logging.info(f"実際のpyannote-audio分離完了: {len(segments)}セグメント")
            return segments
            
        except Exception as e:
            logging.error(f"pyannote-audio分離でエラー: {e}")
            logging.info("簡易分離にフォールバック")
            return self._diarize_simple(audio_path, duration, min_duration, max_speakers, force_num_speakers)
    
    def _diarize_simple(
        self,
        audio_path: Path,
        duration: float,
        min_duration: float,
        max_speakers: Optional[int],
        force_num_speakers: Optional[int] = None
    ) -> List[SpeakerSegment]:
        """
        簡易話者分離実装
        
        Args:
            audio_path: 音声ファイルパス
            duration: 音声の長さ
            min_duration: 最小セグメント長
            max_speakers: 最大話者数
            
        Returns:
            List[SpeakerSegment]: 簡易話者セグメント
        """
        logging.info("簡易話者分離実行中...")
        
        # 音声を読み込んで振幅ベースで話者変化点を推定
        try:
            audio_data, sample_rate = AudioUtils.load_audio(audio_path)
            
            # 振幅ベースのセグメンテーション
            segments = self._segment_by_amplitude(audio_data, sample_rate, duration, min_duration)
            
            # 話者ID割り当て（簡易的）
            target_speakers = force_num_speakers if force_num_speakers is not None else max_speakers
            segments = self._assign_speaker_ids(segments, target_speakers)
            
            # 強制話者数処理（簡易分離版）
            if force_num_speakers is not None:
                unique_speakers = len(set(seg.speaker_id for seg in segments))
                logging.info(f"簡易分離: 検出された話者数: {unique_speakers}人, 強制話者数: {force_num_speakers}人")
                
                if unique_speakers > force_num_speakers:
                    # 発話時間の長い上位N人に制限
                    logging.info(f"簡易分離: 話者数を{unique_speakers}人から{force_num_speakers}人に制限します")
                    
                    # 話者ごとの総発話時間を計算
                    speaker_durations = {}
                    for segment in segments:
                        if segment.speaker_id not in speaker_durations:
                            speaker_durations[segment.speaker_id] = 0.0
                        speaker_durations[segment.speaker_id] += segment.duration
                    
                    # 発話時間の長い順にソート
                    top_speakers = sorted(
                        speaker_durations.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:force_num_speakers]
                    
                    top_speaker_ids = [speaker_id for speaker_id, _ in top_speakers]
                    
                    # 上位話者のセグメントのみを保持
                    segments = [seg for seg in segments if seg.speaker_id in top_speaker_ids]
                    
                    logging.info(f"簡易分離: 強制話者数制限適用完了: {len(top_speaker_ids)}人の話者を保持")
            
            logging.info(f"簡易話者分離完了: {len(segments)}セグメント")
            return segments
            
        except Exception as e:
            logging.warning(f"簡易分離でもエラー: {e}")
            # 最後の手段：時間ベース分割
            return self._diarize_time_based(duration, min_duration, max_speakers)
    
    def _segment_by_amplitude(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        duration: float,
        min_duration: float
    ) -> List[SpeakerSegment]:
        """
        振幅ベースでの音声セグメンテーション
        """
        # 1秒ごとのRMS計算
        frame_length = sample_rate  # 1秒
        hop_length = frame_length // 2  # 0.5秒ずつスライド
        
        rms_values = []
        for i in range(0, len(audio_data) - frame_length, hop_length):
            frame = audio_data[i:i + frame_length]
            rms = np.sqrt(np.mean(frame ** 2))
            rms_values.append(rms)
        
        # 閾値以上の部分を音声区間とする
        threshold = np.percentile(rms_values, 30)  # 下位30%を無音として除外
        
        segments = []
        in_speech = False
        start_time = 0.0
        
        for i, rms in enumerate(rms_values):
            current_time = i * hop_length / sample_rate
            
            if rms > threshold and not in_speech:
                # 音声開始
                start_time = current_time
                in_speech = True
            elif rms <= threshold and in_speech:
                # 音声終了
                end_time = current_time
                if (end_time - start_time) >= min_duration:
                    segments.append(SpeakerSegment(
                        start_time=start_time,
                        end_time=end_time,
                        speaker_id="TEMP",  # 後で割り当て
                        confidence=0.7
                    ))
                in_speech = False
        
        # 最後のセグメント処理
        if in_speech and (duration - start_time) >= min_duration:
            segments.append(SpeakerSegment(
                start_time=start_time,
                end_time=duration,
                speaker_id="TEMP",
                confidence=0.7
            ))
        
        return segments
    
    def _assign_speaker_ids(
        self,
        segments: List[SpeakerSegment],
        max_speakers: Optional[int]
    ) -> List[SpeakerSegment]:
        """
        セグメントに話者IDを割り当て（簡易的な実装）
        """
        if not segments:
            return segments
        
        # 話者数を決定
        if max_speakers is not None:
            num_speakers = min(max_speakers, 3)
        else:
            num_speakers = min(len(segments) // 2 + 1, 3)
        
        speaker_ids = [f"SPEAKER_{i:02d}" for i in range(num_speakers)]
        
        # セグメントの長さに基づいて話者を循環的に割り当て
        for i, segment in enumerate(segments):
            speaker_index = i % num_speakers
            segment.speaker_id = speaker_ids[speaker_index]
        
        return segments
    
    def _diarize_time_based(
        self,
        duration: float,
        min_duration: float,
        max_speakers: Optional[int]
    ) -> List[SpeakerSegment]:
        """
        時間ベースの分割（最後の手段）
        """
        logging.info("時間ベース分割による話者分離")
        
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
                    confidence=0.6  # 時間ベースは信頼度低め
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
        create_combined: bool = True,
        naming_style: str = "detailed"  # "simple" or "detailed"
    ) -> Dict[str, List[str]]:
        """
        話者セグメントから音声ファイルを抽出
        
        Args:
            audio_path: 元音声ファイルパス
            segments: 話者セグメントリスト
            output_dir: 出力ディレクトリ
            create_individual: 個別セグメントファイルを作成するか
            create_combined: 結合ファイルを作成するか
            naming_style: ファイル命名スタイル ("simple": segment_001.wav, "detailed": filename_speaker01_seg001_0m15s-0m23s.wav)
            
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
            
            # 元ファイル名のベース名を取得
            base_name = audio_path.stem  # 拡張子なしのファイル名
            
            # 話者ごとにグループ化
            speaker_segments = {}
            for segment in segments:
                if segment.speaker_id not in speaker_segments:
                    speaker_segments[segment.speaker_id] = []
                speaker_segments[segment.speaker_id].append(segment)
            
            output_files = {}
            
            for speaker_id, speaker_segs in speaker_segments.items():
                logging.info(f"話者{speaker_id}の音声抽出: {len(speaker_segs)}セグメント")
                
                # 話者ディレクトリ作成（naming_styleに応じて）
                if naming_style == "detailed":
                    speaker_num = speaker_id.replace("SPEAKER_", "")
                    try:
                        speaker_num = f"{int(speaker_num)+1:02d}"
                    except ValueError:
                        speaker_num = "01"
                    speaker_dir = output_dir / f"speaker_{speaker_num}_{base_name}"
                else:
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
                            
                            # ファイル名生成
                            filename = self._generate_filename(
                                base_name=base_name,
                                speaker_id=speaker_id,
                                naming_style=naming_style,
                                segment_idx=i+1,
                                start_time=segment.start_time,
                                end_time=segment.end_time
                            )
                            
                            # ファイル保存
                            segment_file = speaker_dir / filename
                            AudioUtils.save_audio(segment_audio, segment_file, sample_rate)
                            output_files[speaker_id].append(str(segment_file))
                            extracted_segments.append(segment_audio)
                
                # 結合ファイル作成
                if create_combined and extracted_segments:
                    combined_audio = AudioUtils.concatenate_audio(extracted_segments)
                    combined_audio = AudioUtils.normalize_audio(combined_audio)
                    
                    # 結合ファイル名生成
                    combined_filename = self._generate_filename(
                        base_name=base_name,
                        speaker_id=speaker_id,
                        naming_style=naming_style
                    )
                    
                    combined_file = speaker_dir / combined_filename
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
    
    def _remove_overlapping_speech(self, segments: List[SpeakerSegment]) -> List[SpeakerSegment]:
        """
        重複する話者セグメントを除去または調整する
        
        Args:
            segments: 話者セグメントのリスト
            
        Returns:
            List[SpeakerSegment]: 重複を除去したセグメントリスト
        """
        if not segments:
            return segments
        
        # 時間順にソート
        sorted_segments = sorted(segments, key=lambda x: x.start_time)
        filtered_segments = []
        
        overlap_threshold = 0.1  # 0.1秒以上の重複は除去対象
        removed_overlaps = 0
        
        for current_seg in sorted_segments:
            # 既存セグメントとの重複チェック
            overlapping = False
            
            for existing_seg in filtered_segments:
                # 重複判定
                overlap_start = max(current_seg.start_time, existing_seg.start_time)
                overlap_end = min(current_seg.end_time, existing_seg.end_time)
                overlap_duration = max(0, overlap_end - overlap_start)
                
                # 重複時間が閾値を超える場合
                if overlap_duration > overlap_threshold:
                    # より長いセグメントを優先、同じ長さなら既存を優先
                    current_duration = current_seg.duration
                    existing_duration = existing_seg.duration
                    
                    if current_duration > existing_duration:
                        # 現在のセグメントの方が長い場合、既存を削除
                        filtered_segments.remove(existing_seg)
                        logging.debug(f"重複セグメント除去: {existing_seg.speaker_id} {existing_seg.start_time:.2f}-{existing_seg.end_time:.2f}s（より短い）")
                        removed_overlaps += 1
                        break
                    else:
                        # 既存のセグメントを優先、現在のセグメントを除外
                        overlapping = True
                        logging.debug(f"重複セグメント除去: {current_seg.speaker_id} {current_seg.start_time:.2f}-{current_seg.end_time:.2f}s（重複）")
                        removed_overlaps += 1
                        break
            
            # 重複していない場合のみ追加
            if not overlapping:
                filtered_segments.append(current_seg)
        
        if removed_overlaps > 0:
            logging.info(f"重複セグメント除去完了: {removed_overlaps}個のセグメントを除去")
        
        # 再度時間順にソート
        return sorted(filtered_segments, key=lambda x: x.start_time)
    
    def _force_split_speakers(self, segments: List[SpeakerSegment], target_num_speakers: int) -> List[SpeakerSegment]:
        """
        1つの話者として検出されたセグメントを強制的に複数話者に分割
        
        Args:
            segments: 話者セグメントのリスト
            target_num_speakers: 目標話者数
            
        Returns:
            List[SpeakerSegment]: 分割されたセグメントリスト
        """
        if not segments or target_num_speakers <= 1:
            return segments
        
        # セグメントを時間順にソート
        sorted_segments = sorted(segments, key=lambda x: x.start_time)
        
        # セグメントを均等に分割してそれぞれに異なる話者IDを割り当て
        total_segments = len(sorted_segments)
        segments_per_speaker = total_segments // target_num_speakers
        remainder = total_segments % target_num_speakers
        
        result_segments = []
        current_index = 0
        
        for speaker_idx in range(target_num_speakers):
            # この話者が担当するセグメント数
            current_count = segments_per_speaker + (1 if speaker_idx < remainder else 0)
            
            # 新しい話者IDを生成
            new_speaker_id = f"SPEAKER_{speaker_idx:02d}"
            
            # セグメントに新しい話者IDを割り当て
            for i in range(current_count):
                if current_index < total_segments:
                    original_seg = sorted_segments[current_index]
                    new_segment = SpeakerSegment(
                        start_time=original_seg.start_time,
                        end_time=original_seg.end_time,
                        speaker_id=new_speaker_id,
                        confidence=original_seg.confidence
                    )
                    result_segments.append(new_segment)
                    current_index += 1
            
            logging.info(f"強制分割: {new_speaker_id} に {current_count}セグメントを割り当て")
        
        return result_segments
    
    def _format_time_for_filename(self, seconds: float) -> str:
        """
        秒数をファイル名用の時間文字列に変換
        
        Args:
            seconds: 秒数
            
        Returns:
            str: "1m23s" 形式の時間文字列
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m{secs:02d}s"
    
    def separate_speakers(
        self,
        input_file: Path,
        output_dir: Path,
        min_segment_length: float = 1.0,
        max_segment_length: float = 30.0,
        overlap_ratio: float = 0.1,
        create_combined: bool = True,
        create_individual: bool = True,
        naming_style: str = "detailed",
        progress_callback: Optional[Callable[[float], None]] = None,
        **kwargs  # 追加パラメータを受け取る
    ) -> Dict[str, Any]:
        """
        話者分離処理を実行（GUI用の統合メソッド）
        
        Args:
            input_file: 入力音声ファイルのパス
            output_dir: 出力ディレクトリ
            min_segment_length: 最小セグメント長（秒）
            max_segment_length: 最大セグメント長（秒）
            overlap_ratio: オーバーラップ比率
            create_combined: 結合ファイルを作成するか
            create_individual: 個別セグメントファイルを作成するか
            naming_style: ファイル命名スタイル
            progress_callback: 進捗コールバック関数
            
        Returns:
            Dict[str, Any]: 処理結果情報
        """
        try:
            # 進捗通知
            if progress_callback:
                progress_callback(0.0)
            
            # GUIパラメータを抽出（存在する場合のみ使用）
            clustering_threshold = kwargs.get('clustering_threshold', 0.5)
            segmentation_onset = kwargs.get('segmentation_onset', 0.3)
            segmentation_offset = kwargs.get('segmentation_offset', 0.3)
            force_num_speakers = kwargs.get('force_num_speakers', None)
            
            # デバッグログ：受け取ったパラメータを確認
            logging.info(f"SpeakerProcessor受け取りパラメータ:")
            logging.info(f"  force_num_speakers: {force_num_speakers} (型: {type(force_num_speakers)})")
            logging.info(f"  kwargs全体: {kwargs}")
            
            # 話者分離実行
            segments = self.diarize(
                audio_path=str(input_file),
                min_duration=min_segment_length,
                max_speakers=None,  # デフォルトは自動検出
                clustering_threshold=clustering_threshold,
                segmentation_onset=segmentation_onset,
                segmentation_offset=segmentation_offset,
                force_num_speakers=force_num_speakers
            )
            
            # 進捗通知
            if progress_callback:
                progress_callback(50.0)
            
            # 音声抽出
            output_files = self.extract_speaker_audio(
                audio_path=str(input_file),
                segments=segments,
                output_dir=str(output_dir),
                create_individual=create_individual,
                create_combined=create_combined,
                naming_style=naming_style
            )
            
            # 進捗通知
            if progress_callback:
                progress_callback(100.0)
            
            # 処理結果を作成
            result = {
                'output_files': output_files,
                'segments_detected': len(segments),
                'speakers_detected': len(output_files),
                'total_duration': sum(seg.duration for seg in segments)
            }
            
            logging.info(f"話者分離処理完了: {len(output_files)}人の話者、{len(segments)}セグメント")
            return result
            
        except Exception as e:
            logging.error(f"話者分離処理エラー: {e}")
            raise

    def _generate_filename(
        self, 
        base_name: str, 
        speaker_id: str, 
        naming_style: str,
        segment_idx: Optional[int] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """
        ファイル名を生成
        
        Args:
            base_name: 元ファイルのベース名（拡張子なし）
            speaker_id: 話者ID
            naming_style: 命名スタイル ("simple" or "detailed")
            segment_idx: セグメント番号
            start_time: 開始時間（秒）
            end_time: 終了時間（秒）
            
        Returns:
            str: 生成されたファイル名
        """
        if naming_style == "simple":
            if segment_idx is not None:
                return f"segment_{segment_idx:03d}.wav"
            else:
                return f"speaker_{speaker_id}_combined.wav"
        
        elif naming_style == "detailed":
            # 話者IDを数値に変換（SPEAKER_00 -> 01）
            speaker_num = speaker_id.replace("SPEAKER_", "")
            try:
                speaker_num = f"{int(speaker_num)+1:02d}"
            except ValueError:
                speaker_num = "01"
            
            if segment_idx is not None:
                # セグメント個別ファイル
                start_str = self._format_time_for_filename(start_time)
                end_str = self._format_time_for_filename(end_time)
                return f"{base_name}_speaker{speaker_num}_seg{segment_idx:03d}_{start_str}-{end_str}.wav"
            else:
                # 統合ファイル
                return f"{base_name}_speaker{speaker_num}_combined.wav"
        
        else:
            # デフォルトはsimple
            return self._generate_filename(base_name, speaker_id, "simple", segment_idx, start_time, end_time)