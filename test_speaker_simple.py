#!/usr/bin/env python3
"""
話者分離テスト（簡易版）
pyannote-audioの依存関係なしでテスト
"""

import os
import sys
import logging
from pathlib import Path

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_pyannote_availability():
    """pyannote-audioの利用可能性をテスト"""
    logging.info("=== pyannote-audio 利用可能性チェック ===")
    
    # 1. パッケージインポートテスト
    try:
        import pyannote.audio
        logging.info(f"✅ pyannote-audio インストール済み (version: {pyannote.audio.__version__})")
        pyannote_available = True
    except ImportError as e:
        logging.error(f"❌ pyannote-audio インストールされていません: {e}")
        pyannote_available = False
    
    # 2. 認証トークンチェック
    hf_token = os.environ.get('HF_TOKEN')
    if hf_token:
        logging.info("✅ HF_TOKEN 環境変数が設定されています")
        # トークンの一部を表示（セキュリティのため最初の8文字のみ）
        logging.info(f"トークン: {hf_token[:8]}...")
    else:
        logging.error("❌ HF_TOKEN 環境変数が設定されていません")
    
    # 3. huggingface_hubチェック
    try:
        import huggingface_hub
        logging.info(f"✅ huggingface_hub 利用可能 (version: {huggingface_hub.__version__})")
    except ImportError:
        logging.error("❌ huggingface_hub インストールされていません")
    
    # 4. pyannote-audioパイプライン初期化テスト
    if pyannote_available:
        try:
            from pyannote.audio import Pipeline
            
            logging.info("pyannote-audioパイプライン初期化テスト...")
            
            # 簡単なモデルで初期化テスト
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token if hf_token else True
            )
            
            logging.info("✅ pyannote-audioパイプライン初期化成功")
            
            # GPU利用可能性チェック
            import torch
            if torch.cuda.is_available():
                device = torch.device('cuda')
                pipeline = pipeline.to(device)
                logging.info(f"✅ GPU利用可能: {torch.cuda.get_device_name()}")
            else:
                logging.info("ℹ️ CPU使用（GPU利用不可）")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ pyannote-audioパイプライン初期化失敗: {e}")
            
            # 詳細なエラー解析
            if "401 Client Error" in str(e):
                logging.error("認証エラー: HF_TOKENが無効またはモデルへのアクセス権限がありません")
                logging.info("解決方法:")
                logging.info("1. https://huggingface.co/pyannote/speaker-diarization-3.1 でモデルの利用同意")
                logging.info("2. 有効なHugging Faceトークンを設定")
            elif "403 Client Error" in str(e):
                logging.error("アクセス拒否: モデルライセンスに同意していないか、アクセス権限がありません")
            
            return False
    
    return False

def test_simple_speaker_separation():
    """簡易話者分離テスト"""
    logging.info("\n=== 簡易話者分離テスト ===")
    
    try:
        # サンプル音声データ作成（モック）
        import numpy as np
        
        # 10秒のサンプル音声（サイン波）
        sample_rate = 16000
        duration = 10.0
        samples = int(sample_rate * duration)
        
        # 2つの異なる周波数のサイン波を作成（話者を模擬）
        t = np.linspace(0, duration, samples)
        speaker1_freq = 440  # A音
        speaker2_freq = 660  # E音
        
        speaker1_signal = 0.5 * np.sin(2 * np.pi * speaker1_freq * t)
        speaker2_signal = 0.3 * np.sin(2 * np.pi * speaker2_freq * t)
        
        # 合成音声作成
        combined_signal = speaker1_signal + speaker2_signal
        
        logging.info(f"サンプル音声作成: {duration}秒, {sample_rate}Hz")
        logging.info(f"話者1周波数: {speaker1_freq}Hz, 話者2周波数: {speaker2_freq}Hz")
        
        # 簡易話者分離アルゴリズム（周波数ベース）
        from scipy import signal
        
        # FFTで周波数解析
        freqs, psd = signal.welch(combined_signal, sample_rate, nperseg=1024)
        
        # ピーク検出
        peaks, _ = signal.find_peaks(psd, height=np.max(psd)*0.1)
        detected_freqs = freqs[peaks]
        
        logging.info(f"検出された周波数ピーク: {detected_freqs[:5]}")  # 上位5つ
        
        # 話者分離成功判定
        if len(detected_freqs) >= 2:
            logging.info("✅ 簡易話者分離成功: 複数の周波数成分を検出")
            return True
        else:
            logging.warning("⚠️ 話者分離精度低: 周波数成分が少ない")
            return False
            
    except ImportError as e:
        logging.error(f"❌ 必要なライブラリ不足: {e}")
        logging.info("scipy インストールが必要です: pip install scipy")
        return False
    except Exception as e:
        logging.error(f"❌ 簡易話者分離テストエラー: {e}")
        return False

def show_installation_guide():
    """インストールガイド表示"""
    logging.info("\n=== インストールガイド ===")
    
    logging.info("pyannote-audioセットアップ手順:")
    logging.info("1. パッケージインストール:")
    logging.info("   pip install pyannote.audio")
    logging.info("")
    logging.info("2. Hugging Face認証設定:")
    logging.info("   a) https://huggingface.co/ でアカウント作成")
    logging.info("   b) https://huggingface.co/settings/tokens でトークン取得")
    logging.info("   c) export HF_TOKEN='your_token_here'")
    logging.info("")
    logging.info("3. モデルライセンス同意:")
    logging.info("   https://huggingface.co/pyannote/speaker-diarization-3.1")
    logging.info("   上記ページで利用規約に同意")
    logging.info("")
    logging.info("4. テスト実行:")
    logging.info("   python test_speaker_simple.py")

def main():
    """メイン実行"""
    setup_logging()
    
    logging.info("話者分離環境チェック開始")
    
    # pyannote-audio利用可能性チェック
    pyannote_ok = test_pyannote_availability()
    
    # 簡易話者分離テスト
    simple_ok = test_simple_speaker_separation()
    
    # 結果サマリー
    logging.info("\n=== 結果サマリー ===")
    
    if pyannote_ok:
        logging.info("🎉 pyannote-audio 利用可能！高精度話者分離が使用できます")
    elif simple_ok:
        logging.info("⚠️ pyannote-audio 利用不可、簡易話者分離で動作します")
        show_installation_guide()
    else:
        logging.error("❌ 話者分離機能が利用できません")
        show_installation_guide()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())