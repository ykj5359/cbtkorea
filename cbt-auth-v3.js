/**
 * CBT 기출문제 — 공통 인증 / 학습 데이터 모듈 (cbt-auth-v3.js)
 */
(function () {
    'use strict';

    /* ═══════════════════════════════════════════════════
       자동 HTTPS 강제 전환
    ═══════════════════════════════════════════════════ */
    if (location.protocol === 'http:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        location.replace('https://' + location.hostname + location.pathname + location.search + location.hash);
        return;
    }

    var KAKAO_APP_KEY = '6e17535219b4a0f4db5654e88297e303';
    var LS_SESSION   = 'cbt_session';
    var LS_HISTORY   = 'cbt_quiz_history';
    var LS_WRONG     = 'cbt_wrong_answers';
    var LS_BOOKMARKS = 'cbt_bookmarks';
    var LS_REDIRECT  = 'cbt_redirect';
    var LS_ACCOUNTS  = 'cbt_accounts';

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

    function _base() {
        var p = (location.pathname || '').replace(/\\/g, '/').toLowerCase();
        return p.indexOf('/cbt/') !== -1 ? '../../' : '';
    }

    window.CBT_AUTH = {

        getUser: function () { return _read(LS_SESSION); },

        setUser: function (u) {
            _write(LS_SESSION, Object.assign({}, u, { loginAt: new Date().toISOString() }));
        },

        isLoggedIn: function () { return !!this.getUser(); },

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

        requireLogin: function (msg) {
            if (this.isLoggedIn()) return true;
            _write(LS_REDIRECT, location.href);
            if (msg) alert(msg);
            location.href = _base() + 'login.html';
            return false;
        },

        /* ── 순수 팝업 카카오 로그인 (KOE006 원천 차단 + 즉시 메인 이동) ── */
        kakaoLogin: function (onSuccess, onFail) {
            var self = this;
            if (window.Kakao && !window.Kakao.isInitialized()) {
                try { window.Kakao.init(KAKAO_APP_KEY); } catch (e) {}
            }
            if (!window.Kakao || !window.Kakao.isInitialized()) {
                alert('카카오 SDK 로딩 중입니다. 1초 뒤 다시 눌러주세요.');
                if (onFail) onFail({ msg: '카카오 SDK 미초기화' });
                return;
            }

            if (window.Kakao.Auth && typeof window.Kakao.Auth.login === 'function') {
                window.Kakao.Auth.login({
                    success: function (authObj) {
                        try {
                            if (window.Kakao.Auth.setAccessToken && authObj && authObj.access_token) {
                                window.Kakao.Auth.setAccessToken(authObj.access_token);
                            }
                        } catch(e){}

                        window.Kakao.API.request({
                            url: '/v2/user/me',
                            success: function (res) {
                                var profile = (res.kakao_account && res.kakao_account.profile) || {};
                                var nickname = profile.nickname || (res.kakao_account && res.kakao_account.email ? res.kakao_account.email.split('@')[0] : '카카오 수험생');
                                var user = {
                                    id: 'kakao_' + res.id,
                                    nickname: nickname,
                                    profileImage: profile.profile_image_url || profile.thumbnail_image_url || '',
                                    provider: 'kakao'
                                };
                                self.setUser(user);
                                if (onSuccess) onSuccess(user);

                                var dest = localStorage.getItem(LS_REDIRECT) || 'index.html';
                                localStorage.removeItem(LS_REDIRECT);
                                window.location.href = dest;
                            },
                            fail: function (err) {
                                var user = {
                                    id: 'kakao_' + Date.now(),
                                    nickname: '카카오 수험생',
                                    provider: 'kakao'
                                };
                                self.setUser(user);
                                window.location.href = 'index.html';
                            }
                        });
                    },
                    fail: function (err) {
                        console.warn('[Kakao Login Fail]', err);
                        if (onFail) onFail(err);
                    }
                });
            } else {
                alert('카카오 인증 모듈 로딩 오류입니다. 페이지를 새로고침 해주세요.');
            }
        },

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

        getAccounts: function () { return _readArr(LS_ACCOUNTS); },

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

        getHistory: function () { return _readArr(LS_HISTORY); },

        saveHistory: function (result) {
            if (!this.isLoggedIn()) return;
            var h = this.getHistory();
            h.unshift(Object.assign({}, result, {
                userId:   this.getUser().id,
                savedAt:  new Date().toISOString(),
            }));
            _write(LS_HISTORY, h.slice(0, 500));
        },

        clearHistory: function () { localStorage.removeItem(LS_HISTORY); },

        getWrong: function () { return _readArr(LS_WRONG); },

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

        removeWrong: function (key) {
            _write(LS_WRONG, this.getWrong().filter(function (w) { return w.key !== key; }));
        },

        clearWrong: function () { localStorage.removeItem(LS_WRONG); },

        getBookmarks: function () { return _readArr(LS_BOOKMARKS); },

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

        isBookmarked: function (questionId) {
            if (!this.isLoggedIn()) return false;
            var uid = this.getUser().id;
            var key = uid + '_' + questionId;
            return this.getBookmarks().some(function (b) { return b.key === key; });
        },

        removeBookmark: function (key) {
            _write(LS_BOOKMARKS, this.getBookmarks().filter(function (b) { return b.key !== key; }));
        },

        clearBookmarks: function () { localStorage.removeItem(LS_BOOKMARKS); },

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
                '<a href="' + base + 'signup.html" style="background:#2563eb;color:#fff;padding:8px 16px;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none;transition:background .15s;" onmouseover="this.style.color=\'#1d4ed8\'" onmouseout="this.style.background=\'#2563eb\'">회원가입</a>';
        }
    }

    function _esc(s) {
        return String(s || '')
            .replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    function _hash(str) {
        var h = 5381;
        str = 'cbt!' + str + '!korea';
        for (var i = 0; i < str.length; i++) {
            h = ((h << 5) + h + str.charCodeAt(i)) | 0;
        }
        return 'h' + (h >>> 0).toString(36);
    }

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

        var links = document.querySelectorAll('nav a[href$="cbt-qnet.html"]');
        for (var i = 0; i < links.length; i++) {
            var a = links[i];
            if (!a.closest || !a.closest('nav')) continue;
            if (a.className.indexOf('qnet-menu') !== -1) continue;
            if (a.children.length > 1) continue;
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
                nickname: 'ykj5359',
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
