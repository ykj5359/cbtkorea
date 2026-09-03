# -*- coding: utf-8 -*-
"""
fix_fake_stats.py — 사이트에 표시되던 허위 통계·가상 인물 콘텐츠 정리
=====================================================================
· index.html      : 홈 통계 4종을 실제 수치로 교체 (57,111,536+ / 방문자 / 합격수기 → 실제)
· community.html  : 커뮤니티 통계 실제화, 가상 인물 게시글·베스트회원·합격수기 제거,
                    인기글은 운영자 실제 글에서 생성, 태그의 허위 카운트 제거
방문자에게 사실과 다른 정보를 보여주지 않도록 하는 것이 목적.
"""
from pathlib import Path

ROOT = Path(r"E:\00.CBT")

# 실제 수치 (cbt-qnet-data.js / 사이트맵 기준)
N_CATS = "546"
N_ROUNDS = "13,998"
N_QUESTIONS = "약 96만"

# ─────────────────────────────────────────────────────────────
# 1) index.html — 홈 통계
# ─────────────────────────────────────────────────────────────
idx = ROOT / "index.html"
t = idx.read_text(encoding="utf-8")

OLD_STATS = '''            <div class="text-center border-r border-gray-100">
                <p class="text-sm text-gray-500">전체 문제 수</p>
                <p class="text-xl font-bold text-blue-600">57,111,536+</p>
            </div>
            <div class="text-center border-r border-gray-100">
                <p class="text-sm text-gray-500">오늘 방문자</p>
                <p class="text-xl font-bold text-blue-600">1,258</p>
            </div>
            <div class="text-center border-r border-gray-100">
                <p class="text-sm text-gray-500">합격 수기</p>
                <p class="text-xl font-bold text-blue-600">12,402</p>
            </div>
            <div class="text-center">
                <p class="text-sm text-gray-500">진행 중인 시험</p>
                <p class="text-xl font-bold text-blue-600">546+</p>
            </div>'''

NEW_STATS = f'''            <div class="text-center border-r border-gray-100">
                <p class="text-sm text-gray-500">자격증 종목</p>
                <p class="text-xl font-bold text-blue-600">{N_CATS}개</p>
            </div>
            <div class="text-center border-r border-gray-100">
                <p class="text-sm text-gray-500">기출문제 회차</p>
                <p class="text-xl font-bold text-blue-600">{N_ROUNDS}회</p>
            </div>
            <div class="text-center border-r border-gray-100">
                <p class="text-sm text-gray-500">수록 문항</p>
                <p class="text-xl font-bold text-blue-600">{N_QUESTIONS}</p>
            </div>
            <div class="text-center">
                <p class="text-sm text-gray-500">이용료</p>
                <p class="text-xl font-bold text-blue-600">전액 무료</p>
            </div>'''

assert OLD_STATS in t, "index.html 통계 블록 미발견"
t = t.replace(OLD_STATS, NEW_STATS)
idx.write_text(t, encoding="utf-8")
print("✓ index.html 통계 4종 → 실제 수치로 교체")

# ─────────────────────────────────────────────────────────────
# 2) community.html
# ─────────────────────────────────────────────────────────────
com = ROOT / "community.html"
c = com.read_text(encoding="utf-8")

# 2-1) 상단 통계 카드
OLD_C_STATS = '''            <div class="stat-card text-center border-r border-gray-100">
                <p class="text-xs text-gray-500 mb-1">전체 게시글</p>
                <p class="text-xl font-bold text-blue-600" id="statTotalPosts">42,318</p>
            </div>
            <div class="stat-card text-center border-r border-gray-100">
                <p class="text-xs text-gray-500 mb-1">오늘의 새 글</p>
                <p class="text-xl font-bold text-blue-600" id="statToday">128</p>
            </div>
            <div class="stat-card text-center border-r border-gray-100">
                <p class="text-xs text-gray-500 mb-1">활동 회원</p>
                <p class="text-xl font-bold text-blue-600">3,541</p>
            </div>
            <div class="stat-card text-center">
                <p class="text-xs text-gray-500 mb-1">합격 수기</p>
                <p class="text-xl font-bold text-blue-600">12,402</p>
            </div>'''

NEW_C_STATS = f'''            <div class="stat-card text-center border-r border-gray-100">
                <p class="text-xs text-gray-500 mb-1">커뮤니티 글</p>
                <p class="text-xl font-bold text-blue-600" id="statTotalPosts">-</p>
            </div>
            <div class="stat-card text-center border-r border-gray-100">
                <p class="text-xs text-gray-500 mb-1">오늘의 새 글</p>
                <p class="text-xl font-bold text-blue-600" id="statToday">-</p>
            </div>
            <div class="stat-card text-center border-r border-gray-100">
                <p class="text-xs text-gray-500 mb-1">자격증 종목</p>
                <p class="text-xl font-bold text-blue-600">{N_CATS}개</p>
            </div>
            <div class="stat-card text-center">
                <p class="text-xs text-gray-500 mb-1">기출문제 회차</p>
                <p class="text-xl font-bold text-blue-600">{N_ROUNDS}회</p>
            </div>'''
assert OLD_C_STATS in c, "community 통계 블록 미발견"
c = c.replace(OLD_C_STATS, NEW_C_STATS)

# 2-2) 사이드바: 베스트 회원 / 최근 합격 수기 카드 제거 → 학습 도우미 카드로 교체
OLD_SIDE = '''                <div class="bg-white rounded-xl shadow-sm p-6">
                    <h3 class="text-base font-bold text-gray-800 mb-4">
                        <i class="fas fa-crown text-yellow-500 mr-2"></i>이달의 베스트 회원
                    </h3>
                    <div class="space-y-3" id="bestUsers"></div>
                </div>'''
NEW_SIDE = '''                <div class="bg-white rounded-xl shadow-sm p-6">
                    <h3 class="text-base font-bold text-gray-800 mb-4">
                        <i class="fas fa-compass text-blue-600 mr-2"></i>학습에 도움되는 곳
                    </h3>
                    <ul class="space-y-2.5 text-sm">
                        <li><a href="guides.html" class="text-gray-700 hover:text-blue-600"><i class="fas fa-book text-blue-500 mr-2"></i>자격증별 합격 가이드</a></li>
                        <li><a href="cbt-qnet.html" class="text-gray-700 hover:text-emerald-600"><i class="fas fa-desktop text-emerald-500 mr-2"></i>실전 CBT 모의시험</a></li>
                        <li><a href="exams.html" class="text-gray-700 hover:text-blue-600"><i class="fas fa-list text-blue-500 mr-2"></i>전체 기출문제 목록</a></li>
                        <li><a href="mypage.html" class="text-gray-700 hover:text-blue-600"><i class="fas fa-clipboard-check text-blue-500 mr-2"></i>내 오답노트</a></li>
                    </ul>
                </div>'''
assert OLD_SIDE in c
c = c.replace(OLD_SIDE, NEW_SIDE)

OLD_PASS = '''                <div class="bg-white rounded-xl shadow-sm p-6">
                    <h3 class="text-base font-bold text-gray-800 mb-4">
                        <i class="fas fa-trophy text-green-600 mr-2"></i>최근 합격 수기
                    </h3>
                    <div class="space-y-3" id="recentPass"></div>
                    <a href="#" class="block text-center text-xs text-blue-600 hover:underline mt-3">전체보기 →</a>
                </div>'''
assert OLD_PASS in c
c = c.replace(OLD_PASS, "")

# 2-3) 인기 게시글 → 운영자 최신 글 (실제 글 기반)
c = c.replace('<i class="fas fa-fire text-red-500 mr-2"></i>인기 게시글',
              '<i class="fas fa-bullhorn text-blue-600 mr-2"></i>운영자 최신 글')

# 2-4) 가상 인물 데이터 배열 정리
old_hot_start = c.index("    const hotPosts = [")
old_hot_end = c.index("];", old_hot_start) + 3
c = c[:old_hot_start] + "    let hotPosts = [];   // 운영자 실제 글에서 채움\n" + c[old_hot_end:]

old_sp_start = c.index("    const samplePosts = [")
old_sp_end = c.index("    ];", old_sp_start) + len("    ];\n")
NEW_SAMPLE = '''    const samplePosts = [
        { id:-1, tag:'notice', pinned:true, author:'운영자', date:'09-01', views:0, likes:0,
          title:'[공지] 커뮤니티 이용 안내',
          content:'CBT 기출문제 커뮤니티에 오신 것을 환영합니다.\\n\\n· 로그인 없이 익명으로 글을 작성할 수 있습니다.\\n· 광고, 욕설, 개인정보 노출, 저작권 침해 자료는 삼가 주세요.\\n· 작성한 글은 이용하시는 브라우저에 저장됩니다.\\n\\n서로 존중하는 분위기에서 합격 정보를 나누는 공간이 되었으면 합니다.' },
        { id:-2, tag:'review', pinned:true, author:'운영자', date:'09-01', views:0, likes:0,
          title:'[안내] 기출문제 오류를 발견하셨나요?',
          content:'문제나 정답에 오류가 있다면 「문제오류신고」 카테고리로 알려주세요.\\n\\n알려주실 때 아래 내용을 함께 적어주시면 훨씬 빠르게 확인할 수 있습니다.\\n1) 자격증 종목과 시행 회차(예: 정보처리기사 2022년 4월 24일)\\n2) 문제 번호\\n3) 어떤 부분이 이상한지\\n\\n제보해 주시는 내용은 자료 정확도를 높이는 데 큰 도움이 됩니다. 감사합니다.' },
    ];
'''
c = c[:old_sp_start] + NEW_SAMPLE + c[old_sp_end:]

old_bu_start = c.index("    const bestUsers = [")
old_bu_end = c.index("    ];", old_bu_start) + len("    ];\n")
c = c[:old_bu_start] + c[old_bu_end:]

old_rp_start = c.index("    const recentPass = [")
old_rp_end = c.index("    ];", old_rp_start) + len("    ];\n")
c = c[:old_rp_start] + c[old_rp_end:]

# 2-5) 태그 허위 카운트 제거
old_tag_start = c.index("    const popularTags = [")
old_tag_end = c.index("    ];", old_tag_start) + len("    ];\n")
NEW_TAGS = '''    const popularTags = [
        { name:'정보처리기사', color:'bg-blue-100 text-blue-700' },
        { name:'컴활1급',     color:'bg-green-100 text-green-700' },
        { name:'한국사',      color:'bg-purple-100 text-purple-700' },
        { name:'공인중개사',  color:'bg-pink-100 text-pink-700' },
        { name:'전기기능사',  color:'bg-yellow-100 text-yellow-700' },
        { name:'지게차',      color:'bg-indigo-100 text-indigo-700' },
        { name:'산업안전기사', color:'bg-red-100 text-red-700' },
        { name:'스터디모집',  color:'bg-teal-100 text-teal-700' },
        { name:'실기시험',    color:'bg-orange-100 text-orange-700' },
    ];
'''
c = c[:old_tag_start] + NEW_TAGS + c[old_tag_end:]

# 2-6) 운영자 글 병합 직후 hotPosts 채우기
OLD_MERGE = '''    if (window.CBT_OPS_POSTS && window.CBT_OPS_POSTS.length) {
        samplePosts.unshift(...window.CBT_OPS_POSTS);
    }'''
NEW_MERGE = '''    if (window.CBT_OPS_POSTS && window.CBT_OPS_POSTS.length) {
        samplePosts.unshift(...window.CBT_OPS_POSTS);
        hotPosts = window.CBT_OPS_POSTS.slice(0, 5);   // 실제 운영자 글로 구성
    }'''
assert OLD_MERGE in c
c = c.replace(OLD_MERGE, NEW_MERGE)

# 2-7) 렌더러: 인기글에서 허위 조회/추천 수치 제거
OLD_HOT_RENDER = '''                <span class="hidden md:flex items-center gap-3 text-xs text-gray-500 flex-shrink-0">
                    <span><i class="fas fa-eye mr-1"></i>${p.views.toLocaleString()}</span>
                    <span><i class="fas fa-heart mr-1 text-red-400"></i>${p.likes}</span>
                </span>'''
NEW_HOT_RENDER = '''                <span class="hidden md:flex items-center gap-2 text-xs text-gray-400 flex-shrink-0">
                    <span>${p.date || ''}</span>
                </span>'''
assert OLD_HOT_RENDER in c
c = c.replace(OLD_HOT_RENDER, NEW_HOT_RENDER)

# 2-8) 태그 렌더러에서 count 제거
c = c.replace('#${t.name} <span class="opacity-60">${t.count}</span>', '#${t.name}')

# 2-9) 총 게시글 수 / 통계 실제화
c = c.replace("        const total = 42318 + loadUserPosts().length;",
              "        const total = getMergedPosts().length;")
c = c.replace("        document.getElementById('statTotalPosts').textContent = (42318 + userPosts.length).toLocaleString();",
              "        document.getElementById('statTotalPosts').textContent = getMergedPosts().length.toLocaleString();")
c = c.replace("        document.getElementById('statToday').textContent = (128 + todayCount).toLocaleString();",
              "        document.getElementById('statToday').textContent = todayCount.toLocaleString();")

# 2-10) 이제 없는 렌더 함수 호출 제거
for fn in ("renderBestUsers", "renderRecentPass"):
    c = c.replace(f"    function {fn}() {{", f"    function {fn}() {{ return;\n        // (제거됨)")
c = c.replace("document.getElementById('bestUsers').innerHTML", "void 0 && document.getElementById('bestUsers').innerHTML")
c = c.replace("document.getElementById('recentPass').innerHTML", "void 0 && document.getElementById('recentPass').innerHTML")

com.write_text(c, encoding="utf-8")
print("✓ community.html 통계 실제화 + 가상 인물 콘텐츠 제거 완료")
print("  - 게시글 20개(가상 인물 18) → 운영자 공지 2개 + 운영자 자동글")
print("  - 베스트 회원(가상 5명) → 학습 링크 카드로 교체")
print("  - 최근 합격 수기(가상 4건) 제거 / 태그 허위 카운트 제거")
