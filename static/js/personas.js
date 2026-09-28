/**
 * User Persona Management Module
 */

const PersonaManager = {
    activePersona: null,
    personas: [],

    async init() {
        this.bindEvents();
        await this.loadPersonas();
    },

    bindEvents() {
        document.getElementById('user-persona-btn')?.addEventListener('click', () => {
            this.openPersonaModal();
        });

        document.getElementById('btn-save-persona')?.addEventListener('click', () => {
            this.saveCurrentPersona();
        });

        document.getElementById('btn-create-new-persona')?.addEventListener('click', () => {
            this.clearPersonaForm();
        });
    },

    async loadPersonas() {
        try {
            const res = await fetch('/api/user-personas');
            if (res.ok) {
                this.personas = await res.json();
                this.activePersona = this.personas.find(p => p.is_active === 1) || this.personas[0] || null;
                this.updateSidebarUI();
            }
        } catch (err) {
            console.error('Failed to load user personas:', err);
        }
    },

    updateSidebarUI() {
        if (!this.activePersona) return;
        const nameEl = document.getElementById('user-display-name');
        const pronounsEl = document.getElementById('user-display-pronouns');
        const initialsEl = document.getElementById('user-avatar-initials');

        if (nameEl) nameEl.textContent = this.activePersona.name || 'User';
        if (pronounsEl) pronounsEl.textContent = this.activePersona.pronouns || 'they/them';
        if (initialsEl) initialsEl.textContent = (this.activePersona.name || 'U').charAt(0).toUpperCase();
    },

    openPersonaModal() {
        this.renderProfileList();
        this.fillPersonaForm(this.activePersona);
        document.getElementById('modal-persona')?.classList.add('open');
    },

    renderProfileList() {
        const container = document.getElementById('persona-profiles-list');
        if (!container) return;
        container.innerHTML = '';

        this.personas.forEach(p => {
            const item = document.createElement('div');
            item.className = `persona-profile-item ${p.id === this.activePersona?.id ? 'active' : ''}`;
            item.innerHTML = `
                <div>
                    <strong>${escapeHtml(p.name)}</strong>
                    <span style="font-size:0.72rem; color:var(--text-muted); margin-left:0.5rem;">${escapeHtml(p.pronouns || '')}</span>
                </div>
                ${p.id === this.activePersona?.id 
                    ? '<span class="badge online">Active</span>' 
                    : `<button class="btn-secondary-sm btn-activate-persona" data-id="${p.id}">Select</button>`}
            `;
            container.appendChild(item);
        });

        container.querySelectorAll('.btn-activate-persona').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const pid = btn.getAttribute('data-id');
                await this.activatePersona(pid);
            });
        });
    },

    fillPersonaForm(persona) {
        document.getElementById('persona-edit-id').value = persona ? persona.id : '';
        document.getElementById('persona-edit-name').value = persona ? persona.name : '';
        document.getElementById('persona-edit-pronouns').value = persona ? persona.pronouns : '';
        document.getElementById('persona-edit-traits').value = persona ? persona.traits : '';
        document.getElementById('persona-edit-desc').value = persona ? persona.description : '';
    },

    clearPersonaForm() {
        document.getElementById('persona-edit-id').value = '';
        document.getElementById('persona-edit-name').value = 'New Persona';
        document.getElementById('persona-edit-pronouns').value = 'they/them';
        document.getElementById('persona-edit-traits').value = '';
        document.getElementById('persona-edit-desc').value = '';
        document.getElementById('persona-edit-name').focus();
    },

    async activatePersona(personaId) {
        try {
            const res = await fetch(`/api/user-personas/${personaId}/activate`, { method: 'POST' });
            if (res.ok) {
                await this.loadPersonas();
                this.renderProfileList();
                this.fillPersonaForm(this.activePersona);
            }
        } catch (err) {
            console.error('Failed to activate persona:', err);
        }
    },

    async saveCurrentPersona() {
        const id = document.getElementById('persona-edit-id').value;
        const name = document.getElementById('persona-edit-name').value.trim() || 'User';
        const pronouns = document.getElementById('persona-edit-pronouns').value.trim();
        const traits = document.getElementById('persona-edit-traits').value.trim();
        const description = document.getElementById('persona-edit-desc').value.trim();

        const payload = { name, pronouns, traits, description, is_active: 1 };

        try {
            const url = id ? `/api/user-personas/${id}` : '/api/user-personas';
            const method = id ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                await this.loadPersonas();
                document.getElementById('modal-persona')?.classList.remove('open');
            }
        } catch (err) {
            console.error('Failed to save persona:', err);
        }
    }
};

window.PersonaManager = PersonaManager;
