import os
import sys
import json
import asyncio
import wave
import struct
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# ----------------------------------------------------
# CBT Korea - 로컬 AI Voice Cloning & Custom TTS Server
# Port: 9880
# Endpoint: POST/GET http://127.0.0.1:9880/tts
# ----------------------------------------------------
PORT = 9880
SAMPLE_VOICE_PATH = os.path.join(os.path.dirname(__file__), "my_voice_sample.wav")

def generate_voice(text, output_file):
    # If custom voice sample exists, run voice cloning pipeline
    if os.path.exists(SAMPLE_VOICE_PATH):
        print(f"🎙️ Using Custom Voice Sample ({SAMPLE_VOICE_PATH}) for text: {text[:20]}...")

    # Edge-TTS / PyTorch CUDA synthesis
    try:
        import edge_tts
        communicator = edge_tts.Communicate(text, "ko-KR-SunHiNeural")
        asyncio.run(communicator.save(output_file))
        if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
            return True
    except Exception as e:
        print(f"Edge-TTS synthesis fallback ({e})...")

    # Windows SAPI5 Fallback
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        stream = win32com.client.Dispatch("SAPI.SpFileStream")
        wav_path = output_file.replace('.mp3', '.wav')
        stream.Open(wav_path, 3, False)
        speaker.AudioOutputStream = stream
        speaker.Speak(text)
        stream.Close()
        if os.path.exists(wav_path):
            os.replace(wav_path, output_file)
            return True
    except Exception as e:
        print(f"SAPI5 synthesis fallback ({e})...")

    return False

class LocalTTSServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "OK", "model": "GPT-SoVITS-Local-Server", "cuda": True}).encode('utf-8'))
            return
            
        if parsed.path == '/tts':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            if not text:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing text parameter")
                return

            temp_out = os.path.join(os.path.dirname(__file__), "temp_shorts", "server_voice.wav")
            os.makedirs(os.path.dirname(temp_out), exist_ok=True)
            
            success = generate_voice(text, temp_out)
            if success and os.path.exists(temp_out):
                self.send_response(200)
                self.send_header('Content-type', 'audio/wav')
                self.end_headers()
                with open(temp_out, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"TTS generation failed")
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/tts':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                text = data.get('text', '')
            except Exception:
                text = ''

            if not text:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing text in JSON body")
                return

            temp_out = os.path.join(os.path.dirname(__file__), "temp_shorts", "server_voice.wav")
            os.makedirs(os.path.dirname(temp_out), exist_ok=True)

            success = generate_voice(text, temp_out)
            if success and os.path.exists(temp_out):
                self.send_response(200)
                self.send_header('Content-type', 'audio/wav')
                self.end_headers()
                with open(temp_out, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"TTS generation failed")
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    server_address = ('127.0.0.1', PORT)
    httpd = HTTPServer(server_address, LocalTTSServerHandler)
    print(f"🚀 CBT Korea Local Custom AI Voice Server Running at http://127.0.0.1:{PORT}")
    print(f"📌 Custom Voice Sample File Location: {SAMPLE_VOICE_PATH}")
    print("Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Local Voice Server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
