/**
 * CBT 기출문제 — 공통 인증 / 학습 데이터 모듈  (cbt-auth.js)
 *
 * 사용법:
 *   메인 페이지 (E:\00.CBT\*.html)     → <script src="cbt-auth.js"></script>
 *   시험 페이지 (E:\00.CBT\CBT\**\*)   → <script src="../../cbt-auth.js"></script>
 *
 * 공개 API:  window.CBT_AUTH.*
 */
(function () {
    'use strict';

    /* ═══════════════════════════════════════════════════
       자동 HTTPS 강제 전환 (카카오 로그인 및 보안 필수)
    ═══════════════════════════════════════════════════ */
    if (location.protocol === 'http:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        location.replace('https://' + location.hostname + location.pathname + location.search + location.hash);
        return;
    }

    /* ═══════════════════════════════════════════════════
       상수
    ═══════════════════════════════════════════════════ */
    var KAKAO_APP_KEY = '6e17535219b4a0f4db5654e88297e303';

    var LS_SESSION   = 'cbt_session';
    var LS_HISTORY   = 'cbt_quiz_history';
    var LS_WRONG     = 'cbt_wrong_answers';
    var LS_BOOKMARKS = 'cbt_bookmarks';
    var LS_REDIRECT  = 'cbt_redirect';
    var LS_ACCOUNTS  = 'cbt_accounts';

    /* ═══════════════════════════════════════════════════
       내부 헬퍼
    ═══════════════════════════════════════════════════ */
    function _read(key) {
        try { return JSON.parse(localStorage.getItem(key) || 'null'); }
        catch (e) { return null; }
    }
    function _readArr(key) {
        try { return JSON.parse(localStorage.getItem(key) || '[]'); }
        catch (e) { return []; }
    }
    function _write(key, val) {
        try { localStorage.setItem(key, JSON.stringify(val)); }
        catch (e) { console.warn('[CBT_AUTH] localStorage write failed:', e); }
    }

    /* 현재 페이지가 CBT/ 하위인지 판단 → 상대경로 계산 */
    function _base() {
        var p = (location.pathname || '').replace(/\\/g, '/').toLowerCase();
        return p.indexOf('/cbt/') !== -1 ? '../../' : '';
    }

    /* ═══════════════════════════════════════════════════
       PUBLIC API
    ═══════════════════════════════════════════════════ */
    window.CBT_AUTH = {

        /* ── 세션 ─────────────────────────────────── */

        /** 현재 로그인된 유저 객체 반환 (없으면 null) */
        getUser: function () { return _read(LS_SESSION); },

        /** 유저 정보 저장 */
        setUser: function (u) {
            _write(LS_SESSION, Object.assign({}, u, { loginAt: new Date().toISOString() }));
        },

        /** 로그인 여부 */
        isLoggedIn: function () { return !!this.getUser(); },

        /** 로그아웃 */
        logout: function () {
            _write(LS_SESSION, null);
            localStorage.removeItem(LS_SESSION);
            try {
                if (window.Kakao && Kakao.Auth && Kakao.Auth.getAccessToken()) {
                    Kakao.Auth.logout(function () {});
                }
            } catch (e) {}
            location.reload();
        },

        /**
         * 로그인이 필요한 경우 login.html 로 리다이렉트.
         * @param {string} [msg]  리다이렉트 전 표시할 메시지
         * @returns {boolean}  로그인됐으면 true, 아니면 false (이후 코드 실행 불필요)
         */
        requireLogin: function (msg) {
            if (this.isLoggedIn()) return true;
            _write(LS_REDIRECT, location.href);
            if (msg) alert(msg);
            location.href = _base() + 'login.html';
            return false;
        },

        /* ── 카카오 OAuth 로그인 ────────────────────── */

        /**
         * 카카오 팝업 로그인 실행
         * @param {function} onSuccess  성공 콜백 (user 객체)
         * @param {function} onFail     실패 콜백 (error)
         */
        kakaoLogin: function (onSuccess, onFail) {
            var self = this;
            if (window.Kakao && !window.Kakao.isInitialized()) {
                try { window.Kakao.init(KAKAO_APP_KEY); } catch (e) {}
            }
            if (!window.Kakao || !window.Kakao.isInitialized()) {
                if (onFail) onFail({ msg: '카카오 SDK 초기화 실패. 페이지를 새로고침 해주세요.' });
                return;
            }

            try {
                // 1순위: Kakao SDK v2 공식 authorize (리다이렉트 방식 - 팝업 차단 0%)
                if (window.Kakao.Auth && typeof window.Kakao.Auth.authorize === 'function') {
                    var cleanUrl = location.protocol + '//' + location.host + location.pathname;
                    window.Kakao.Auth.authorize({
                        redirectUri: cleanUrl
                    });
                    return;
                }

                // 2순위: Kakao SDK v1 login (팝업 방식)
                if (window.Kakao.Auth && typeof window.Kakao.Auth.login === 'function') {
                    window.Kakao.Auth.login({
                        success: function () {
                            window.Kakao.API.request({
                                url: '/v2/user/me',
                                success: function (res) {
                                    var profile = (res.kakao_account && res.kakao_account.profile) || {};
                                    var user = {
                                        id:           'kakao_' + res.id,
                                        nickname:     profile.nickname || '카카오유저',
                                        profileImage: profile.profile_image_url || profile.thumbnail_image_url || '',
                                        provider:     'kakao',
                                    };
                                    self.setUser(user);
                                    if (onSuccess) onSuccess(user);
                                },
                                fail: function (e) {
                                    if (onFail) onFail({ msg: '사용자 정보 요청 실패: ' + (e.error_description || JSON.stringify(e)) });
                                }
                            });
                        },
                        fail: function (e) {
                            var errStr = e.error_description || e.error || JSON.stringify(e);
                            if (onFail) onFail({ msg: errStr });
                        }
                    });
                    return;
                }
            } catch (err) {
                console.error('[CBT_AUTH] Kakao Login Exception:', err);
                if (onFail) onFail({ msg: '카카오 실행 예외: ' + err.message });
            }
        },

        /**
         * 닉네임(데모/로컬) 로그인 — Kakao 없이 로컬 테스트용
         * @param {string} nickname
         * @returns {object} user
         */
        nicknameLogin: function (nickname) {
            var user = {
                id:           'user_' + Date.now(),
                nickname:     nickname || '익명유저',
                profileImage: '',
                provider:     'nickname',
            };
            this.setUser(user);
            return user;
        },

        /* ── 회원가입 / 비밀번호 로그인 (로컬 계정) ── */

        /** 가입된 계정 목록 */
        getAccounts: function () { return _readArr(LS_ACCOUNTS); },

        /**
         * 회원가입
         * @param {string} nickname  닉네임(아이디 겸용, 2~16자)
         * @param {string} email     이메일(선택)
         * @param {string} password  비밀번호(4자 이상)
         * @returns {{ok:boolean, msg:string, user?:object}}
         */
        signup: function (nickname, email, password) {
            nickname = String(nickname || '').trim();
            email    = String(email || '').trim();
            password = String(password || '');
            if (nickname.length < 2)  return { ok: false, msg: '닉네임은 2자 이상 입력해 주세요.' };
            if (nickname.length > 16) return { ok: false, msg: '닉네임은 16자 이하로 입력해 주세요.' };
            if (password.length < 4)  return { ok: false, msg: '비밀번호는 4자 이상 입력해 주세요.' };
            if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                return { ok: false, msg: '이메일 형식이 올바르지 않습니다.' };
            }
            var accounts = this.getAccounts();
            var lower = nickname.toLowerCase();
            for (var i = 0; i < accounts.length; i++) {
                if ((accounts[i].nickname || '').toLowerCase() === lower) {
                    return { ok: false, msg: '이미 사용 중인 닉네임입니다.' };
                }
            }
            var account = {
                id:        'member_' + Date.now(),
                nickname:  nickname,
                email:     email,
                pwHash:    _hash(password),
                createdAt: new Date().toISOString(),
            };
            accounts.push(account);
            _write(LS_ACCOUNTS, accounts);
            var user = {
                id:           account.id,
                nickname:     account.nickname,
                email:        account.email,
                profileImage: '',
                provider:     'member',
            };
            this.setUser(user);
            return { ok: true, msg: '가입 완료', user: user };
        },

        /**
         * 닉네임+비밀번호 로그인
         * @returns {{ok:boolean, msg:string, user?:object}}
         */
        pwLogin: function (nickname, password) {
            nickname = String(nickname || '').trim();
            password = String(password || '');
            if (!nickname || !password) return { ok: false, msg: '닉네임과 비밀번호를 입력해 주세요.' };
            var accounts = this.getAccounts();
            var lower = nickname.toLowerCase();
            for (var i = 0; i < accounts.length; i++) {
                var a = accounts[i];
                if ((a.nickname || '').toLowerCase() === lower) {
                    if (a.pwHash !== _hash(password)) {
                        return { ok: false, msg: '비밀번호가 일치하지 않습니다.' };
                    }
                    var user = {
                        id:           a.id,
                        nickname:     a.nickname,
                        email:        a.email || '',
                        profileImage: '',
                        provider:     'member',
                    };
                    this.setUser(user);
                    return { ok: true, msg: '로그인 성공', user: user };
                }
            }
            return { ok: false, msg: '등록되지 않은 닉네임입니다. 회원가입을 먼저 해주세요.' };
        },

        /* ── 퀴즈 풀이 기록 ────────────────────────── */

        /** 전체 풀이 기록 배열 (최신순) */
        getHistory: function () { return _readArr(LS_HISTORY); },

        /**
         * 채점 결과 저장
         * @param {{ examId, category, totalQ, answered, correct, score, solvedAt }} result
         */
        saveHistory: function (result) {
            if (!this.isLoggedIn()) return;
            var h = this.getHistory();
            h.unshift(Object.assign({}, result, {
                userId:   this.getUser().id,
                savedAt:  new Date().toISOString(),
            }));
            _write(LS_HISTORY, h.slice(0, 500));
        },

        /** 풀이 기록 전체 삭제 */
        clearHistory: function () { localStorage.removeItem(LS_HISTORY); },

        /* ── 오답노트 ──────────────────────────────── */

        /** 오답 목록 */
        getWrong: function () { return _readArr(LS_WRONG); },

        /**
         * 오답 항목 배열 저장 (중복 시 wrongCount 증가)
         * @param {Array<{questionId, questionText, options, correctAnswer, userAnswer, examId, category}>} items
         */
        saveWrong: function (items) {
            if (!this.isLoggedIn()) return;
            var list = this.getWrong();
            var uid  = this.getUser().id;
            var now  = new Date().toISOString();
            items.forEach(function (w) {
                var key = uid + '_' + w.questionId;
                var idx = -1;
                for (var i = 0; i < list.length; i++) {
                    if (list[i].key === key) { idx = i; break; }
                }
                if (idx >= 0) {
                    list[idx].wrongCount  = (list[idx].wrongCount || 1) + 1;
                    list[idx].lastWrong   = now;
                    list[idx].userAnswer  = w.userAnswer;
                } else {
                    list.unshift(Object.assign({ key: key, userId: uid, wrongCount: 1, lastWrong: now }, w));
                }
            });
            _write(LS_WRONG, list.slice(0, 2000));
        },

        /** 특정 오답 항목 삭제 */
        removeWrong: function (key) {
            _write(LS_WRONG, this.getWrong().filter(function (w) { return w.key !== key; }));
        },

        /** 오답노트 전체 초기화 */
        clearWrong: function () { localStorage.removeItem(LS_WRONG); },

        /* ── 북마크 (체크) ─────────────────────────── */

        /** 북마크 목록 */
        getBookmarks: function () { return _readArr(LS_BOOKMARKS); },

        /**
         * 북마크 토글 (있으면 제거, 없으면 추가)
         * @returns {boolean|null}  true=추가, false=제거, null=로그인 안 됨
         */
        toggleBookmark: function (item) {
            if (!this.isLoggedIn()) return null;
            var list = this.getBookmarks();
            var uid  = this.getUser().id;
            var key  = uid + '_' + item.questionId;
            var idx  = -1;
            for (var i = 0; i < list.length; i++) {
                if (list[i].key === key) { idx = i; break; }
            }
            if (idx >= 0) {
                list.splice(idx, 1);
                _write(LS_BOOKMARKS, list);
                return false;
            } else {
                list.unshift(Object.assign({ key: key, userId: uid, savedAt: new Date().toISOString() }, item));
                _write(LS_BOOKMARKS, list.slice(0, 500));
                return true;
            }
        },

        /** 특정 질문이 북마크됐는지 확인 */
        isBookmarked: function (questionId) {
            if (!this.isLoggedIn()) return false;
            var uid = this.getUser().id;
            var key = uid + '_' + questionId;
            return this.getBookmarks().some(function (b) { return b.key === key; });
        },

        /** 특정 북마크 제거 */
        removeBookmark: function (key) {
            _write(LS_BOOKMARKS, this.getBookmarks().filter(function (b) { return b.key !== key; }));
        },

        /** 북마크 전체 초기화 */
        clearBookmarks: function () { localStorage.removeItem(LS_BOOKMARKS); },

        /* ── 학습 통계 계산 (편의 메서드) ─────────── */

        /** { totalAttempts, avgScore, totalCorrect, totalQuestions } */
        calcStats: function () {
            var uid = this.isLoggedIn() ? this.getUser().id : null;
            if (!uid) return { totalAttempts: 0, avgScore: 0, totalCorrect: 0, totalQ: 0 };
            var h = this.getHistory().filter(function (r) { return r.userId === uid; });
            var totalAttempts = h.length;
            var avgScore = totalAttempts
                ? Math.round(h.reduce(function (s, r) { return s + (r.score || 0); }, 0) / totalAttempts)
                : 0;
            var totalCorrect = h.reduce(function (s, r) { return s + (r.correct || 0); }, 0);
            var totalQ       = h.reduce(function (s, r) { return s + (r.totalQ || 0); }, 0);
            return { totalAttempts: totalAttempts, avgScore: avgScore, totalCorrect: totalCorrect, totalQ: totalQ };
        },
    };

    /* ═══════════════════════════════════════════════════
       공통 네비게이션 업데이트
       id="navAuthArea" 요소가 있는 페이지에서 자동 실행
    ═══════════════════════════════════════════════════ */
    function _updateNav() {
        var el = document.getElementById('navAuthArea');
        if (!el) return;

        var user = CBT_AUTH.getUser();
        var base = _base();

        if (user) {
            var avatarHtml = user.profileImage
                ? '<img src="' + user.profileImage + '" alt="" style="width:28px;height:28px;border-radius:50%;object-fit:cover;vertical-align:middle;">'
                : '<span style="display:inline-flex;width:28px;height:28px;border-radius:50%;background:#2563eb;color:#fff;font-size:12px;font-weight:700;align-items:center;justify-content:center;vertical-align:middle;">' + (user.nickname || '?').charAt(0) + '</span>';

            el.innerHTML =
                '<span style="display:flex;align-items:center;gap:6px;font-size:14px;color:#1f2937;font-weight:600;">' +
                    avatarHtml + '<span>' + _esc(user.nickname) + '님</span>' +
                '</span>' +
                '<a href="' + base + 'mypage.html" style="font-size:14px;color:#2563eb;font-weight:700;text-decoration:none;transition:color .15s;" onmouseover="this.style.color=\'#1d4ed8\'" onmouseout="this.style.color=\'#2563eb\'">마이페이지</a>' +
                '<button onclick="CBT_AUTH.logout()" style="font-size:13px;color:#6b7280;background:none;border:none;cursor:pointer;padding:0;transition:color .15s;" onmouseover="this.style.color=\'#ef4444\'" onmouseout="this.style.color=\'#6b7280\'">로그아웃</button>';
        } else {
            el.innerHTML =
                '<a href="' + base + 'login.html" style="font-size:14px;font-weight:500;color:#4b5563;text-decoration:none;transition:color .15s;" onmouseover="this.style.color=\'#2563eb\'" onmouseout="this.style.color=\'#4b5563\'">로그인</a>' +
                '<a href="' + base + 'signup.html" style="background:#2563eb;color:#fff;padding:8px 16px;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none;transition:background .15s;" onmouseover="this.style.background=\'#1d4ed8\'" onmouseout="this.style.background=\'#2563eb\'">회원가입</a>';
        }
    }

    function _esc(s) {
        return String(s || '')
            .replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    /* 간이 해시 (DJB2 변형) — 로컬 저장용 */
    function _hash(str) {
        var h = 5381;
        str = 'cbt!' + str + '!korea';
        for (var i = 0; i < str.length; i++) {
            h = ((h << 5) + h + str.charCodeAt(i)) | 0;
        }
        return 'h' + (h >>> 0).toString(36);
    }

    /* ═══════════════════════════════════════════════════
       뀨-Net CBT 메뉴 강조 (이벤트 페이지)
       — 모든 페이지의 네비에서 눈에 띄도록 자동 스타일링
    ═══════════════════════════════════════════════════ */
    function _highlightQnet() {
        if (document.getElementById('cbtq-hot-style')) return;
        var st = document.createElement('style');
        st.id = 'cbtq-hot-style';
        st.textContent =
            '.cbtq-hot{position:relative;display:inline-flex !important;align-items:center;gap:5px;' +
            'background:linear-gradient(135deg,#059669,#047857);color:#fff !important;font-weight:800;' +
            'padding:7px 15px 7px 13px;border-radius:999px;box-shadow:0 3px 12px rgba(5,150,105,.4);' +
            'text-decoration:none;transition:transform .15s,box-shadow .15s;animation:cbtqPulse 2.2s ease-in-out infinite;border:none;}' +
            '.cbtq-hot:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(5,150,105,.55);color:#fff !important;}' +
            '.cbtq-hot .cbtq-ico{color:#fde047;}' +
            '.cbtq-hot .cbtq-badge{position:absolute;top:-7px;right:-6px;background:#ef4444;color:#fff;' +
            'font-size:9px;font-weight:900;padding:1px 5px;border-radius:999px;letter-spacing:.5px;box-shadow:0 1px 4px rgba(0,0,0,.25);}' +
            '@keyframes cbtqPulse{0%,100%{box-shadow:0 3px 12px rgba(5,150,105,.4);}50%{box-shadow:0 3px 18px rgba(5,150,105,.75);}}';
        document.head.appendChild(st);

        var links = document.querySelectorAll('nav a[href$="cbt-qnet.html"]');   // 네비 메뉴 링크만
        for (var i = 0; i < links.length; i++) {
            var a = links[i];
            if (!a.closest || !a.closest('nav')) continue;            // 네비 밖(배너 등)은 제외
            if (a.className.indexOf('qnet-menu') !== -1) continue;    // index.html 자체 스타일은 유지
            if (a.children.length > 1) continue;                     // 복합 콘텐츠(배너 등) 보호
            var txt = (a.textContent || '').replace(/\s+/g, ' ').trim();
            if (txt.indexOf('CBT') === -1) continue;
            a.className = 'cbtq-hot';
            a.innerHTML = '<i class="fas fa-desktop cbtq-ico"></i>뀨-Net CBT<span class="cbtq-badge">EVENT</span>';
        }
    }

    /* ═══════════════════════════════════════════════════
       카카오 OAuth 리다이렉트 응답 (code=) 자동 처리
    ═══════════════════════════════════════════════════ */
    try {
        var _searchParams = new URLSearchParams(location.search);
        var _kakaoCode = _searchParams.get('code');
        if (_kakaoCode) {
            var _user = {
                id: 'kakao_' + Date.now(),
                nickname: '카카오 수험생',
                profileImage: '',
                provider: 'kakao'
            };
            _write(LS_SESSION, Object.assign({}, _user, { loginAt: new Date().toISOString() }));
            if (window.history && window.history.replaceState) {
                window.history.replaceState({}, document.title, location.pathname);
            }
            var _dest = localStorage.getItem(LS_REDIRECT) || 'index.html';
            localStorage.removeItem(LS_REDIRECT);
            location.replace(_dest);
        }
    } catch (e) {}

    function _onReady() { _updateNav(); _highlightQnet(); }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _onReady);
    } else {
        _onReady();
    }

})();
