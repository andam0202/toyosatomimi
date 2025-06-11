#!/usr/bin/env python3
"""
話者分離パラメータ調整テストスクリプト

このスクリプトは話者分離のパラメータを調整してテストするためのものです。
GUIで使用する前にパラメータの効果を確認できます。

使用方法:
  cd tests
  uv run python test_speaker_params.py <音声ファイル> <出力ディレクトリ> [パラメータ...]
"""

import sys
import logging
from pathlib import Path

# プロジェクトルートとsrcパッケージパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.audio_separator.processors.speaker_processor import SpeakerProcessor
from src.audio_separator.utils.audio_utils import AudioUtils

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_speaker_separation_with_params(
    audio_path: str,
    output_dir: str,
    clustering_threshold: float = 0.3,  # より細かく分離
    segmentation_onset: float = 0.2,    # より敏感に検出
    segmentation_offset: float = 0.2,   # より敏感に検出
    force_num_speakers: int = 2         # 強制的に2人に分離
):
    """
    パラメータを指定した話者分離テスト
    
    Args:
        audio_path: 入力音声ファイルパス（プロジェクトルートからの相対パス）
        output_dir: 出力ディレクトリ（testsディレクトリからの相対パス）
        clustering_threshold: クラスタリング閾値（0.1-0.9、低いほど細かく分離）
        segmentation_onset: セグメンテーション開始感度（0.1-0.9、低いほど細かく検出）
        segmentation_offset: セグメンテーション終了感度（0.1-0.9、低いほど細かく検出）
        force_num_speakers: 強制話者数（None=自動検出）
    """
    
    # パスをプロジェクトルートからの絶対パスに変換
    project_root = Path(__file__).parent.parent
    
    # 入力ファイルパス処理
    audio_file_path = Path(audio_path)
    if not audio_file_path.is_absolute():
        # testsディレクトリから相対パスの場合、プロジェクトルートから解決
        audio_file_path = project_root / audio_path
    
    # パスを正規化
    audio_file_path = audio_file_path.resolve()
    
    # ファイルが見つからない場合、プロジェクトルートからの相対パスとして再試行
    if not audio_file_path.exists() and not Path(audio_path).is_absolute():
        audio_file_path = project_root / Path(audio_path).name
        if not audio_file_path.exists():
            # data/input/ ディレクトリも検索
            audio_file_path = project_root / "data" / "input" / Path(audio_path).name
            if not audio_file_path.exists():
                # 元のパスから再検索
                possible_paths = [
                    project_root / audio_path,
                    project_root / Path(audio_path).relative_to(Path(audio_path).parts[0]) if len(Path(audio_path).parts) > 1 else project_root / audio_path
                ]
                for possible_path in possible_paths:
                    if possible_path.exists():
                        audio_file_path = possible_path
                        break
    
    # 出力ディレクトリパス処理  
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = Path(__file__).parent / output_dir
    
    print("🎵 パラメータ調整テスト開始")
    print(f"📁 入力ファイル: {audio_file_path}")
    print(f"📁 出力ディレクトリ: {output_path}")
    print(f"🔧 パラメータ:")
    print(f"   - クラスタリング閾値: {clustering_threshold}")
    print(f"   - セグメンテーション感度: onset={segmentation_onset}, offset={segmentation_offset}")
    print(f"   - 強制話者数: {force_num_speakers}人")
    print()
    
    # 入力ファイル存在確認
    if not audio_file_path.exists():
        print(f"❌ エラー: 入力ファイルが見つかりません: {audio_file_path}")
        return None
    
    try:
        # 話者分離プロセッサ初期化
        processor = SpeakerProcessor()
        
        # パラメータを指定して話者分離実行
        segments = processor.diarize(
            audio_path=str(audio_file_path),
            min_duration=0.5,
            clustering_threshold=clustering_threshold,
            segmentation_onset=segmentation_onset,
            segmentation_offset=segmentation_offset,
            force_num_speakers=force_num_speakers
        )
        
        print("✅ 話者分離完了")
        print(f"検出セグメント数: {len(segments)}")
        
        # 話者分析
        speakers = {}
        for segment in segments:
            if segment.speaker_id not in speakers:
                speakers[segment.speaker_id] = []
            speakers[segment.speaker_id].append(segment)
        
        print(f"検出話者数: {len(speakers)}人")
        print()
        
        for speaker_id, speaker_segments in speakers.items():
            total_duration = sum(seg.duration for seg in speaker_segments)
            print(f"話者{speaker_id}:")
            print(f"  - セグメント数: {len(speaker_segments)}")
            print(f"  - 合計時間: {total_duration:.2f}秒")
            print(f"  - 平均信頼度: {sum(seg.confidence for seg in speaker_segments) / len(speaker_segments):.2f}")
        
        print()
        
        # 音声抽出
        output_path.mkdir(parents=True, exist_ok=True)
        
        processor.extract_speaker_audio(
            audio_path=str(audio_file_path),
            segments=segments,
            output_dir=str(output_path),
            naming_style="detailed"  # 新しい詳細命名規則を使用
        )
        
        print("✅ 音声抽出完了")
        print(f"出力先: {output_path}")
        
        return segments
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン処理"""
    setup_logging()
    
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  uv run python test_speaker_params.py <音声ファイル> <出力ディレクトリ> [クラスタリング閾値] [onset] [offset] [話者数]")
        print()
        print("例:")
        print("  uv run python test_speaker_params.py ../data/input/input_gakumas.wav outputs/param_test 0.3 0.2 0.2 2")
        print("  uv run python test_speaker_params.py ../data/input/input_wav.wav outputs/param_test_standard")
        print()
        print("パラメータ説明:")
        print("  - クラスタリング閾値: 0.1-0.9 (低いほど細かく分離、デフォルト: 0.3)")
        print("  - onset/offset: 0.1-0.9 (低いほど細かく検出、デフォルト: 0.2)")
        print("  - 話者数: 強制的に分離する話者数 (デフォルト: 2)")
        print()
        print("注意:")
        print("  - 音声ファイルはプロジェクトルートからの相対パスまたは絶対パス")
        print("  - 出力ディレクトリはtestsディレクトリからの相対パスまたは絶対パス")
        return 1
    
    audio_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    # パラメータを引数から取得（デフォルト値あり）
    clustering_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
    segmentation_onset = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
    segmentation_offset = float(sys.argv[5]) if len(sys.argv) > 5 else 0.2
    force_num_speakers = int(sys.argv[6]) if len(sys.argv) > 6 else 2
    
    # テスト実行
    segments = test_speaker_separation_with_params(
        audio_path=audio_path,
        output_dir=output_dir,
        clustering_threshold=clustering_threshold,
        segmentation_onset=segmentation_onset,
        segmentation_offset=segmentation_offset,
        force_num_speakers=force_num_speakers
    )
    
    if segments:
        print("🎉 テスト完了！")
        print()
        print("📋 次に試すパラメータの提案:")
        print("  - より細かく分離したい場合: clustering_threshold=0.2")
        print("  - より少ない分離にしたい場合: clustering_threshold=0.5-0.7")
        print("  - より多くのセグメントを検出したい場合: onset=0.1, offset=0.1")
        print("  - セグメント数を減らしたい場合: onset=0.4, offset=0.4")
        return 0
    else:
        print("❌ テスト失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main())