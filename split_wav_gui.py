import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import soundfile as sf

CONFIG_FILE = os.path.expanduser("~/.split_wav_config.json")

class SplitWavApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MultiChannel WAV Splitter (Big Session Version)")

        self.input_folder = ""
        self.output_folder = ""

        tk.Button(root, text="Select Input Folder", command=self.select_input).pack(pady=5)
        tk.Button(root, text="Select Output Folder", command=self.select_output).pack(pady=5)

        tk.Label(root, text="Number of Channels (e.g., 16)").pack()
        self.channel_entry = tk.Entry(root)
        self.channel_entry.insert(0, "16")
        self.channel_entry.pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        tk.Button(root, text="Start", command=self.start_processing).pack(pady=10)

        self.log = tk.Text(root, height=20, width=80)
        self.log.pack(pady=5)

        self.load_config()

    def select_input(self):
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder = folder

    def select_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder

    def log_message(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.root.update()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.input_folder = config.get("input", "")
                    self.output_folder = config.get("output", "")
                    self.channel_entry.delete(0, tk.END)
                    self.channel_entry.insert(0, str(config.get("channels", 16)))
            except Exception:
                pass

    def save_config(self):
        config = {
            "input": self.input_folder,
            "output": self.output_folder,
            "channels": int(self.channel_entry.get())
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def start_processing(self):
        if not self.input_folder or not self.output_folder:
            messagebox.showerror("Error", "Please select both input and output folders.")
            return

        try:
            max_channels = int(self.channel_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for the channel count.")
            return

        self.save_config()

        files = sorted([f for f in os.listdir(self.input_folder) if f.lower().endswith(".wav")])
        total_files = len(files)
        self.progress["maximum"] = total_files

        sample_rate = None
        subtype = 'PCM_24'

        try:
            for idx, filename in enumerate(files):
                filepath = os.path.join(self.input_folder, filename)
                self.log_message(f"Processing: {filepath}")

                with sf.SoundFile(filepath) as sf_read:
                    if sample_rate is None:
                        sample_rate = sf_read.samplerate
                    channels_in_file = sf_read.channels
                    channels_to_process = min(channels_in_file, max_channels)

                    frames = sf_read.frames
                    blocksize = 1024 * 1024
                    sf_read.seek(0)

                    while True:
                        data = sf_read.read(frames=blocksize, dtype='float32', always_2d=True)
                        if data.size == 0:
                            break

                        for ch in range(channels_to_process):
                            output_path = os.path.join(self.output_folder, f"channel_{ch+1}.wav")
                            if not os.path.exists(output_path):
                                with sf.SoundFile(output_path, mode='w', samplerate=sample_rate, channels=1, subtype=subtype) as sf_write:
                                    sf_write.write(data[:, ch])
                            else:
                                with sf.SoundFile(output_path, mode='r+') as sf_write:
                                    sf_write.seek(0, sf.SEEK_END)
                                    sf_write.write(data[:, ch])

                self.progress["value"] = idx + 1
                self.root.update()

            self.log_message("All files were successfully created!")
            messagebox.showinfo("Done", "All files were successfully created!")
            self.progress["value"] = 0

        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = SplitWavApp(root)
    root.mainloop()
