

import { initEditor } from './editor.js';


function getDjangoData(id) {
    const element = document.getElementById(id);
    if (element) {
        return JSON.parse(element.textContent);
    }
    console.error(`Could not find element with ID: ${id}`);
    return null;
}


const autosaveUrl = getDjangoData('autosave-url-data');
const csrfToken = getDjangoData('csrf-url-data');


if (autosaveUrl && csrfToken) {
    initEditor({
        csrfToken: csrfToken,
        autosaveUrl: autosaveUrl
    });
    console.log("CodeMirror editor initialized and running.");
} else {
    console.error("Editor initialization failed: Missing URL or CSRF token.");
}
