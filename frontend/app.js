const stagedFiles = new Map();
let fileCounter = 0;

/* DOM Refs*/
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const uploadBtn = document.getElementById('uploadBtn');
const resultSection = document.getElementById('resultSection');
const resultCards = document.getElementById('resultCards');
const invoicesBody = document.getElementById('invoicesBody');
const refreshBtn = document.getElementById('refreshBtn');

const SUPPORTED = new Set(['.pdf', 'jpg', 'jpeg', '.png', '.tiff']);

/* Helper functions*/

/* Returns the lower case file extension for a given file name, */
function ext(filename) {
    const i = filename.lastIndexOf('.');
    return i >= 0 ? filename.slice(i).toLowerCase() : '';
}

/* Converts a raw byte count into human readable string (B / KB / MB)*/
function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

/* Returns the value as-is, or an em-dash when the value is null / undefined. */
function fmt(val) { return val != null ? val : '-';}

/* Staging files */
function stageFiles (fileArray) {
    Array.from(fileArray).forEach(file => {
        if (!SUPPORTED.has(ext(file.name))) {
            alert(`"${file.name}" is not supported file type.`);
            return;
        }

        if (stagedFiles.has(file.name)) return;
        stagedFiles.set(file.name, file);
        renderFileItem(file);
    });
    uploadBtn.disabled = stagedFiles.size === 0;
}

/* Renders a file */
function renderFileItem(file) {
    const id = `f-${fileCounter++}`;
    const li = document.createElement('li');
    li.id = id;
    li.innerHTML = `
    <span class = "file-name" title="${file.name}">${file.name}</span>
    <span class = "file-size">${formatBytes(file.size)}</span>
    <button class="remove-btn" title="Remove" data-name="${file.name}">x</button>
    `;
    li.querySelector('.remove-btn').addEventListener('click', () => {
        stagedFiles.delete(file.name);
        li.remove();
        uploadBtn.disabled = stagedFiles.size === 0;
    });
    fileList.appendChild(li);
}