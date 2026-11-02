const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const suggestionsEl = document.getElementById("suggestions");

function appendMessage(text, role) {
  const bubble = document.createElement("div");
  bubble.className = `msg ${role}`;
  bubble.textContent = text;
  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

async function sendMessage(text) {
  const message = text.trim();
  if (!message) return;

  appendMessage(message, "user");
  inputEl.value = "";
  sendBtn.disabled = true;

  const typing = appendMessage("Thinking…", "bot typing");

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();
    typing.remove();

    if (!res.ok) {
      appendMessage(data.error || "Something went wrong.", "bot");
      return;
    }

    appendMessage(data.reply, "bot");
  } catch (_) {
    typing.remove();
    appendMessage("Can't reach the server right now. Try again.", "bot");
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(inputEl.value);
});

async function loadSuggestions() {
  try {
    const res = await fetch("/api/suggestions");
    const data = await res.json();
    suggestionsEl.innerHTML = "";
    (data.suggestions || []).forEach((text) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = text;
      btn.addEventListener("click", () => sendMessage(text));
      suggestionsEl.appendChild(btn);
    });
  } catch (_) {
    // Suggestions are optional
  }
}

appendMessage(
  "Hi — I'm FreeBirdsBot. Ask me about opening hours, mopeds, payments, or rentals.",
  "bot"
);
loadSuggestions();
inputEl.focus();
