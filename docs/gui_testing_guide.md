# Windows向けGUI テスト・リリースガイド

## 🖥️ WSL環境でのGUIテスト方法

### 方法1: X11サーバー（VcXsrv）を使用

#### セットアップ手順
1. **VcXsrvをインストール**
   - [VcXsrv Windows X Server](https://sourceforge.net/projects/vcxsrv/)をダウンロード・インストール
   
2. **XLaunchを起動**
   ```
   - Multiple windows を選択
   - Display number: 0
   - Start no client にチェック
   - Clipboard, Primary Selection にチェック
   - Disable access control にチェック（重要）
   ```

3. **WSL側でDISPLAY設定**
   ```bash
   # ~/.bashrc に追加
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   
   # または手動設定
   export DISPLAY=172.x.x.x:0  # WindowsのIPアドレス
   ```

4. **テスト実行**
   ```bash
   # X11テスト
   xclock  # 時計アプリが表示されれば成功
   
   # toyosatomimi GUI起動
   uv run python -m src.audio_separator.gui
   ```

### 方法2: WSL2 + WSLg（Windows 11推奨）

Windows 11なら標準でGUI対応：
```bash
# 追加設定不要、直接実行可能
uv run python -m src.audio_separator.gui
```

### 方法3: Windowsネイティブ環境

最も確実な方法：
```cmd
REM Windows PowerShell/コマンドプロンプト
cd C:\Users\mao0202\Documents\GitHub\toyosatomimi
uv run python -m src.audio_separator.gui
```

## 🚀 リリース方法

### 1. Pythonスタンドアロン実行ファイル作成

#### Nuitkaを使用（推奨）
```bash
# Nuitkaインストール
uv add --dev nuitka

# 実行ファイル作成
uv run python -m nuitka \
  --standalone \
  --onefile \
  --windows-console-mode=disable \
  --enable-plugin=tk-inter \
  --include-data-dir=config=config \
  --output-filename=toyosatomimi.exe \
  --output-dir=dist \
  src/audio_separator/gui/views/main_window.py
```

#### PyInstallerを使用（代替）
```bash
# PyInstallerインストール
uv add --dev pyinstaller

# 実行ファイル作成
uv run pyinstaller --onefile --windowed \
  --add-data "src;src" \
  --hidden-import="tkinter" \
  --hidden-import="tkinter.ttk" \
  --hidden-import="tkinter.filedialog" \
  --name="toyosatomimi" \
  src/audio_separator/gui/views/main_window.py
```

### 2. インストーラー作成

#### Inno Setupを使用
```inno
[Setup]
AppName=toyosatomimi
AppVersion=1.0
DefaultDirName={pf}\toyosatomimi
DefaultGroupName=toyosatomimi
OutputDir=dist

[Files]
Source: "dist\toyosatomimi.exe"; DestDir: "{app}"
Source: "models\*"; DestDir: "{app}\models"; Flags: recursesubdirs

[Icons]
Name: "{group}\toyosatomimi"; Filename: "{app}\toyosatomimi.exe"
```

#### NSIS使用
```nsis
Name "toyosatomimi"
OutFile "toyosatomimi-installer.exe"
InstallDir "$PROGRAMFILES\toyosatomimi"

Section
  SetOutPath $INSTDIR
  File "dist\toyosatomimi.exe"
  CreateShortCut "$DESKTOP\toyosatomimi.lnk" "$INSTDIR\toyosatomimi.exe"
SectionEnd
```

### 3. MSIパッケージ作成

Windows標準のMSI形式：
```bash
# cx_Freezeを使用
uv add --dev cx_freeze

# setup.py作成
python setup.py bdist_msi
```

## 📦 実用的なリリース戦略

### 開発・テストフロー
```
WSL開発 → Windowsテスト → ビルド → リリース
    ↓          ↓         ↓        ↓
 コード作成   GUI確認   実行ファイル  配布
```

### 推奨アプローチ
1. **開発**: WSL環境で継続
2. **テスト**: Windows環境で定期的に確認
3. **ビルド**: GitHub ActionsでCI/CD
4. **配布**: GitHub Releases

## 🔧 自動化されたビルド・リリース

### GitHub Actionsワークフロー
```yaml
name: Build Windows Release

on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install uv
      run: pip install uv
    
    - name: Install dependencies
      run: uv sync
    
    - name: Build executable
      run: |
        uv add --dev pyinstaller
        uv run pyinstaller toyosatomimi.spec
    
    - name: Create release
      uses: actions/upload-artifact@v3
      with:
        name: toyosatomimi-windows
        path: dist/toyosatomimi.exe
```

## 🎯 実践的なテスト手順

### 1. 日常開発
```bash
# WSLで開発・基本テスト
uv run python test_gui_import_only.py
```

### 2. 定期的なGUIテスト
```bash
# Windowsで実際のGUI確認（週1-2回）
# PowerShellで実行
cd C:\Users\mao0202\Documents\GitHub\toyosatomimi
uv run python -m src.audio_separator.gui
```

### 3. リリース前テスト
```bash
# 全機能テスト
# - ファイル選択
# - パラメータ調整
# - 実際の音声分離処理
# - 結果確認
# - エラーハンドリング
```

## 📱 配布パッケージ構成

### Portable版（推奨）
```
toyosatomimi-1.0-windows/
├── toyosatomimi.exe          # メイン実行ファイル
├── models/                   # AIモデルファイル
├── config/                   # 設定ファイル
├── README.txt               # 使用方法
└── LICENSE.txt              # ライセンス
```

### インストーラー版
```
toyosatomimi-setup-1.0.exe   # インストーラー
```

## 🚨 注意事項

### ライセンス・依存関係
- **pyannote-audio**: 学術・研究用途制限あり
- **CUDA**: GPU使用時のランタイム配布
- **FFmpeg**: 音声形式対応のため必要

### パフォーマンス
- **ファイルサイズ**: PyInstallerは大きくなりがち（100MB+）
- **起動時間**: 初回起動は時間がかかる場合あり
- **メモリ使用量**: AIモデル読み込みで大量メモリ使用

### セキュリティ
- **コード署名**: Windows SmartScreenを回避
- **ウイルス対策**: 誤検知対策
- **権限**: 管理者権限は不要に設計