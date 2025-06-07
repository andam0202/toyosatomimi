"""
ファイル処理ユーティリティ

ファイル操作、パス処理、ディレクトリ管理などの機能を提供
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import json


class FileUtils:
    """ファイル処理ユーティリティクラス"""
    
    @staticmethod
    def ensure_directory(directory_path: Union[str, Path]) -> Path:
        """
        ディレクトリの存在を確保（必要に応じて作成）
        
        Args:
            directory_path: ディレクトリパス
            
        Returns:
            Path: 作成されたディレクトリパス
        """
        directory_path = Path(directory_path)
        directory_path.mkdir(parents=True, exist_ok=True)
        return directory_path
    
    @staticmethod
    def get_unique_filename(file_path: Union[str, Path]) -> Path:
        """
        重複しないファイル名を生成
        
        Args:
            file_path: 元のファイルパス
            
        Returns:
            Path: 重複しないファイルパス
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return file_path
        
        # ファイル名と拡張子を分離
        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent
        
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
    
    @staticmethod
    def copy_file(source: Union[str, Path], destination: Union[str, Path]) -> Path:
        """
        ファイルをコピー
        
        Args:
            source: コピー元ファイルパス
            destination: コピー先ファイルパス
            
        Returns:
            Path: コピー先ファイルパス
            
        Raises:
            FileNotFoundError: コピー元ファイルが見つからない場合
        """
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            raise FileNotFoundError(f"コピー元ファイルが見つかりません: {source}")
        
        # コピー先ディレクトリを作成
        FileUtils.ensure_directory(destination.parent)
        
        # ファイルをコピー
        shutil.copy2(source, destination)
        
        logging.info(f"ファイルコピー完了: {source} -> {destination}")
        return destination
    
    @staticmethod
    def move_file(source: Union[str, Path], destination: Union[str, Path]) -> Path:
        """
        ファイルを移動
        
        Args:
            source: 移動元ファイルパス
            destination: 移動先ファイルパス
            
        Returns:
            Path: 移動先ファイルパス
            
        Raises:
            FileNotFoundError: 移動元ファイルが見つからない場合
        """
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            raise FileNotFoundError(f"移動元ファイルが見つかりません: {source}")
        
        # 移動先ディレクトリを作成
        FileUtils.ensure_directory(destination.parent)
        
        # ファイルを移動
        shutil.move(source, destination)
        
        logging.info(f"ファイル移動完了: {source} -> {destination}")
        return destination
    
    @staticmethod
    def delete_file(file_path: Union[str, Path], safe: bool = True) -> bool:
        """
        ファイルを削除
        
        Args:
            file_path: 削除するファイルパス
            safe: 安全削除モード（存在しない場合もエラーにしない）
            
        Returns:
            bool: 削除が成功したかどうか
        """
        file_path = Path(file_path)
        
        try:
            if file_path.exists():
                file_path.unlink()
                logging.info(f"ファイル削除完了: {file_path}")
                return True
            elif not safe:
                raise FileNotFoundError(f"削除対象ファイルが見つかりません: {file_path}")
            
            return False
            
        except Exception as e:
            logging.error(f"ファイル削除エラー: {e}")
            if not safe:
                raise
            return False
    
    @staticmethod
    def list_files(
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """
        ディレクトリ内のファイル一覧を取得
        
        Args:
            directory: 検索ディレクトリ
            pattern: ファイルパターン（例: "*.wav"）
            recursive: 再帰的に検索するかどうか
            
        Returns:
            List[Path]: ファイルパスのリスト
        """
        directory = Path(directory)
        
        if not directory.exists():
            return []
        
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        # ファイルのみを返す（ディレクトリは除外）
        return [f for f in files if f.is_file()]
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """
        ファイルサイズを取得
        
        Args:
            file_path: ファイルパス
            
        Returns:
            int: ファイルサイズ（バイト）
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return 0
        
        return file_path.stat().st_size
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        ファイルサイズを人間が読みやすい形式にフォーマット
        
        Args:
            size_bytes: サイズ（バイト）
            
        Returns:
            str: フォーマットされたサイズ
        """
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        size_index = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and size_index < len(size_names) - 1:
            size_index += 1
            size /= 1024.0
        
        return f"{size:.1f}{size_names[size_index]}"
    
    @staticmethod
    def clean_directory(
        directory: Union[str, Path],
        pattern: str = "*",
        keep_directory: bool = True
    ) -> int:
        """
        ディレクトリをクリーンアップ
        
        Args:
            directory: クリーンアップするディレクトリ
            pattern: 削除するファイルのパターン
            keep_directory: ディレクトリ自体は保持するかどうか
            
        Returns:
            int: 削除されたファイル数
        """
        directory = Path(directory)
        
        if not directory.exists():
            return 0
        
        files = FileUtils.list_files(directory, pattern, recursive=True)
        deleted_count = 0
        
        for file_path in files:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                logging.warning(f"ファイル削除失敗: {file_path}, エラー: {e}")
        
        # 空のディレクトリを削除（keep_directoryがFalseの場合）
        if not keep_directory:
            try:
                if not any(directory.iterdir()):  # ディレクトリが空の場合
                    directory.rmdir()
            except Exception as e:
                logging.warning(f"ディレクトリ削除失敗: {directory}, エラー: {e}")
        
        logging.info(f"ディレクトリクリーンアップ完了: {deleted_count}個のファイルを削除")
        return deleted_count
    
    @staticmethod
    def backup_file(file_path: Union[str, Path], backup_suffix: str = ".backup") -> Optional[Path]:
        """
        ファイルのバックアップを作成
        
        Args:
            file_path: バックアップ対象ファイル
            backup_suffix: バックアップファイルの接尾辞
            
        Returns:
            Optional[Path]: バックアップファイルパス（失敗時はNone）
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None
        
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        backup_path = FileUtils.get_unique_filename(backup_path)
        
        try:
            shutil.copy2(file_path, backup_path)
            logging.info(f"バックアップ作成完了: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"バックアップ作成失敗: {e}")
            return None
    
    @staticmethod
    def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        JSONファイルを読み込み
        
        Args:
            file_path: JSONファイルパス
            
        Returns:
            Dict[str, Any]: 読み込まれたデータ
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"JSONファイル読み込みエラー: {e}")
            return {}
    
    @staticmethod
    def write_json(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
        """
        JSONファイルに書き込み
        
        Args:
            file_path: JSONファイルパス
            data: 書き込むデータ
            indent: インデント数
            
        Returns:
            bool: 書き込みが成功したかどうか
        """
        file_path = Path(file_path)
        
        # ディレクトリを作成
        FileUtils.ensure_directory(file_path.parent)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"JSONファイル書き込みエラー: {e}")
            return False