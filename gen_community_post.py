# -*- coding: utf-8 -*-
"""
gen_community_post.py — CBT 기출문제 커뮤니티 '운영자 글' 자동 생성기
============================================================
정적 사이트용. 운영자 명의의 '유용한 글'을 매일 1개 생성해
cbt-community-feed.js 의 window.CBT_OPS_POSTS 배열에 추가한다.
(모든 방문자에게 보이는 씨앗 글 = community.html 이 이 파일을 읽어 병합)

사용법:
    python gen_community_post.py                # 오늘자 글 1개 추가 (매일 실행)
    python gen_community_post.py --backfill 14  # 최근 14일치 글 채우기 (최초 1회)

특징:
    · 같은 날짜 글이 이미 있으면 건너뜀(중복 방지) → 매일 자동실행 안전
    · 최대 60개 유지(오래된 글 자동 정리)
    · 실제 시험 대비에 도움되는 진짜 콘텐츠 (가짜 잡담 X)
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import random
import re
from pathlib import Path

FEED_FILE = Path(r"E:\00.CBT\cbt-community-feed.js")
COMMUNITY_HTML = Path(r"E:\00.CBT\community.html")
MAX_POSTS = 60


def bump_feed_version(date: dt.date) -> None:
    """community.html 의 cbt-community-feed.js?v=... 를 그날 날짜로 갱신 → 캐시 무효화"""
    if not COMMUNITY_HTML.exists():
        return
    txt = COMMUNITY_HTML.read_bytes().decode("utf-8")
    ver = date.strftime("%Y%m%d")
    new = re.sub(r'cbt-community-feed\.js(?:\?v=[^"]*)?', f'cbt-community-feed.js?v={ver}', txt)
    if new != txt:
        COMMUNITY_HTML.write_bytes(new.encode("utf-8"))

CERTS = [
    "정보처리기사", "정보처리산업기사", "정보처리기능사", "전기기사", "전기산업기사",
    "전기기능사", "산업안전기사", "산업안전산업기사", "건축기사", "토목기사",
    "공조냉동기계기사", "위험물산업기사", "위험물기능사", "소방설비기사(전기분야)",
    "소방설비기사(기계분야)", "지게차운전기능사", "굴삭기운전기능사", "한식조리기능사",
    "제과기능사", "제빵기능사", "미용사(일반)", "미용사(네일)", "컴퓨터활용능력 1급",
    "컴퓨터활용능력 2급", "전산세무 2급", "전산회계 1급", "사회조사분석사 2급",
    "직업상담사 2급", "화학분석기사", "환경기능사", "품질경영기사", "가스기능사",
    "용접기능사", "조경기능사", "공인중개사 1차", "한국사능력검정시험 심화",
]

# 각 템플릿: (tag, 제목함수, 본문함수)  — cert 는 필요 시 사용
TEMPLATES = [
    ("study",
     lambda c, d: f"{c} 필기, 남은 기간 이렇게 공부하세요 (단계별 플랜)",
     lambda c, d: (
        f"{c} 필기 준비하시는 분들을 위한 단계별 학습 플랜을 정리했습니다.\n\n"
        "1단계 (전체 1회독): 개념을 완벽히 이해하려 하지 말고, 과목별로 어떤 내용이 나오는지 '지도'를 그린다는 느낌으로 빠르게 훑습니다.\n"
        "2단계 (기출 회독): 이 사이트의 기출문제를 최신 회차부터 3~5개년 풀어봅니다. 문제를 푸는 것보다 '왜 틀렸는지'를 아는 게 핵심입니다.\n"
        "3단계 (오답 집중): 채점하기 버튼으로 채점하면 틀린 문제가 마이페이지 오답노트에 자동 저장됩니다. 시험 3일 전에는 오답노트만 반복하세요.\n\n"
        "기출은 반드시 반복 출제됩니다. 하루 30문제씩만 꾸준히 풀어도 합격선은 충분히 넘습니다. 화이팅입니다!"
     )),
    ("share",
     lambda c, d: f"{c} 자주 나오는 빈출 포인트 정리 (합격 필수)",
     lambda c, d: (
        f"{c} 기출을 분석해 보면 매년 반복되는 빈출 포인트가 분명히 있습니다.\n\n"
        "· 최근 5개년에서 2번 이상 나온 개념은 '무조건' 정리하세요.\n"
        "· 계산 문제는 공식을 외우기보다 기출 3~4문제를 반복해 풀이 흐름을 손에 익히는 게 빠릅니다.\n"
        "· 헷갈리는 보기는 체크(북마크) 버튼으로 저장해 두고 시험 전날 몰아서 봅니다.\n\n"
        "이 사이트 기출문제에서 정답·해설 버튼을 함께 활용하면 개념 정리가 훨씬 빨라집니다. 여러분의 합격을 응원합니다."
     )),
    ("notice",
     lambda c, d: f"[안내] {c} 시험, 이렇게 준비하면 됩니다 (일정·합격기준)",
     lambda c, d: (
        f"{c} 응시를 준비하시는 분들을 위한 기본 안내입니다.\n\n"
        "· 합격 기준: 대부분의 국가기술자격 필기는 과목당 40점 이상, 전 과목 평균 60점 이상이면 합격입니다.\n"
        "· 정확한 시험 일정과 응시료는 큐넷(q-net.or.kr) 공식 공지를 확인하세요.\n"
        "· 이 사이트에서는 실제 CBT와 유사한 환경으로 미리 연습할 수 있습니다. 상단 메뉴 '뀨-Net CBT'에서 종목을 선택해 응시해 보세요.\n\n"
        "준비 기간이 짧아도 기출 중심으로 전략적으로 공부하면 충분히 합격할 수 있습니다."
     )),
    ("study",
     lambda c, d: "오답노트 200% 활용법 — 틀린 문제가 자동으로 정리됩니다",
     lambda c, d: (
        "많은 분들이 놓치는 이 사이트의 핵심 기능, 오답노트 사용법을 안내합니다.\n\n"
        "1. 로그인 후 기출문제를 풉니다.\n"
        "2. 하단의 '채점하기' 버튼을 누르면 점수와 함께 틀린 문제가 마이페이지 > 오답노트에 자동 저장됩니다.\n"
        "3. 같은 문제를 또 틀리면 '몇 회 틀림'으로 표시돼, 내 약점을 한눈에 볼 수 있습니다.\n\n"
        "합격의 지름길은 '새 문제 많이 풀기'가 아니라 '틀린 문제 다시 안 틀리기'입니다. 오답노트를 꼭 활용하세요!"
     )),
    ("study",
     lambda c, d: "실제 CBT 시험장 꿀팁 5가지 (미리 연습해 두세요)",
     lambda c, d: (
        "실제 CBT(컴퓨터 기반 시험) 시험장에서 당황하지 않도록 꿀팁을 정리했습니다.\n\n"
        "1. 화면 우측 '답안 표기란'에서 안 푼 문제를 한눈에 확인할 수 있습니다.\n"
        "2. 헷갈리는 문제는 '체크' 표시해 두고 나중에 다시 봅니다.\n"
        "3. 계산기 기능과 글자 크기 조절을 미리 익혀 두면 시간을 아낄 수 있습니다.\n"
        "4. 남은 시간이 10분이면 타이머가 빨간색으로 바뀝니다 — 마킹 여부를 마지막에 꼭 확인하세요.\n"
        "5. 상단 '뀨-Net CBT' 메뉴에서 실제와 유사한 화면으로 미리 연습할 수 있습니다.\n\n"
        "처음 보는 화면이 아니면 실전에서 훨씬 여유가 생깁니다."
     )),
    ("free",
     lambda c, d: "오늘의 한마디 — 하루 30분, 꾸준함이 합격을 만듭니다",
     lambda c, d: (
        "자격증 공부에서 가장 큰 적은 어려운 문제가 아니라 '오늘은 쉬자'는 마음입니다.\n\n"
        "하루에 딱 30분, 기출 20~30문제라도 매일 풀어 보세요. 일주일이면 200문제, 한 달이면 800문제가 쌓입니다. "
        "기출은 반복되기 때문에, 이 정도만 꾸준히 해도 어느 순간 '어? 이거 봤던 문제네' 하는 순간이 옵니다.\n\n"
        "오늘 하루도 한 문제라도 더. 여러분의 합격을 진심으로 응원합니다!"
     )),
    ("share",
     lambda c, d: f"{c} 계산문제, 이 유형만 잡아도 됩니다",
     lambda c, d: (
        f"{c}에서 계산문제가 부담되는 분들이 많습니다. 하지만 출제 유형은 생각보다 정해져 있습니다.\n\n"
        "· 먼저 기출에서 계산문제만 모아 유형을 분류해 보세요. 보통 3~5개 유형으로 압축됩니다.\n"
        "· 각 유형별로 대표 문제 2~3개의 풀이 과정을 손으로 직접 써보며 익힙니다.\n"
        "· 공식은 '암기'가 아니라 '적용'이 중요합니다. 같은 유형을 반복하면 자연히 외워집니다.\n\n"
        "계산문제 몇 개만 확실히 잡아도 합격선이 훨씬 편해집니다."
     )),
    ("study",
     lambda c, d: f"{c} 필기 합격 후 실기 준비, 이렇게 시작하세요",
     lambda c, d: (
        f"{c} 필기에 합격하셨다면, 실기 준비는 미루지 말고 바로 시작하는 것이 좋습니다.\n\n"
        "· 필기 지식이 남아 있을 때 실기로 넘어가야 흐름이 끊기지 않습니다.\n"
        "· 실기는 필답형/작업형에 따라 준비 방법이 완전히 다르니, 내 종목의 실기 유형부터 확인하세요.\n"
        "· 실기도 기출(복원) 문제가 가장 중요합니다. 자주 나오는 작업/문제를 반복 연습하세요.\n\n"
        "필기 합격의 유효기간 안에 실기까지 마무리하는 것을 목표로 계획을 세워 보세요."
     )),
    ("notice",
     lambda c, d: "[팁] 정답·해설·채점 버튼 100% 활용하는 법",
     lambda c, d: (
        "이 사이트의 학습 기능을 제대로 쓰면 공부 효율이 크게 올라갑니다.\n\n"
        "· 정답: 각 문제의 정답을 바로 확인합니다.\n"
        "· 해설: 왜 그 답이 맞는지 설명을 볼 수 있습니다(문제에 따라 제공).\n"
        "· 체크: 헷갈리는 문제를 북마크해 마이페이지에서 모아 봅니다.\n"
        "· 채점하기: 실제 시험처럼 전체를 채점하고, 틀린 문제는 오답노트에 자동 저장합니다.\n\n"
        "로그인하면 풀이 기록·오답노트·북마크가 모두 저장되어 다음에 이어서 공부할 수 있습니다."
     )),
    ("free",
     lambda c, d: "직장인 자격증 공부, 시간 확보하는 현실적인 방법",
     lambda c, d: (
        "일하면서 자격증 공부하기, 정말 쉽지 않죠. 현실적인 시간 확보 팁을 공유합니다.\n\n"
        "· 출퇴근 시간에 모바일로 기출 10문제씩만 풀어도 하루 20문제가 확보됩니다.\n"
        "· 점심시간 15분은 오답노트 복습에 딱 좋습니다.\n"
        "· 주말에 몰아서 하기보다 '평일 조금씩'이 기억에 훨씬 오래 남습니다.\n\n"
        "완벽한 공부 환경을 기다리면 시작할 수 없습니다. 지금 딱 10문제부터 시작해 보세요!"
     )),
]


def read_feed() -> list:
    if not FEED_FILE.exists():
        return []
    txt = FEED_FILE.read_text(encoding="utf-8")
    m = re.search(r"window\.CBT_OPS_POSTS\s*=\s*(\[[\s\S]*?\]);", txt)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except Exception:
        return []


def write_feed(posts: list) -> None:
    body = json.dumps(posts, ensure_ascii=False, indent=2)
    out = (
        "/* 자동 생성 — gen_community_post.py\n"
        "   커뮤니티 '운영자 글' 피드. community.html 이 읽어 게시판에 병합합니다.\n"
        "   직접 수정하지 마세요(스크립트가 관리). */\n"
        f"window.CBT_OPS_POSTS = {body};\n"
    )
    FEED_FILE.write_text(out, encoding="utf-8")


def make_post(date: dt.date, seq_id: int) -> dict:
    # 날짜 기반 결정적 선택 → 매일 다른 글, 같은 날 재실행 시 동일
    idx = date.toordinal()
    tag, title_fn, body_fn = TEMPLATES[idx % len(TEMPLATES)]
    cert = CERTS[(idx // len(TEMPLATES)) % len(CERTS)]
    rnd = random.Random(idx)
    return {
        "id": seq_id,
        "tag": tag,
        "title": title_fn(cert, date),
        "author": "운영자",
        "date": date.strftime("%m-%d"),
        "timestamp": date.strftime("%Y-%m-%d") + "T09:00",
        "views": rnd.randint(120, 900),
        "likes": rnd.randint(8, 60),
        "comments": rnd.randint(0, 12),
        "content": body_fn(cert, date),
    }


def add_for_date(posts: list, date: dt.date) -> bool:
    ds = date.strftime("%Y-%m-%d")
    if any((p.get("timestamp", "").startswith(ds)) for p in posts):
        return False  # 이미 그 날짜 글 있음
    min_id = min([p.get("id", -1000) for p in posts], default=-1000)
    new_id = min(min_id - 1, -1001)
    posts.insert(0, make_post(date, new_id))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", type=int, default=0, help="최근 N일치 채우기")
    args = ap.parse_args()

    posts = read_feed()
    today = dt.date.today()
    added = 0

    if args.backfill > 0:
        for i in range(args.backfill - 1, -1, -1):  # 오래된 → 최신 순
            if add_for_date(posts, today - dt.timedelta(days=i)):
                added += 1
    else:
        if add_for_date(posts, today):
            added += 1

    # 최신순 정렬 + 상한 유지
    posts.sort(key=lambda p: p.get("timestamp", ""), reverse=True)
    if len(posts) > MAX_POSTS:
        posts = posts[:MAX_POSTS]

    write_feed(posts)
    bump_feed_version(today)
    print(f"추가된 글: {added}개 / 현재 총 {len(posts)}개 → {FEED_FILE.name}")
    print(f"community.html 피드 버전 → ?v={today.strftime('%Y%m%d')}")


if __name__ == "__main__":
    main()
