#!/usr/bin/env python3
"""
音声分離アプリケーションのセットアップスクリプト
"""

import subprocess
import sys
import os

def install_requirements():
    """必要なパッケージをインストール"""
    print("必要なパッケージをインストールしています...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("基本パッケージのインストールが完了しました。")
    except subprocess.CalledProcessError as e:
        print(f"パッケージインストールでエラーが発生しました: {e}")
        return False
    
    # オプション: ドラッグアンドドロップ機能
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkinterdnd2"])
        print("ドラッグアンドドロップ機能のインストールが完了しました。")
    except subprocess.CalledProcessError:
        print("注意: ドラッグアンドドロップ機能のインストールに失敗しました。手動でファイル選択を使用してください。")
    
    return True

def setup_pyannote():
    """pyannote-audioのセットアップ"""
    print("\npyannote-audioのセットアップを行います...")
    print("注意: Hugging Faceのトークンが必要な場合があります。")
    print("https://huggingface.co/settings/tokens でトークンを取得してください。")
    
    token = input("Hugging Faceトークンを入力してください (スキップする場合はEnter): ").strip()
    
    if token:
        os.environ['HUGGINGFACE_HUB_TOKEN'] = token
        print("トークンが設定されました。")
    else:
        print("トークンがスキップされました。モデルが利用できない場合は後で設定してください。")

def main():
    """メインセットアップ関数"""
    print("音声分離アプリケーションのセットアップを開始します...\n")
    
    if not install_requirements():
        print("セットアップが失敗しました。")
        sys.exit(1)
    
    setup_pyannote()
    
    print("\nセットアップが完了しました！")
    print("アプリケーションを起動するには以下のコマンドを実行してください:")
    print("python audio_separator.py")

if __name__ == "__main__":
    main()