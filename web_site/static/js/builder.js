function updatePreview() {
    document.getElementById('preview-title').innerText = document.getElementById('title').value;
    document.getElementById('preview-desc').innerText = document.getElementById('desc').value;
}

document.querySelectorAll('input, textarea').forEach(el => el.addEventListener('input', updatePreview));

function sendToServer() {
    const data = {
        channel_id: "1234567890", // Пример ID канала
        embed: {
            title: document.getElementById('title').value,
            description: document.getElementById('desc').value
        }
    };
    fetch('/api/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
}
