#!/usr/bin/env python3
"""
実際の音声ファイルを使用した音声分離テストスクリプト

使用方法:
    python test_real_audio.py <音声ファイルパス> [出力ディレクトリ]

例:
    python test_real_audio.py /path/to/youtube_audio.wav
    python test_real_audio.py /path/to/youtube_audio.wav ./output
"""

import sys
import os
from pathlib import Path
import argparse
import logging

# プロジェクトルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audio_separator.processors import DemucsProcessor, SpeakerProcessor
from src.audio_separator.utils import AudioUtils, FileUtils, ConfigManager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_audio_separation(input_file: str, output_dir: str = None):
    """
    実際の音声ファイルで音声分離をテスト
    
    Args:
        input_file: 入力音声ファイルパス
        output_dir: 出力ディレクトリ（指定しない場合は入力ファイルと同じ場所）
    """
    input_path = Path(input_file)
    
    # 入力ファイルの検証
    if not input_path.exists():
        print(f"❌ エラー: 入力ファイルが見つかりません: {input_path}")
        return False
    
    if not AudioUtils.validate_audio_file(input_path):
        print(f"❌ エラー: 有効な音声ファイルではありません: {input_path}")
        return False
    
    # 出力ディレクトリの設定
    output_dir = Path(output_dir)
    
    print(f"🎵 音声分離テスト開始")
    print(f"📁 入力ファイル: {input_path}")
    print(f"📁 出力ディレクトリ: {output_dir}")
    print("\n📋 処理フロー:")
    print("  1️⃣ BGM分離: 混合音声 → ボーカル + BGM")
    print("  2️⃣ 話者分離: ボーカル音声 → 各話者の発話セグメント検出")
    print("  3️⃣ 音声抽出: セグメント → 話者別音声ファイル")
    print("=" * 60)
    
    try:
        # 音声ファイル情報表示
        print("📊 音声ファイル情報:")
        audio_info = AudioUtils.get_audio_info(input_path)
        for key, value in audio_info.items():
            if key == 'file_size':
                print(f"  {key}: {FileUtils.format_file_size(value)}")
            elif key == 'duration':
                print(f"  {key}: {value:.2f}秒")
            elif key == 'file_path':
                print(f"  {key}: {Path(value).name}")
            else:
                print(f"  {key}: {value}")
        
        duration = audio_info['duration']
        
        # ステップ1: BGM分離
        print(f"\n🎼 ステップ1: BGM分離")
        print(f"使用モデル: htdemucs")
        
        demucs = DemucsProcessor('htdemucs')
        bgm_dir = output_dir / "bgm_separated"
        
        # 処理時間推定
        estimated_bgm_time = demucs.estimate_processing_time(duration)
        print(f"推定処理時間: {estimated_bgm_time:.1f}秒")
        
        vocals_path, bgm_path = demucs.separate(
            str(input_path),
            str(bgm_dir),
            'vocals.wav',
            'bgm.wav'
        )
        
        print(f"✅ BGM分離完了:")
        print(f"  ボーカル: {vocals_path}")
        print(f"  BGM: {bgm_path}")
        
        # ファイルサイズ確認
        vocals_size = FileUtils.get_file_size(vocals_path)
        bgm_size = FileUtils.get_file_size(bgm_path)
        print(f"  ボーカルサイズ: {FileUtils.format_file_size(vocals_size)}")
        print(f"  BGMサイズ: {FileUtils.format_file_size(bgm_size)}")
        
        # ステップ2: 話者分離（BGM除去済みボーカル音声で実行）
        print(f"\n👥 ステップ2: 話者分離（BGM除去済み音声で実行）")
        print(f"使用モデル: pyannote/speaker-diarization-3.1")
        print(f"入力: BGM除去済みボーカル音声 ({Path(vocals_path).name})")
        
        # ボーカル音声の情報確認
        vocals_info = AudioUtils.get_audio_info(vocals_path)
        print(f"ボーカル音声情報:")
        print(f"  長さ: {vocals_info['duration']:.2f}秒")
        print(f"  サイズ: {FileUtils.format_file_size(vocals_info['file_size'])}")
        
        speaker = SpeakerProcessor()
        
        # 設定値取得
        config_file = Path(__file__).parent / "config" / "test_config.json"
        if config_file.exists():
            config = ConfigManager(config_file)
            print(f"📋 設定ファイル使用: {config_file.name}")
        else:
            config = ConfigManager()
            print(f"📋 デフォルト設定使用")
            
        min_duration = config.get('speaker_separation.min_duration', 1.0)
        max_speakers = config.get('speaker_separation.max_speakers', None)
        print(f"最小セグメント長: {min_duration}秒")
        if max_speakers:
            print(f"最大話者数: {max_speakers}人")
        else:
            print(f"最大話者数: 自動検出")
        
        # 処理時間推定（ボーカル音声の長さで計算）
        estimated_speaker_time = speaker.estimate_processing_time(vocals_info['duration'])
        print(f"推定処理時間: {estimated_speaker_time:.1f}秒")
        
        print(f"⚡ BGM除去済みボーカル音声で話者分離を実行中...")
        segments = speaker.diarize(
            vocals_path,  # BGM除去済みのボーカル音声を使用
            min_duration=min_duration,
            max_speakers=max_speakers  # 設定から取得
        )
        
        print(f"✅ 話者分離完了: {len(segments)}セグメント検出")
        
        # 話者分析
        analysis = speaker.analyze_speakers(segments)
        print(f"\n📈 話者分析結果:")
        print(f"  検出話者数: {analysis['num_speakers']}人")
        print(f"  総発話時間: {analysis['total_duration']:.2f}秒")
        print(f"  全セグメント数: {analysis['num_segments']}")
        
        for speaker_id, stats in analysis['speakers'].items():
            print(f"  話者{speaker_id}:")
            print(f"    セグメント数: {stats['segments']}")
            print(f"    合計時間: {stats['total_duration']:.2f}秒")
            print(f"    平均信頼度: {stats['avg_confidence']:.2f}")
        
        # セグメント詳細表示
        print(f"\n📝 セグメント詳細:")
        for i, segment in enumerate(segments, 1):
            print(f"  {i:2d}: {segment}")
        
        # ステップ3: 話者音声抽出（BGM除去済みボーカル音声から）
        print(f"\n🎤 ステップ3: 話者音声抽出")
        print(f"入力: BGM除去済みボーカル音声 ({Path(vocals_path).name})")
        print(f"セグメント: {len(segments)}個の話者セグメント")
        speaker_output_dir = output_dir / "speakers"
        
        print(f"⚡ BGM除去済みボーカル音声から話者別音声を抽出中...")
        speaker_files = speaker.extract_speaker_audio(
            vocals_path,  # BGM除去済みのボーカル音声から抽出
            segments,
            str(speaker_output_dir),
            create_individual=True,
            create_combined=True
        )
        
        print(f"✅ 話者音声抽出完了:")
        total_files = 0
        for speaker_id, files in speaker_files.items():
            print(f"  話者{speaker_id}: {len(files)}ファイル")
            for file_path in files:
                file_size = FileUtils.get_file_size(file_path)
                print(f"    - {Path(file_path).name} ({FileUtils.format_file_size(file_size)})")
                total_files += 1
        
        # 最終結果サマリー
        print(f"\n🎉 処理完了サマリー:")
        print(f"  入力音声: {duration:.2f}秒")
        print(f"  検出話者数: {analysis['num_speakers']}人")
        print(f"  出力ファイル数: {total_files}ファイル")
        print(f"  総推定時間: {estimated_bgm_time + estimated_speaker_time:.1f}秒")
        print(f"  出力ディレクトリ: {output_dir}")
        
        # 出力ディレクトリ構造表示
        print(f"\n📂 出力ディレクトリ構造:")
        all_files = FileUtils.list_files(output_dir, '*', recursive=True)
        for file_path in sorted(all_files):
            rel_path = file_path.relative_to(output_dir)
            file_size = FileUtils.get_file_size(file_path)
            print(f"  {rel_path} ({FileUtils.format_file_size(file_size)})")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        logging.exception("処理中にエラーが発生")
        return False

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="実際の音声ファイルで音声分離をテストします",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python test_real_audio.py audio.wav
  python test_real_audio.py /path/to/youtube_audio.wav ./output
  python test_real_audio.py music.mp3 /tmp/separated_output

対応形式: wav, mp3, flac, m4a, aac, ogg
        """
    )
    
    parser.add_argument(
        'input_file',
        help='入力音声ファイルパス'
    )
    
    parser.add_argument(
        'output_dir',
        nargs='?',
        default='tests/outputs/latest',
        help='出力ディレクトリ（デフォルト: tests/outputs/latest）'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細ログを表示'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # テスト実行
    success = test_audio_separation(args.input_file, args.output_dir)
    
    if success:
        print(f"\n✅ テスト完了！")
        sys.exit(0)
    else:
        print(f"\n❌ テスト失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()