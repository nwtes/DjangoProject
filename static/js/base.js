import { EditorState } from '@codemirror/state';
import { openSearchPanel, highlightSelectionMatches } from '@codemirror/search';
import { indentWithTab, history, defaultKeymap, historyKeymap } from '@codemirror/commands';
import { foldGutter, indentOnInput, indentUnit, bracketMatching, foldKeymap, syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language';
import { closeBrackets, autocompletion, closeBracketsKeymap, completionKeymap } from '@codemirror/autocomplete';
import { lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, dropCursor, rectangularSelection, crosshairCursor, highlightActiveLine, keymap, EditorView ,ViewPlugin} from '@codemirror/view';

// Theme
import { oneDark } from "@codemirror/theme-one-dark";

// Language
import { javascript } from "@codemirror/lang-javascript";

export function initEditor({ csrfToken, autosaveUrl }) {
    const textarea = document.getElementById("content");
    const status = document.getElementById("autosave-status");

    // The editor variable is no longer needed in the outer scope for the plugin
    // let editor;

    // The triggerAutosave function needs to be defined *before* the plugin that uses it.
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
        // Use the view from the update object
        update(update) {
            if (update.docChanged) {
                // Get the current document content from the update.view
                textarea.value = update.view.state.doc.toString();
                triggerAutosave(textarea.value);
            }
        }
    });

    const editor = new EditorView({ // Use `const` as it's assigned here once
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

    return editor;
}
