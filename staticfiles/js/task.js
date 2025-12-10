window.autosaveUrl = ""
window.csrfToken = ""
function toggleDesc(headerElem){
    const card = headerElem.parentElement;
    card.classList.toggle("open")
    console.log("Clicked")
    console.log(window.csrfToken)
        console.log(11)
}