import os
import sys
import asyncio
import json
import random
import wave
import math
import struct
from PIL import Image, ImageDraw, ImageFont

# Load environment variables from .env if present
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# ----------------------------------------------------
# 1. 프리미엄 디자인 시스템 & 컬러 토큰 (1080x1920 9:16)
# ----------------------------------------------------
WIDTH = 1080
HEIGHT = 1920

COLOR_BG_START = (15, 23, 42)        # Deep Slate Navy (#0F172A)
COLOR_BG_END = (30, 41, 59)          # Slate Blue (#1E293B)
COLOR_TEXT_MAIN = (15, 23, 42)
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_ACCENT_BLUE = (37, 99, 235)
COLOR_SUCCESS_BG = (16, 185, 129)    # Emerald Green
COLOR_SUCCESS_BORDER = (5, 150, 105)
COLOR_TIMER_BAR = (245, 158, 11)     # Amber

FONT_PATH_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_PATH_REGULAR = "C:/Windows/Fonts/malgun.ttf"

def get_font(size, is_bold=True):
    path = FONT_PATH_BOLD if is_bold else FONT_PATH_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    lines = []
    words = text.split(' ')
    current_line = []
    for word in words:
        current_line.append(word)
        test_str = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), test_str, font=font)
        w = bbox[2] - bbox[0]
        if w > max_width:
            current_line.pop()
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def draw_rounded_rectangle(draw, xy, corner_radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=corner_radius, fill=fill, outline=outline, width=width)

# ----------------------------------------------------
# 2. 고화질 세로 비디오 프레임 렌더러
# ----------------------------------------------------
def create_frame_image(data, is_answer_revealed=False, timer_progress=1.0):
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # 1) 그라데이션 배경
    for y in range(HEIGHT):
        r = int(COLOR_BG_START[0] + (COLOR_BG_END[0] - COLOR_BG_START[0]) * (y / HEIGHT))
        g = int(COLOR_BG_START[1] + (COLOR_BG_END[1] - COLOR_BG_START[1]) * (y / HEIGHT))
        b = int(COLOR_BG_START[2] + (COLOR_BG_END[2] - COLOR_BG_START[2]) * (y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # 2) 상단 브랜딩 뱃지
    draw_rounded_rectangle(draw, [100, 120, 980, 220], 50, fill=(37, 99, 235, 255))
    font_badge = get_font(42, is_bold=True)
    badge_text = f"⚡ 오늘의 1분 퀴즈 | {data['category']}"
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, 145), badge_text, fill=COLOR_TEXT_WHITE, font=font_badge)

    # 3) 질문 카드 (Question Card)
    draw_rounded_rectangle(draw, [80, 260, 1000, 680], 30, fill=(255, 255, 255, 245), outline=(226, 232, 240), width=3)
    font_q = get_font(44, is_bold=True)
    lines_q = wrap_text(data['question'], font_q, 840, draw)
    curr_y = 310
    for l in lines_q[:6]:
        draw.text((120, curr_y), l, fill=COLOR_TEXT_MAIN, font=font_q)
        curr_y += 60

    # 4) 타이머 프로그레스 바
    if not is_answer_revealed:
        draw_rounded_rectangle(draw, [80, 710, 1000, 730], 10, fill=(71, 85, 105, 255))
        bar_w = int(920 * timer_progress)
        if bar_w > 0:
            draw_rounded_rectangle(draw, [80, 710, 80 + bar_w, 730], 10, fill=COLOR_TIMER_BAR)

    # 5) 4지선다 보기 카드들
    opt_y = 760
    font_opt = get_font(38, is_bold=True)
    correct_idx = data['correct_option'] - 1

    for idx, opt in enumerate(data['options']):
        opt_rect = [80, opt_y, 1000, opt_y + 115]
        if is_answer_revealed and idx == correct_idx:
            draw_rounded_rectangle(draw, opt_rect, 20, fill=COLOR_SUCCESS_BG, outline=COLOR_SUCCESS_BORDER, width=4)
            opt_text = f"✅  {idx + 1}. {opt}"
            fill_color = COLOR_TEXT_WHITE
        else:
            draw_rounded_rectangle(draw, opt_rect, 20, fill=(241, 245, 249, 245), outline=(203, 213, 225), width=2)
            opt_text = f"{idx + 1}. {opt}"
            fill_color = (30, 41, 59)

        opt_lines = wrap_text(opt_text, font_opt, 860, draw)
        draw.text((120, opt_y + 35), opt_lines[0], fill=fill_color, font=font_opt)
        opt_y += 135

    # 6) 정답 해설 박스
    if is_answer_revealed and 'explanation' in data:
        draw_rounded_rectangle(draw, [80, 1340, 1000, 1580], 25, fill=(30, 41, 59, 240), outline=(59, 130, 246), width=3)
        font_exp_title = get_font(36, is_bold=True)
        draw.text((120, 1365), "💡 3초 핵심 포인트 해설", fill=(96, 165, 250), font=font_exp_title)
        font_exp_content = get_font(34, is_bold=False)
        exp_lines = wrap_text(data['explanation'], font_exp_content, 840, draw)
        ey = 1435
        for el in exp_lines[:2]:
            draw.text((120, ey), el, fill=COLOR_TEXT_WHITE, font=font_exp_content)
            ey += 50

    # 7) 하단 브랜드 CTA 풋터
    draw_rounded_rectangle(draw, [80, 1640, 1000, 1780], 35, fill=(37, 99, 235, 255), outline=(255, 255, 255), width=3)
    font_footer_main = get_font(42, is_bold=True)
    footer_text = "👉 풀버전 기출문제 풀기: cbtkorea.kr"
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer_main)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, 1690), footer_text, fill=COLOR_TEXT_WHITE, font=font_footer_main)

    return img

# ----------------------------------------------------
# 3. 오디오 시네마틱 효과음 & OpenAI / Edge / SAPI5 TTS 엔진
# ----------------------------------------------------
def create_silent_wav(output_file, duration_sec=5.0, sample_rate=44100):
    num_samples = int(duration_sec * sample_rate)
    with wave.open(output_file, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('<h', 0))

def generate_audio_file(text, output_file, duration_fallback=5.0, voice_type="onyx"):
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    # 1) OpenAI TTS API (If API Key Present in .env)
    if openai_key and len(openai_key) > 20 and not openai_key.startswith("your_"):
        try:
            import urllib.request
            req_data = json.dumps({
                "model": "tts-1-hd",
                "input": text,
                "voice": "nova" if voice_type == "female" else "onyx"
            }).encode('utf-8')
            
            req = urllib.request.Request(
                "https://api.openai.com/v1/audio/speech",
                data=req_data,
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req) as response:
                with open(output_file, 'wb') as f:
                    f.write(response.read())
            print(f"✨ High-Definition OpenAI TTS Audio Generated: {output_file}")
            return
        except Exception as e:
            print(f"OpenAI TTS call failed ({e}), trying fallback engines...")

    # 2) Edge-TTS Fallback
    try:
        import edge_tts
        async def _edge_gen():
            communicator = edge_tts.Communicate(text, "ko-KR-SunHiNeural")
            await communicator.save(output_file)
        asyncio.run(_edge_gen())
        if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
            print(f"🔊 Edge-TTS Audio Generated: {output_file}")
            return
    except Exception:
        pass

    # 3) Windows SAPI5 Offline Fallback
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        stream = win32com.client.Dispatch("SAPI.SpFileStream")
        wav_path = output_file.replace('.mp3', '.wav')
        stream.Open(wav_path, 3, False)
        speaker.AudioOutputStream = stream
        speaker.Speak(text)
        stream.Close()
        if os.path.exists(wav_path) and os.path.getsize(wav_path) > 100:
            os.replace(wav_path, output_file)
            print(f"🎙️ SAPI5 Audio Generated: {output_file}")
            return
    except Exception:
        pass

    # 4) Silent Fallback
    wav_path = output_file.replace('.mp3', '.wav')
    create_silent_wav(wav_path, duration_sec=duration_fallback)
    if os.path.exists(wav_path):
        os.replace(wav_path, output_file)

# ----------------------------------------------------
# 4. 파이프라인 메인 비디오 합성 함수
# ----------------------------------------------------
def build_shorts_video(quiz_data, output_mp4_path):
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_shorts")
    os.makedirs(temp_dir, exist_ok=True)

    # Audio 1: 질문 읽어주기
    q_speech_text = f"오늘의 {quiz_data['category']} 퀴즈! 3초 안에 맞혀보세요. 질문! {quiz_data['question']}"
    audio1_path = os.path.join(temp_dir, "q_audio.wav")
    generate_audio_file(q_speech_text, audio1_path, duration_fallback=6.0, voice_type="female")

    # Audio 2: 정답 및 해설 읽어주기
    a_speech_text = f"정답은 {quiz_data['correct_option']}번! {quiz_data['options'][quiz_data['correct_option']-1]} 입니다. {quiz_data.get('explanation', '')} 더 많은 기출문제는 CBT 코리아에서 풀어보세요!"
    audio2_path = os.path.join(temp_dir, "a_audio.wav")
    generate_audio_file(a_speech_text, audio2_path, duration_fallback=6.0, voice_type="male")

    audio1_clip = AudioFileClip(audio1_path)
    audio2_clip = AudioFileClip(audio2_path)

    q_duration = max(audio1_clip.duration + 0.3, 4.0)
    timer_duration = 2.0
    a_duration = max(audio2_clip.duration + 0.3, 5.0)

    # 1) 질문 클립
    img_q = create_frame_image(quiz_data, is_answer_revealed=False, timer_progress=1.0)
    img_q_path = os.path.join(temp_dir, "frame_q.png")
    img_q.save(img_q_path)
    clip_q = ImageClip(img_q_path).set_duration(q_duration).set_audio(audio1_clip)

    # 2) 카운트다운 타이머 클립
    timer_clips = []
    fps = 10
    total_timer_frames = int(timer_duration * fps)
    for i in range(total_timer_frames):
        prog = 1.0 - (i / total_timer_frames)
        img_t = create_frame_image(quiz_data, is_answer_revealed=False, timer_progress=prog)
        t_path = os.path.join(temp_dir, f"frame_t_{i}.png")
        img_t.save(t_path)
        clip_t = ImageClip(t_path).set_duration(1.0 / fps)
        timer_clips.append(clip_t)

    clip_timer = concatenate_videoclips(timer_clips)

    # 3) 정답 클립
    img_a = create_frame_image(quiz_data, is_answer_revealed=True, timer_progress=0.0)
    img_a_path = os.path.join(temp_dir, "frame_a.png")
    img_a.save(img_a_path)
    clip_a = ImageClip(img_a_path).set_duration(a_duration).set_audio(audio2_clip)

    final_clip = concatenate_videoclips([clip_q, clip_timer, clip_a])
    final_clip.write_videofile(
        output_mp4_path,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile=os.path.join(temp_dir, "temp-audio.m4a"),
        remove_temp=True
    )

    print(f"🎬 Successful 9:16 Shorts Video Created: {output_mp4_path}")

def run_sample_demo():
    output_dir = os.path.join(os.path.dirname(__file__), "shorts_output")
    os.makedirs(output_dir, exist_ok=True)

    sample_quizzes = [
        {
            "category": "전기기사",
            "question": "다음 중 앙페르의 오른나사 법칙에서 오른나사가 진행하는 방향이 뜻하는 것은 무엇일까요?",
            "options": ["전류의 방향", "자계의 방향", "전기장의 방향", "기전력의 방향"],
            "correct_option": 1,
            "explanation": "오른나사가 진행하는 방향은 전류의 방향이며, 나사를 회전시키는 방향이 자계의 방향입니다."
        },
        {
            "category": "컴퓨터활용능력 1급",
            "question": "다음 중 인터넷 IP 주소 체계인 IPv6에 대한 설명으로 옳은 것은 무엇일까요?",
            "options": ["16비트씩 8부분으로 구성된다", "8비트씩 4부분으로 구성된다", "32비트씩 4부분으로 구성된다", "64비트씩 2부분으로 구성된다"],
            "correct_option": 1,
            "explanation": "IPv6 주소는 16비트씩 8부분, 총 128비트로 구성되며 16진수로 표기합니다."
        },
        {
            "category": "한국사능력검정",
            "question": "조선 세종 대에 훈민정음을 창제한 목적과 가장 직접적인 관련이 깊은 기구는 무엇일까요?",
            "options": ["집현전", "규장각", "성균관", "홍문관"],
            "correct_option": 1,
            "explanation": "세종대왕은 학문 연구 기관인 집현전 학자들과 함께 훈민정음을 연구하고 창제하였습니다."
        }
    ]

    for idx, quiz in enumerate(sample_quizzes):
        out_file = os.path.join(output_dir, f"shorts_{quiz['category']}_{idx+1}.mp4")
        build_shorts_video(quiz, out_file)

if __name__ == '__main__':
    run_sample_demo()
