import { EditorState } from '@codemirror/state';
import { highlightSelectionMatches } from '@codemirror/search';
import { indentWithTab, history, defaultKeymap, historyKeymap } from '@codemirror/commands';
import { foldGutter, indentOnInput, indentUnit, bracketMatching, foldKeymap, syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language';
import { closeBrackets, autocompletion, closeBracketsKeymap, completionKeymap } from '@codemirror/autocomplete';
import { lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, rectangularSelection, crosshairCursor, highlightActiveLine, keymap, EditorView, ViewPlugin } from '@codemirror/view';
import { python } from '@codemirror/lang-python';

let socket = null;
window.LAST_SENT_SEQ = 0;
window.LAST_REMOTE_SEQ = {};
window.LAST_LOCAL_EDIT_TS = 0;
let liveSendTimer = null;
let isApplyingRemote = false;

export function initEditor({ csrfToken, autosaveUrl, snapshotUrl, userRole }) {
    const textarea = document.getElementById("content");
    const status = document.getElementById("autosave-status");

    let autoSaveTimer = null;
    let lastSavedContent = textarea ? textarea.value : '';

    const LS_KEY = `task_draft_${window.docID || 'unknown'}`;
    const stored = localStorage.getItem(LS_KEY);
    if (stored && textarea && !textarea.value) {
        textarea.value = stored;
    }

    function triggerAutosave(text) {
        clearTimeout(autoSaveTimer);
        if (status) status.textContent = "Saving...";
        autoSaveTimer = setTimeout(() => {
            fetch(autosaveUrl, {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken, "Content-Type": "application/json" },
                body: JSON.stringify({ content: text })
            })
            .then(r => r.json())
            .then(data => {
                if (status) status.textContent = data.saved_at || "Saved";
                lastSavedContent = text;
                localStorage.setItem(LS_KEY, text);
            })
            .catch(() => { if (status) status.textContent = "Error saving"; });
        }, 800);
    }

    const liveUpdatePlugin = EditorView.updateListener.of((update) => {
        if (!update.docChanged || isApplyingRemote) return;
        const text = update.state.doc.toString();
        window.LAST_LOCAL_EDIT_TS = Date.now();
        clearTimeout(liveSendTimer);
        liveSendTimer = setTimeout(() => {
            try {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    const seq = Date.now();
                    window.LAST_SENT_SEQ = seq;
                    socket.send(JSON.stringify({ student_id: window.CURRENT_STUDENT_ID, content: text, seq }));
                }
            } catch (e) {
                console.warn('[WS] send failed', e);
            }
        }, 300);
    });

    const autosavePlugin = ViewPlugin.define(() => ({
        update(update) {
            if (update.docChanged) {
                const txt = update.view.state.doc.toString();
                triggerAutosave(txt);
                try { if (textarea) textarea.value = txt; } catch (e) {}
            }
        }
    }));

    const editor = new EditorView({
        state: EditorState.create({
            doc: textarea ? textarea.value : '',
            extensions: [
                autosavePlugin,
                lineNumbers(),
                highlightActiveLineGutter(),
                highlightSpecialChars(),
                history(),
                foldGutter(),
                drawSelection(),
                indentUnit.of("    "),
                EditorState.allowMultipleSelections.of(true),
                indentOnInput(),
                bracketMatching(),
                closeBrackets(),
                autocompletion(),
                rectangularSelection(),
                crosshairCursor(),
                highlightActiveLine(),
                highlightSelectionMatches(),
                keymap.of([
                    indentWithTab,
                    ...closeBracketsKeymap,
                    ...defaultKeymap,
                    ...historyKeymap,
                    ...foldKeymap,
                    ...completionKeymap,
                ]),
                python(),
                syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
                isLive ? liveUpdatePlugin : [],
            ]
        }),
        parent: document.getElementById("editor")
    });

    try { window.editorInstance = editor; window.editorReady = true; } catch (e) {}

    function applyRemoteContent(newText) {
        const current = editor.state.doc.toString();
        if (newText === current) return;
        isApplyingRemote = true;
        editor.dispatch({ changes: { from: 0, to: current.length, insert: newText } });
        setTimeout(() => { isApplyingRemote = false; }, 0);
    }

    const snapshotBtn = document.getElementById('btn-save-snapshot');
    if (snapshotBtn && snapshotUrl) {
        snapshotBtn.addEventListener('click', () => {
            const content = editor.state.doc.toString();
            snapshotBtn.textContent = 'Saving...';
            fetch(snapshotUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            })
            .then(r => r.json())
            .then(data => {
                lastSavedContent = content;
                if (status) status.textContent = data.saved_at || 'Snapshot saved';
                snapshotBtn.textContent = 'Save snapshot';
            })
            .catch(() => { snapshotBtn.textContent = 'Save snapshot'; });
        });
    }

    const diffBtn = document.getElementById('btn-show-diff');
    const diffModal = document.getElementById('diff-modal');
    const diffBackdrop = document.getElementById('diff-backdrop');

    function openDiff() {
        const current = editor.state.doc.toString();
        diffModal.querySelector('pre.old').textContent = lastSavedContent || '(no saved version)';
        diffModal.querySelector('pre.new').textContent = current;
        diffModal.style.display = 'block';
        if (diffBackdrop) diffBackdrop.style.display = 'block';
    }
    function closeDiff() {
        diffModal.style.display = 'none';
        if (diffBackdrop) diffBackdrop.style.display = 'none';
    }

    if (diffBtn && diffModal) {
        diffBtn.addEventListener('click', openDiff);
        const closeBtn = diffModal.querySelector('button.close');
        if (closeBtn) closeBtn.addEventListener('click', closeDiff);
    }
    if (diffBackdrop) diffBackdrop.addEventListener('click', closeDiff);

    const lockBtn = document.getElementById('toggle-lock');
    if (lockBtn) {
        let locked = false;
        lockBtn.addEventListener('click', () => {
            locked = !locked;
            editor.setEditable(!locked);
            lockBtn.textContent = locked ? 'Unlock editing' : 'Lock editing';
            lockBtn.style.opacity = locked ? '0.6' : '1';
        });
    }

    if (!isLive) {
        console.log("Task is NOT live — websockets disabled.");
        return editor;
    }

    console.log("Task is live — attempting websocket connection...");
    socket = new WebSocket(window.WS_URL);

    function updateConnIndicator(state) {
        const el = document.getElementById('ws-connection-indicator');
        if (!el) return;
        const dot = el.querySelector('.dot');
        const text = el.querySelector('.text');
        el.dataset.state = state;
        const colors = { connected: '#39d1a2', error: '#ff6b6b', offline: '#94a3b8' };
        const labels = { connected: 'Connected', error: 'Error', offline: 'Offline' };
        if (dot) dot.style.background = colors[state] || colors.offline;
        if (text) text.textContent = labels[state] || 'Offline';
    }

    socket.onopen = () => { updateConnIndicator('connected'); };
    socket.onerror = () => { updateConnIndicator('error'); };
    socket.onclose = () => { updateConnIndicator('offline'); };

    socket.onmessage = (event) => {
        let data;
        try { data = JSON.parse(event.data); } catch (e) { return; }

        if (data.type === "broadcast_change") {
            const sid = data.student_id;
            const seq = Number(data.seq) || 0;
            const last = window.LAST_REMOTE_SEQ[sid] || 0;
            if (seq <= last) return;
            window.LAST_REMOTE_SEQ[sid] = seq;
            const recentEdit = (Date.now() - (window.LAST_LOCAL_EDIT_TS || 0)) < 500;
            if (userRole === "student") {
                if (sid === window.CURRENT_STUDENT_ID && seq !== window.LAST_SENT_SEQ && !recentEdit) {
                    applyRemoteContent(data.content);
                }
            } else if (userRole === "teacher") {
                window.STUDENT_CACHE[sid] = data.content;
                if (sid === window.CURRENT_STUDENT_ID && !recentEdit) {
                    applyRemoteContent(data.content);
                }
            }
            return;
        }

        if (data.type === "student_list") {
            if (userRole !== "teacher") return;
            const ul = document.getElementById("student-list");
            if (!ul) return;
            const prevSelected = window.CURRENT_STUDENT_ID;
            ul.innerHTML = "";
            data.students.forEach(student => {
                window.STUDENT_CACHE[student.id] = student.content || "";
                const li = document.createElement("li");
                li.className = 'student-item' + (student.id === prevSelected ? ' active' : '');
                li.dataset.id = student.id;
                const title = document.createElement('div');
                title.className = 'student-title';
                title.textContent = student.username;
                const meta = document.createElement('div');
                meta.className = 'student-meta';
                const lastSeen = student.last_seen ? new Date(Number(student.last_seen)).toLocaleTimeString() : '—';
                meta.textContent = 'Last active: ' + lastSeen;
                li.appendChild(title);
                li.appendChild(meta);
                li.addEventListener("click", () => {
                    ul.querySelectorAll('.student-item').forEach(el => el.classList.remove('active'));
                    li.classList.add('active');
                    const prev = window.CURRENT_STUDENT_ID;
                    window.CURRENT_STUDENT_ID = student.id;
                    const hdr = document.getElementById('teacher-current-student');
                    if (hdr) hdr.textContent = student.username;
                    const cached = window.STUDENT_CACHE[student.id];
                    if (cached !== undefined) {
                        isApplyingRemote = true;
                        editor.dispatch({ changes: { from: 0, to: editor.state.doc.length, insert: cached } });
                        setTimeout(() => { isApplyingRemote = false; }, 0);
                    }
                    try {
                        if (socket && socket.readyState === WebSocket.OPEN) {
                            if (prev && prev !== student.id) socket.send(JSON.stringify({ type: 'watch_stop', student_id: prev }));
                            socket.send(JSON.stringify({ type: 'watch', student_id: student.id }));
                        }
                    } catch (e) { console.warn('watch send failed', e); }
                });
                ul.appendChild(li);
            });
            const countEl = document.getElementById('students-online-count');
            if (countEl) countEl.textContent = (data.students || []).length;
            return;
        }

        if (data.type === 'teacher_watch') {
            if (userRole !== "student") return;
            const ind = document.getElementById('teacher-watching-indicator');
            if (!ind) return;
            if (data.action === 'start' && String(data.student_id) === String(window.CURRENT_STUDENT_ID)) {
                ind.style.display = 'flex';
            } else if (data.action === 'stop' && String(data.student_id) === String(window.CURRENT_STUDENT_ID)) {
                ind.style.display = 'none';
            }
            return;
        }

        if (data.type === 'help_request' && userRole === "teacher") {
            showHelpToast(`${data.username} needs help`, data.note || '');
        }
    };

    function showHelpToast(title, note) {
        const toast = document.getElementById('help-toast');
        if (!toast) return;
        const titleEl = document.getElementById('help-toast-title');
        const noteEl = document.getElementById('help-toast-note');
        if (titleEl) titleEl.textContent = title;
        if (noteEl) noteEl.textContent = note;
        toast.classList.add('show');
        clearTimeout(toast._hideTimer);
        toast._hideTimer = setTimeout(hideHelpToast, 20000);
    }

    function hideHelpToast() {
        const toast = document.getElementById('help-toast');
        if (!toast) return;
        toast.classList.remove('show');
    }

    const toastClose = document.getElementById('help-toast-close');
    if (toastClose) toastClose.addEventListener('click', hideHelpToast);

    const helpBtn = document.getElementById('btn-request-help');
    if (helpBtn) {
        helpBtn.addEventListener('click', () => {
            const note = prompt('Describe briefly what you need help with (optional):', '');
            if (note === null) return;
            try {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({ type: 'help_request', note }));
                    helpBtn.textContent = 'Request sent ✓';
                    helpBtn.disabled = true;
                    setTimeout(() => { helpBtn.textContent = 'Need help'; helpBtn.disabled = false; }, 5000);
                } else {
                    alert('Not connected — try again in a moment.');
                }
            } catch (e) { console.warn('Failed to send help request', e); }
        });
    }

    return editor;
}
