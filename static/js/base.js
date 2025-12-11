import { EditorState } from '@codemirror/state';
import { highlightSelectionMatches } from '@codemirror/search';
import { indentWithTab, history, defaultKeymap, historyKeymap } from '@codemirror/commands';
import { foldGutter, indentOnInput, indentUnit, bracketMatching, foldKeymap, syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language';
import { closeBrackets, autocompletion, closeBracketsKeymap, completionKeymap } from '@codemirror/autocomplete';
import { lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, rectangularSelection, crosshairCursor, highlightActiveLine, keymap, EditorView, ViewPlugin } from '@codemirror/view';

import { javascript } from "@codemirror/lang-javascript";
let socket = null;
export function initEditor({ csrfToken, autosaveUrl,userRole }) {
    const textarea = document.getElementById("content");
    const status = document.getElementById("autosave-status");

    let autoSaveTimer = null;

    function triggerAutosave(text) {
        clearTimeout(autoSaveTimer);
        status.textContent = "Saving...";

        autoSaveTimer = setTimeout(() => {
            fetch(autosaveUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ content: text })
            })
            .then(response => response.json())
            .then(data => {
                status.textContent = data.saved_at;
            })
            .catch(() => {
                status.textContent = "Error saving";
            });
        }, 800);
    }
    const liveUpdatePlugin = EditorView.updateListener.of((update) => {
        if (update.docChanged) {
            const text = update.state.doc.toString();
            try {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({ student_id: window.CURRENT_STUDENT_ID, content: text }));
                }
            } catch (e) {
                console.warn('[WS] send failed', e);
            }
        }
    });
    const autosavePlugin = ViewPlugin.define(() => ({
        update(update) {
            if (update.docChanged) {
                const txt = update.view.state.doc.toString();
                triggerAutosave(txt);
            }
        }
    }));

    const editor = new EditorView({
        state: EditorState.create({
            doc: textarea.value,
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
                javascript(),
                syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
                isLive ? liveUpdatePlugin : [],
            ]
        }),
        parent: document.getElementById("editor")
    });
    if (isLive) {
    console.log("Task is live — attempting websocket connection...");

    socket = new WebSocket(window.WS_URL);

    socket.onopen = () => {
        console.log("%c[WS] Connected successfully!", "color: #00c853; font-weight: bold;");
        updateConnIndicator('connected');
    };

    socket.onerror = (err) => {
        console.log("%c[WS] Error:", "color: #d50000; font-weight: bold;", err);
        updateConnIndicator('error');
    };

    socket.onclose = () => {
        console.log("%c[WS] Connection closed.", "color: #ffab00; font-weight: bold;");
        updateConnIndicator('offline');
    };

    function updateConnIndicator(state) {
        const el = document.getElementById('ws-connection-indicator');
        if (!el) return;
        const dot = el.querySelector('.dot');
        const text = el.querySelector('.text');
        el.dataset.state = state;
        if (state === 'connected') {
            if (dot) dot.style.background = '#39d1a2';
            if (text) text.textContent = 'Connected';
        } else if (state === 'error') {
            if (dot) dot.style.background = '#ff6b6b';
            if (text) text.textContent = 'Error';
        } else if (state === 'offline') {
            if (dot) dot.style.background = '#94a3b8';
            if (text) text.textContent = 'Offline';
        } else {
            if (dot) dot.style.background = '#94a3b8';
            if (text) text.textContent = 'Offline';
        }
    }

    function applyRemoteContent(newText) {
        const current = editor.state.doc.toString();

        if (newText === current) return;

        editor.dispatch({
            changes: {
                from: 0,
                to: current.length,
                insert: newText
            }
        });
    }

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (userRole === "student") {
            if (data.student_id !== CURRENT_STUDENT_ID) return;
            if (data.type === 'help_request') {
                return;
            }
            applyRemoteContent(data.content);
        }

        if (userRole === "teacher") {

            if (data.type === "broadcast_change") {
                window.STUDENT_CACHE[data.student_id] = data.content;
                if (data.student_id === CURRENT_STUDENT_ID) {
                    applyRemoteContent(data.content);
                }
            }

            if (data.type === 'help_request') {
                try {
                    const title = `${data.username} requested help`;
                    const note = data.note || '';
                    showHelpToast(title, note, data.timestamp);
                } catch (e) {
                    console.warn('Invalid help_request payload', e);
                }
            }

            if (data.type === "student_list") {
                const ul = document.getElementById("student-list");
                if (!ul) return;
                ul.innerHTML = "";

                data.students.forEach(student => {
                    window.STUDENT_CACHE[student.id] = student.content || "";

                    const li = document.createElement("li");
                    li.className = 'student-item';
                    li.dataset.id = student.id;

                    const title = document.createElement('div');
                    title.className = 'student-title';
                    title.textContent = student.username + ' (id: ' + student.id + ')';

                    const meta = document.createElement('div');
                    meta.className = 'student-meta';
                    meta.style.fontSize = '12px';
                    meta.style.color = 'var(--muted)';
                    const lastSeen = student.last_seen ? new Date(Number(student.last_seen)).toLocaleTimeString() : '—';
                    meta.textContent = 'Last: ' + lastSeen;

                    li.appendChild(title);
                    li.appendChild(meta);

                    li.addEventListener("click", () => {
                        window.CURRENT_STUDENT_ID = student.id;
                        console.log("Teacher is now viewing student:", student.username, CURRENT_STUDENT_ID);

                        const hdr = document.getElementById('teacher-current-student');
                        if (hdr) hdr.textContent = student.username + ' (id: ' + student.id + ')';

                        const cached = window.STUDENT_CACHE[student.id];
                        if (cached !== undefined) {
                            editor.dispatch({
                                changes: { from: 0, to: editor.state.doc.length, insert: cached }
                            });
                        }
                    });

                    ul.appendChild(li);
                });

                const countEl = document.getElementById('students-online-count');
                if (countEl) countEl.textContent = (data.students || []).length;
            }
        }
    };

    function showHelpToast(title, note, timestamp) {
        const toast = document.getElementById('help-toast');
        if (!toast) return;
        const titleEl = document.getElementById('help-toast-title');
        const noteEl = document.getElementById('help-toast-note');
        if (titleEl) titleEl.textContent = title;
        if (noteEl) noteEl.textContent = note;
        toast.style.display = 'block';
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        toast.dataset.ts = timestamp || Date.now();
        clearTimeout(toast._hideTimer);
        toast._hideTimer = setTimeout(() => { hideHelpToast(); }, 20000);
    }

    function hideHelpToast() {
        const toast = document.getElementById('help-toast');
        if (!toast) return;
        toast.classList.remove('show');
        setTimeout(() => { toast.style.display = 'none'; }, 260);
    }

    const toastClose = document.getElementById('help-toast-close');
    if (toastClose) toastClose.addEventListener('click', () => { hideHelpToast(); });

    const helpBtn = document.getElementById('btn-request-help');
    if (helpBtn) {
        helpBtn.addEventListener('click', () => {
            const note = prompt('Describe briefly what you need help with (optional)', '');
            const payload = { type: 'help_request', note: note || '' };
            try {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify(payload));
                    helpBtn.textContent = 'Request sent';
                    helpBtn.disabled = true;
                    setTimeout(() => { helpBtn.textContent = 'Need help'; helpBtn.disabled = false; }, 5000);
                } else {
                    alert('Cannot send help request: socket not connected');
                }
            } catch (e) {
                console.warn('Failed to send help request', e);
                alert('Failed to send help request');
            }
        });
    }

}
else {
    console.log("Task is NOT live — websockets disabled.");
}
    return editor;
}
