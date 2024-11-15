
      window.addEventListener('load', function() {
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    });
    // htmx:afterSwap,afterRequest
    // HTMX event listener for when the request is finished and the content is swapped
    document.body.addEventListener('htmx:wsAfterMessage', function(event) {
        console.log('youuu')
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
