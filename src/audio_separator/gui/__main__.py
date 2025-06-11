"""
GUI アプリケーション エントリーポイント

python -m src.audio_separator.gui でGUIアプリケーションを起動します。
"""

if __name__ == "__main__":
    from .views.main_window import main
    main()