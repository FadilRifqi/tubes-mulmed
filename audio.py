import numpy as np
import librosa 
import sounddevice as sd
import threading
import queue
import sys

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
            # print(status)
            pass
        self._audio_queue.put(indata.copy())

    def _process_audio(self):
        # Buffer digunakan untuk mengumpulkan data audio sebelum diolah menjadi frame
        buffer = np.zeros(0, dtype=np.float32)
        while self._running:
            try:
                # Ambil data dari queue
                data = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if data is None:
                break

            # Konversi ke mono (rata-rata antar channel) dan tambahkan ke buffer
            buffer = np.append(buffer, np.mean(data, axis=1))
            
            # Cek jika buffer sudah cukup untuk satu frame bloksize
            if len(buffer) >= self.blocksize:
                frame = buffer[:self.blocksize]
                # Geser buffer berdasarkan hop_length
                buffer = buffer[self.hop_length:]

                try:
                    # Deteksi pitch menggunakan YIN
                    f0 = librosa.yin(
                        frame,
                        fmin=self.fmin,
                        fmax=self.fmax,
                        sr=self.samplerate,
                    )
                    # Ambil nilai median pitch yang terdeteksi dalam frame
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

        # Stream dimulai dengan ukuran blok hop_length
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
        return self.pitch_value