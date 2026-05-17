// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const gameContainer = document.getElementById('game-container');
    const dialogueTextElement = document.getElementById('dialogue-text');
    const speakerNameElement = document.getElementById('speaker-name');
    const playerInput = document.getElementById('player-input');
    const sendBtn = document.getElementById('send-btn');
    const dayCounter = document.getElementById('day-counter');
    const guardCounter = document.getElementById('guard-counter');
    const portraitElement = document.getElementById('character-portrait');
    const typingIndicator = document.getElementById('typing-indicator');
    const gameOverScreen = document.getElementById('game-over-screen');
    const gameOverTitle = document.getElementById('game-over-title');
    const gameOverText = document.getElementById('game-over-text');
    const restartBtn = document.getElementById('restart-btn');

    // --- Typewriter Effect ---
    function typeWriter(element, text, callback) {
        let i = 0;
        element.innerHTML = ""; // Clear existing text
        function type() {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
                setTimeout(type, 25); // Adjust typing speed here
            } else if (callback) {
                callback();
            }
        }
        type();
    }

    // --- Update UI ---
    function updateUI(data) {
        if (data.day) dayCounter.textContent = `Day: ${data.day}`;
        if (data.guard_level) guardCounter.textContent = `Guard: ${data.guard_level}/3`;
        
        const guardInfo = data.guard_info || initialGameState.guard_info;
        if (guardInfo) {
            if (guardInfo.background) {
                gameContainer.style.backgroundImage = `url('/static/images/${guardInfo.background}')`;
            }
        }
    }

    function showGameOver(status, message) {
        gameOverTitle.textContent = status === 'won' ? 'Victory!' : 'Mission Failed';
        gameOverTitle.style.color = status === 'won' ? '#2ecc71' : '#e74c3c';
        typeWriter(gameOverText, message, null);
        gameOverScreen.classList.remove('hidden');
    }

    // --- Display a message in the dialogue box ---
    function displayMessage(speaker, text, portrait) {
        speakerNameElement.textContent = speaker;
        if(portrait) {
            portraitElement.src = portrait;
            portraitElement.style.opacity = 1;
        } else {
            portraitElement.style.opacity = 0; // Hide portrait for system messages
        }
        
        playerInput.disabled = true;
        sendBtn.disabled = true;
        typingIndicator.classList.add('hidden');

        typeWriter(dialogueTextElement, text, () => {
             // Re-enable input only if the game is not over
            if (gameOverScreen.classList.contains('hidden')) {
                playerInput.disabled = false;
                sendBtn.disabled = false;
                playerInput.focus();
            }
        });
    }
    
    // --- Send Message to Backend ---
    async function sendMessage() {
        const message = playerInput.value.trim();
        if (!message) return;

        // Display player's message immediately
        displayMessage('Agent', message, '/static/images/player.png');
        playerInput.value = '';
        
        // Show typing indicator while waiting for AI
        setTimeout(() => {
            typingIndicator.classList.remove('hidden');
        }, 500);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message }),
            });
            const data = await response.json();

            // Handle the different response statuses from the backend
            handleResponse(data);

        } catch (error) {
            console.error('Error:', error);
            displayMessage('System', 'Error connecting to the server. Please check the console.', null);
        }
    }

    // --- Handle Backend Response ---
    function handleResponse(data) {
        // First, display the last thing the previous character said, if applicable
        if (data.final_response) {
            // Need to determine who said the final response before the state change
            displayMessage(document.getElementById('speaker-name').textContent, data.final_response, portraitElement.src);
        }
        
        // Wait for the final response to type out before showing the next message
        const delay = data.final_response ? (data.final_response.length * 25) + 1000 : 0;

        setTimeout(() => {
            switch (data.status) {
                case 'won':
                    showGameOver('won', data.message);
                    break;
                case 'lost':
                    showGameOver('lost', data.message);
                    break;
                case 'debriefing':
                    gameContainer.style.backgroundImage = `url('/static/images/${data.captain_info.background}')`;
                    displayMessage(data.captain_info.name, data.message, `/static/images/${data.captain_info.portrait}`);
                    break;
                case 'next_guard':
                    displayMessage('System', data.message, null);
                    const transitionDelay = (data.message.length * 25) + 1000;
                    setTimeout(() => {
                        updateUI(data);
                        displayMessage(data.guard_info.name, data.next_guard_intro, `/static/images/${data.guard_info.portrait}`);
                    }, transitionDelay);
                    break;
                case 'retry':
                    updateUI(data);
                    displayMessage('Captain Eva', data.captain_response, '/static/images/captain.png');
                     const retryDelay = (data.captain_response.length * 25) + 1000;
                    setTimeout(() => {
                        gameContainer.style.backgroundImage = `url('/static/images/${data.guard_info.background}')`;
                        displayMessage(data.initial_message.name, data.initial_message.content, data.initial_message.portrait);
                    }, retryDelay);
                    break;
                case 'continue':
                    displayMessage(data.speaker_name, data.message, data.portrait);
                    break;
            }
        }, delay);
    }


    // --- Event Listeners ---
    sendBtn.addEventListener('click', sendMessage);
    playerInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    restartBtn.addEventListener('click', () => {
        window.location.href = '/reset';
    });


    // --- Initial Game Load ---
    function loadInitialState() {
        updateUI(initialGameState);
        const initialDialogue = initialGameState.initial_dialogue;
        displayMessage(initialDialogue.name, initialDialogue.content, initialDialogue.portrait);
    }
    
    loadInitialState();
});