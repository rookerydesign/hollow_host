// Main JavaScript for Hollow Host UI

document.addEventListener('DOMContentLoaded', function() {
    // Handle command form submission
    const commandForm = document.getElementById('command-form');
    const playerInput = document.getElementById('player-input');
    const messageLog = document.querySelector('.message-log');

    if (commandForm) {
        commandForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const input = playerInput.value.trim();
            if (!input) return;

            try {
                // Add player message to log
                const playerMessage = document.createElement('div');
                playerMessage.className = 'message player-message';
                playerMessage.textContent = input;
                messageLog.appendChild(playerMessage);

                // Clear input
                playerInput.value = '';

                // Send command to server
                const response = await fetch('/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `player_input=${encodeURIComponent(input)}`
                });

                const data = await response.json();

                // Handle different response types
                if (data.type === 'roll') {
                    const dmMessage = document.createElement('div');
                    dmMessage.className = 'message dm-message';
                    dmMessage.textContent = data.formatted;
                    messageLog.appendChild(dmMessage);
                } else if (data.type === 'narrative') {
                    const dmMessage = document.createElement('div');
                    dmMessage.className = 'message dm-message';
                    dmMessage.textContent = data.response;
                    messageLog.appendChild(dmMessage);
                } else if (data.type === 'command') {
                    const dmMessage = document.createElement('div');
                    dmMessage.className = 'message dm-message';
                    dmMessage.textContent = data.result.message;
                    messageLog.appendChild(dmMessage);
                }

                // Scroll to bottom
                messageLog.scrollTop = messageLog.scrollHeight;

            } catch (error) {
                console.error('Error:', error);
                const errorMessage = document.createElement('div');
                errorMessage.className = 'message error-message';
                errorMessage.textContent = 'Error processing command. Please try again.';
                messageLog.appendChild(errorMessage);
            }
        });
    }

    // Auto-focus input field on game page
    if (playerInput) {
        playerInput.focus();
    }
});