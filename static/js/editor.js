import {initEditor} from "./base.js"

function getDjangoData(id){
    const element = document.getElementById(id)
    if(element){
        return JSON.parse(element.textContent)
    }
    console.error(`Coulnd find element with id ${id}`)
    return null
}

const autosaveUrl = getDjangoData('autosave-url-data')
const csrfToken = getDjangoData("csrf-token-data")
const userRole = getDjangoData("user-role")

if (autosaveUrl && csrfToken){
    initEditor(
        {
            autosaveUrl: autosaveUrl,
            csrfToken: csrfToken,
            userRole: userRole
        }
    )
}else{
    console.error("Editor configuration error")
}