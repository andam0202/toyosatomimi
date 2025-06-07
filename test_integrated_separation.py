#!/usr/bin/env python3
"""
統合音声分離テスト
BGM分離 + 話者分離の完全なパイプライン統合テスト
"""

import os
import sys
import logging
from pathlib import Path

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent / "src"))

from audio_separator.processors.demucs_processor import DemucsProcessor
from audio_separator.processors.speaker_processor import SpeakerProcessor
from audio_separator.utils.audio_utils import AudioUtils
from audio_separator.utils.file_utils import FileUtils


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('integrated_test.log')
        ]
    )


def test_integrated_separation(input_file: str, output_dir: str):
    """
    統合音声分離テスト
    
    Args:
        input_file: 入力音声ファイル
        output_dir: 出力ディレクトリ
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")
    
    logging.info("=== 統合音声分離テスト開始 ===")
    logging.info(f"入力ファイル: {input_path}")
    logging.info(f"出力ディレクトリ: {output_path}")
    
    # 出力ディレクトリ作成
    FileUtils.ensure_directory(output_path)
    
    # 音声情報表示
    audio_info = AudioUtils.get_audio_info(input_path)
    logging.info(f"音声情報: {audio_info}")
    
    # === フェーズ1: BGM分離 ===
    logging.info("\n=== フェーズ1: BGM分離 (Demucs) ===")
    
    bgm_output_dir = output_path / "01_bgm_separation"
    FileUtils.ensure_directory(bgm_output_dir)
    
    demucs = DemucsProcessor(model_name='htdemucs')
    vocals_path, bgm_path = demucs.separate(
        input_path=str(input_path),
        output_dir=str(bgm_output_dir)
    )
    
    logging.info(f"ボーカル分離完了: {vocals_path}")
    logging.info(f"BGM分離完了: {bgm_path}")
    
    # === フェーズ2: 話者分離 ===
    logging.info("\n=== フェーズ2: 話者分離 (pyannote-audio) ===")
    
    speaker_output_dir = output_path / "02_speaker_separation"
    FileUtils.ensure_directory(speaker_output_dir)
    
    # ボーカル音声に対して話者分離実行
    speaker_processor = SpeakerProcessor(
        model_name='pyannote/speaker-diarization-3.1',
        device='auto'
    )
    
    # 話者分離実行
    segments = speaker_processor.diarize(
        audio_path=vocals_path,
        min_duration=2.0,  # 最小2秒のセグメント
        max_speakers=None  # 自動検出
    )
    
    logging.info(f"検出された話者セグメント数: {len(segments)}")
    
    # 話者分析
    analysis = speaker_processor.analyze_speakers(segments)
    logging.info(f"話者分析結果: {analysis}")
    
    # === フェーズ3: 話者音声抽出 ===
    logging.info("\n=== フェーズ3: 話者音声抽出 ===")
    
    extraction_output_dir = speaker_output_dir / "extracted_speakers"
    FileUtils.ensure_directory(extraction_output_dir)
    
    # 各話者の音声を抽出
    extracted_files = speaker_processor.extract_speaker_audio(
        audio_path=vocals_path,
        segments=segments,
        output_dir=str(extraction_output_dir),
        create_individual=True,
        create_combined=True
    )
    
    logging.info(f"抽出された話者ファイル: {extracted_files}")
    
    # === 結果サマリー ===
    logging.info("\n=== 処理結果サマリー ===")
    
    # ファイル構造表示
    display_output_structure(output_path)
    
    # 各話者の統計表示
    for speaker_id, stats in analysis['speakers'].items():
        logging.info(f"話者{speaker_id}: "
                    f"{stats['segments']}セグメント, "
                    f"{stats['total_duration']:.2f}秒, "
                    f"信頼度平均{stats['avg_confidence']:.2f}")
    
    logging.info("=== 統合音声分離テスト完了 ===")
    
    return {
        'bgm_separation': {
            'vocals_path': vocals_path,
            'bgm_path': bgm_path
        },
        'speaker_separation': {
            'segments': segments,
            'analysis': analysis,
            'extracted_files': extracted_files
        }
    }


def display_output_structure(output_dir: Path):
    """出力ディレクトリ構造を表示"""
    logging.info("\n出力ファイル構造:")
    
    def print_tree(path: Path, prefix: str = ""):
        if path.is_file():
            size = path.stat().st_size
            logging.info(f"{prefix}📄 {path.name} ({size:,} bytes)")
        elif path.is_dir():
            logging.info(f"{prefix}📁 {path.name}/")
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                new_prefix = prefix + ("    " if is_last else "│   ")
                item_prefix = prefix + ("└── " if is_last else "├── ")
                logging.info(f"{item_prefix}{item.name}" + 
                           ("/" if item.is_dir() else f" ({item.stat().st_size:,} bytes)"))
                if item.is_dir() and len(list(item.iterdir())) > 0:
                    for sub_item in sorted(item.iterdir(), key=lambda x: (x.is_file(), x.name)):
                        sub_is_file = sub_item.is_file()
                        sub_size = f" ({sub_item.stat().st_size:,} bytes)" if sub_is_file else "/"
                        logging.info(f"{new_prefix}{'└── ' if sub_item == list(item.iterdir())[-1] else '├── '}"
                                   f"{sub_item.name}{sub_size}")
    
    print_tree(output_dir)


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="統合音声分離テスト")
    parser.add_argument("input_file", help="入力音声ファイル")
    parser.add_argument("output_dir", help="出力ディレクトリ")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細ログ出力")
    
    args = parser.parse_args()
    
    # ログ設定
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_logging()
    
    try:
        result = test_integrated_separation(args.input_file, args.output_dir)
        
        print("\n🎉 統合テスト成功!")
        print(f"結果は {args.output_dir} に保存されました")
        
        return 0
        
    except Exception as e:
        logging.error(f"統合テストでエラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())