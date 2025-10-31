document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    const clearBtn = document.getElementById('clearBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');

    // 메시지 전송 함수
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // 사용자 메시지 표시
        addMessageToChat(message, 'user');
        messageInput.value = '';
        sendBtn.disabled = true;
        loadingIndicator.classList.add('show');

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            if (response.ok) {
                // auth_required 자동 처리 (카카오 전용)
                let authContent = null;
                if (typeof data.response === 'object' && data.response !== null && data.response.auth_required && data.response.auth_url && data.response.provider === 'kakao') {
                    authContent = `<b>카카오 인증이 필요합니다.</b><br><a href="${data.response.auth_url}" class="kakao-login-btn">카카오 로그인</a>`;
                } else if (typeof data.response === 'string' && data.response.includes('auth_required')) {
                    // 문자열에 JSON이 섞여 온 경우만 처리하되 provider가 kakao인 경우에만 버튼 출력
                    try {
                        const jsonInString = JSON.parse(data.response);
                        if (jsonInString.auth_required && jsonInString.auth_url && jsonInString.provider === 'kakao') {
                            authContent = `<b>카카오 인증이 필요합니다.</b><br><a href="${jsonInString.auth_url}" class="kakao-login-btn">카카오 로그인</a>`;
                        }
                    } catch(e){}
                }

                // GitHub 리포지토리 표 렌더링
                let reposTableHtml = null;
                const tryBuildReposTable = (obj) => {
                    if (obj && Array.isArray(obj.repos) && obj.repos.length > 0) {
                        const rows = obj.repos.map(r => {
                            const name = (r.full_name || r.name || '').toString();
                            const url = (r.html_url || '#').toString();
                            const vis = (r.visibility !== undefined ? r.visibility : (r.private ? 'private' : 'public'));
                            const lang = (r.language || '')
                            const desc = (r.description || '')
                            const pushed = (r.pushed_at || '')
                            return `<tr>
                                <td><a href="${url}" target="_blank" rel="noopener noreferrer">${name}</a></td>
                                <td>${vis}</td>
                                <td>${lang}</td>
                                <td>${desc}</td>
                                <td>${pushed}</td>
                            </tr>`;
                        }).join('');
                        reposTableHtml = `
                            <div class="table-wrapper">
                                <table class="repo-table">
                                    <thead>
                                        <tr>
                                            <th>Repository</th>
                                            <th>Visibility</th>
                                            <th>Language</th>
                                            <th>Description</th>
                                            <th>Last Push</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${rows}
                                    </tbody>
                                </table>
                            </div>`;
                    }
                };

                // Kakao 휴일 표 렌더링
                let holidaysTableHtml = null;
                const tryBuildHolidaysTable = (obj) => {
                    if (obj && Array.isArray(obj.events) && obj.events.length > 0) {
                        const rows = obj.events.map(ev => {
                            const title = (ev.title || '').toString();
                            const t = ev.time || {};
                            const startAt = (t.start_at || '').toString();
                            const endAt = (t.end_at || '').toString();
                            const allDay = t.all_day === true ? 'Yes' : 'No';
                            const isHoliday = ev.holiday === true ? 'Yes' : 'No';
                            return `<tr>
                                <td>${title}</td>
                                <td>${startAt}</td>
                                <td>${endAt}</td>
                                <td>${allDay}</td>
                                <td>${isHoliday}</td>
                            </tr>`;
                        }).join('');
                        holidaysTableHtml = `
                            <div class="table-wrapper">
                                <table class="repo-table">
                                    <thead>
                                        <tr>
                                            <th>Title</th>
                                            <th>Start</th>
                                            <th>End</th>
                                            <th>All-day</th>
                                            <th>Holiday</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${rows}
                                    </tbody>
                                </table>
                            </div>`;
                    }
                };

                // Kakao 캘린더 목록 표 렌더링
                let calendarsTableHtml = null;
                const tryBuildCalendarsTable = (obj) => {
                    if (obj && (Array.isArray(obj.calendars) || Array.isArray(obj.subscribe_calendars))) {
                        const makeRows = (items, kind) => (items || []).map(c => {
                            const id = (c.id || '').toString();
                            const name = (c.name || '').toString();
                            const color = (c.color || '').toString();
                            const reminder = (c.reminder !== undefined && c.reminder !== null) ? c.reminder : '';
                            const reminderAll = (c.reminder_all_day !== undefined && c.reminder_all_day !== null) ? c.reminder_all_day : '';
                            return `<tr>
                                <td>${kind}</td>
                                <td>${id}</td>
                                <td>${name}</td>
                                <td>${color}</td>
                                <td>${reminder}</td>
                                <td>${reminderAll}</td>
                            </tr>`;
                        }).join('');

                        const rowsUser = makeRows(obj.calendars, 'USER');
                        const rowsSub = makeRows(obj.subscribe_calendars, 'SUBSCRIBE');
                        const rows = `${rowsUser}${rowsSub}`;
                        if (rows && rows.length > 0) {
                            calendarsTableHtml = `
                                <div class="table-wrapper">
                                    <table class="repo-table">
                                        <thead>
                                            <tr>
                                                <th>Type</th>
                                                <th>Calendar ID</th>
                                                <th>Name</th>
                                                <th>Color</th>
                                                <th>Reminder</th>
                                                <th>Reminder (All-day)</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${rows}
                                        </tbody>
                                    </table>
                                </div>`;
                        }
                    }
                };

                // Kakao 일정 목록 표 렌더링
                let eventsTableHtml = null;
                const tryBuildEventsTable = (obj) => {
                    if (obj && Array.isArray(obj.events) && obj.events.length > 0) {
                        const rows = obj.events.map(ev => {
                            const title = (ev.title || '').toString();
                            const cal = (ev.calendar_id || '').toString();
                            const color = (ev.color || '').toString();
                            const t = ev.time || {};
                            const startAt = (t.start_at || '').toString();
                            const endAt = (t.end_at || '').toString();
                            const tz = (t.time_zone || '').toString();
                            const allDay = t.all_day === true ? 'Yes' : 'No';
                            return `<tr>
                                <td>${title}</td>
                                <td>${cal}</td>
                                <td>${startAt}</td>
                                <td>${endAt}</td>
                                <td>${tz}</td>
                                <td>${allDay}</td>
                                <td>${color}</td>
                            </tr>`;
                        }).join('');
                        eventsTableHtml = `
                            <div class="table-wrapper">
                                <table class="repo-table">
                                    <thead>
                                        <tr>
                                            <th>Title</th>
                                            <th>Calendar</th>
                                            <th>Start</th>
                                            <th>End</th>
                                            <th>TZ</th>
                                            <th>All-day</th>
                                            <th>Color</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${rows}
                                    </tbody>
                                </table>
                            </div>`;
                    }
                };

                // Month calendar grid 렌더링
                let monthCalendarHtml = null;
                const tryBuildMonthCalendar = (obj) => {
                    const cv = obj && obj.calendar_view;
                    if (!cv || !Array.isArray(cv.weeks)) return;
                    const header = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
                    const thead = `<thead><tr>${header.map(h=>`<th>${h}</th>`).join('')}</tr></thead>`;
                    const rows = cv.weeks.map(week => {
                        const tds = week.map(cell => {
                            const dayCls = cell.in_month ? '' : ' style="opacity:0.35"';
                            const holidayBadges = (cell.holidays||[]).map(h=>`<div class="badge holiday">${h}</div>`).join('');
                            const eventBadges = (cell.events||[]).map(e=>`<div class="badge event" title="${e.title}">${e.title}</div>`).join('');
                            return `<td${dayCls}><div class="cal-day">${cell.day}</div>${holidayBadges}${eventBadges}</td>`;
                        }).join('');
                        return `<tr>${tds}</tr>`;
                    }).join('');
                    monthCalendarHtml = `
                        <div class="table-wrapper">
                            <div class="month-title">${cv.year}.${String(cv.month).padStart(2,'0')}</div>
                            <table class="repo-table month-cal">
                                ${thead}
                                <tbody>${rows}</tbody>
                            </table>
                        </div>`;
                };

                if (!authContent) {
                    if (typeof data.response === 'object' && data.response !== null) {
                        tryBuildReposTable(data.response);
                        tryBuildHolidaysTable(data.response);
                        tryBuildCalendarsTable(data.response);
                        tryBuildEventsTable(data.response);
                        tryBuildMonthCalendar(data.response);
                    } else if (typeof data.response === 'string') {
                        try {
                            const parsed = JSON.parse(data.response);
                            tryBuildReposTable(parsed);
                            tryBuildHolidaysTable(parsed);
                            tryBuildCalendarsTable(parsed);
                            tryBuildEventsTable(parsed);
                            tryBuildMonthCalendar(parsed);
                        } catch(e){}
                    }
                }

                if (authContent) {
                    addMessageToChat(authContent, 'ai', data.timestamp);
                } else if (reposTableHtml) {
                    addMessageToChat(reposTableHtml, 'ai', data.timestamp);
                } else if (holidaysTableHtml) {
                    addMessageToChat(holidaysTableHtml, 'ai', data.timestamp);
                } else if (calendarsTableHtml) {
                    addMessageToChat(calendarsTableHtml, 'ai', data.timestamp);
                } else if (eventsTableHtml) {
                    addMessageToChat(eventsTableHtml, 'ai', data.timestamp);
                } else if (monthCalendarHtml) {
                    addMessageToChat(monthCalendarHtml, 'ai', data.timestamp);
                } else {
                    addMessageToChat(data.response, 'ai', data.timestamp);
                }
            } else {
                // 에러 메시지 표시
                addMessageToChat(`오류: ${data.error}`, 'ai');
            }
        } catch (error) {
            console.error('Error:', error);
            addMessageToChat('네트워크 오류가 발생했습니다. 다시 시도해주세요.', 'ai');
        } finally {
            loadingIndicator.classList.remove('show');
            sendBtn.disabled = false;
            messageInput.focus();
        }
    }

    // 채팅에 메시지 추가
    function addMessageToChat(content, sender, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (sender === 'ai') {
            // Markdown 테이블을 간단히 HTML 테이블로 변환 시도
            const convertMarkdownTable = (text) => {
                try {
                    const lines = text.split('\n');
                    const startIdx = lines.findIndex(l => l.trim().startsWith('|'));
                    if (startIdx === -1) return null;
                    // 찾은 블록 추출
                    let endIdx = startIdx;
                    while (endIdx < lines.length && lines[endIdx].trim().startsWith('|')) endIdx++;
                    const block = lines.slice(startIdx, endIdx);
                    if (block.length < 2) return null; // header + separator 필요
                    const header = block[0].trim();
                    const separator = block[1].trim();
                    if (!separator.match(/^\|[-:\s|]+\|$/)) return null;
                    const rows = block.slice(2);
                    const splitCells = (row) => row.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
                    const headers = splitCells(header);
                    const thead = `<thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead>`;
                    const tbody = `<tbody>${rows.map(r=>{
                        const cells = splitCells(r);
                        return `<tr>${cells.map(c=>`<td>${c}</td>`).join('')}</tr>`;
                    }).join('')}</tbody>`;
                    const before = lines.slice(0, startIdx).join('\n');
                    const after = lines.slice(endIdx).join('\n');
                    const tableHtml = `<div class="table-wrapper"><table class="repo-table">${thead}${tbody}</table></div>`;
                    return [before, tableHtml, after].filter(Boolean).join('\n');
                } catch(_) { return null; }
            };

            let finalContent = content;
            if (typeof content === 'string' && content.includes('|')) {
                const converted = convertMarkdownTable(content);
                if (converted) finalContent = converted;
            }

            messageContent.innerHTML = `<i class="fas fa-robot"></i>${finalContent}`;
            
            // 프로필 이미지 로드 실패 처리
            messageContent.querySelectorAll('img.profile-image').forEach(img => {
                img.addEventListener('error', function() {
                    // 이미지 로드 실패 시 기본 아이콘으로 대체
                    this.style.display = 'none';
                    const fallback = document.createElement('i');
                    fallback.className = 'fas fa-user-circle';
                    fallback.style.cssText = 'font-size: 40px; color: #ccc; margin-right: 8px;';
                    this.parentNode.insertBefore(fallback, this);
                });
            });
        } else {
            messageContent.textContent = content;
        }

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = timestamp || new Date().toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        chatMessages.appendChild(messageDiv);

        // 스크롤을 맨 아래로
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 채팅 기록 삭제
    async function clearChat() {
        if (confirm('채팅 기록을 모두 삭제하시겠습니까?')) {
            try {
                const response = await fetch('/clear', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                if (response.ok) {
                    // 채팅 메시지 초기화 (시스템 메시지만 남김)
                    chatMessages.innerHTML = `
                        <div class="message ai-message">
                            <div class="message-content">
                                <i class="fas fa-robot"></i>
                                안녕하세요! 저는 AI 어시스턴트입니다. 무엇을 도와드릴까요?
                            </div>
                            <div class="message-time">시스템</div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('채팅 삭제 중 오류가 발생했습니다.');
            }
        }
    }

    // 이벤트 리스너
    sendBtn.addEventListener('click', sendMessage);
    clearBtn.addEventListener('click', clearChat);

    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 입력 필드 포커스
    messageInput.focus();

    // 입력 필드에서 타이핑할 때 버튼 활성화/비활성화
    messageInput.addEventListener('input', function() {
        sendBtn.disabled = !this.value.trim();
    });

    // 페이지 로드 시 채팅 기록 불러오기
    async function loadChatHistory() {
        try {
            const response = await fetch('/history');
            const data = await response.json();
            
            if (response.ok && data.history.length > 0) {
                // 기존 시스템 메시지 제거
                chatMessages.innerHTML = '';
                
                // 채팅 기록 표시
                data.history.forEach(msg => {
                    addMessageToChat(msg.content, msg.role, msg.timestamp);
                });
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    // 페이지 로드 시 채팅 기록 불러오기
    loadChatHistory();
});
