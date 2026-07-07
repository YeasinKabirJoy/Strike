
      window.addEventListener('load', function() {
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    });
    // htmx:afterSwap,afterRequest
    // HTMX event listener for when the request is finished and the content is swapped
    document.body.addEventListener('htmx:wsAfterMessage', function(event) {

           const chatContainer = document.getElementById('chat-messages');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
                // setTimeout(() => {
                //
                // }, 200); // Adjust delay as needed
            }

    });

document.addEventListener("htmx:oobAfterSwap", (event) => {
    if (event.target.classList.contains('chatroom_name')) {
        const updatedDiv = event.target;
        const chatContainer = document.getElementById('chatroom-container');

        if (updatedDiv && chatContainer && chatContainer.firstElementChild !== updatedDiv) {
            updatedDiv.classList.add('fade-in-up');
            chatContainer.insertBefore(updatedDiv, chatContainer.firstElementChild);
        }
    }
});




 // const container = document.getElementById(event.target.id)
 //        const first_element_id = container.firstChild.nextSibling.id
 //        const url=event.target.baseURI
 //        const match = url.match(/\/chatroom\/([^\/]+)/);
 //        const chatroomId = match[1];
 //
 //        const chatroomDiv = document.getElementById(chatroomId);
 //
 //        if(first_element_id === chatroomId){
 //            event.preventDefault()
 //        }
 //        else{
 //            if (chatroomDiv) {
 //            chatroomDiv.remove();
 //                } else {
 //                    console.log(`Div with ID ${chatroomId} not found.`);
 //                }
 //        }

document.addEventListener("DOMContentLoaded", () => {
    const maxChatImageSize = 5 * 1024 * 1024;
    const allowedChatImageTypes = new Set([
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]);
    const fileInput = document.getElementById("file-input");
    const attachButton = document.getElementById("attach-button");
    const messageInput = document.getElementById("message-input");
    const filesPreview = document.getElementById("files-preview");
    const form = document.getElementById("send-chat-form");
    const chatMessages = document.getElementById("chat-messages");
    const chatSearchInput = document.getElementById("chat-search-input");
    const olderMessagesThreshold = 80;

    if (!fileInput || !attachButton || !messageInput || !filesPreview || !form) {
        return;
    }

    let selectedFiles = []; // Array to store selected files
    let typingTimeout = null;
    let searchTimeout = null;
    let isTyping = false;
    const isPrivateChat = chatMessages && chatMessages.dataset.isPrivate === "true";
    const currentChatroomName = typeof chatroom_name === "undefined" ? null : chatroom_name;
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const chatSocket = currentChatroomName
        ? new WebSocket(`${wsProtocol}://${window.location.host}/ws/chatroom/${currentChatroomName}/`)
        : null;
    let isLoadingOlderMessages = false;

    async function refreshChatMessages(query = "") {
        if (!chatMessages) {
            return;
        }

        const params = new URLSearchParams();
        if (query.trim()) {
            params.set("q", query.trim());
        }

        const requestUrl = params.toString()
            ? `${chatMessages.dataset.listUrl}?${params.toString()}`
            : chatMessages.dataset.listUrl;

        try {
            const response = await fetch(requestUrl, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            });

            if (!response.ok) {
                throw new Error("Failed to load chat messages.");
            }

            chatMessages.innerHTML = await response.text();
            chatMessages.dataset.searchMode = query.trim() ? "true" : "false";
            const nextCursor = document.getElementById("older-messages-cursor");
            chatMessages.dataset.hasMore = nextCursor && nextCursor.dataset.beforeCreatedAt ? "true" : "false";

            if (!query.trim()) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
                markPrivateChatRead();
            }
        } catch (error) {
            console.error("Chat messages refresh failed:", error);
        }
    }

    async function loadOlderMessages() {
        if (!chatMessages || isLoadingOlderMessages || chatMessages.dataset.hasMore !== "true" || chatMessages.dataset.searchMode === "true") {
            return;
        }

        const cursor = document.getElementById("older-messages-cursor");
        if (!cursor || !cursor.dataset.beforeCreatedAt || !cursor.dataset.beforeId) {
            chatMessages.dataset.hasMore = "false";
            return;
        }

        isLoadingOlderMessages = true;
        const previousScrollHeight = chatMessages.scrollHeight;
        const previousScrollTop = chatMessages.scrollTop;

        const params = new URLSearchParams({
            before_created_at: cursor.dataset.beforeCreatedAt,
            before_id: cursor.dataset.beforeId,
        });

        try {
            const response = await fetch(`${chatMessages.dataset.loadOlderUrl}?${params.toString()}`, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            });

            if (!response.ok) {
                throw new Error("Failed to load older messages.");
            }

            const html = await response.text();
            const template = document.createElement("template");
            template.innerHTML = html.trim();

            cursor.remove();
            chatMessages.prepend(template.content);

            const nextCursor = document.getElementById("older-messages-cursor");
            if (!nextCursor || !nextCursor.dataset.beforeCreatedAt || !nextCursor.dataset.beforeId) {
                chatMessages.dataset.hasMore = "false";
            }

            chatMessages.scrollTop = chatMessages.scrollHeight - previousScrollHeight + previousScrollTop;
        } catch (error) {
            console.error("Older messages load failed:", error);
        } finally {
            isLoadingOlderMessages = false;
        }
    }

    function sendChatSocketEvent(payload) {
        if (!chatSocket) {
            return;
        }

        const sendPayload = () => chatSocket.send(JSON.stringify(payload));
        if (chatSocket.readyState === WebSocket.OPEN) {
            sendPayload();
        } else if (chatSocket.readyState === WebSocket.CONNECTING) {
            chatSocket.addEventListener("open", sendPayload, { once: true });
        }
    }

    function sendTypingStatus(nextTypingStatus) {
        if (isTyping === nextTypingStatus) {
            return;
        }

        isTyping = nextTypingStatus;
        sendChatSocketEvent({
            type: "chat.typing",
            is_typing: nextTypingStatus,
        });
    }

    function markPrivateChatRead() {
        if (!isPrivateChat || document.visibilityState !== "visible") {
            return;
        }

        sendChatSocketEvent({
            type: "chat.mark_read",
        });
    }

    // Trigger file input when attach button is clicked
    attachButton.addEventListener("click", () => {
        fileInput.click();
    });

    // Handle file selection
    fileInput.addEventListener("change", () => {
        const files = Array.from(fileInput.files);
        const invalidFile = files.find((file) => {
            return !allowedChatImageTypes.has(file.type) || file.size > maxChatImageSize;
        });

        if (invalidFile) {
            alert(`${invalidFile.name} must be a JPG, PNG, GIF, or WebP image under 5MB.`);
            fileInput.value = "";
            selectedFiles = [];
            updateUI();
            return;
        }

        // Add new files to the selected files list
        files.forEach((file) => {
            if (!selectedFiles.find(f => f.name === file.name)) {
                selectedFiles.push(file);
            }
        });

        updateUI();
    });

    messageInput.addEventListener("input", () => {
        if (messageInput.readOnly) {
            return;
        }

        clearTimeout(typingTimeout);
        if (messageInput.value.trim()) {
            sendTypingStatus(true);
            typingTimeout = setTimeout(() => sendTypingStatus(false), 1200);
        } else {
            sendTypingStatus(false);
        }
    });

    if (chatMessages) {
        chatMessages.addEventListener("scroll", () => {
            if (chatMessages.scrollTop <= olderMessagesThreshold) {
                loadOlderMessages();
            }
        });
    }

    if (chatSearchInput) {
        chatSearchInput.addEventListener("input", () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                refreshChatMessages(chatSearchInput.value);
            }, 250);
        });
    }

    if (chatSocket) {
        chatSocket.addEventListener("open", () => {
            markPrivateChatRead();
        });
    }

    document.body.addEventListener("htmx:wsAfterMessage", () => {
        markPrivateChatRead();
    });

    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") {
            markPrivateChatRead();
        }
    });

    // Update the UI: text input and file preview
    function updateUI() {
        // Update the text input with file names
        if (selectedFiles.length > 0) {
            messageInput.readOnly = true;
            messageInput.value = null;
        } else {
            messageInput.readOnly = false;
            messageInput.value = "";
        }

        // Update the file preview area
        filesPreview.innerHTML = "";
        selectedFiles.forEach((file, index) => {
            const filePreview = document.createElement("div");
            filePreview.classList.add("file-preview-item");
            filePreview.style.display = "flex";
            filePreview.style.alignItems = "center";
            filePreview.style.marginBottom = "8px";

            // Check if the file is an image
            const isImage = file.type.startsWith("image/");
            const thumbnail = document.createElement("img");
            const icon = document.createElement("span");

            if (isImage) {
                const fileReader = new FileReader();
                fileReader.onload = (e) => {
                    thumbnail.src = e.target.result; // Set the thumbnail source
                    thumbnail.style.width = "50px";
                    thumbnail.style.height = "50px";
                    thumbnail.style.marginRight = "10px";
                    thumbnail.style.objectFit = "cover";
                    filePreview.prepend(thumbnail);
                };
                fileReader.readAsDataURL(file); // Read the image file
            } else {
                icon.textContent = "📄"; // Default file icon
                icon.style.fontSize = "30px";
                icon.style.marginRight = "10px";
                filePreview.prepend(icon);
            }

            // Add the file name and remove button
            filePreview.innerHTML += `
                <span>${file.name}</span>
                <button type="button" class="remove-file btn btn-sm btn-danger" data-index="${index}" style="margin-left: 10px;">❌</button>
            `;

            filesPreview.appendChild(filePreview);
        });

        filesPreview.style.display = selectedFiles.length > 0 ? "block" : "none";
    }

    // Remove a file from the list and update the UI
    filesPreview.addEventListener("click", (event) => {
        if (event.target.classList.contains("remove-file")) {
            const fileIndex = parseInt(event.target.dataset.index, 10);

            // Remove the file from the selected files array
            selectedFiles.splice(fileIndex, 1);

            // Recreate the FileList object for the file input
            const dataTransfer = new DataTransfer();
            selectedFiles.forEach(file => dataTransfer.items.add(file));
            fileInput.files = dataTransfer.files;

            updateUI();
        }
    });

    document.addEventListener("click", (event) => {
        const editButton = event.target.closest(".message-edit-button");
        if (editButton) {
            const currentText = editButton.dataset.messageText || "";
            const nextText = prompt("Edit message", currentText);

            if (nextText && nextText.trim() && nextText.trim() !== currentText) {
                sendChatSocketEvent({
                    type: "chat.message_edit",
                    message_id: editButton.dataset.messageId,
                    message: nextText.trim(),
                });
            }

            return;
        }

        const deleteButton = event.target.closest(".message-delete-button");
        if (deleteButton && confirm("Delete this message?")) {
            sendChatSocketEvent({
                type: "chat.message_delete",
                message_id: deleteButton.dataset.messageId,
            });
        }
    });

    // Handle form submission
    form.addEventListener("submit", (event) => {
        event.preventDefault();

        const files = fileInput.files;

        if (files.length > 0) {
            // Handle file upload via fetch
            const formData = new FormData();
            Array.from(files).forEach((file) => {
                formData.append("files", file);
            });

            fetch(`/chat/file/${chatroom_name}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFTokenFromCookies(), // Add the CSRF token from cookies
                    "Accept": "application/json",
                },
                body: formData,
            })
                .then((response) => {
                    return response.json().then((data) => {
                        if (!response.ok) {
                            throw new Error(data.error || "File upload failed.");
                        }
                        return data;
                    });
                })
                .then((data) => {
                    // console.log("Files uploaded successfully:", data);

                    // Reset file input and UI
                    fileInput.value = "";
                    selectedFiles = [];
                    updateUI();
                })
                .catch((error) => {
                    console.error("File upload failed:", error);
                    alert(error.message);
                });
        } else {
            // Handle text message via WebSocket
            const textInput = form.querySelector("[name='message']");
            sendChatSocketEvent({
                type: "chat.message",
                message: textInput.value.trim(),
            });
            textInput.value = ""; // Clear the text input
            clearTimeout(typingTimeout);
            sendTypingStatus(false);
        }
    });

    window.addEventListener("beforeunload", () => {
        if (isTyping && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                type: "chat.typing",
                is_typing: false,
            }));
        }
    });
});


function getCSRFTokenFromCookies() {
    const cookies = document.cookie.split("; ");
    for (let cookie of cookies) {
        const [name, value] = cookie.split("=");
        if (name === "csrftoken") {
            return value;
        }
    }
    return null; // Return null if not found
}
