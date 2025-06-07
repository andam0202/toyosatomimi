#!/usr/bin/env python3
"""
話者分離パラメータ調整テスト
異なるパラメータでの話者分離性能比較
"""

import os
import sys
import logging
from pathlib import Path

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

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
            logging.FileHandler('speaker_tuning.log')
        ]
    )


def test_speaker_separation_parameters(vocals_file: str, output_dir: str):
    """
    異なるパラメータで話者分離性能をテスト
    
    Args:
        vocals_file: ボーカル音声ファイル（BGM分離済み）
        output_dir: 出力ディレクトリ
    """
    vocals_path = Path(vocals_file)
    output_path = Path(output_dir)
    
    if not vocals_path.exists():
        raise FileNotFoundError(f"ボーカルファイルが見つかりません: {vocals_path}")
    
    logging.info("=== 話者分離パラメータ調整テスト開始 ===")
    
    FileUtils.ensure_directory(output_path)
    
    # 音声情報表示
    audio_info = AudioUtils.get_audio_info(vocals_path)
    logging.info(f"音声情報: {audio_info}")
    
    # テストパラメータ設定
    test_cases = [
        {
            'name': '標準設定',
            'min_duration': 1.0,
            'clustering_threshold': 0.7,
            'max_speakers': None
        },
        {
            'name': '細かい分離',
            'min_duration': 0.5,
            'clustering_threshold': 0.5,
            'max_speakers': None
        },
        {
            'name': '粗い分離',
            'min_duration': 2.0,
            'clustering_threshold': 0.9,
            'max_speakers': 3
        },
        {
            'name': '2話者限定',
            'min_duration': 1.0,
            'clustering_threshold': 0.6,
            'max_speakers': 2
        },
        {
            'name': '高品質設定',
            'min_duration': 0.8,
            'clustering_threshold': 0.65,
            'max_speakers': 4
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        logging.info(f"\n=== テストケース {i+1}: {test_case['name']} ===")
        
        # テスト用ディレクトリ作成
        test_output_dir = output_path / f"test_{i+1:02d}_{test_case['name'].replace(' ', '_')}"
        FileUtils.ensure_directory(test_output_dir)
        
        try:
            # 話者分離プロセッサ初期化
            processor = SpeakerProcessor(
                model_name='pyannote/speaker-diarization-3.1',
                device='auto'
            )
            
            # パラメータでの話者分離実行
            segments = processor.diarize(
                audio_path=str(vocals_path),
                min_duration=test_case['min_duration'],
                max_speakers=test_case['max_speakers'],
                clustering_threshold=test_case['clustering_threshold']
            )
            
            # 話者分析
            analysis = processor.analyze_speakers(segments)
            
            # 音声抽出
            extracted_files = processor.extract_speaker_audio(
                audio_path=str(vocals_path),
                segments=segments,
                output_dir=str(test_output_dir),
                create_individual=False,  # 結合ファイルのみ
                create_combined=True
            )
            
            # 結果記録
            result = {
                'test_case': test_case,
                'num_speakers': analysis['num_speakers'],
                'num_segments': analysis['num_segments'],
                'total_duration': analysis['total_duration'],
                'speakers': analysis['speakers'],
                'extracted_files': extracted_files
            }
            results.append(result)
            
            # 結果表示
            logging.info(f"検出話者数: {analysis['num_speakers']}")
            logging.info(f"セグメント数: {analysis['num_segments']}")
            logging.info(f"総発話時間: {analysis['total_duration']:.2f}秒")
            
            for speaker_id, stats in analysis['speakers'].items():
                logging.info(f"  話者{speaker_id}: "
                           f"{stats['segments']}セグメント, "
                           f"{stats['total_duration']:.2f}秒, "
                           f"信頼度{stats['avg_confidence']:.2f}")
            
        except Exception as e:
            logging.error(f"テストケース {i+1} でエラー: {e}")
            result = {
                'test_case': test_case,
                'error': str(e)
            }
            results.append(result)
    
    # 結果比較
    logging.info("\n=== 結果比較 ===")
    
    successful_results = [r for r in results if 'error' not in r]
    
    if successful_results:
        # 話者数の比較
        logging.info("話者数比較:")
        for result in successful_results:
            name = result['test_case']['name']
            num_speakers = result['num_speakers']
            num_segments = result['num_segments']
            logging.info(f"  {name}: {num_speakers}話者, {num_segments}セグメント")
        
        # 推奨設定の提案
        recommend_best_settings(successful_results)
    
    return results


def recommend_best_settings(results):
    """最適設定の推奨"""
    logging.info("\n=== 推奨設定 ===")
    
    # 話者数が2-4の適切な範囲のものを評価
    good_results = [r for r in results if 2 <= r['num_speakers'] <= 4]
    
    if good_results:
        # セグメント密度（話者数/セグメント数）で評価
        for result in good_results:
            density = result['num_segments'] / result['num_speakers'] if result['num_speakers'] > 0 else 0
            result['segment_density'] = density
        
        # セグメント密度が適切（3-10）なものを優先
        optimal_results = [r for r in good_results if 3 <= r['segment_density'] <= 10]
        
        if optimal_results:
            best = max(optimal_results, key=lambda x: x['total_duration'])
            logging.info(f"推奨設定: {best['test_case']['name']}")
            logging.info(f"  パラメータ: {best['test_case']}")
            logging.info(f"  結果: {best['num_speakers']}話者, {best['num_segments']}セグメント")
        else:
            logging.info("最適な設定が見つかりませんでした。音声の性質に応じて手動調整が必要です。")
    else:
        logging.info("適切な話者数の結果が得られませんでした。音声品質や内容を確認してください。")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="話者分離パラメータ調整テスト")
    parser.add_argument("vocals_file", help="ボーカル音声ファイル（BGM分離済み）")
    parser.add_argument("output_dir", nargs='?', default="tests/outputs/latest", help="出力ディレクトリ（デフォルト: tests/outputs/latest）")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細ログ出力")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_logging()
    
    try:
        results = test_speaker_separation_parameters(args.vocals_file, args.output_dir)
        
        print("\n🎯 話者分離パラメータテスト完了!")
        print(f"結果は {args.output_dir} に保存されました")
        
        return 0
        
    except Exception as e:
        logging.error(f"テストでエラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())