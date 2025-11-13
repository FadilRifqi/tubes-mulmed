import numpy as np
import librosa
import sounddevice as sd
import threading
import queue


class Audio:
    def __init__(self, samplerate=22050, blocksize=2048, hop_length=512, fmin=65, fmax=2093):
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.hop_length = hop_length
        self.fmin = fmin
        self.fmax = fmax

        self.pitch_value = 0.0
        self._audio_queue = queue.Queue()
        self._running = False
        self._thread = None
        self._stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status)
        self._audio_queue.put(indata.copy())

    def _process_audio(self):
        buffer = np.zeros(0, dtype=np.float32)
        while self._running:
            try:
                data = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if data is None:
                break

            buffer = np.append(buffer, np.mean(data, axis=1))
            if len(buffer) >= self.blocksize:
                frame = buffer[:self.blocksize]
                buffer = buffer[self.hop_length:]

                try:
                    f0 = librosa.yin(
                        frame,
                        fmin=self.fmin,
                        fmax=self.fmax,
                        sr=self.samplerate,
                    )
                    pitch = np.nanmedian(f0)
                    if not np.isnan(pitch):
                        self.pitch_value = float(pitch)
                except Exception:
                    pass

    def start(self):
        """Mulai audio stream dan thread pemrosesan"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._process_audio, daemon=True)
        self._thread.start()

        self._stream = sd.InputStream(
            channels=1,
            samplerate=self.samplerate,
            blocksize=self.hop_length,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self):
        """Hentikan audio processing"""
        self._running = False
        self._audio_queue.put(None)
        if self._stream:
            self._stream.stop()
            self._stream.close()
        if self._thread:
            self._thread.join(timeout=1)

    def get_pitch(self):
        """Kembalikan nilai pitch saat ini"""
        print("Pitch value:", self.pitch_value)
        return self.pitch_value
