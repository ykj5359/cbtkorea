import os
import sys
import asyncio
import json
import random
import wave
import math
import struct
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
# 1. 2K 슈퍼샘플링 (2160x3840) 렌더링 -> 1080x1920 고화질 내보내기
# ----------------------------------------------------
RENDER_W = 2160
RENDER_H = 3840
FINAL_W = 1080
FINAL_H = 1920

# 럭셔리 네온 & 다크모드 컬러 펠리트
COLOR_BG_TOP = (15, 23, 42)         # #0F172A (Deep Slate)
COLOR_BG_BOTTOM = (30, 41, 59)      # #1E293B
COLOR_ACCENT_BLUE = (59, 130, 246)   # #3B82F6 Bright Blue
COLOR_ACCENT_PURPLE = (139, 92, 246) # #8B5CF6 Electric Purple
COLOR_CARD_BG = (255, 255, 255, 250)
COLOR_TEXT_MAIN = (15, 23, 42)
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_SUCCESS_BG = (16, 185, 129)    # Emerald Green
COLOR_SUCCESS_BORDER = (5, 150, 105)
COLOR_TIMER_BAR = (245, 158, 11)     # Amber

FONT_PATH_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_PATH_REGULAR = "C:/Windows/Fonts/malgun.ttf"

def get_font(size, is_bold=True):
    # 2K Supersample font size multiplier (2x)
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
    # Create an RGBA layer for smooth rounded corners and drop shadows
    draw = ImageDraw.Draw(base_img)
    x1, y1, x2, y2 = rect
    
    # Shadow layer
    shadow_img = Image.new('RGBA', (base_img.width, base_img.height), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_rect = [x1 + 10, y1 + 14, x2 + 10, y2 + 14]
    s_draw.rounded_rectangle(s_rect, radius=radius, fill=(0, 0, 0, 90))
    shadow_blur_img = shadow_img.filter(ImageFilter.GaussianBlur(shadow_blur))
    base_img.alpha_composite(shadow_blur_img)

    # Main Card
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=outline_width)

# ----------------------------------------------------
# 2. 2K 고해상도 비디오 프레임 렌더러
# ----------------------------------------------------
def create_frame_image_2k(data, is_answer_revealed=False, timer_progress=1.0):
    img = Image.new('RGBA', (RENDER_W, RENDER_H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # 1) 2K 그라데이션 배경
    for y in range(RENDER_H):
        r = int(COLOR_BG_TOP[0] + (COLOR_BG_BOTTOM[0] - COLOR_BG_TOP[0]) * (y / RENDER_H))
        g = int(COLOR_BG_TOP[1] + (COLOR_BG_BOTTOM[1] - COLOR_BG_TOP[1]) * (y / RENDER_H))
        b = int(COLOR_BG_TOP[2] + (COLOR_BG_BOTTOM[2] - COLOR_BG_TOP[2]) * (y / RENDER_H))
        draw.line([(0, y), (RENDER_W, y)], fill=(r, g, b, 255))

    # 장식용 네온 글로우 서클
    glow_img = Image.new('RGBA', (RENDER_W, RENDER_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_img)
    g_draw.ellipse([200, 300, 1960, 2060], fill=(59, 130, 246, 35))
    g_draw.ellipse([-200, 1800, 1500, 3500], fill=(139, 92, 246, 30))
    glow_blur = glow_img.filter(ImageFilter.GaussianBlur(120))
    img.alpha_composite(glow_blur)
    draw = ImageDraw.Draw(img)

    # 2) 상단 브랜딩 네온 뱃지
    badge_rect = [200, 240, 1960, 440]
    draw_rounded_rect_with_shadow(img, badge_rect, radius=100, fill=(37, 99, 235, 255), outline=(147, 197, 253), outline_width=6)
    font_badge = get_font(42, is_bold=True)
    badge_text = f"⚡ 오늘의 1분 퀴즈 | {data['category']}"
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    tw = bbox[2] - bbox[0]
    draw.text(((RENDER_W - tw) // 2, 290), badge_text, fill=COLOR_TEXT_WHITE, font=font_badge)

    # 3) 질문 메인 카드 (Question Card)
    q_card_rect = [160, 520, 2000, 1360]
    draw_rounded_rect_with_shadow(img, q_card_rect, radius=60, fill=(255, 255, 255, 248), outline=(226, 232, 240), outline_width=6)
    
    font_q = get_font(44, is_bold=True)
    lines_q = wrap_text(data['question'], font_q, 1680, draw)
    
    curr_y = 620
    for l in lines_q[:6]:
        draw.text((240, curr_y), l, fill=COLOR_TEXT_MAIN, font=font_q)
        curr_y += 120

    # 4) 타이머 프로그레스 바
    if not is_answer_revealed:
        timer_bg_rect = [160, 1420, 2000, 1460]
        draw.rounded_rectangle(timer_bg_rect, radius=20, fill=(71, 85, 105, 255))
        bar_w = int(1840 * timer_progress)
        if bar_w > 0:
            timer_bar_rect = [160, 1420, 160 + bar_w, 1460]
            draw.rounded_rectangle(timer_bar_rect, radius=20, fill=COLOR_TIMER_BAR)

    # 5) 4지선다 보기 카드들 (Options)
    opt_y = 1520
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

    # 6) 정답 해설 박스
    if is_answer_revealed and 'explanation' in data:
        exp_rect = [160, 2680, 2000, 3160]
        draw_rounded_rect_with_shadow(img, exp_rect, radius=50, fill=(30, 41, 59, 245), outline=(96, 165, 250), outline_width=6)
        
        font_exp_title = get_font(36, is_bold=True)
        draw.text((240, 2730), "💡 3초 핵심 포인트 해설", fill=(96, 165, 250), font=font_exp_title)
        
        font_exp_content = get_font(34, is_bold=False)
        exp_lines = wrap_text(data['explanation'], font_exp_content, 1680, draw)
        ey = 2870
        for el in exp_lines[:2]:
            draw.text((240, ey), el, fill=COLOR_TEXT_WHITE, font=font_exp_content)
            ey += 100

    # 7) 하단 브랜드 CTA 풋터
    footer_rect = [160, 3280, 2000, 3560]
    draw_rounded_rect_with_shadow(img, footer_rect, radius=70, fill=(37, 99, 235, 255), outline=(255, 255, 255), outline_width=6)
    
    font_footer_main = get_font(42, is_bold=True)
    footer_text = "👉 풀버전 기출문제 풀기: cbtkorea.kr"
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer_main)
    tw = bbox[2] - bbox[0]
    draw.text(((RENDER_W - tw) // 2, 3380), footer_text, fill=COLOR_TEXT_WHITE, font=font_footer_main)

    # 2K 슈퍼샘플링 ➔ 1080x1920 고화질 리사이즈 (LANCZOS 필터로 안티앨리어싱 극대화)
    img_final = img.resize((FINAL_W, FINAL_H), Image.LANCZOS)
    return img_final

# ----------------------------------------------------
# 3. 다양한 OpenAI AI 성우 목소리 선택 지원 (Voice Selector)
# ----------------------------------------------------
# 지원되는 OpenAI 음성 종류:
# - 'shimmer': 명확하고 또렷한 아나운서 여성 목소리 (기본 질문용 추천)
# - 'nova': 활기차고 에너지 넘치는 여성 목소리
# - 'alloy': 신뢰감 있고 친근한 중성/여성 톤
# - 'echo': 부드럽고 깔끔한 남성 크리에이터 톤 (정답/해설용 추천)
# - 'onyx': 묵직하고 차분한 중저음 남성 아나운서
# - 'fable': 지적이고 안정적인 톤

def generate_audio_file(text, output_file, voice="shimmer", duration_fallback=5.0):
    openai_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_AI_API_KEY")
    
    if openai_key and len(openai_key) > 20 and not openai_key.startswith("your_"):
        try:
            import urllib.request
            req_data = json.dumps({
                "model": "tts-1-hd",
                "input": text,
                "voice": voice
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
            print(f"✨ OpenAI HD Voice [{voice}] Audio Generated: {output_file}")
            return
        except Exception as e:
            print(f"OpenAI TTS call failed ({e}), trying fallback engines...")

    # Edge-TTS Fallback
    try:
        import edge_tts
        async def _edge_gen():
            communicator = edge_tts.Communicate(text, "ko-KR-SunHiNeural")
            await communicator.save(output_file)
        asyncio.run(_edge_gen())
        if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
            return
    except Exception:
        pass

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
        if os.path.exists(wav_path) and os.path.getsize(wav_path) > 100:
            os.replace(wav_path, output_file)
            return
    except Exception:
        pass

# ----------------------------------------------------
# 4. 고화질 (12Mbps Bitrate) 비디오 렌더링
# ----------------------------------------------------
def build_shorts_video(quiz_data, output_mp4_path, voice_question="shimmer", voice_answer="echo"):
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_shorts")
    os.makedirs(temp_dir, exist_ok=True)

    # Audio 1: 질문
    q_speech_text = f"오늘의 {quiz_data['category']} 퀴즈! 3초 안에 맞혀보세요. 질문! {quiz_data['question']}"
    audio1_path = os.path.join(temp_dir, "q_audio.wav")
    generate_audio_file(q_speech_text, audio1_path, voice=voice_question, duration_fallback=6.0)

    # Audio 2: 정답 및 해설
    a_speech_text = f"정답은 {quiz_data['correct_option']}번! {quiz_data['options'][quiz_data['correct_option']-1]} 입니다. {quiz_data.get('explanation', '')} 더 많은 기출문제는 CBT 코리아에서 풀어보세요!"
    audio2_path = os.path.join(temp_dir, "a_audio.wav")
    generate_audio_file(a_speech_text, audio2_path, voice=voice_answer, duration_fallback=6.0)

    audio1_clip = AudioFileClip(audio1_path)
    audio2_clip = AudioFileClip(audio2_path)

    q_duration = max(audio1_clip.duration + 0.3, 4.0)
    timer_duration = 2.0
    a_duration = max(audio2_clip.duration + 0.3, 5.0)

    # 1) 질문 2K 슈퍼샘플링 프레임
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

    # 3) 정답 프레임
    img_a = create_frame_image_2k(quiz_data, is_answer_revealed=True, timer_progress=0.0)
    img_a_path = os.path.join(temp_dir, "frame_a.png")
    img_a.save(img_a_path, quality=95)
    clip_a = ImageClip(img_a_path).set_duration(a_duration).set_audio(audio2_clip)

    final_clip = concatenate_videoclips([clip_q, clip_timer, clip_a])
    
    # 12Mbps 고비트레이트 내보내기 (화질 뭉개짐 방지)
    final_clip.write_videofile(
        output_mp4_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        bitrate="12000k",
        temp_audiofile=os.path.join(temp_dir, f"temp-audio-{random.randint(1000, 9999)}.m4a"),
        remove_temp=False
    )

    print(f"🎬 PRO 2K High-Bitrate Shorts Video Created: {output_mp4_path}")

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

    # 각각 다른 목소리 조합으로 테스트 생성
    voices = [
        ("shimmer", "echo"),   # 여성 아나운서 + 남성 크리에이터 (추천 1위)
        ("nova", "onyx"),      # 에너제틱 여성 + 중저음 남성
        ("alloy", "fable")     # 친근한 톤 + 지적인 톤
    ]

    for idx, quiz in enumerate(sample_quizzes):
        v_q, v_a = voices[idx % len(voices)]
        out_file = os.path.join(output_dir, f"shorts_{quiz['category']}_PRO_{v_q}_{v_a}.mp4")
        print(f"🎥 Rendering 2K Supersampled Shorts Video [{idx+1}/3] ({v_q} / {v_a})...")
        build_shorts_video(quiz, out_file, voice_question=v_q, voice_answer=v_a)

if __name__ == '__main__':
    run_sample_demo()
