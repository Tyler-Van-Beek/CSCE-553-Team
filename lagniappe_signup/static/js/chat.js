document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById('chat-toggle');
    const box = document.getElementById('chat-box');
    const sendBtn = document.getElementById('chat-send');
    const input = document.getElementById('chat-input');
    const chat = document.getElementById('chat-messages');
  
    toggle.addEventListener('click', () => {
      box.style.display = box.style.display === 'none' ? 'flex' : 'none';
    });
  
    sendBtn.addEventListener('click', async () => {
      const msg = input.value.trim();
      if (!msg) return;
  
      // Show user message
      const userMsg = document.createElement('div');
      userMsg.textContent = "You: " + msg;
      chat.appendChild(userMsg);
  
      input.value = '';
  
      // Send to Django change chat
      const response = await fetch('/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ message: msg })
      });
  
      const data = await response.json();
  
      // Show bot response
      const botMsg = document.createElement('div');
      botMsg.textContent = "Bot: " + data.reply;
      chat.appendChild(botMsg);
    });
  });
  