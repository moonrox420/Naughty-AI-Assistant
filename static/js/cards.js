/**
 * Character Card & Presets Management Module
 */

const CardManager = {
    characters: [],
    activeCharacter: null,

    async init() {
        this.bindEvents();
        await this.loadCharacters();
    },

    bindEvents() {
        // Create new character button
        document.getElementById('btn-new-character')?.addEventListener('click', () => {
            this.openCharacterModal(null);
        });

        // Edit active character button in header
        document.getElementById('btn-edit-active-char')?.addEventListener('click', () => {
            if (this.activeCharacter) {
                this.openCharacterModal(this.activeCharacter);
            }
        });

        // Export Tavern V2 JSON card
        document.getElementById('btn-export-active-char')?.addEventListener('click', () => {
            if (this.activeCharacter) {
                window.location.href = `/api/characters/${this.activeCharacter.id}/export`;
            }
        });

        // Import Tavern Card
        const fileInput = document.getElementById('card-file-input');
        document.getElementById('btn-import-card')?.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput?.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            try {
                const text = await file.text();
                const json = JSON.parse(text);
                const res = await fetch('/api/characters/import', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(json)
                });

                if (res.ok) {
                    const imported = await res.json();
                    await this.loadCharacters();
                    this.selectCharacter(imported.id);
                } else {
                    const err = await res.json();
                    alert(`Failed to import card: ${err.detail || 'Unknown error'}`);
                }
            } catch (err) {
                alert(`Error reading character card: ${err.message}`);
            }
            fileInput.value = '';
        });

        // Save character button inside modal
        document.getElementById('btn-save-character')?.addEventListener('click', () => {
            this.saveCharacter();
        });

        // Delete character button inside modal
        document.getElementById('btn-delete-character')?.addEventListener('click', () => {
            this.deleteCharacter();
        });
    },

    async loadCharacters() {
        try {
            const res = await fetch('/api/characters');
            if (res.ok) {
                this.characters = await res.json();
                this.renderCharacterList();

                // Select default character if none selected
                if (!this.activeCharacter && this.characters.length > 0) {
                    this.selectCharacter(this.characters[0].id);
                }
            }
        } catch (err) {
            console.error('Failed to load characters:', err);
        }
    },

    renderCharacterList() {
        const container = document.getElementById('character-list');
        if (!container) return;
        container.innerHTML = '';

        this.characters.forEach(char => {
            const item = document.createElement('div');
            item.className = `character-card-item ${char.id === this.activeCharacter?.id ? 'active' : ''}`;
            item.setAttribute('data-id', char.id);

            item.innerHTML = `
                <div class="char-item-avatar">
                    ${char.avatar.startsWith('data:image') || char.avatar.startsWith('<svg') 
                        ? (char.avatar.startsWith('<svg') ? char.avatar : `<img src="${char.avatar}" alt="${escapeHtml(char.name)}">`)
                        : `<div style="font-weight:700; color:var(--accent-primary); font-size:1.1rem;">${escapeHtml(char.name.charAt(0))}</div>`}
                </div>
                <div class="char-item-info">
                    <div class="char-item-name">${escapeHtml(char.name)}</div>
                    <div class="char-item-tagline">${escapeHtml(char.tagline || char.personality || '')}</div>
                </div>
            `;

            item.addEventListener('click', () => {
                this.selectCharacter(char.id);
            });

            container.appendChild(item);
        });
    },

    selectCharacter(charId) {
        const found = this.characters.find(c => c.id === charId);
        if (!found) return;

        this.activeCharacter = found;

        // Update active class on items
        document.querySelectorAll('.character-card-item').forEach(el => {
            if (el.getAttribute('data-id') === charId) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });

        // Update Header UI
        const nameEl = document.getElementById('header-char-name');
        const taglineEl = document.getElementById('header-char-tagline');
        const avatarEl = document.getElementById('header-char-avatar');

        if (nameEl) nameEl.textContent = found.name;
        if (taglineEl) taglineEl.textContent = found.tagline || found.personality || 'In Character';
        if (avatarEl) {
            if (found.avatar.startsWith('data:image') || found.avatar.startsWith('<svg')) {
                avatarEl.innerHTML = found.avatar.startsWith('<svg') 
                    ? found.avatar 
                    : `<img src="${found.avatar}" alt="${escapeHtml(found.name)}">`;
            } else {
                avatarEl.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-weight:700;color:var(--accent-primary);font-size:1.2rem;">${escapeHtml(found.name.charAt(0))}</div>`;
            }
        }

        // Notify Chat manager to load sessions for this character
        if (window.ChatManager) {
            window.ChatManager.onCharacterSelected(found);
        }

        if (window.innerWidth <= 900 && typeof window.closeSidebar === 'function') {
            window.closeSidebar();
        }
    },

    openCharacterModal(character) {
        const isEdit = !!character;
        document.getElementById('modal-character-title').textContent = isEdit ? `Edit: ${character.name}` : 'New Character';
        document.getElementById('char-edit-id').value = isEdit ? character.id : '';
        document.getElementById('char-edit-name').value = isEdit ? character.name : '';
        document.getElementById('char-edit-tagline').value = isEdit ? (character.tagline || '') : '';
        document.getElementById('char-edit-personality').value = isEdit ? (character.personality || '') : '';
        document.getElementById('char-edit-scenario').value = isEdit ? (character.scenario || '') : '';
        document.getElementById('char-edit-description').value = isEdit ? (character.description || '') : '';
        document.getElementById('char-edit-firstmsg').value = isEdit ? (character.first_message || '') : '';
        document.getElementById('char-edit-example').value = isEdit ? (character.example_dialogue || '') : '';
        document.getElementById('char-edit-system').value = isEdit ? (character.system_prompt || '') : '';
        document.getElementById('char-edit-visual-tags').value = isEdit ? (character.visual_tags || '') : '';
        document.getElementById('char-edit-negative-prompt').value = isEdit ? (character.negative_prompt || '') : '';

        const deleteBtn = document.getElementById('btn-delete-character');
        if (deleteBtn) {
            // Can only delete custom characters, not presets
            if (isEdit && !character.is_builtin) {
                deleteBtn.style.display = 'block';
            } else {
                deleteBtn.style.display = 'none';
            }
        }

        document.getElementById('modal-character')?.classList.add('open');
    },

    async saveCharacter() {
        const id = document.getElementById('char-edit-id').value;
        const name = document.getElementById('char-edit-name').value.trim();
        if (!name) {
            alert('Character name is required.');
            return;
        }

        const payload = {
            name,
            tagline: document.getElementById('char-edit-tagline').value.trim(),
            personality: document.getElementById('char-edit-personality').value.trim(),
            scenario: document.getElementById('char-edit-scenario').value.trim(),
            description: document.getElementById('char-edit-description').value.trim(),
            first_message: document.getElementById('char-edit-firstmsg').value.trim(),
            example_dialogue: document.getElementById('char-edit-example').value.trim(),
            system_prompt: document.getElementById('char-edit-system').value.trim(),
            visual_tags: document.getElementById('char-edit-visual-tags').value.trim(),
            negative_prompt: document.getElementById('char-edit-negative-prompt').value.trim(),
        };

        try {
            const url = id ? `/api/characters/${id}` : '/api/characters';
            const method = id ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const saved = await res.json();
                await this.loadCharacters();
                this.selectCharacter(saved.id);
                document.getElementById('modal-character')?.classList.remove('open');
            } else {
                const err = await res.json();
                alert(`Error saving character: ${err.detail || 'Unknown error'}`);
            }
        } catch (err) {
            console.error('Failed to save character:', err);
        }
    },

    async deleteCharacter() {
        const id = document.getElementById('char-edit-id').value;
        if (!id) return;

        if (!confirm('Are you sure you want to delete this character and all its chats?')) {
            return;
        }

        try {
            const res = await fetch(`/api/characters/${id}`, { method: 'DELETE' });
            if (res.ok) {
                document.getElementById('modal-character')?.classList.remove('open');
                this.activeCharacter = null;
                await this.loadCharacters();
            }
        } catch (err) {
            console.error('Failed to delete character:', err);
        }
    }
};

window.CardManager = CardManager;
