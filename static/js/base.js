import { EditorState } from "https://esm.sh/@codemirror/state";
    import { EditorView, basicSetup } from "https://esm.sh/codemirror";
    import { oneDark } from "https://esm.sh/@codemirror/theme-one-dark";


let editor = new EditorView({
    state: EditorState.create({
        doc: "",
        extensions:[basicSetup,oneDark]
    }),
    parent:document.getElementById("editor")
})