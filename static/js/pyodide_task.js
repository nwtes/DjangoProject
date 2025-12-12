console.warn('pyodide_task.js removed: runs disabled.');
window.runTaskPy = async function(){
    return Promise.reject(new Error('Pyodide runner is disabled.'));
};

