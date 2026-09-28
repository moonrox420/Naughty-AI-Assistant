/**
 * Inference Runner & Settings Controller
 */

const SettingsManager = {
    settings: {
        runner: "ollama",
        model: "",
        temperature: 0.85,
        top_p: 0.90,
        min_p: 0.05,
        repeat_penalty: 1.15,
        max_tokens: 2048,
    },
    runnersStatus: {},
    availableModels: [],

    async init() {
        this.bindEvents();
        await this.loadSettings();
        await this.refreshModels();
    },

    bindEvents() {
        // Slider value update reflections
        const syncSlider = (id, valId, decimals = 2) => {
            const slider = document.getElementById(id);
            const valDisplay = document.getElementById(valId);
            if (slider && valDisplay) {
                slider.addEventListener('input', () => {
                    const v = parseFloat(slider.value);
                    valDisplay.textContent = decimals === 0 ? v : v.toFixed(decimals);
                });
            }
        };

        syncSlider('param-temp', 'val-temp', 2);
        syncSlider('param-topp', 'val-topp', 2);
        syncSlider('param-reppen', 'val-reppen', 2);
        syncSlider('param-maxtok', 'val-maxtok', 0);

        // Runner selector toggle buttons
        document.querySelectorAll('.runner-selector .btn-toggle').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.runner-selector .btn-toggle').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.settings.runner = btn.getAttribute('data-runner');
                this.filterModelsForRunner();
            });
        });

        // Refresh models button
        document.getElementById('btn-refresh-models')?.addEventListener('click', () => {
            this.refreshModels();
        });

        // Launch Forge in background button
        document.getElementById('btn-launch-forge')?.addEventListener('click', () => {
            this.launchForgeBackground();
        });

        // Save settings button
        document.getElementById('btn-save-settings')?.addEventListener('click', () => {
            this.saveSettings();
        });

        // Open settings modal
        document.getElementById('btn-open-settings')?.addEventListener('click', () => {
            this.openSettingsModal();
        });
    },

    async loadSettings() {
        try {
            const res = await fetch('/api/settings');
            if (res.ok) {
                const data = await res.json();
                this.settings = { ...this.settings, ...data };
                this.updateUIFromSettings();
            }
        } catch (err) {
            console.error('Failed to load settings:', err);
        }
    },

    updateUIFromSettings() {
        // Runner toggles
        document.querySelectorAll('.runner-selector .btn-toggle').forEach(btn => {
            if (btn.getAttribute('data-runner') === this.settings.runner) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Sliders
        const setSlider = (id, valId, val, decimals = 2) => {
            const slider = document.getElementById(id);
            const valDisplay = document.getElementById(valId);
            if (slider && valDisplay && val !== undefined) {
                slider.value = val;
                valDisplay.textContent = decimals === 0 ? val : parseFloat(val).toFixed(decimals);
            }
        };

        setSlider('param-temp', 'val-temp', this.settings.temperature, 2);
        setSlider('param-topp', 'val-topp', this.settings.top_p, 2);
        setSlider('param-reppen', 'val-reppen', this.settings.repeat_penalty, 2);
        setSlider('param-maxtok', 'val-maxtok', this.settings.max_tokens, 0);

        this.updateHeaderModelBadge();
    },

    updateHeaderModelBadge() {
        const badge = document.getElementById('header-active-model');
        if (badge) {
            badge.textContent = this.settings.model || 'No Model Selected';
        }
    },

    async refreshModels() {
        const statusText = document.getElementById('runner-probe-status');
        const runnerBadge = document.getElementById('runner-status-badge');
        if (statusText) statusText.textContent = 'Probing local runners (Ollama & LM Studio)...';

        try {
            const res = await fetch('/api/models');
            if (res.ok) {
                const data = await res.json();
                this.runnersStatus = data;
                this.availableModels = data.models || [];

                // Update runner status badge
                const ollamaOnline = data.ollama?.online;
                const lmOnline = data.lmstudio?.online;

                if (runnerBadge) {
                    if (ollamaOnline || lmOnline) {
                        runnerBadge.className = 'badge online';
                        runnerBadge.textContent = ollamaOnline ? 'Ollama Online' : 'LM Studio Online';
                    } else {
                        runnerBadge.className = 'badge offline';
                        runnerBadge.textContent = 'Runners Offline';
                    }
                }

                if (statusText) {
                    if (this.availableModels.length === 0) {
                        statusText.innerHTML = '<span style="color:#f59e0b">No running models found. Start Ollama (<code>ollama serve</code>) or start the LM Studio local server.</span>';
                    } else {
                        statusText.textContent = `Found ${this.availableModels.length} models across active runners.`;
                    }
                }

                this.filterModelsForRunner();
            }
        } catch (err) {
            console.error('Failed to probe models:', err);
            if (statusText) statusText.textContent = 'Failed to connect to local API.';
        }
    },

    filterModelsForRunner() {
        const select = document.getElementById('select-model');
        if (!select) return;

        select.innerHTML = '';
        const currentRunner = this.settings.runner;

        const filtered = this.availableModels.filter(m => m.runner === currentRunner);
        if (filtered.length === 0) {
            const opt = document.createElement('option');
            opt.value = "";
            opt.textContent = `No models found for ${currentRunner}. (Is it running?)`;
            select.appendChild(opt);
        } else {
            filtered.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.size ? `${m.name} (${m.size})` : m.name;
                if (m.id === this.settings.model) {
                    opt.selected = true;
                }
                select.appendChild(opt);
            });

            // If active model wasn't set or not in list, pick the first
            if (!this.settings.model || !filtered.some(m => m.id === this.settings.model)) {
                this.settings.model = filtered[0].id;
                select.value = this.settings.model;
                this.updateHeaderModelBadge();
            }
        }
    },

    openSettingsModal() {
        this.updateUIFromSettings();
        this.filterModelsForRunner();
        this.checkForgeStatus();
        document.getElementById('modal-settings')?.classList.add('open');
    },

    async checkForgeStatus() {
        const badge = document.getElementById('forge-status-badge');
        const select = document.getElementById('select-sd-model');
        try {
            const res = await fetch('/api/image/status');
            if (res.ok) {
                const data = await res.json();
                if (badge) {
                    if (data.online) {
                        badge.className = 'badge online';
                        badge.textContent = `Online (${data.count} models)`;
                    } else {
                        badge.className = 'badge offline';
                        badge.textContent = 'Offline';
                    }
                }

                if (select && data.checkpoints) {
                    select.innerHTML = '';
                    if (data.checkpoints.length === 0) {
                        select.innerHTML = '<option value="">No checkpoints found in Forge</option>';
                    } else {
                        data.checkpoints.forEach(cp => {
                            const opt = document.createElement('option');
                            opt.value = cp.title;
                            opt.textContent = cp.model_name || cp.title;
                            select.appendChild(opt);
                        });
                    }
                }
                return data.online;
            }
        } catch (err) {
            if (badge) {
                badge.className = 'badge offline';
                badge.textContent = 'Offline';
            }
        }
        return false;
    },

    async launchForgeBackground() {
        const btn = document.getElementById('btn-launch-forge');
        const hint = document.getElementById('forge-launch-hint');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Launching Forge...';
        }

        try {
            const res = await fetch('/api/image/launch', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                if (hint) hint.innerHTML = '<span style="color:#10b981">✓ Forge process started. Waiting for API port 7860 to respond...</span>';

                // Poll status every 3 seconds for up to 60 seconds
                let attempts = 0;
                const interval = setInterval(async () => {
                    attempts++;
                    const online = await this.checkForgeStatus();
                    if (online) {
                        clearInterval(interval);
                        if (btn) {
                            btn.disabled = false;
                            btn.textContent = 'Forge is Online ✓';
                        }
                        if (hint) hint.innerHTML = '<span style="color:#10b981">✓ Connected to Forge on port 7860!</span>';
                    } else if (attempts > 20) {
                        clearInterval(interval);
                        if (btn) {
                            btn.disabled = false;
                            btn.textContent = 'Launch Forge in Background';
                        }
                        if (hint) hint.textContent = 'Check webui-user.bat console if it is still loading weights.';
                    }
                }, 3000);
            } else {
                alert(`Could not launch Forge: ${data.error}`);
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = 'Launch Forge in Background';
                }
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Launch Forge in Background';
            }
        }
    },

    async saveSettings() {
        const modelSelect = document.getElementById('select-model');
        const selectedModel = modelSelect ? modelSelect.value : '';

        this.settings.model = selectedModel;
        this.settings.temperature = parseFloat(document.getElementById('param-temp').value);
        this.settings.top_p = parseFloat(document.getElementById('param-topp').value);
        this.settings.repeat_penalty = parseFloat(document.getElementById('param-reppen').value);
        this.settings.max_tokens = parseInt(document.getElementById('param-maxtok').value, 10);

        try {
            await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.settings)
            });
            this.updateHeaderModelBadge();
            document.getElementById('modal-settings')?.classList.remove('open');
        } catch (err) {
            console.error('Failed to save settings:', err);
        }
    }
};

window.SettingsManager = SettingsManager;
