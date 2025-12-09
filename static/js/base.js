import { EditorState } from '@codemirror/state';
import { openSearchPanel, highlightSelectionMatches } from '@codemirror/search';
import { indentWithTab, history, defaultKeymap, historyKeymap } from '@codemirror/commands';
import { foldGutter, indentOnInput, indentUnit, bracketMatching, foldKeymap, syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language';
import { closeBrackets, autocompletion, closeBracketsKeymap, completionKeymap } from '@codemirror/autocomplete';
import { lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, dropCursor, rectangularSelection, crosshairCursor, highlightActiveLine, keymap, EditorView ,ViewPlugin} from '@codemirror/view';


import { oneDark } from "@codemirror/theme-one-dark";


import { javascript } from "@codemirror/lang-javascript";
let socket = null;
export function initEditor({ csrfToken, autosaveUrl }) {
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

    const autosavePlugin = ViewPlugin.fromClass(class {
        update(update) {
            if (update.docChanged) {
                textarea.value = update.view.state.doc.toString();
                triggerAutosave(textarea.value);
            }
        }
    });

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
            ]
        }),
        parent: document.getElementById("editor")
    });
    if (isLive) {
        console.log("Task is live — attempting websocket connection...");

        socket = new WebSocket(window.WS_URL);


        socket.onopen = () => {
            console.log("%c[WS] Connected successfully!", "color: #00c853; font-weight: bold;");
        };

        socket.onmessage = (event) => {
            console.log("%c[WS] Message received:", "color: #2962ff; font-weight: bold;", event.data);
        };

        socket.onerror = (err) => {
            console.log("%c[WS] Error:", "color: #d50000; font-weight: bold;", err);
        };

        socket.onclose = () => {
            console.log("%c[WS] Connection closed.", "color: #ffab00; font-weight: bold;");
        };
    } else {
        console.log("Task is NOT live — websockets disabled.");
    }
    return editor;
}
