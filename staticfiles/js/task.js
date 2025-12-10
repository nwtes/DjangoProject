window.autosaveUrl = ""
window.csrfToken = ""

function toggleDesc(headerElem){
    const header = headerElem;
    const container = header.closest('.task-header');
    if (!container) return;
    const desc = container.querySelector('.header-desc');
    const arrow = header.querySelector('.arrow');

    const expanded = header.getAttribute('aria-expanded') === 'true';

    if (desc) {
        desc.hidden = expanded;
    }


    header.setAttribute('aria-expanded', (!expanded).toString());

    container.classList.toggle('open', !expanded);

    if (arrow) {
        arrow.textContent = (!expanded) ? '▲' : '▼';
    }
}

window.toggleDesc = toggleDesc;

document.addEventListener('keydown', function(e){
    const el = document.activeElement;
    if (!el) return;
    if (el.classList && el.classList.contains('header-title')){
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleDesc(el);
        }
    }
});
