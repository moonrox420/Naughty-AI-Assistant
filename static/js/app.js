/**
 * Main Application Orchestrator
 */

document.addEventListener('DOMContentLoaded', async () => {
    console.log("Initializing Naughty AI Assistant Client...");

    // Bind generic modal closing behaviors
    document.querySelectorAll('.btn-modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            if (targetId) {
                document.getElementById(targetId)?.classList.remove('open');
            }
        });
    });

    document.querySelectorAll('.modal-backdrop').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('open');
            }
        });
    });

    // Sidebar Collapse / Expand Controller
    const sidebar = document.getElementById('sidebar');
    const collapseBtn = document.getElementById('btn-collapse-sidebar');
    const toggleBtn = document.getElementById('btn-toggle-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');

    function closeSidebar() {
        if (!sidebar) return;
        if (window.innerWidth <= 900) {
            sidebar.classList.remove('mobile-open');
            backdrop?.classList.remove('active');
        } else {
            sidebar.classList.add('collapsed');
            try {
                localStorage.setItem('naughty_sidebar_collapsed', '1');
            } catch (e) {}
        }
    }

    function openSidebar() {
        if (!sidebar) return;
        if (window.innerWidth <= 900) {
            sidebar.classList.add('mobile-open');
            backdrop?.classList.add('active');
        } else {
            sidebar.classList.remove('collapsed');
            try {
                localStorage.setItem('naughty_sidebar_collapsed', '0');
            } catch (e) {}
        }
    }

    function toggleSidebar(forceCollapse) {
        if (!sidebar) return;
        const isMobile = window.innerWidth <= 900;
        if (forceCollapse === true) {
            closeSidebar();
        } else if (forceCollapse === false) {
            openSidebar();
        } else {
            if (isMobile) {
                if (sidebar.classList.contains('mobile-open')) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            } else {
                if (sidebar.classList.contains('collapsed')) {
                    openSidebar();
                } else {
                    closeSidebar();
                }
            }
        }
    }

    // Expose globally so chat.js and cards.js can call it directly
    window.closeSidebar = closeSidebar;
    window.openSidebar = openSidebar;
    window.toggleSidebar = toggleSidebar;

    collapseBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        closeSidebar();
    });

    toggleBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleSidebar();
    });

    backdrop?.addEventListener('click', () => {
        closeSidebar();
    });

    // Universal Hotkey: Ctrl+B or Cmd+B to toggle sidebar, or Escape to close on mobile
    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
            e.preventDefault();
            toggleSidebar();
        } else if (e.key === 'Escape' && window.innerWidth <= 900 && sidebar?.classList.contains('mobile-open')) {
            closeSidebar();
        }
    });

    // Restore saved collapsed preference on desktop
    try {
        if (window.innerWidth > 900 && localStorage.getItem('naughty_sidebar_collapsed') === '1') {
            sidebar?.classList.add('collapsed');
        }
    } catch (e) {}

    // Initialize all sub-modules sequentially
    try {
        await PersonaManager.init();
        await SettingsManager.init();
        ChatManager.init();
        await CardManager.init();
        console.log("Naughty AI Assistant successfully mounted.");
    } catch (err) {
        console.error("Initialization error:", err);
    }
});
