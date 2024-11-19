
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

// document.addEventListener("htmx:oobBeforeSwap", (event) => {
//     if (event.target.id === 'chatroom-container'){
//         const container = document.getElementById(event.target.id)
//         const first_element_id = container.firstChild.nextSibling.id
//         const url=event.target.baseURI
//         const match = url.match(/\/chatroom\/([^\/]+)/);
//         const chatroomId = match[1];
//
//         const chatroomDiv = document.getElementById(chatroomId);
//
//         if(first_element_id === chatroomId){
//             event.preventDefault()
//         }
//         else{
//             if (chatroomDiv) {
//             chatroomDiv.remove();
//                 } else {
//                     console.log(`Div with ID ${chatroomId} not found.`);
//                 }
//         }
//
//
//
//     }
//
// });