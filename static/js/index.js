
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

            const messageInput = document.querySelector('input[name="message"]');
            if (messageInput) {
                messageInput.value = '';  // Clear the input field
            }
    });

document.addEventListener("htmx:oobBeforeSwap", (event) => {
    if (event.target.classList.contains('chatroom_name')) {
        const removeDivId = event.target.id;

        // Prevent the default swap behavior
        event.preventDefault();

        // Get the div to be removed
        const removedDiv = document.getElementById(removeDivId);

        // Get the target container where you want to insert the div
        const chatContainer = document.getElementById('chatroom-container');

        if (removedDiv && chatContainer) {
            // Check if the first child is an element and compare the ids
            const firstChild = chatContainer.firstChild;

            // Check if the first child exists and its id is not the same as removedDiv's id
            if (firstChild && firstChild.id !== removedDiv.id) {
                // Remove the div from its current position
                removedDiv.remove();
                removedDiv.classList.add('fade-in-up');
                // Insert the removed div as the first child of chatContainer
                chatContainer.insertBefore(removedDiv, firstChild);
            }
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
    const fileInput = document.getElementById("file-input");
    const attachButton = document.getElementById("attach-button");
    const messageInput = document.getElementById("message-input");
    const filesPreview = document.getElementById("files-preview");

    let selectedFiles = []; // Array to store selected files

    // Trigger file input when attach button is clicked
    attachButton.addEventListener("click", () => {
        fileInput.click();
    });

    // Handle file selection
    fileInput.addEventListener("change", () => {
        const files = Array.from(fileInput.files);

        // Add new files to the selected files list
        files.forEach((file) => {
            if (!selectedFiles.find(f => f.name === file.name)) {
                selectedFiles.push(file);
            }
        });

        updateUI();
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

    // Handle form submission
    const form = document.getElementById("send-chat-form");
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
                .then((response) => response.json())
                .then((data) => {
                    // console.log("Files uploaded successfully:", data);

                    // Reset file input and UI
                    fileInput.value = "";
                    selectedFiles = [];
                    updateUI();
                })
                .catch((error) => {
                    console.error("File upload failed:", error);
                });
        } else {
            // Handle text message via WebSocket
            const textInput = form.querySelector("[name='message']");
            const ws = new WebSocket(`ws://127.0.0.1:8000/ws/chatroom/${chatroom_name}/`);

            ws.onopen = () => {
                ws.send(JSON.stringify({ message: textInput.value.trim() }));
                textInput.value = ""; // Clear the text input
            };
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
