import os
import sys
import asyncio
import json
import random
import wave
import math
import struct
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ----------------------------------------------------
# 0. aiohttp ThreadedResolver Monkey-Patch (Edge-TTS 1순위 보장)
# ----------------------------------------------------
import aiohttp
import aiohttp.resolver
_old_tcp_init = aiohttp.TCPConnector.__init__
def _new_tcp_init(self, *args, **kwargs):
    kwargs['resolver'] = aiohttp.ThreadedResolver()
    _old_tcp_init(self, *args, **kwargs)
aiohttp.TCPConnector.__init__ = _new_tcp_init

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
# 1. 2K 슈퍼샘플링 (2160x3840) PRO 렌더링 시스템
# ----------------------------------------------------
RENDER_W = 2160
RENDER_H = 3840
FINAL_W = 1080
FINAL_H = 1920

COLOR_BG_TOP = (15, 23, 42)         # Deep Slate (#0F172A)
COLOR_BG_BOTTOM = (30, 41, 59)      # Slate Blue (#1E293B)
COLOR_TEXT_MAIN = (15, 23, 42)
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_SUCCESS_BG = (16, 185, 129)    # Emerald Green
COLOR_SUCCESS_BORDER = (5, 150, 105)
COLOR_TIMER_BAR = (245, 158, 11)     # Amber
COLOR_QNET_BLUE = (37, 99, 235)      # Q-Net Blue

FONT_PATH_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_PATH_REGULAR = "C:/Windows/Fonts/malgun.ttf"

def get_font(size, is_bold=True):
    render_size = int(size * 2)
    path = FONT_PATH_BOLD if is_bold else FONT_PATH_REGULAR
    try:
        return ImageFont.truetype(path, render_size)
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

def draw_rounded_rect_with_shadow(base_img, rect, radius, fill, outline=None, outline_width=2, shadow_blur=20):
    draw = ImageDraw.Draw(base_img)
    x1, y1, x2, y2 = rect
    
    # Shadow
    shadow_img = Image.new('RGBA', (base_img.width, base_img.height), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_rect = [x1 + 10, y1 + 14, x2 + 10, y2 + 14]
    s_draw.rounded_rectangle(s_rect, radius=radius, fill=(0, 0, 0, 90))
    shadow_blur_img = shadow_img.filter(ImageFilter.GaussianBlur(shadow_blur))
    base_img.alpha_composite(shadow_blur_img)

    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=outline_width)

# ----------------------------------------------------
# 2. 2K 고해상도 비디오 프레임 렌더러 (Q-Net 시험장 안내 뱃지 추가)
# ----------------------------------------------------
def create_frame_image_2k(data, is_answer_revealed=False, timer_progress=1.0):
    img = Image.new('RGBA', (RENDER_W, RENDER_H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # 1) 그라데이션 배경
    for y in range(RENDER_H):
        r = int(COLOR_BG_TOP[0] + (COLOR_BG_BOTTOM[0] - COLOR_BG_TOP[0]) * (y / RENDER_H))
        g = int(COLOR_BG_TOP[1] + (COLOR_BG_BOTTOM[1] - COLOR_BG_TOP[1]) * (y / RENDER_H))
        b = int(COLOR_BG_TOP[2] + (COLOR_BG_BOTTOM[2] - COLOR_BG_TOP[2]) * (y / RENDER_H))
        draw.line([(0, y), (RENDER_W, y)], fill=(r, g, b, 255))

    # 글로우 서클 효과
    glow_img = Image.new('RGBA', (RENDER_W, RENDER_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_img)
    g_draw.ellipse([200, 300, 1960, 2060], fill=(59, 130, 246, 35))
    g_draw.ellipse([-200, 1800, 1500, 3500], fill=(139, 92, 246, 30))
    glow_blur = glow_img.filter(ImageFilter.GaussianBlur(120))
    img.alpha_composite(glow_blur)
    draw = ImageDraw.Draw(img)

    # 2) 상단 브랜딩 네온 뱃지
    badge_rect = [160, 220, 2000, 420]
    draw_rounded_rect_with_shadow(img, badge_rect, radius=100, fill=(37, 99, 235, 255), outline=(147, 197, 253), outline_width=6)
    font_badge = get_font(40, is_bold=True)
    badge_text = f"⚡ 오늘의 1분 퀴즈 | {data['category']}"
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    tw = bbox[2] - bbox[0]
    draw.text(((RENDER_W - tw) // 2, 270), badge_text, fill=COLOR_TEXT_WHITE, font=font_badge)

    # 3) 질문 메인 카드 (Question Card)
    q_card_rect = [160, 480, 2000, 1320]
    draw_rounded_rect_with_shadow(img, q_card_rect, radius=60, fill=(255, 255, 255, 248), outline=(226, 232, 240), outline_width=6)
    
    font_q = get_font(44, is_bold=True)
    lines_q = wrap_text(data['question'], font_q, 1680, draw)
    curr_y = 580
    for l in lines_q[:6]:
        draw.text((240, curr_y), l, fill=COLOR_TEXT_MAIN, font=font_q)
        curr_y += 120

    # 4) 타이머 프로그레스 바
    if not is_answer_revealed:
        timer_bg_rect = [160, 1380, 2000, 1420]
        draw.rounded_rectangle(timer_bg_rect, radius=20, fill=(71, 85, 105, 255))
        bar_w = int(1840 * timer_progress)
        if bar_w > 0:
            timer_bar_rect = [160, 1380, 160 + bar_w, 1420]
            draw.rounded_rectangle(timer_bar_rect, radius=20, fill=COLOR_TIMER_BAR)

    # 5) 4지선다 보기 카드들 (Options)
    opt_y = 1480
    font_opt = get_font(38, is_bold=True)
    correct_idx = data['correct_option'] - 1

    for idx, opt in enumerate(data['options']):
        opt_rect = [160, opt_y, 2000, opt_y + 230]
        if is_answer_revealed and idx == correct_idx:
            draw_rounded_rect_with_shadow(img, opt_rect, radius=40, fill=COLOR_SUCCESS_BG, outline=(167, 243, 208), outline_width=8)
            opt_text = f"✅  {idx + 1}. {opt}"
            fill_color = COLOR_TEXT_WHITE
        else:
            draw_rounded_rect_with_shadow(img, opt_rect, radius=40, fill=(241, 245, 249, 248), outline=(203, 213, 225), outline_width=4)
            opt_text = f"{idx + 1}. {opt}"
            fill_color = (30, 41, 59)

        opt_lines = wrap_text(opt_text, font_opt, 1700, draw)
        draw.text((240, opt_y + 70), opt_lines[0], fill=fill_color, font=font_opt)
        opt_y += 270

    # 6) 정답 해설 및 Q-Net 시험장 시뮬레이터 강조 박스
    if is_answer_revealed:
        # Q-Net 실전 시험장 구현 안내 카드
        qnet_rect = [160, 2600, 2000, 3160]
        draw_rounded_rect_with_shadow(img, qnet_rect, radius=50, fill=(30, 41, 59, 250), outline=(59, 130, 246), outline_width=6)
        
        font_qnet_header = get_font(38, is_bold=True)
        draw.text((240, 2650), "🎯 실제 Q-Net 시험장 양식 100% 동일 구현!", fill=(251, 191, 36), font=font_qnet_header)
        
        font_qnet_sub = get_font(34, is_bold=False)
        draw.text((240, 2750), "시험 전 필수! cbtkorea.kr 에서 실제 수험자 확인 및", fill=COLOR_TEXT_WHITE, font=font_qnet_sub)
        draw.text((240, 2830), "2분할 실전 모의시험(뀨-Net CBT)을 꼭 무료로 테스트해보세요!", fill=(147, 197, 253), font=font_qnet_sub)

        font_exp = get_font(32, is_bold=False)
        if 'explanation' in data:
            exp_lines = wrap_text(f"💡 [해설] {data['explanation']}", font_exp, 1680, draw)
            draw.text((240, 2950), exp_lines[0], fill=(226, 232, 240), font=font_exp)

    # 7) 하단 브랜드 CTA 풋터
    footer_rect = [160, 3280, 2000, 3560]
    draw_rounded_rect_with_shadow(img, footer_rect, radius=70, fill=(37, 99, 235, 255), outline=(255, 255, 255), outline_width=6)
    
    font_footer_main = get_font(42, is_bold=True)
    footer_text = "👉 Q-Net 양식 무료 실전 테스트: cbtkorea.kr"
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer_main)
    tw = bbox[2] - bbox[0]
    draw.text(((RENDER_W - tw) // 2, 3380), footer_text, fill=COLOR_TEXT_WHITE, font=font_footer_main)

    img_final = img.resize((FINAL_W, FINAL_H), Image.LANCZOS)
    return img_final

# ----------------------------------------------------
# 3. Microsoft Edge-TTS 1순위 아나운서 음성 엔진 (ThreadedResolver)
# ----------------------------------------------------
def generate_audio_file_edge(text, output_file, voice="ko-KR-SunHiNeural", duration_fallback=6.0):
    # 1순위: Microsoft Edge-TTS
    try:
        import edge_tts
        async def _edge_gen():
            communicator = edge_tts.Communicate(text, voice)
            await communicator.save(output_file)
        asyncio.run(_edge_gen())
        if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
            print(f"🔊 Edge-TTS [{voice}] Audio Generated: {output_file}")
            return
    except Exception as e:
        print(f"Edge-TTS failed ({e}), trying fallback engines...")

    # 2순위: OpenAI TTS Fallback (If API Key Available)
    openai_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_AI_API_KEY")
    if openai_key and len(openai_key) > 20 and not openai_key.startswith("your_"):
        try:
            import urllib.request
            req_data = json.dumps({
                "model": "tts-1-hd",
                "input": text,
                "voice": "nova" if "SunHi" in voice else "onyx"
            }).encode('utf-8')
            req = urllib.request.Request(
                "https://api.openai.com/v1/audio/speech",
                data=req_data,
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                with open(output_file, 'wb') as f:
                    f.write(response.read())
            print(f"✨ OpenAI HD Voice Audio Generated: {output_file}")
            return
        except Exception:
            pass

    # 3순위: Windows SAPI5 Offline Fallback
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
            return
    except Exception:
        pass

# ----------------------------------------------------
# 4. 파이프라인 메인 비디오 합성 함수 (Q-Net 시험장 안내 멘트 포함)
# ----------------------------------------------------
def build_shorts_video(quiz_data, output_mp4_path, voice_question="ko-KR-SunHiNeural", voice_answer="ko-KR-InJoonNeural"):
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_shorts")
    os.makedirs(temp_dir, exist_ok=True)

    # Audio 1: 질문
    q_speech_text = f"오늘의 {quiz_data['category']} 퀴즈! 3초 안에 맞혀보세요. 질문! {quiz_data['question']}"
    audio1_path = os.path.join(temp_dir, "q_audio.wav")
    generate_audio_file_edge(q_speech_text, audio1_path, voice=voice_question, duration_fallback=6.0)

    # Audio 2: 정답 및 Q-Net 실전 시험장 양식 모의고사 추천 멘트
    a_speech_text = (
        f"정답은 {quiz_data['correct_option']}번! {quiz_data['options'][quiz_data['correct_option']-1]} 입니다. "
        f"잠깐! 시험 보기 전 필수! CBT 코리아에는 실제 Q-Net 시험장 화면과 100% 동일하게 구현된 "
        f"모의시험 시뮬레이터가 있으니, 실전 시험 보기 전 cbtkorea.kr 에서 꼭 무료로 테스트해 보세요!"
    )
    audio2_path = os.path.join(temp_dir, "a_audio.wav")
    generate_audio_file_edge(a_speech_text, audio2_path, voice=voice_answer, duration_fallback=8.0)

    audio1_clip = AudioFileClip(audio1_path)
    audio2_clip = AudioFileClip(audio2_path)

    q_duration = max(audio1_clip.duration + 0.3, 4.0)
    timer_duration = 2.0
    a_duration = max(audio2_clip.duration + 0.3, 7.0)

    # 1) 질문 프레임
    img_q = create_frame_image_2k(quiz_data, is_answer_revealed=False, timer_progress=1.0)
    img_q_path = os.path.join(temp_dir, "frame_q.png")
    img_q.save(img_q_path, quality=95)
    clip_q = ImageClip(img_q_path).set_duration(q_duration).set_audio(audio1_clip)

    # 2) 카운트다운 프레임
    timer_clips = []
    fps = 10
    total_timer_frames = int(timer_duration * fps)
    for i in range(total_timer_frames):
        prog = 1.0 - (i / total_timer_frames)
        img_t = create_frame_image_2k(quiz_data, is_answer_revealed=False, timer_progress=prog)
        t_path = os.path.join(temp_dir, f"frame_t_{i}.png")
        img_t.save(t_path, quality=95)
        clip_t = ImageClip(t_path).set_duration(1.0 / fps)
        timer_clips.append(clip_t)

    clip_timer = concatenate_videoclips(timer_clips)

    # 3) 정답 & Q-Net 시험장 구현 안내 프레임
    img_a = create_frame_image_2k(quiz_data, is_answer_revealed=True, timer_progress=0.0)
    img_a_path = os.path.join(temp_dir, "frame_a.png")
    img_a.save(img_a_path, quality=95)
    clip_a = ImageClip(img_a_path).set_duration(a_duration).set_audio(audio2_clip)

    final_clip = concatenate_videoclips([clip_q, clip_timer, clip_a])
    
    # 12Mbps 고비트레이트 내보내기 (Windows 파일 잠금 예외 방지)
    rnd_id = random.randint(1000, 9999)
    final_clip.write_videofile(
        output_mp4_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        bitrate="12000k",
        temp_audiofile=os.path.join(temp_dir, f"temp-audio-{rnd_id}.m4a"),
        remove_temp=False
    )

    print(f"🎬 Edge-TTS PRO Shorts Video Created: {output_mp4_path}")

def run_sample_demo():
    output_dir = os.path.join(os.path.dirname(__file__), "shorts_output")
    os.makedirs(output_dir, exist_ok=True)

    sample_quizzes = [
        {
            "category": "건설기계설비기사",
            "question": "다음 중 재료역학에서 단면의 2차 모멘트 단위를 올바르게 나타낸 것은 무엇일까요?",
            "options": ["mm⁴", "mm³", "N/mm²", "N·m"],
            "correct_option": 1,
            "explanation": "단면 2차 모멘트(I)의 단위는 길이의 4제곱인 mm⁴ 또는 m⁴로 나타냅니다."
        },
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
        }
    ]

    for idx, quiz in enumerate(sample_quizzes):
        out_file = os.path.join(output_dir, f"shorts_{quiz['category']}_QNET_EdgeTTS.mp4")
        print(f"🎥 Rendering Edge-TTS Q-Net Shorts Video [{idx+1}/3]: {quiz['category']}...")
        build_shorts_video(quiz, out_file, voice_question="ko-KR-SunHiNeural", voice_answer="ko-KR-InJoonNeural")

if __name__ == '__main__':
    run_sample_demo()
