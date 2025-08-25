r"""
図面フォルダ監視システム（単一ファイル版）
d:\zumen フォルダを監視し、PDF/TIF/TIFFファイルの変更を検出してJSONファイルを自動更新
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
import concurrent.futures


# --- 設定項目 ---
MONITOR_ROOT = r"d:\zumen"
OUTPUT_DIR = r"D:\file_monitor\zumen"
PROJECT_NAME = "zumen"


class FileMonitorHandler(FileSystemEventHandler):
    """ファイル変更イベントを処理するハンドラー"""
    
    def __init__(self, monitor_instance):
        self.monitor = monitor_instance
        self.last_update = 0
        self.update_delay = 2  # 2秒間のバッファを設けて連続更新を防ぐ
    
    def is_target_file(self, file_path: str) -> bool:
        """監視対象のファイルかチェック"""
        extensions = ['.pdf', '.tif', '.tiff', '.PDF', '.TIF', '.TIFF']
        return any(file_path.lower().endswith(ext.lower()) for ext in extensions)
    
    def should_update(self) -> bool:
        """更新すべきかどうかを判定（連続更新を防ぐ）"""
        current_time = time.time()
        if current_time - self.last_update > self.update_delay:
            self.last_update = current_time
            return True
        return False

    
    
    def on_created(self, event):
        if not event.is_directory and self.is_target_file(event.src_path):
            self.log_event("CREATED", event.src_path)
            if self.should_update():
                self.monitor.schedule_update()
    
    def on_deleted(self, event):
        if not event.is_directory and self.is_target_file(event.src_path):
            self.log_event("DELETED", event.src_path)
            if self.should_update():
                self.monitor.schedule_update()
    
    def on_moved(self, event):
        if not event.is_directory and (self.is_target_file(event.src_path) or 
                                       self.is_target_file(event.dest_path)):
            self.log_event("MOVED", f"{event.src_path} -> {event.dest_path}")
            if self.should_update():
                self.monitor.schedule_update()
    
    def on_modified(self, event):
        # ファイル内容の変更（上書き等）
        if not event.is_directory and self.is_target_file(event.src_path):
            self.log_event("MODIFIED", event.src_path)
            if self.should_update():
                self.monitor.schedule_update()
    
    def log_event(self, event_type: str, path: str):
        """イベントをログに記録"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {event_type}: {path}"
        
        self.monitor.write_log(log_message)


class ZumenWatchdog:
    """図面ファイル監視システム"""
    
    def __init__(self):
        self.monitor_root = Path(MONITOR_ROOT)
        self.output_dir = Path(OUTPUT_DIR)
        self.project_name = PROJECT_NAME
        
        # 出力ディレクトリを作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイルパス
        self.structure_path = self.output_dir / "folder_structure.json"
        self.metadata_path = self.output_dir / "folder_metadata.json"
        self.log_path = self.output_dir / "monitor_log.txt"
        
        # 監視設定
        self.observer = Observer()
        self.handler = FileMonitorHandler(self)
        self.update_scheduled = False
        self.current_timer = None
    
    def write_log(self, message: str):
        """ログファイルに書き込み"""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception:
            pass
    
    def schedule_update(self):
        """JSON更新をスケジュール"""
        # 既存のタイマーをキャンセル
        if self.current_timer is not None:
            self.current_timer.cancel()
        
        self.update_scheduled = True
        # 30秒間遅延させて複数の変更を一括処理
        import threading
        self.current_timer = threading.Timer(30.0, self.perform_update)
        self.current_timer.start()
    
    def perform_update(self):
        """実際のJSON更新処理"""
        try:
            # フォルダ構造をスキャン
            structure = self.scan_folder_structure()
            metadata = self.get_folder_metadata()
            
            # JSONファイルに保存
            with open(self.structure_path, 'w', encoding='utf-8') as f:
                json.dump(structure, f, ensure_ascii=False, indent=2)
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.write_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] JSON更新完了: {len(structure)}個の分類")
            
        except Exception as e:
            self.write_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] JSON更新エラー: {e}")
        finally:
            self.update_scheduled = False  # 更新対象をリセット
            self.current_timer = None      # タイマーをリセット
    
    def get_folder_metadata(self) -> Dict[str, Dict]:
        """各第1階層フォルダの更新時刻、ファイル数、総サイズ、ファイル名ハッシュを取得"""
        metadata = {}
        if not self.monitor_root.exists() or not self.monitor_root.is_dir():
            return metadata
        
        try:
            file_extensions = ['pdf', 'tif', 'tiff']
            for item in self.monitor_root.iterdir():
                if item.is_dir():
                    total_files = 0
                    total_size = 0
                    file_names = set()
                    
                    try:
                        # 直下のファイルを処理
                        for ext in file_extensions:
                            for file_obj in list(item.glob(f"*.{ext}")) + list(item.glob(f"*.{ext.upper()}")):
                                if file_obj.is_file():
                                    total_files += 1
                                    try:
                                        total_size += file_obj.stat().st_size
                                        file_names.add(file_obj.name)
                                    except Exception:
                                        pass
                        
                        # サブフォルダ内のファイルも処理
                        for sub_item in item.iterdir():
                            if sub_item.is_dir():
                                for ext in file_extensions:
                                    for file_obj in list(sub_item.glob(f"*.{ext}")) + list(sub_item.glob(f"*.{ext.upper()}")):
                                        if file_obj.is_file():
                                            total_files += 1
                                            try:
                                                total_size += file_obj.stat().st_size
                                                relative_name = f"{sub_item.name}/{file_obj.name}"
                                                file_names.add(relative_name)
                                            except Exception:
                                                pass
                    except Exception:
                        pass
                    
                    # ファイル名セットのハッシュを生成
                    files_hash = ""
                    if file_names:
                        sorted_names = sorted(file_names)
                        names_string = "|".join(sorted_names)
                        files_hash = hashlib.md5(names_string.encode('utf-8')).hexdigest()[:16]
                    
                    metadata[item.name] = {
                        "mtime": item.stat().st_mtime,
                        "file_count": total_files,
                        "total_size": total_size,
                        "files_hash": files_hash
                    }
        except Exception:
            pass
        
        return metadata

    
    
    def scan_folder_with_direct_files(self, first_level_path: Path, folder_name: str) -> Tuple[str, Dict[str, List[str]]]:
        """第1階層フォルダとその直下のファイルもスキャンする"""
        folder_structure = {}
        
        try:
            # 第1階層直下のファイルをチェック
            direct_files = set()
            file_extensions = ['pdf', 'tif', 'tiff']
            for ext in file_extensions:
                try:
                    for file_obj in list(first_level_path.glob(f"*.{ext}")) + list(first_level_path.glob(f"*.{ext.upper()}")):
                        if file_obj.is_file():
                            direct_files.add(file_obj.name)
                except Exception:
                    continue
            
            # 直下にファイルがある場合は特別なキーで保存
            if direct_files:
                folder_structure["__direct_files__"] = sorted(list(direct_files))
            
            # 第2階層フォルダをスキャン
            second_level_folders = [item for item in first_level_path.iterdir() if item.is_dir()]
            
            for second_level_item in second_level_folders:
                second_level_name = second_level_item.name
                
                # ファイルリストを取得
                files = set()
                for ext in file_extensions:
                    try:
                        for file_obj in list(second_level_item.glob(f"*.{ext}")) + list(second_level_item.glob(f"*.{ext.upper()}")):
                            if file_obj.is_file():
                                files.add(file_obj.name)
                    except Exception:
                        continue
                
                folder_structure[second_level_name] = sorted(list(files))
                    
        except Exception:
            pass
        
        return folder_name, folder_structure
    
    def scan_folder_structure(self) -> Dict[str, Dict[str, List[str]]]:
        """フォルダ構造をスキャン（並列処理）"""
        structure = {}
        
        if not self.monitor_root.exists() or not self.monitor_root.is_dir():
            return structure
        
        try:
            # 第1階層フォルダを取得
            target_folders = [(item, item.name) for item in self.monitor_root.iterdir() if item.is_dir()]
            
            # 並列処理でスキャン
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for first_level_path, folder_name in target_folders:
                    future = executor.submit(self.scan_folder_with_direct_files, first_level_path, folder_name)
                    futures.append(future)
                
                # 結果を取得
                for future in concurrent.futures.as_completed(futures):
                    try:
                        folder_name, folder_structure = future.result()
                        structure[folder_name] = folder_structure
                    except Exception:
                        continue
            
        except Exception:
            pass
        
        return structure
    
    def start_monitoring(self):
        """監視開始"""
        # 監視対象フォルダの存在確認
        if not self.monitor_root.exists():
            return
        
        # 初回スキャン
        self.perform_update()
        
        # 監視開始
        self.observer.schedule(self.handler, str(self.monitor_root), recursive=True)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """監視停止"""
        self.observer.stop()
        self.observer.join()


def main():
        """メイン実行関数"""
        try:
            # 監視インスタンスを作成
            monitor = ZumenWatchdog()
            
            # 監視開始
            monitor.start_monitoring()
            
        except KeyboardInterrupt:
            pass
        except Exception:
            pass


if __name__ == "__main__":
    main()