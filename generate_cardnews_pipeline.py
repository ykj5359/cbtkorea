import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------
# 1080x1080 카드뉴스 인스타그램 / 스레드 / 블로그용 디자인
# ----------------------------------------------------
CARD_WIDTH = 1080
CARD_HEIGHT = 1080

COLOR_BG_START = (15, 23, 42)        # Deep Slate Navy
COLOR_BG_END = (30, 41, 59)          # Slate Blue
COLOR_TEXT_MAIN = (15, 23, 42)
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_ACCENT_BLUE = (37, 99, 235)
COLOR_SUCCESS_BG = (16, 185, 129)
COLOR_SUCCESS_BORDER = (5, 150, 105)

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

def create_card_background():
    img = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    for y in range(CARD_HEIGHT):
        r = int(COLOR_BG_START[0] + (COLOR_BG_END[0] - COLOR_BG_START[0]) * (y / CARD_HEIGHT))
        g = int(COLOR_BG_START[1] + (COLOR_BG_END[1] - COLOR_BG_START[1]) * (y / CARD_HEIGHT))
        b = int(COLOR_BG_START[2] + (COLOR_BG_END[2] - COLOR_BG_START[2]) * (y / CARD_HEIGHT))
        draw.line([(0, y), (CARD_WIDTH, y)], fill=(r, g, b, 255))
    return img, draw

# ----------------------------------------------------
# 슬라이드 1: 문제 카드 (Card 1)
# ----------------------------------------------------
def build_card_1(quiz_data):
    img, draw = create_card_background()
    
    # 뱃지
    draw.rounded_rectangle([70, 70, 1010, 160], radius=40, fill=(37, 99, 235, 255))
    font_badge = get_font(38, is_bold=True)
    btext = f"⚡ 오늘의 1분 퀴즈 | {quiz_data['category']} (1/3)"
    bbox = draw.textbbox((0, 0), btext, font=font_badge)
    draw.text(((CARD_WIDTH - (bbox[2] - bbox[0])) // 2, 95), btext, fill=COLOR_TEXT_WHITE, font=font_badge)

    # 문제 박스
    draw.rounded_rectangle([70, 200, 1010, 880], radius=30, fill=(255, 255, 255, 245), outline=(226, 232, 240), width=3)
    font_q = get_font(42, is_bold=True)
    lines_q = wrap_text(quiz_data['question'], font_q, 860, draw)
    
    cy = 260
    for l in lines_q:
        draw.text((110, cy), l, fill=COLOR_TEXT_MAIN, font=font_q)
        cy += 60

    # 하단 힌트 안내
    font_sub = get_font(34, is_bold=True)
    stext = "👉 다음 장을 넘겨 정답과 해설을 확인하세요!"
    bbox = draw.textbbox((0, 0), stext, font=font_sub)
    draw.text(((CARD_WIDTH - (bbox[2] - bbox[0])) // 2, 940), stext, fill=(148, 163, 184), font=font_sub)

    return img

# ----------------------------------------------------
# 슬라이드 2: 4지선다 보기 카드 (Card 2)
# ----------------------------------------------------
def build_card_2(quiz_data):
    img, draw = create_card_background()
    
    # 뱃지
    draw.rounded_rectangle([70, 70, 1010, 160], radius=40, fill=(37, 99, 235, 255))
    font_badge = get_font(38, is_bold=True)
    btext = f"⚡ {quiz_data['category']} 4지선다 보기 (2/3)"
    bbox = draw.textbbox((0, 0), btext, font=font_badge)
    draw.text(((CARD_WIDTH - (bbox[2] - bbox[0])) // 2, 95), btext, fill=COLOR_TEXT_WHITE, font=font_badge)

    # 4지선다 카드들
    font_opt = get_font(36, is_bold=True)
    opt_y = 210
    for idx, opt in enumerate(quiz_data['options']):
        draw.rounded_rectangle([70, opt_y, 1010, opt_y + 140], radius=20, fill=(241, 245, 249, 245), outline=(203, 213, 225), width=2)
        otext = f"{idx + 1}. {opt}"
        draw.text((110, opt_y + 45), otext, fill=(30, 41, 59), font=font_opt)
        opt_y += 165

    # 풋터
    font_sub = get_font(34, is_bold=True)
    stext = "⏱️ 몇 번이 정답일까요? 3초 생각 후 다음 장 클릭!"
    bbox = draw.textbbox((0, 0), stext, font=font_sub)
    draw.text(((CARD_WIDTH - (bbox[2] - bbox[0])) // 2, 935), stext, fill=(251, 191, 36), font=font_sub)

    return img

# ----------------------------------------------------
# 슬라이드 3: 정답 및 해설 + CTA 카드 (Card 3)
# ----------------------------------------------------
def build_card_3(quiz_data):
    img, draw = create_card_background()
    
    # 뱃지
    draw.rounded_rectangle([70, 70, 1010, 160], radius=40, fill=COLOR_SUCCESS_BG)
    font_badge = get_font(38, is_bold=True)
    correct_text = quiz_data['options'][quiz_data['correct_option'] - 1]
    btext = f"✅ 정답: {quiz_data['correct_option']}번 ({correct_text}) (3/3)"
    bbox = draw.textbbox((0, 0), btext, font=font_badge)
    draw.text(((CARD_WIDTH - (bbox[2] - bbox[0])) // 2, 95), btext, fill=COLOR_TEXT_WHITE, font=font_badge)

    # 해설 박스
    draw.rounded_rectangle([70, 200, 1010, 760], radius=30, fill=(30, 41, 59, 245), outline=(59, 130, 246), width=3)
    font_title = get_font(40, is_bold=True)
    draw.text((110, 240), "💡 3초 핵심 포인트 해설", fill=(96, 165, 250), font=font_title)
    
    font_exp = get_font(36, is_bold=False)
    lines_exp = wrap_text(quiz_data.get('explanation', ''), font_exp, 840, draw)
    ey = 330
    for el in lines_exp:
        draw.text((110, ey), el, fill=COLOR_TEXT_WHITE, font=font_exp)
        ey += 55

    # 하단 브랜드 CTA 풋터
    draw.rounded_rectangle([70, 830, 1010, 970], radius=35, fill=(37, 99, 235, 255), outline=(255, 255, 255), width=3)
    font_footer = get_font(42, is_bold=True)
    ftext = "👉 풀버전 기출문제 풀기: cbtkorea.kr"
    bbox = draw.textbbox((0, 0), ftext, font=font_footer)
    draw.text(((CARD_WIDTH - (bbox[2] - bbox[0])) // 2, 880), ftext, fill=COLOR_TEXT_WHITE, font=font_footer)

    return img

# ----------------------------------------------------
# 메인 카드뉴스 세트 자동 생성 함수
# ----------------------------------------------------
def generate_cardnews_set(quiz_data, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    cat_clean = quiz_data['category'].replace(' ', '_')

    # Card 1
    c1 = build_card_1(quiz_data)
    c1_path = os.path.join(output_folder, f"card_{cat_clean}_1_problem.png")
    c1.save(c1_path)

    # Card 2
    c2 = build_card_2(quiz_data)
    c2_path = os.path.join(output_folder, f"card_{cat_clean}_2_choices.png")
    c2.save(c2_path)

    # Card 3
    c3 = build_card_3(quiz_data)
    c3_path = os.path.join(output_folder, f"card_{cat_clean}_3_answer.png")
    c3.save(c3_path)

    print(f"✅ Cardnews 3-Slide Set Created in: {output_folder}")

def run_cardnews_demo():
    out_dir = os.path.join(os.path.dirname(__file__), "cardnews_output")
    
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

    for quiz in sample_quizzes:
        q_folder = os.path.join(out_dir, quiz['category'].replace(' ', '_'))
        generate_cardnews_set(quiz, q_folder)

if __name__ == '__main__':
    run_cardnews_demo()
