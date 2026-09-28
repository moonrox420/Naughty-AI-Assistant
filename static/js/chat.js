/**
 * Real-time Chat, WebSocket Streaming & Roleplay Controls
 */

const ChatManager = {
    activeCharacter: null,
    activeSession: null,
    sessions: [],
    messages: [],
    socket: null,
    isStreaming: false,
    isGeneratingImage: false,
    activeStreamingBubble: null,
    activeStreamingContent: "",

    init() {
        this.bindEvents();
    },

    bindEvents() {
        // Send message button & Enter key
        const textarea = document.getElementById('chat-textarea');
        const sendBtn = document.getElementById('btn-send-message');
        const stopBtn = document.getElementById('btn-stop-stream');

        sendBtn?.addEventListener('click', () => this.sendMessage());

        textarea?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-expand textarea
        textarea?.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
        });

        // Stop stream button
        stopBtn?.addEventListener('click', () => this.stopStreaming());

        // New Session button
        document.getElementById('btn-new-session')?.addEventListener('click', () => {
            if (this.activeCharacter) {
                this.createSession(this.activeCharacter.id);
            }
        });

        // Memory Drawer toggles
        document.getElementById('btn-toggle-memory')?.addEventListener('click', () => {
            document.getElementById('memory-drawer')?.classList.toggle('open');
            if (this.activeSession) {
                this.loadMemoryFacts();
            }
        });

        document.getElementById('btn-close-memory')?.addEventListener('click', () => {
            document.getElementById('memory-drawer')?.classList.remove('open');
        });

        document.getElementById('btn-save-scratchpad')?.addEventListener('click', () => {
            this.saveScratchpad();
        });

        document.getElementById('btn-add-fact')?.addEventListener('click', () => {
            this.addManualFact();
        });

        document.getElementById('btn-refresh-facts')?.addEventListener('click', () => {
            this.loadMemoryFacts();
        });

        // Lightbox close
        document.getElementById('btn-close-lightbox')?.addEventListener('click', () => {
            document.getElementById('modal-lightbox')?.classList.remove('open');
        });

        document.getElementById('modal-lightbox')?.addEventListener('click', (e) => {
            if (e.target.id === 'modal-lightbox') {
                document.getElementById('modal-lightbox')?.classList.remove('open');
            }
        });
    },

    async onCharacterSelected(character) {
        this.activeCharacter = character;
        await this.loadSessionsForCharacter(character.id);
    },

    async loadSessionsForCharacter(characterId) {
        try {
            const res = await fetch(`/api/characters/${characterId}/sessions`);
            if (res.ok) {
                this.sessions = await res.json();
                this.renderSessionList();

                if (this.sessions.length > 0) {
                    this.selectSession(this.sessions[0].id);
                } else {
                    await this.createSession(characterId);
                }
            }
        } catch (err) {
            console.error('Failed to load sessions:', err);
        }
    },

    renderSessionList() {
        const container = document.getElementById('session-list');
        if (!container) return;
        container.innerHTML = '';

        this.sessions.forEach(sess => {
            const item = document.createElement('div');
            item.className = `session-item ${sess.id === this.activeSession?.id ? 'active' : ''}`;
            item.setAttribute('data-id', sess.id);

            item.innerHTML = `
                <span class="session-title-text" title="${escapeHtml(sess.title)}">${escapeHtml(sess.title)}</span>
                <div class="session-actions">
                    <button class="icon-btn-sm btn-delete-sess" title="Delete Chat" data-id="${sess.id}">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            `;

            item.addEventListener('click', (e) => {
                if (e.target.closest('.btn-delete-sess')) return;
                this.selectSession(sess.id);
            });

            const delBtn = item.querySelector('.btn-delete-sess');
            delBtn?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSession(sess.id);
            });

            container.appendChild(item);
        });
    },

    async createSession(characterId) {
        try {
            const res = await fetch(`/api/characters/${characterId}/sessions`, { method: 'POST' });
            if (res.ok) {
                const newSess = await res.json();
                this.sessions.unshift(newSess);
                this.renderSessionList();
                await this.selectSession(newSess.id);
            }
        } catch (err) {
            console.error('Failed to create session:', err);
        }
    },

    async selectSession(sessionId) {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }

        try {
            const res = await fetch(`/api/sessions/${sessionId}`);
            if (res.ok) {
                const data = await res.json();
                this.activeSession = data.session;
                this.messages = data.messages || [];

                // Update UI active class
                document.querySelectorAll('.session-item').forEach(el => {
                    el.classList.toggle('active', el.getAttribute('data-id') === sessionId);
                });

                // Set scratchpad
                const scratchpad = document.getElementById('session-memory-scratchpad');
                if (scratchpad) {
                    scratchpad.value = this.activeSession.memory_notes || '';
                }

                this.renderMessages();
                this.connectWebSocket(sessionId);
                this.loadMemoryFacts();

                if (window.innerWidth <= 900 && typeof window.closeSidebar === 'function') {
                    window.closeSidebar();
                }
            }
        } catch (err) {
            console.error('Failed to select session:', err);
        }
    },

    async deleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this chat session?')) return;

        try {
            const res = await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
            if (res.ok) {
                this.sessions = this.sessions.filter(s => s.id !== sessionId);
                this.renderSessionList();
                if (this.activeSession?.id === sessionId) {
                    if (this.sessions.length > 0) {
                        this.selectSession(this.sessions[0].id);
                    } else if (this.activeCharacter) {
                        this.createSession(this.activeCharacter.id);
                    }
                }
            }
        } catch (err) {
            console.error('Failed to delete session:', err);
        }
    },

    connectWebSocket(sessionId) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${sessionId}`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log(`WebSocket connected to session ${sessionId}`);
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleSocketEvent(data);
            } catch (err) {
                console.error('WebSocket parse error:', err);
            }
        };

        this.socket.onclose = () => {
            console.log('WebSocket closed');
            this.setStreamingState(false);
        };

        this.socket.onerror = (err) => {
            console.error('WebSocket error:', err);
            this.setStreamingState(false);
        };
    },

    handleSocketEvent(data) {
        const event = data.event;

        if (event === 'user_saved') {
            this.messages.push(data.message);
            this.renderMessages();
        } else if (event === 'stream_start') {
            this.setStreamingState(true);

            if (data.is_regenerate || data.is_continue) {
                // Find existing bubble to stream into
                const targetMsg = this.messages.find(m => m.id === data.target_id);
                this.activeStreamingContent = data.is_continue ? (targetMsg ? targetMsg.content + " " : "") : "";
                this.activeStreamingBubble = document.getElementById(`msg-body-${data.target_id}`);
            } else {
                // New assistant turn placeholder
                this.activeStreamingContent = "";
                this.appendStreamingBubble();
            }
        } else if (event === 'stream_chunk') {
            this.activeStreamingContent += data.delta;
            if (this.activeStreamingBubble) {
                this.activeStreamingBubble.innerHTML = formatRoleplayMarkdown(this.activeStreamingContent);
                this.scrollToBottom();
            }
        } else if (event === 'stream_done') {
            this.setStreamingState(false);
            if (data.message) {
                // If it replaced/updated a message (e.g. regenerate or continue)
                const existingIdx = this.messages.findIndex(m => m.id === data.message.id);
                if (existingIdx !== -1) {
                    this.messages[existingIdx] = data.message;
                } else {
                    this.messages.push(data.message);
                }
            }
            this.renderMessages();
            this.loadMemoryFacts();
        } else if (event === 'stopped') {
            this.setStreamingState(false);
        } else if (event === 'error') {
            alert(`Assistant error: ${data.message}`);
            this.setStreamingState(false);
        }
    },

    setStreamingState(streaming) {
        this.isStreaming = streaming;
        const stopBtn = document.getElementById('btn-stop-stream');
        const sendBtn = document.getElementById('btn-send-message');
        const statusEl = document.getElementById('header-char-tagline');

        if (stopBtn) stopBtn.classList.toggle('hidden', !streaming);
        if (sendBtn) sendBtn.style.display = streaming ? 'none' : 'flex';
        if (statusEl) {
            if (streaming) {
                statusEl.textContent = 'Thinking and writing...';
            } else if (this.isGeneratingImage) {
                statusEl.textContent = 'Rendering photo with Forge (GPU busy)...';
            } else {
                statusEl.textContent = this.activeCharacter?.tagline || 'In Character';
            }
        }

        // Disable photo buttons during LLM streaming to protect GPU VRAM
        document.querySelectorAll('.btn-photo-turn').forEach(b => {
            b.disabled = streaming || this.isGeneratingImage;
            b.style.opacity = (streaming || this.isGeneratingImage) ? '0.5' : '1';
            b.style.pointerEvents = (streaming || this.isGeneratingImage) ? 'none' : 'auto';
        });
    },

    async sendMessage() {
        const textarea = document.getElementById('chat-textarea');
        const text = textarea?.value.trim();
        if (!text || this.isStreaming || this.isGeneratingImage) {
            return;
        }

        // Slash command: /image <optional prompt>
        if (text.startsWith('/image')) {
            const promptOverride = text.replace(/^\/image\s*/i, '').trim();
            textarea.value = '';
            textarea.style.height = 'auto';
            await this.handleSlashImageCommand(promptOverride);
            return;
        }

        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            alert('Chat connection is not open. Please reload or select a session.');
            return;
        }

        const genParams = SettingsManager ? SettingsManager.settings : {};
        const payload = {
            action: 'send',
            content: text,
            params: genParams
        };

        this.socket.send(JSON.stringify(payload));
        textarea.value = '';
        textarea.style.height = 'auto';
    },

    async handleSlashImageCommand(promptOverride) {
        if (!this.activeSession || !this.activeCharacter) {
            alert('Please select a character and session first.');
            return;
        }

        if (this.isStreaming || this.isGeneratingImage) {
            alert('GPU is currently busy. Please wait for current generation to complete.');
            return;
        }

        try {
            // 1. Post user command message
            const userContent = promptOverride ? `/image ${promptOverride}` : '/image';
            const userRes = await fetch(`/api/sessions/${this.activeSession.id}/messages`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: 'user', content: userContent })
            });

            if (userRes.ok) {
                const userMsg = await userRes.json();
                this.messages.push(userMsg);
            }

            // 2. Post assistant response placeholder message
            const assistantContent = promptOverride 
                ? `*Prepares a photograph matching: "${promptOverride}"*`
                : `*Takes a photo of herself for you...*`;

            const asstRes = await fetch(`/api/sessions/${this.activeSession.id}/messages`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: 'assistant', content: assistantContent })
            });

            if (asstRes.ok) {
                const asstMsg = await asstRes.json();
                this.messages.push(asstMsg);
                this.renderMessages();
                // 3. Generate photo for this assistant turn
                await this.generatePhotoForMessage(asstMsg.id, promptOverride);
            }
        } catch (err) {
            console.error('Error handling /image command:', err);
            alert(`Failed to execute /image: ${err.message}`);
        }
    },

    async generatePhotoForMessage(messageId, promptOverride = "") {
        if (!this.activeCharacter || !this.activeSession) return;

        if (this.isStreaming || this.isGeneratingImage) {
            alert('GPU is currently processing another request. Please wait a moment.');
            return;
        }

        const msgBody = document.getElementById(`msg-body-${messageId}`);
        if (!msgBody) return;

        this.isGeneratingImage = true;
        this.setStreamingState(false);

        const statusEl = document.getElementById('header-char-tagline');
        if (statusEl) {
            statusEl.textContent = 'Rendering photo with Stable Diffusion Forge...';
        }

        // Add visual spinner placeholder into the target bubble
        const loader = document.createElement('div');
        loader.className = 'img-generating-placeholder';
        loader.id = `img-loader-${messageId}`;
        loader.innerHTML = `
            <div class="spinner-small"></div>
            <span>Generating photo with Stable Diffusion Forge (exclusive GPU lock)...</span>
        `;
        msgBody.appendChild(loader);
        this.scrollToBottom();

        try {
            const width = SettingsManager?.settings?.image_width ? parseInt(SettingsManager.settings.image_width) : 512;
            const height = SettingsManager?.settings?.image_height ? parseInt(SettingsManager.settings.image_height) : 768;

            const res = await fetch('/api/image/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character_id: this.activeCharacter.id,
                    session_id: this.activeSession.id,
                    message_id: messageId,
                    prompt_override: promptOverride || null,
                    width: width,
                    height: height
                })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                const errMsg = errData.detail || errData.error || `Server returned error ${res.status}`;
                throw new Error(errMsg);
            }

            const data = await res.json();
            if (data.success && data.image_url) {
                const targetMsg = this.messages.find(m => m.id === messageId);
                if (targetMsg) {
                    targetMsg.image_url = data.image_url;
                }
                this.renderMessages();
            } else {
                throw new Error(data.error || 'Failed to render image.');
            }
        } catch (err) {
            console.error('Image generation failed:', err);
            alert(`Image Generation Failed: ${err.message}\n\nPlease verify that Stable Diffusion Forge is running at port 7860.`);
            loader.remove();
        } finally {
            this.isGeneratingImage = false;
            const activeLoader = document.getElementById(`img-loader-${messageId}`);
            if (activeLoader) activeLoader.remove();
            this.setStreamingState(false);
        }
    },

    openLightbox(imgUrl, caption = "") {
        const modal = document.getElementById('modal-lightbox');
        const img = document.getElementById('lightbox-img');
        const cap = document.getElementById('lightbox-caption');
        if (modal && img) {
            img.src = imgUrl;
            if (cap) cap.textContent = caption;
            modal.classList.add('open');
        }
    },

    stopStreaming() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ action: 'stop' }));
        }
        this.setStreamingState(false);
    },

    regenerateMessage(messageId) {
        if (this.isStreaming || !this.socket || this.socket.readyState !== WebSocket.OPEN) return;
        const genParams = SettingsManager ? SettingsManager.settings : {};
        this.socket.send(JSON.stringify({
            action: 'regenerate',
            message_id: messageId,
            params: genParams
        }));
    },

    continueMessage(messageId) {
        if (this.isStreaming || !this.socket || this.socket.readyState !== WebSocket.OPEN) return;
        const genParams = SettingsManager ? SettingsManager.settings : {};
        this.socket.send(JSON.stringify({
            action: 'continue',
            message_id: messageId,
            params: genParams
        }));
    },

    async swipeMessage(messageId, direction) {
        const msg = this.messages.find(m => m.id === messageId);
        if (!msg || !msg.alternatives || msg.alternatives.length <= 1) return;

        let nextIdx = msg.swipe_index + direction;
        if (nextIdx < 0) nextIdx = msg.alternatives.length - 1;
        if (nextIdx >= msg.alternatives.length) nextIdx = 0;

        try {
            const res = await fetch(`/api/messages/${messageId}/swipe`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ swipe_index: nextIdx })
            });

            if (res.ok) {
                const updated = await res.json();
                const idx = this.messages.findIndex(m => m.id === messageId);
                if (idx !== -1) {
                    this.messages[idx] = updated;
                    this.renderMessages();
                }
            }
        } catch (err) {
            console.error('Failed to swipe message:', err);
        }
    },

    async deleteMessage(messageId) {
        if (!confirm('Delete this message?')) return;
        try {
            const res = await fetch(`/api/messages/${messageId}`, { method: 'DELETE' });
            if (res.ok) {
                this.messages = this.messages.filter(m => m.id !== messageId);
                this.renderMessages();
            }
        } catch (err) {
            console.error('Failed to delete message:', err);
        }
    },

    openInlineEdit(messageId) {
        const msg = this.messages.find(m => m.id === messageId);
        const bodyEl = document.getElementById(`msg-body-${messageId}`);
        if (!msg || !bodyEl) return;

        bodyEl.innerHTML = `
            <textarea class="inline-edit-area" id="edit-input-${messageId}">${escapeHtml(msg.content)}</textarea>
            <div class="inline-edit-actions">
                <button class="btn-secondary-sm" id="btn-cancel-edit-${messageId}">Cancel</button>
                <button class="btn-primary-sm" id="btn-save-edit-${messageId}">Save</button>
            </div>
        `;

        document.getElementById(`btn-cancel-edit-${messageId}`)?.addEventListener('click', () => {
            this.renderMessages();
        });

        document.getElementById(`btn-save-edit-${messageId}`)?.addEventListener('click', async () => {
            const newContent = document.getElementById(`edit-input-${messageId}`).value.trim();
            if (newContent) {
                await this.saveEditedMessage(messageId, newContent);
            }
        });
    },

    async saveEditedMessage(messageId, newContent) {
        try {
            const res = await fetch(`/api/messages/${messageId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: newContent })
            });

            if (res.ok) {
                const msg = this.messages.find(m => m.id === messageId);
                if (msg) {
                    msg.content = newContent;
                    if (msg.alternatives && msg.alternatives[msg.swipe_index] !== undefined) {
                        msg.alternatives[msg.swipe_index] = newContent;
                    }
                }
                this.renderMessages();
            }
        } catch (err) {
            console.error('Failed to save edited message:', err);
        }
    },

    renderMessages() {
        const container = document.getElementById('chat-messages-container');
        if (!container) return;

        if (this.messages.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                        </svg>
                    </div>
                    <h3>Conversation Ready</h3>
                    <p>Send a message below to start your private interaction with ${escapeHtml(this.activeCharacter?.name || 'your companion')}.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';

        this.messages.forEach(msg => {
            const bubble = document.createElement('div');
            bubble.className = `message-bubble ${msg.role}`;
            bubble.id = `msg-wrap-${msg.id}`;

            const senderName = msg.role === 'user' 
                ? (PersonaManager?.activePersona?.name || 'You') 
                : (this.activeCharacter?.name || 'Companion');

            const hasAlternatives = msg.alternatives && msg.alternatives.length > 1;
            const swipeCurrent = (msg.swipe_index || 0) + 1;
            const swipeTotal = msg.alternatives ? msg.alternatives.length : 1;

            const hasImage = Boolean(msg.image_url && msg.image_url.trim());

            bubble.innerHTML = `
                <div class="msg-header">
                    <span>${escapeHtml(senderName)}</span>
                </div>
                <div class="msg-body-wrapper">
                    ${hasImage ? `
                        <div class="msg-image-attachment" data-img="${escapeHtml(msg.image_url)}" title="Click to view full photo">
                            <img src="${escapeHtml(msg.image_url)}" alt="Generated Scene" loading="lazy" />
                        </div>
                    ` : ''}
                    <div class="msg-content" id="msg-body-${msg.id}">
                        ${formatRoleplayMarkdown(msg.content)}
                    </div>
                    <div class="msg-toolbar">
                        ${msg.role === 'assistant' && hasAlternatives ? `
                            <div class="swipe-pager">
                                <button class="icon-btn-sm btn-swipe-left" data-id="${msg.id}" title="Previous Alternative">◀</button>
                                <span>${swipeCurrent}/${swipeTotal}</span>
                                <button class="icon-btn-sm btn-swipe-right" data-id="${msg.id}" title="Next Alternative">▶</button>
                            </div>
                        ` : ''}
                        ${msg.role === 'assistant' ? `
                            <button class="tool-btn photo btn-photo-turn" data-id="${msg.id}" title="Generate scene photo with Stable Diffusion Forge">
                                📸 Photo
                            </button>
                            <button class="tool-btn btn-regen-turn" data-id="${msg.id}" title="Regenerate new swipe alternative">
                                ↺ Swipe
                            </button>
                            <button class="tool-btn btn-continue-turn" data-id="${msg.id}" title="Continue writing">
                                ➔ Continue
                            </button>
                        ` : ''}
                        <button class="tool-btn btn-edit-turn" data-id="${msg.id}" title="Edit message text">
                            Edit
                        </button>
                        <button class="tool-btn danger btn-del-turn" data-id="${msg.id}" title="Delete message">
                            Delete
                        </button>
                    </div>
                </div>
            `;

            // Bind toolbar events
            bubble.querySelector('.btn-photo-turn')?.addEventListener('click', () => {
                this.generatePhotoForMessage(msg.id);
            });

            bubble.querySelector('.msg-image-attachment')?.addEventListener('click', () => {
                this.openLightbox(msg.image_url, `${senderName} - Scene Visual`);
            });

            bubble.querySelector('.btn-edit-turn')?.addEventListener('click', () => {
                this.openInlineEdit(msg.id);
            });

            bubble.querySelector('.btn-del-turn')?.addEventListener('click', () => {
                this.deleteMessage(msg.id);
            });

            bubble.querySelector('.btn-regen-turn')?.addEventListener('click', () => {
                this.regenerateMessage(msg.id);
            });

            bubble.querySelector('.btn-continue-turn')?.addEventListener('click', () => {
                this.continueMessage(msg.id);
            });

            bubble.querySelector('.btn-swipe-left')?.addEventListener('click', () => {
                this.swipeMessage(msg.id, -1);
            });

            bubble.querySelector('.btn-swipe-right')?.addEventListener('click', () => {
                this.swipeMessage(msg.id, 1);
            });

            container.appendChild(bubble);
        });

        this.scrollToBottom();
    },

    appendStreamingBubble() {
        const container = document.getElementById('chat-messages-container');
        if (!container) return;

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble assistant';
        bubble.id = 'streaming-temp-bubble';

        bubble.innerHTML = `
            <div class="msg-header">
                <span>${escapeHtml(this.activeCharacter?.name || 'Companion')}</span>
            </div>
            <div class="msg-body-wrapper">
                <div class="msg-content" id="streaming-content-target"></div>
            </div>
        `;

        container.appendChild(bubble);
        this.activeStreamingBubble = document.getElementById('streaming-content-target');
        this.scrollToBottom();
    },

    scrollToBottom() {
        const container = document.getElementById('chat-messages-container');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    },

    // --- Persistent Memory Drawer Methods ---
    async loadMemoryFacts() {
        if (!this.activeSession) return;
        try {
            const res = await fetch(`/api/sessions/${this.activeSession.id}/facts`);
            if (res.ok) {
                const facts = await res.json();
                this.renderMemoryFacts(facts);
            }
        } catch (err) {
            console.error('Failed to load facts:', err);
        }
    },

    renderMemoryFacts(facts) {
        const list = document.getElementById('memory-facts-list');
        if (!list) return;
        list.innerHTML = '';

        if (facts.length === 0) {
            list.innerHTML = '<div style="font-size:0.75rem; color:var(--text-muted); padding:0.5rem 0;">No facts extracted yet. As you talk, details will appear here automatically.</div>';
            return;
        }

        facts.forEach(f => {
            const item = document.createElement('div');
            item.className = 'fact-item';
            item.innerHTML = `
                <div>
                    <span class="fact-badge">${escapeHtml(f.category)}</span>
                    <span>${escapeHtml(f.fact_text)}</span>
                </div>
                <button class="icon-btn-sm btn-del-fact" data-id="${f.id}" title="Remove memory">✕</button>
            `;

            item.querySelector('.btn-del-fact')?.addEventListener('click', async () => {
                await this.deleteFact(f.id);
            });

            list.appendChild(item);
        });
    },

    async addManualFact() {
        const input = document.getElementById('input-new-fact');
        const text = input?.value.trim();
        if (!text || !this.activeSession) return;

        try {
            const res = await fetch(`/api/sessions/${this.activeSession.id}/facts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fact_text: text, category: 'general' })
            });

            if (res.ok) {
                input.value = '';
                await this.loadMemoryFacts();
            }
        } catch (err) {
            console.error('Failed to add fact:', err);
        }
    },

    async deleteFact(factId) {
        try {
            const res = await fetch(`/api/facts/${factId}`, { method: 'DELETE' });
            if (res.ok) {
                await this.loadMemoryFacts();
            }
        } catch (err) {
            console.error('Failed to delete fact:', err);
        }
    },

    async saveScratchpad() {
        const scratchpad = document.getElementById('session-memory-scratchpad');
        const notes = scratchpad?.value || '';
        if (!this.activeSession) return;

        try {
            const res = await fetch(`/api/sessions/${this.activeSession.id}/memory`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ memory_notes: notes })
            });

            if (res.ok) {
                const btn = document.getElementById('btn-save-scratchpad');
                if (btn) {
                    btn.textContent = 'Saved!';
                    setTimeout(() => { btn.textContent = 'Save Scratchpad'; }, 1500);
                }
            }
        } catch (err) {
            console.error('Failed to save scratchpad:', err);
        }
    }
};

window.ChatManager = ChatManager;
