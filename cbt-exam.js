/**
 * CBT 기출문제 — 시험 페이지 학습 기능  (cbt-exam.js)
 *
 * 의존성:
 *   - jQuery (시험 페이지에 기본 포함)
 *   - cbt-auth.js  (window.CBT_AUTH 노출)
 *
 * 기능:
 *   1. 답안 클릭 선택 (li 클릭)
 *   2. 체크 버튼 → 로그인 확인 후 북마크 저장
 *   3. 플로팅 [📊 채점하기] 버튼
 *   4. 채점 결과 모달 (정오답 시각화)
 *   5. 풀이 기록 + 오답 자동 저장 (로그인 시)
 */
(function ($) {
    'use strict';
    if (typeof $ === 'undefined') {
        console.warn('[cbt-exam.js] jQuery를 찾을 수 없습니다.');
        return;
    }

    /* ═══════════════════════════════════════════════
       1. 동적 CSS 주입
    ═══════════════════════════════════════════════ */
    var CSS = [
        /* ── 시험지 레이아웃 보정 ──
           · 과목 띠(가로 파란줄)는 가운데 세로선 위에 오도록 (세로선은 과목 뒤로)
           · 과목 띠가 앞뒤 문제와 겹치지 않도록 여백/블록 보장 */
        '.exams { position:relative; }',
        '.exams::after { z-index:0 !important; }',
        '.exam-class-title { position:relative !important; z-index:3 !important; display:block !important; clear:both; overflow:hidden; margin:14px 0 20px 0 !important; }',
        '.exam-class-title .col { position:relative; z-index:1; }',

        /* 답안 선택 */
        'ol.circlednumbers li { cursor:pointer; border-radius:6px; padding:3px 6px; transition:background .15s,border-left .15s; }',
        'ol.circlednumbers li:hover { background:#f0f7ff; }',
        'ol.circlednumbers li.cbt-selected { background:#dbeafe; border-left:3px solid #3b82f6; font-weight:700; color:#1e40af; padding-left:9px; }',

        /* 채점 결과 표시 */
        '.exam-box.cbt-ok  ol.circlednumbers li.cbt-selected { background:#d1fae5; border-left:3px solid #10b981; color:#065f46; }',
        '.exam-box.cbt-ok  ol.circlednumbers li.cbt-selected::after { content:" ✓"; color:#10b981; }',
        '.exam-box.cbt-ng  ol.circlednumbers li.cbt-selected { background:#fee2e2; border-left:3px solid #ef4444; color:#7f1d1d; }',
        '.exam-box.cbt-ng  ol.circlednumbers li.cbt-selected::after { content:" ✗"; color:#ef4444; }',
        '.exam-box.cbt-ng  ol.circlednumbers li.correct { background:#d1fae5 !important; border-left:3px solid #10b981 !important; }',

        /* 북마크된 체크 버튼 */
        '.chk-question.cbt-bookmarked { background:#fef3c7 !important; border-color:#f59e0b !important; color:#78350f !important; }',

        /* 플로팅 채점 버튼 */
        '#cbt-fab { position:fixed; bottom:72px; right:18px; z-index:900; display:flex; flex-direction:column; align-items:flex-end; gap:8px; }',
        '#cbt-fab-score {',
        '  background:linear-gradient(135deg,#1e3a8a,#3b82f6);',
        '  color:#fff; border:none; border-radius:50px;',
        '  padding:11px 18px; font-size:14px; font-weight:700;',
        '  box-shadow:0 4px 18px rgba(37,99,235,.45); cursor:pointer;',
        '  display:flex; align-items:center; gap:6px;',
        '  transition:transform .2s, box-shadow .2s;',
        '}',
        '#cbt-fab-score:hover { transform:translateY(-2px); box-shadow:0 7px 22px rgba(37,99,235,.55); }',
        '#cbt-fab-login {',
        '  background:#fff; color:#1e3a8a; border:2px solid #bfdbfe;',
        '  border-radius:50px; padding:8px 14px; font-size:12px; font-weight:700;',
        '  cursor:pointer; white-space:nowrap; box-shadow:0 2px 8px rgba(0,0,0,.1);',
        '  transition:all .2s; display:none;',
        '}',
        '#cbt-fab-login:hover { border-color:#3b82f6; }',
        '#cbt-fab-cbt {',
        '  background:linear-gradient(135deg,#059669,#047857);',
        '  color:#fff; border:none; border-radius:50px;',
        '  padding:11px 18px; font-size:14px; font-weight:700;',
        '  box-shadow:0 4px 18px rgba(5,150,105,.45); cursor:pointer;',
        '  display:flex; align-items:center; gap:6px;',
        '  transition:transform .2s, box-shadow .2s;',
        '}',
        '#cbt-fab-cbt:hover { transform:translateY(-2px); box-shadow:0 7px 22px rgba(5,150,105,.55); }',

        /* 채점 모달 */
        '#cbt-modal-wrap { position:fixed; inset:0; background:rgba(0,0,0,.55); z-index:1000; display:flex; align-items:center; justify-content:center; padding:1rem; }',
        '#cbt-modal-box  { background:#fff; border-radius:18px; width:100%; max-width:560px; max-height:90vh; overflow-y:auto; box-shadow:0 25px 60px rgba(0,0,0,.3); }',

        /* 토스트 */
        '#cbt-toast { position:fixed; bottom:145px; left:50%; transform:translateX(-50%); background:#1e3a8a; color:#fff; padding:10px 22px; border-radius:999px; font-size:13px; font-weight:600; z-index:1100; transition:opacity .3s; white-space:nowrap; box-shadow:0 4px 12px rgba(0,0,0,.2); pointer-events:none; }',
    ].join('\n');

    $('<style id="cbt-exam-css">').text(CSS).appendTo('head');

    /* ═══════════════════════════════════════════════
       2. 유틸
    ═══════════════════════════════════════════════ */
    function auth() { return window.CBT_AUTH || null; }

    function examMeta() {
        var parts = location.pathname.replace(/\\/g, '/').split('/');
        var file  = (parts.pop() || '').replace('.html', '');
        var cat   = parts.pop() || '미분류';
        function dec(s) { try { return decodeURIComponent(s); } catch (e) { return s; } }
        return { examId: dec(file), category: dec(cat).replace(/-/g, ' ') };
    }

    /* 루트(메인 페이지) 기준 상대경로 계산 — 마이페이지에서 링크/이미지가 열리도록 */
    function examPaths() {
        var parts   = location.pathname.replace(/\\/g, '/').split('/');
        var fileEnc = parts.pop() || '';
        var catEnc  = parts.pop() || '';
        return {
            examUrl: 'CBT/' + catEnc + '/' + fileEnc,   // 인코딩 유지 → URL 로 그대로 해석
            examDir: 'CBT/' + catEnc + '/',
        };
    }

    /* 캡처한 HTML 안의 상대 이미지경로(images/…)를 루트 기준으로 보정 */
    function rootRel(html) {
        var dir = examPaths().examDir;
        return String(html || '').replace(/(<img[^>]+src=["'])images\//gi, '$1' + dir + 'images/');
    }

    var _toastTmr = null;
    function toast(msg) {
        var $t = $('#cbt-toast');
        if (!$t.length) $t = $('<div id="cbt-toast">').appendTo('body');
        $t.text(msg).css('opacity', 1).show();
        clearTimeout(_toastTmr);
        _toastTmr = setTimeout(function () {
            $t.animate({ opacity: 0 }, 300, function () { $t.hide(); });
        }, 2600);
    }

    function esc(s) {
        return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    /* ═══════════════════════════════════════════════
       3. 답안 선택
    ═══════════════════════════════════════════════ */
    $(document).on('click', 'ol.circlednumbers li', function () {
        var $box = $(this).closest('.exam-box');
        if ($box.hasClass('cbt-scored')) return; // 채점 후 잠금
        $(this).closest('ol').find('li').removeClass('cbt-selected');
        $(this).addClass('cbt-selected');
        $box.addClass('cbt-touched');
    });

    /* ═══════════════════════════════════════════════
       4. 체크(북마크) 버튼
    ═══════════════════════════════════════════════ */
    $(document).on('click', '.chk-question', function (e) {
        e.stopPropagation();
        var a = auth();
        if (!a) return;
        if (!a.requireLogin('체크 기능은 로그인 후 이용할 수 있습니다.')) return;

        var $btn  = $(this);
        var $box  = $btn.closest('.exam-box');
        var qId   = $box.attr('question-id') || ($box.attr('id') || '').replace('#', '');
        var qText = $box.find('.exam-title').text().trim().substring(0, 200);
        var $ol   = $box.find('ol.circlednumbers');
        var opts  = $ol.find('> li').map(function (_, li) { return $(li).text().trim(); }).get();
        var corr  = parseInt($ol.attr('correct') || '0', 10);
        var meta  = examMeta();
        var paths = examPaths();

        /* 이미지 포함 보기/문제를 마이페이지에서도 보이도록 HTML 캡처 (경로 루트 기준으로 보정) */
        var $title = $box.find('.exam-title').clone();
        $title.find('.exam-number').remove();
        var qHtml = rootRel($title.html() || '').replace(/^\s*[.．]\s*/, '');
        var optsHtml = $ol.find('> li').map(function (_, li) {
            var $c = $(li).clone();
            $c.removeClass('correct');
            return rootRel($c.html() || '');
        }).get();

        var added = a.toggleBookmark({
            questionId:    qId,
            questionText:  qText,
            questionHtml:  qHtml,
            options:       opts,
            optionsHtml:   optsHtml,
            correctAnswer: corr,
            examId:        meta.examId,
            category:      meta.category,
            examUrl:       paths.examUrl,
        });

        if (added === true) {
            $btn.addClass('cbt-bookmarked').text('체크됨');
            toast('📌 북마크에 저장되었습니다!');
        } else if (added === false) {
            $btn.removeClass('cbt-bookmarked').text('체크');
            toast('북마크에서 제거되었습니다.');
        }
    });

    /* 페이지 로드 시 북마크 상태 복원 */
    $(function () {
        var a = auth();
        if (!a || !a.isLoggedIn()) return;
        $('.exam-box').each(function () {
            var qId = $(this).attr('question-id') || ($(this).attr('id') || '').replace('#', '');
            if (a.isBookmarked(qId)) {
                $(this).find('.chk-question').addClass('cbt-bookmarked').text('체크됨');
            }
        });

        // 로그인 안내 FAB 숨기기
        $('#cbt-fab-login').hide();
    });

    /* ═══════════════════════════════════════════════
       5. 플로팅 채점 버튼
    ═══════════════════════════════════════════════ */
    var $fab = $('<div id="cbt-fab">' +
        '<button id="cbt-fab-login">🔐 로그인하고 기록 저장</button>' +
        '<button id="cbt-fab-cbt"><i class="fas fa-desktop"></i> 실전 CBT 모드</button>' +
        '<button id="cbt-fab-score"><i class="fas fa-calculator"></i> 채점하기</button>' +
    '</div>');
    $('body').append($fab);

    /* ── 실전 CBT 모드 ──
       현재 페이지 DOM에서 문제를 추출해 localStorage 로 전달 후
       cbt-exam-sim.html 로 이동. fetch 를 쓰지 않아 file:// 에서도 동작. */
    function buildCbtPayload() {
        var parts  = (location.pathname || '').replace(/\\/g, '/').split('/');
        var file   = decodeURIComponent(parts.pop() || '');
        var cat    = decodeURIComponent(parts.pop() || '');
        var examId = file.replace(/\.html?$/i, '');
        var subjects = [], questions = [], curSubIdx = -1, gnum = 0;

        document.querySelectorAll('.exam-class-title, .exam-box').forEach(function (node) {
            if (node.classList.contains('exam-class-title')) {
                var t = node.textContent.trim().replace(/\s+/g, ' ');
                if (t) {
                    subjects.push({ name: t.replace(/^\d+과목\s*:\s*/, ''), start: gnum, count: 0 });
                    curSubIdx = subjects.length - 1;
                }
                return;
            }
            var ol = node.querySelector('ol.circlednumbers');
            if (!ol) return;
            var correct = parseInt(ol.getAttribute('correct'), 10) || 0;

            var titleHtml = '';
            var titleEl = node.querySelector('.exam-title');
            if (titleEl) {
                var tc = titleEl.cloneNode(true);
                var numSpan = tc.querySelector('.exam-number');
                if (numSpan) numSpan.remove();
                titleHtml = tc.innerHTML.replace(/^\s*[.．]\s*/, '');
            }
            var bodyHtml = '', seenTitle = false;
            node.querySelectorAll(':scope > .row').forEach(function (row) {
                if (row.querySelector('.exam-title')) { seenTitle = true; return; }
                if (!seenTitle || row.querySelector('.question-choice')
                    || row.querySelector('.exam-cpercent') || row.querySelector('.exam-buttons')) return;
                bodyHtml += row.innerHTML;
            });
            var options = [];
            ol.querySelectorAll(':scope > li').forEach(function (li) {
                var lc = li.cloneNode(true);
                lc.classList.remove('correct');
                options.push(lc.innerHTML);
            });

            gnum++;
            if (curSubIdx >= 0) subjects[curSubIdx].count++;
            questions.push({
                num: gnum,
                qid: node.getAttribute('question-id') || (examId + '-' + gnum),
                titleHtml: titleHtml, bodyHtml: bodyHtml,
                options: options, correct: correct, subjectIdx: curSubIdx,
            });
        });

        return {
            examId: examId,
            cat: cat.replace(/-/g, ' '),
            round: getUrlParam('round') || '',
            examDir: 'CBT/' + cat + '/',
            subjects: subjects, questions: questions,
        };
    }

    function getUrlParam(name) {
        var m = (location.search || '').match(new RegExp('[?&]' + name + '=([^&]*)'));
        if (!m) return null;
        try { return decodeURIComponent(m[1].replace(/\+/g, ' ')); } catch (e) { return m[1]; }
    }

    function launchCbtSim(autoMode) {
        var payload = buildCbtPayload();
        if (!payload.questions.length) {
            alert('이 페이지에서 문제를 찾지 못했습니다.');
            return;
        }
        var json = JSON.stringify(payload);
        /* 전달 경로 이중화:
           1차 window.name — 같은 탭 이동 간 유지, file:// 오리진 격리와 무관 (Edge 포함)
           2차 localStorage — 일반 http 환경 */
        var ok = false;
        try { window.name = 'CBTSIM1:' + json; ok = true; } catch (e) {}
        try { localStorage.setItem('cbt_sim_payload', json); ok = true; } catch (e) {}
        if (!ok) {
            alert('문제 데이터 전달에 실패했습니다.\n브라우저 저장 공간을 확인해 주세요.');
            return;
        }
        /* v=3: 캐시된 구버전 cbt-exam-sim.html 우회 */
        var url = '../../cbt-exam-sim.html?src=store&v=3';
        if (autoMode) location.replace(url);
        else location.href = url;
    }

    $('#cbt-fab-cbt').on('click', function () { launchCbtSim(false); });

    /* 뀨-Net CBT(file:// 흐름)에서 ?cbt=1 로 진입하면 자동으로 CBT 시작 */
    $(function () {
        if (getUrlParam('cbt') === '1') launchCbtSim(true);
    });

    // 비로그인 시 로그인 유도 버튼 표시
    $(function () {
        var a = auth();
        if (!a || a.isLoggedIn()) return;
        $('#cbt-fab-login').show();
        $('#cbt-fab-login').on('click', function () {
            a.requireLogin('풀이 기록을 저장하려면 로그인이 필요합니다.');
        });
    });

    $('#cbt-fab-score').on('click', doScoring);

    /* ═══════════════════════════════════════════════
       6. 채점 로직
    ═══════════════════════════════════════════════ */
    function doScoring() {
        var meta    = examMeta();
        var results = [];

        $('.exam-box').each(function () {
            var $box  = $(this);
            var qId   = $box.attr('question-id') || ($box.attr('id') || '').replace('#','');
            var qNum  = parseInt($box.attr('question-num') || '0', 10);
            var qText = $box.find('.exam-title').text().trim().substring(0, 200);
            var $ol   = $box.find('ol.circlednumbers');
            if (!$ol.length) return;

            var correct    = parseInt($ol.attr('correct') || '0', 10);
            var $sel       = $ol.find('li.cbt-selected');
            var userAnswer = $sel.length ? ($ol.find('li').index($sel) + 1) : 0;
            var isOk       = userAnswer > 0 && userAnswer === correct;
            var opts       = $ol.find('li').map(function (_, li) { return $(li).text().trim(); }).get();

            results.push({
                questionId:    qId,
                questionNum:   qNum,
                questionText:  qText,
                options:       opts,
                correctAnswer: correct,
                userAnswer:    userAnswer,
                isOk:          isOk,
            });

            // 시각 표시
            $box.addClass('cbt-scored');
            if (userAnswer > 0) $box.addClass(isOk ? 'cbt-ok' : 'cbt-ng');
        });

        var total    = results.length;
        var answered = results.filter(function (r) { return r.userAnswer > 0; }).length;
        var correct  = results.filter(function (r) { return r.isOk; }).length;
        var wrong    = answered - correct;
        var score    = total > 0 ? Math.round(correct / total * 100) : 0;

        /* ── 저장 ── */
        var a = auth();
        if (a && a.isLoggedIn()) {
            a.saveHistory({
                examId:   meta.examId,
                category: meta.category,
                totalQ:   total,
                answered: answered,
                correct:  correct,
                score:    score,
                solvedAt: new Date().toISOString(),
            });
            var wrongs = results
                .filter(function (r) { return r.userAnswer > 0 && !r.isOk; })
                .map(function (r) {
                    return {
                        questionId:    r.questionId,
                        questionText:  r.questionText,
                        options:       r.options,
                        correctAnswer: r.correctAnswer,
                        userAnswer:    r.userAnswer,
                        examId:        meta.examId,
                        category:      meta.category,
                    };
                });
            if (wrongs.length) a.saveWrong(wrongs);
        }

        showScoreModal(results, { total: total, answered: answered, correct: correct, wrong: wrong, score: score, meta: meta });
    }

    /* ═══════════════════════════════════════════════
       7. 채점 결과 모달
    ═══════════════════════════════════════════════ */
    function showScoreModal(results, s) {
        $('#cbt-modal-wrap').remove();

        var a        = auth();
        var loggedIn = a && a.isLoggedIn();
        var grade    = s.score >= 80 ? '🏆 우수' : s.score >= 60 ? '✅ 합격권' : '📚 더 노력하세요';
        var ringColor = s.score >= 60 ? '#059669' : '#dc2626';
        var ringBorder = '6px solid ' + ringColor;

        /* 점수 원형 */
        var scoreCircle =
            '<div style="display:flex;flex-direction:column;align-items:center;gap:4px;">' +
            '<div style="width:108px;height:108px;border-radius:50%;border:' + ringBorder + ';display:flex;flex-direction:column;align-items:center;justify-content:center;">' +
            '<span style="font-size:34px;font-weight:900;color:' + ringColor + ';line-height:1;">' + s.score + '</span>' +
            '<span style="font-size:13px;font-weight:700;color:' + ringColor + ';">점</span>' +
            '</div>' +
            '<p style="font-size:14px;font-weight:700;color:#374151;margin-top:8px;">' + grade + '</p>' +
            '<p style="font-size:12px;color:#6b7280;">' + esc(s.meta.category) + '</p>' +
            '</div>';

        /* 통계 박스 3개 */
        function statBox(n, label, bg, fg) {
            return '<div style="text-align:center;background:' + bg + ';border-radius:12px;padding:14px 8px;">' +
                '<p style="font-size:26px;font-weight:900;color:' + fg + ';line-height:1;">' + n + '</p>' +
                '<p style="font-size:11px;color:' + fg + ';margin-top:4px;font-weight:600;">' + label + '</p>' +
                '</div>';
        }
        var stats3 =
            '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0;">' +
            statBox(s.correct,              '정답', '#f0fdf4', '#059669') +
            statBox(s.wrong,                '오답', '#fff5f5', '#dc2626') +
            statBox(s.total - s.answered,   '미선택', '#f8fafc', '#6b7280') +
            '</div>';

        /* 저장 안내 배너 */
        var saveBanner = loggedIn
            ? '<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:10px 14px;font-size:13px;color:#166534;display:flex;align-items:center;gap:8px;">' +
              '<i class="fas fa-save"></i><span>풀이 기록 및 오답 <strong>' + s.wrong + '개</strong>가 <strong>마이페이지 → 오답노트</strong>에 저장되었습니다.</span></div>'
            : '<div style="background:#fef3c7;border:1px solid #fde68a;border-radius:10px;padding:10px 14px;font-size:13px;color:#78350f;text-align:center;">' +
              '<a href="../../login.html" style="color:#92400e;font-weight:700;text-decoration:underline;">로그인</a>하면 이 결과가 자동 저장됩니다.</div>';

        /* 오답 목록 */
        var wrongItems = results.filter(function (r) { return r.userAnswer > 0 && !r.isOk; });
        var wrongHtml  = '';
        wrongItems.forEach(function (r) {
            var uAns = r.options[r.userAnswer - 1] ? ('① ② ③ ④'.split(' ')[r.userAnswer - 1] + ' ' + esc(r.options[r.userAnswer - 1])) : r.userAnswer;
            var cAns = r.options[r.correctAnswer - 1] ? ('① ② ③ ④'.split(' ')[r.correctAnswer - 1] + ' ' + esc(r.options[r.correctAnswer - 1])) : r.correctAnswer;
            wrongHtml +=
                '<div style="border:1px solid #fecaca;border-radius:10px;padding:12px;margin-bottom:8px;background:#fff;">' +
                '<p style="font-size:13px;font-weight:700;color:#1f2937;margin-bottom:8px;line-height:1.5;">' +
                '<span style="color:#dc2626;margin-right:4px;">Q' + r.questionNum + '.</span>' + esc(r.questionText).substring(0, 90) + '…</p>' +
                '<p style="font-size:12px;color:#dc2626;margin-bottom:3px;"><i class="fas fa-times-circle" style="margin-right:4px;"></i>내 답: ' + uAns + '</p>' +
                '<p style="font-size:12px;color:#059669;"       ><i class="fas fa-check-circle" style="margin-right:4px;"></i>정답: ' + cAns + '</p>' +
                '</div>';
        });
        if (!wrongHtml) {
            wrongHtml = '<div style="text-align:center;padding:20px;color:#6b7280;font-size:14px;">틀린 문제가 없습니다! 🎉</div>';
        }

        /* 하단 버튼 */
        var myBtn = loggedIn
            ? '<a href="../../mypage.html" style="padding:10px 18px;background:#3b82f6;border-radius:8px;font-size:14px;font-weight:700;color:#fff;text-decoration:none;">마이페이지</a>'
            : '';
        var footBtns =
            '<div style="display:flex;gap:10px;justify-content:flex-end;">' +
            '<button onclick="location.reload()" style="padding:10px 18px;border:2px solid #e5e7eb;border-radius:8px;font-size:14px;font-weight:600;color:#374151;background:#fff;cursor:pointer;">다시 풀기</button>' +
            myBtn +
            '<button onclick="$(\'#cbt-modal-wrap\').remove()" style="padding:10px 18px;background:#1e3a8a;border-radius:8px;font-size:14px;font-weight:700;color:#fff;border:none;cursor:pointer;">닫기</button>' +
            '</div>';

        var modalHtml =
            '<div id="cbt-modal-wrap" onclick="if(event.target===this)$(\'#cbt-modal-wrap\').remove()">' +
            '<div id="cbt-modal-box">' +

            /* 헤더 */
            '<div style="display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid #f1f5f9;">' +
            '<h2 style="font-size:17px;font-weight:800;color:#111827;display:flex;align-items:center;gap:8px;"><i class="fas fa-clipboard-check" style="color:#3b82f6;"></i>채점 결과</h2>' +
            '<button onclick="$(\'#cbt-modal-wrap\').remove()" style="width:30px;height:30px;border-radius:50%;background:#f3f4f6;border:none;cursor:pointer;font-size:16px;color:#6b7280;display:flex;align-items:center;justify-content:center;">&times;</button>' +
            '</div>' +

            /* 본문 */
            '<div style="padding:22px;">' +
            scoreCircle + stats3 + saveBanner +
            (s.wrong > 0
                ? '<div style="margin-top:20px;"><p style="font-size:14px;font-weight:700;color:#374151;margin-bottom:10px;"><i class="fas fa-exclamation-triangle" style="color:#f59e0b;margin-right:6px;"></i>틀린 문제 (' + s.wrong + '개)</p>' + wrongHtml + '</div>'
                : '<div style="margin-top:16px;text-align:center;font-size:15px;font-weight:700;color:#059669;">🎉 전부 맞혔습니다!</div>'
            ) +
            '</div>' +

            /* 푸터 */
            '<div style="padding:14px 22px;border-top:1px solid #f1f5f9;">' + footBtns + '</div>' +

            '</div>' +
            '</div>';

        $('body').append(modalHtml);
    }

})(window.jQuery);
