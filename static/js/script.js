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
                // AI 응답 표시
                addMessageToChat(data.response, 'ai', data.timestamp);
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
            messageContent.innerHTML = `<i class="fas fa-robot"></i>${content}`;
            
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
