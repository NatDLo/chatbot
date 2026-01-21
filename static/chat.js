// This file handles the chat interface logic
const $form = document.getElementById('chat-form');
const $input = document.getElementById('chat-input');
const $msgs = document.getElementById('messages');

function addMsg(role, text) {
  const div = document.createElement('div');
  div.className = role;
  div.textContent = (role === 'user' ? 'Tú: ' : 'Bot: ') + text;
  $msgs.appendChild(div);
  $msgs.scrollTop = $msgs.scrollHeight;
}

$form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = $input.value.trim();
  if (!text) return;
  addMsg('user', text);
  $input.value = '';

  try {
    // 🚨 Corregido: apunta a la ruta exacta
    const res = await fetch('/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    const data = await res.json();
    addMsg('bot', data.response || JSON.stringify(data));
  } catch (err) {
    addMsg('bot', 'Error llamando al backend.');
    console.error(err);
  }
});
