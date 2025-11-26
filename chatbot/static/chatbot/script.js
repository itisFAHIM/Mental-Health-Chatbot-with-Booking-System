document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    
    // Get the submit button
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Sidebar elements
    const historySidebar = document.getElementById("history-sidebar");
    const historyListContainer = document.getElementById("history-list-container");
    const newChatBtn = document.getElementById("new-chat-btn");
    const historyToggleBtn = document.getElementById("history-toggle-btn");
    const mainContent = document.getElementById("main-content");

    // This variable tracks which conversation is active
    let currentConversationId = null;

    // --- 1. Load Conversation List on Page Load ---
    loadConversationList();

    // --- 2. Event Listeners ---
    
    // Handle 'Enter' to send and 'Shift+Enter' for newline
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault(); // Prevents adding a new line
            submitButton.click(); // Clicks the 'Send' button
        }
    });
    
    // Toggle sidebar
    historyToggleBtn.addEventListener("click", () => {
        historySidebar.classList.toggle("open");
        mainContent.classList.toggle("shifted");
    });

    // Handle clicking "New Chat"
    newChatBtn.addEventListener("click", () => {
        startNewChat();
    });

    // Handle clicking a conversation in the sidebar (using event delegation)
    historyListContainer.addEventListener("click", (e) => {
        if (e.target && e.target.classList.contains("history-item")) {
            const convId = e.target.dataset.id;
            if (convId !== currentConversationId) {
                loadConversation(convId);
            }
            historySidebar.classList.remove("open"); // Close sidebar
            mainContent.classList.remove("shifted");
        }
    });

    // Handle sending a message
    form.addEventListener("submit", async (e) => {
        e.preventDefault(); // This prevents the page from reloading
        const message = input.value.trim();
        if (!message) return;

        appendMessage(message, "user"); // This will now show your message
        input.value = ""; // Clear textarea

        // --- NEW: Show typing indicator ---
        showTypingIndicator();

        // Check if it's a new chat to reload history list later
        const isNewChat = currentConversationId === null;

        try {
            const response = await fetch("/api/chat/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    message: message,
                    conversation_id: currentConversationId
                }),
            });

            const data = await response.json();
            
            // --- NEW: Remove typing indicator ---
            removeTypingIndicator();
            
            appendMessage(data.reply || "⚠️ Sorry, I didn’t understand that.", "bot");
            
            currentConversationId = data.conversation_id;

            if (isNewChat) {
                loadConversationList();
            }

        } catch (error) {
            // --- NEW: Remove typing indicator even on error ---
            removeTypingIndicator();
            appendMessage("⚠️ Error connecting to the chatbot API.", "bot");
        }
    });

    // --- 3. Helper Functions ---

    function appendMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        messageDiv.textContent = (sender === "user" ? "You: " : "Bot: ") + text;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function clearChatBox() {
        chatBox.innerHTML = "";
    }

    // --- NEW: Typing Indicator Functions ---
    function showTypingIndicator() {
        // Check if one is already showing
        if (document.getElementById("typing-indicator")) return;

        const messageDiv = document.createElement("div");
        messageDiv.id = "typing-indicator"; // Give it an ID to find it later
        messageDiv.classList.add("message", "bot"); // Style it like a bot message
        
        // Minimalistic "..." animation
        messageDiv.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById("typing-indicator");
        if (indicator) {
            indicator.remove();
        }
    }
    // --- End of new functions ---


    function startNewChat() {
        currentConversationId = null;
        clearChatBox();
        historySidebar.classList.remove("open");
        mainContent.classList.remove("shifted");
    }

    async function loadConversationList() {
        try {
            const res = await fetch("/api/history/conversations/");
            const data = await res.json();
            historyListContainer.innerHTML = ""; // Clear list
            if (data.conversations && data.conversations.length > 0) {
                data.conversations.forEach(conv => {
                    const div = document.createElement("div");
                    div.className = "history-item";
                    div.textContent = conv.title;
                    div.dataset.id = conv.id; // Store ID
                    historyListContainer.appendChild(div);
                });
            } else {
                historyListContainer.innerHTML = "<p style='padding-left: 5px; opacity: 0.7;'>No chat history.</p>";
            }
        } catch (e) {
            console.error("Failed to load conversation list", e);
            historyListContainer.innerHTML = "<p>Error loading history.</p>";
        }
    }

    async function loadConversation(convId) {
        try {
            const res = await fetch(`/api/history/conversation/${convId}/`);
            const data = await res.json();
            
            clearChatBox();
            currentConversationId = convId; // Set as active

            if (data.history && data.history.length > 0) {
                data.history.forEach(item => {
                    appendMessage(item.user, "user");
                    appendMessage(item.bot, "bot");
                });
            }
        } catch (e) {
            console.error("Failed to load conversation", e);
            clearChatBox();
            appendMessage("⚠️ Error loading chat history.", "bot");
        }
    }
});