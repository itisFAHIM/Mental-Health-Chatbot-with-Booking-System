document.addEventListener("DOMContentLoaded", async () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");

    // Loading previous chat history
    try {
        const res = await fetch("/api/history/");
        const data = await res.json();
        if (data.history && data.history.length > 0) {
            data.history.forEach(item => {
                appendMessage(item.user, "user");
                appendMessage(item.bot, "bot");
            });
        }
    } catch (e) {
        console.error("Failed to load chat history", e);
    }

    // For Sending messages
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = input.value.trim();
        if (!message) return;

        appendMessage(message, "user");
        input.value = "";

        try {
            const response = await fetch("/api/chat/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message }),
            });

            const data = await response.json();
            appendMessage(data.reply || "⚠️ Sorry, I didn’t understand that.", "bot");
        } catch (error) {
            appendMessage("⚠️ Error connecting to the chatbot API.", "bot");
        }
    });

    function appendMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        messageDiv.textContent = (sender === "user" ? "You: " : "Bot: ") + text;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});
