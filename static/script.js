document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");
    let thread_id = null;

    const addMessage = (sender, message) => {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", `${sender}-message`);
        messageElement.innerText = message;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const sendMessage = async () => {
        const content = userInput.value.trim();
        if (content) {
            addMessage("user", content);
            userInput.value = "";

            try {
                const response = await fetch("/stream", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ content, thread_id }),
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let botMessage = "";
                let botMessageElement = null;

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    botMessage += chunk;

                    if (!botMessageElement) {
                        botMessageElement = document.createElement("div");
                        botMessageElement.classList.add("message", "bot-message");
                        chatBox.appendChild(botMessageElement);
                    }
                    botMessageElement.innerText = botMessage;
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
                if (response.headers.has("x-thread-id")) {
                    thread_id = response.headers.get("x-thread-id");
                }

            } catch (error) {
                console.error("Error:", error);
                addMessage("bot", "Sorry, something went wrong.");
            }
        }
    };

    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
});