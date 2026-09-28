/**
 * Roleplay & Markdown Text Formatter
 * Sanitizes input and applies distinct styling for:
 * - *physical actions & body language* (.rp-action)
 * - "dialogue spoken aloud" (.rp-dialogue)
 * - (inner thoughts & whispers) (.rp-thought)
 */

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatRoleplayMarkdown(rawText) {
    if (!rawText) return "";

    // Step 1: Escape raw HTML to prevent injection
    let safe = escapeHtml(rawText);

    // Step 2: Handle code blocks ```code```
    safe = safe.replace(/```([\s\S]*?)```/g, (match, p1) => {
        return `<pre><code>${p1}</code></pre>`;
    });

    // Step 3: Handle inline code `code`
    safe = safe.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // Step 4: Handle bold **text**
    safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Step 5: Handle *physical actions* (single asterisk)
    // Matches *something* but not **
    safe = safe.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<span class="rp-action">*$1*</span>');

    // Step 6: Handle "dialogue quotes"
    // Matches "something" or “something”
    safe = safe.replace(/&quot;([^&"]+)&quot;/g, '<span class="rp-dialogue">&quot;$1&quot;</span>');
    safe = safe.replace(/"([^"\n]+)"/g, '<span class="rp-dialogue">"$1"</span>');
    safe = safe.replace(/“([^”\n]+)”/g, '<span class="rp-dialogue">“$1”</span>');

    // Step 7: Handle (inner thoughts)
    safe = safe.replace(/\(([^)\n]{3,})\)/g, '<span class="rp-thought">($1)</span>');

    // Step 8: Convert linebreaks to paragraphs / breaks
    safe = safe.replace(/\n\n/g, '<br><br>');
    safe = safe.replace(/\n/g, '<br>');

    return safe;
}

window.formatRoleplayMarkdown = formatRoleplayMarkdown;
window.escapeHtml = escapeHtml;
