import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import subprocess
import sys
from pathlib import Path
import librosa
import numpy as np
from typing import Dict, List, Tuple
import torch
import torchaudio
from demucs.api import separate_audio_file
from pyannote.audio import Pipeline
import warnings
warnings.filterwarnings("ignore")

class AudioSeparatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("音声分離アプリケーション")
        self.root.geometry("800x600")
        
        self.input_file = None
        self.output_dir = None
        self.is_processing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ファイル選択
        ttk.Label(main_frame, text="入力音声ファイル:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=60)
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(file_frame, text="参照", command=self.select_file).grid(row=0, column=1, padx=(5, 0))
        
        file_frame.columnconfigure(0, weight=1)
        
        # 出力ディレクトリ選択
        ttk.Label(main_frame, text="出力ディレクトリ:").grid(row=2, column=0, sticky=tk.W, pady=(20, 5))
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=60)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(output_frame, text="参照", command=self.select_output_dir).grid(row=0, column=1, padx=(5, 0))
        
        output_frame.columnconfigure(0, weight=1)
        
        # パラメータ設定
        param_frame = ttk.LabelFrame(main_frame, text="パラメータ設定", padding="10")
        param_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        
        # Demucsモデル選択
        ttk.Label(param_frame, text="Demucsモデル:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.demucs_model = tk.StringVar(value="htdemucs")
        demucs_combo = ttk.Combobox(param_frame, textvariable=self.demucs_model, 
                                   values=["htdemucs", "htdemucs_ft", "mdx_extra"], 
                                   state="readonly", width=20)
        demucs_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 最小話者分離時間
        ttk.Label(param_frame, text="最小話者分離時間 (秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.min_duration = tk.DoubleVar(value=1.0)
        duration_spin = ttk.Spinbox(param_frame, from_=0.1, to=10.0, increment=0.1, 
                                   textvariable=self.min_duration, width=20)
        duration_spin.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 進行状況
        ttk.Label(main_frame, text="進行状況:").grid(row=5, column=0, sticky=tk.W, pady=(20, 5))
        
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_var = tk.StringVar(value="待機中...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # ログ表示
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="5")
        log_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=20)
        
        self.log_text = tk.Text(log_frame, height=10, width=80)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 実行ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)
        
        self.process_button = ttk.Button(button_frame, text="処理開始", command=self.start_processing)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="終了", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # レスポンシブ設定
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # ドラッグアンドドロップ設定
        self.setup_drag_drop()
        
    def setup_drag_drop(self):
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            self.root = TkinterDnD.Tk()
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.drop_file)
        except ImportError:
            self.log("ドラッグアンドドロップ機能を使用するには tkinterdnd2 をインストールしてください")
    
    def drop_file(self, event):
        files = self.root.tk.splitlist(event.data)
        if files:
            self.file_var.set(files[0])
            self.input_file = files[0]
            self.log(f"ファイルが選択されました: {files[0]}")
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="音声ファイルを選択",
            filetypes=[
                ("音声ファイル", "*.wav *.mp3 *.flac *.m4a *.aac"),
                ("すべてのファイル", "*.*")
            ]
        )
        if file_path:
            self.file_var.set(file_path)
            self.input_file = file_path
            self.log(f"ファイルが選択されました: {file_path}")
    
    def select_output_dir(self):
        dir_path = filedialog.askdirectory(title="出力ディレクトリを選択")
        if dir_path:
            self.output_var.set(dir_path)
            self.output_dir = dir_path
            self.log(f"出力ディレクトリが選択されました: {dir_path}")
    
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, status):
        self.status_var.set(status)
        self.root.update_idletasks()
    
    def start_processing(self):
        if self.is_processing:
            return
            
        if not self.input_file or not os.path.exists(self.input_file):
            messagebox.showerror("エラー", "有効な入力ファイルを選択してください")
            return
        
        if not self.output_dir:
            self.output_dir = os.path.dirname(self.input_file)
            self.output_var.set(self.output_dir)
        
        self.is_processing = True
        self.process_button.configure(state="disabled")
        self.progress.start()
        
        # 別スレッドで処理を実行
        thread = threading.Thread(target=self.process_audio)
        thread.daemon = True
        thread.start()
    
    def process_audio(self):
        try:
            self.log("処理を開始します...")
            
            # ステップ1: Demucsでボーカルとその他を分離
            self.update_status("BGMと音声を分離中...")
            self.log("BGMと音声を分離しています...")
            
            vocals_path = self.separate_bgm_vocals()
            
            # ステップ2: pyannote-audioで話者分離
            self.update_status("話者を分離中...")
            self.log("話者を分離しています...")
            
            self.separate_speakers(vocals_path)
            
            self.log("処理が完了しました！")
            self.update_status("完了")
            
        except Exception as e:
            self.log(f"エラーが発生しました: {str(e)}")
            self.update_status("エラー")
            messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{str(e)}")
        
        finally:
            self.is_processing = False
            self.process_button.configure(state="normal")
            self.progress.stop()
    
    def separate_bgm_vocals(self):
        try:
            model_name = self.demucs_model.get()
            output_path = os.path.join(self.output_dir, "separated")
            
            # Demucsで分離
            separated = separate_audio_file(self.input_file, model_name)
            
            # ボーカル部分を保存
            vocals_path = os.path.join(self.output_dir, "vocals.wav")
            torchaudio.save(vocals_path, separated['vocals'], 44100)
            
            # BGM部分も保存
            bgm_path = os.path.join(self.output_dir, "bgm.wav")
            accompaniment = separated['drums'] + separated['bass'] + separated['other']
            torchaudio.save(bgm_path, accompaniment, 44100)
            
            self.log(f"BGMと音声を分離しました: {vocals_path}")
            return vocals_path
            
        except Exception as e:
            raise Exception(f"BGM分離でエラー: {str(e)}")
    
    def separate_speakers(self, vocals_path):
        try:
            # pyannote-audioパイプラインを初期化
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            
            # 話者分離を実行
            diarization = pipeline(vocals_path)
            
            # 音声データを読み込み
            audio, sr = librosa.load(vocals_path, sr=None)
            
            # 話者ごとに音声を分割して保存
            speaker_segments = {}
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if speaker not in speaker_segments:
                    speaker_segments[speaker] = []
                
                start_time = turn.start
                end_time = turn.end
                
                # 最小時間のフィルタリング
                if end_time - start_time >= self.min_duration.get():
                    start_sample = int(start_time * sr)
                    end_sample = int(end_time * sr)
                    
                    segment = audio[start_sample:end_sample]
                    speaker_segments[speaker].append({
                        'audio': segment,
                        'start': start_time,
                        'end': end_time
                    })
            
            # 話者ごとのファイルを作成
            for speaker, segments in speaker_segments.items():
                if segments:
                    # 各セグメントを個別に保存
                    speaker_dir = os.path.join(self.output_dir, f"speaker_{speaker}")
                    os.makedirs(speaker_dir, exist_ok=True)
                    
                    for i, segment in enumerate(segments):
                        segment_path = os.path.join(speaker_dir, f"segment_{i+1:03d}.wav")
                        librosa.output.write_wav(segment_path, segment['audio'], sr)
                    
                    # 全セグメントを結合したファイルも作成
                    all_segments = np.concatenate([seg['audio'] for seg in segments])
                    combined_path = os.path.join(speaker_dir, f"speaker_{speaker}_combined.wav")
                    librosa.output.write_wav(combined_path, all_segments, sr)
                    
                    self.log(f"話者 {speaker}: {len(segments)}個のセグメントを保存しました")
            
            self.log(f"話者分離が完了しました。{len(speaker_segments)}人の話者を検出しました。")
            
        except Exception as e:
            raise Exception(f"話者分離でエラー: {str(e)}")


def main():
    try:
        root = tk.Tk()
        app = AudioSeparatorGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"アプリケーション起動エラー: {e}")
        messagebox.showerror("エラー", f"アプリケーション起動エラー: {e}")


if __name__ == "__main__":
    main()