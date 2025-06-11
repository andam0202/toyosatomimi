#!/usr/bin/env python3
"""
Nuitka ビルド設定

toyosatomimi の Nuitka を使用したexe化設定
"""

import sys
import os
from pathlib import Path
import subprocess

def build_with_nuitka():
    """Nuitkaを使用してexeファイルをビルド"""
    
    # プロジェクトルート
    project_root = Path(__file__).parent
    entry_point = project_root / "src" / "audio_separator" / "gui" / "views" / "main_window.py"
    
    # ビルドコマンドの構築
    nuitka_args = [
        sys.executable, "-m", "nuitka",
        
        # 基本設定
        "--standalone",           # スタンドアロン実行ファイル
        "--onefile",             # 単一ファイル出力
        "--assume-yes-for-downloads",  # 依存関係の自動ダウンロード
        
        # Windows設定
        "--windows-console-mode=disable",  # コンソールウィンドウを非表示
        
        # プラグイン設定
        "--enable-plugin=tk-inter",        # tkinterサポート
        "--enable-plugin=numpy",           # numpyサポート  
        
        # データファイル・ディレクトリの包含
        "--include-data-dir=config=config",
        f"--include-package-data={project_root}/src",
        
        # 出力設定
        "--output-filename=toyosatomimi.exe",
        "--output-dir=dist",
        
        # 最適化設定
        "--lto=yes",             # リンク時最適化
        "--jobs=4",              # 並列ビルド
        
        # Python パッケージの明示的包含
        "--include-package=audio_separator",
        "--include-package=tkinter",
        "--include-package=torch",
        "--include-package=torchaudio",
        "--include-package=librosa",
        "--include-package=soundfile",
        "--include-package=numpy",
        "--include-package=scipy",
        
        # 隠しインポートの包含
        "--include-module=tkinter.filedialog",
        "--include-module=tkinter.messagebox",
        "--include-module=tkinter.scrolledtext",
        "--include-module=platform",
        "--include-module=subprocess",
        "--include-module=json",
        "--include-module=logging",
        "--include-module=threading",
        "--include-module=pathlib",
        "--include-module=dataclasses",
        
        # エントリーポイント
        str(entry_point)
    ]
    
    # Windows固有の設定
    if sys.platform == "win32":
        # アイコンファイルが存在する場合のみ追加
        icon_path = project_root / "assets" / "icon.ico"
        windows_args = [
            "--product-name=toyosatomimi",
            "--file-description=toyosatomimi - 音声分離アプリケーション",
            "--product-version=1.0.0",
            "--file-version=1.0.0.0",
            "--copyright=Copyright (C) 2024 toyosatomimi development team",
        ]
        
        if icon_path.exists():
            windows_args.insert(0, f"--windows-icon-from-ico={icon_path}")
        
        nuitka_args.extend(windows_args)
    
    print("=" * 60)
    print("toyosatomimi - Nuitka ビルド開始")
    print("=" * 60)
    print(f"エントリーポイント: {entry_point}")
    print(f"出力ディレクトリ: {project_root}/dist")
    print()
    
    # ビルド実行
    try:
        print("Nuitka ビルドコマンド実行中...")
        result = subprocess.run(nuitka_args, cwd=project_root, check=True)
        
        print("\n" + "=" * 60)
        print("✅ ビルド成功！")
        print("=" * 60)
        
        # 出力ファイルの確認
        exe_path = project_root / "dist" / "toyosatomimi.exe"
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"📦 実行ファイル: {exe_path}")
            print(f"📏 ファイルサイズ: {file_size:.1f} MB")
            print()
            print("🚀 実行方法:")
            print(f"   {exe_path}")
        else:
            print("⚠️ 実行ファイルが見つかりません")
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ビルドエラー: {e}")
        print("エラー詳細を確認してください。")
        return False
    except FileNotFoundError:
        print("\n❌ Nuitkaが見つかりません")
        print("以下のコマンドでNuitkaをインストールしてください:")
        print("   uv add --dev nuitka")
        return False
    
    return True

def clean_build():
    """ビルド成果物をクリーンアップ"""
    project_root = Path(__file__).parent
    
    # クリーンアップ対象
    cleanup_paths = [
        project_root / "dist",
        project_root / "build",
        project_root / "toyosatomimi.build",
        project_root / "toyosatomimi.dist",
        project_root / "toyosatomimi.onefile-build",
    ]
    
    print("🧹 ビルド成果物をクリーンアップ中...")
    
    for path in cleanup_paths:
        if path.exists():
            if path.is_file():
                path.unlink()
                print(f"   削除: {path}")
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
                print(f"   削除: {path}/")

def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="toyosatomimi Nuitka ビルドスクリプト")
    parser.add_argument("--clean", action="store_true", help="ビルド成果物をクリーンアップ")
    parser.add_argument("--build", action="store_true", help="Nuitkaビルド実行")
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
        return
    
    if args.build or len(sys.argv) == 1:
        success = build_with_nuitka()
        sys.exit(0 if success else 1)
    
    parser.print_help()

if __name__ == "__main__":
    main()