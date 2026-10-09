/* =========================================
   ELEMENTS
========================================= */

const messageInput =
    document.getElementById("messageInput");

const sendButton =
    document.getElementById("sendBtn");

const chatMessages =
    document.getElementById("chatMessages");

const cameraBtn =
    document.getElementById("cameraBtn");

const cameraInput =
    document.getElementById("cameraInput");

const micBtn =
    document.getElementById("micBtn");

const themeBtn =
    document.getElementById("themeBtn");

const muteBtn =
    document.getElementById("muteBtn");

const languageBtn =
    document.getElementById("languageBtn");

const notesBtn =
    document.getElementById("notesBtn");


/* =========================================
   ACTIVE AI PERSONA
========================================= */

let activePersona = "krishna";


/* =========================================
   TIME
========================================= */

function getCurrentTime() {

    return new Date().toLocaleTimeString(
        [],
        {
            hour: "2-digit",
            minute: "2-digit"
        }
    );
}


/* =========================================
   ESCAPE HTML
========================================= */

function escapeHTML(text) {

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


/* =========================================
   DETECT WHO USER IS CALLING
========================================= */

function detectPersona(message) {

    const text = message.toLowerCase();

    /* Radha keywords */

    if (
        text.includes("radha") ||
        text.includes("radhaji") ||
        text.includes("radha ji") ||
        text.includes("রাধা")
    ) {

        activePersona = "radha";

        return;
    }


    /* Krishna keywords */

    if (
        text.includes("krishna") ||
        text.includes("krishno") ||
        text.includes("krishnaji") ||
        text.includes("krishna ji") ||
        text.includes("কৃষ্ণ")
    ) {

        activePersona = "krishna";

        return;
    }

    /*
     * If no name is mentioned,
     * continue talking to whoever is currently active.
     */
}


/* =========================================
   AVATAR SETUP
========================================= */

function setAIAvatar(element, persona) {

    element.style.width = "48px";
    element.style.height = "48px";
    element.style.minWidth = "48px";

    element.style.borderRadius = "50%";

    element.style.backgroundRepeat = "no-repeat";
    element.style.backgroundSize = "cover";
    element.style.backgroundPosition = "center";

    element.style.backgroundColor = "#24557a";

    element.style.overflow = "hidden";

    element.style.fontSize = "0";


    if (persona === "radha") {

        element.style.backgroundImage =
            'url("assets/radha.jpg")';

    } else {

        element.style.backgroundImage =
            'url("assets/krishna.jpg")';
    }
}


/* =========================================
   ADD USER MESSAGE
========================================= */

function addUserMessage(text) {

    const row =
        document.createElement("div");

    row.className =
        "message-row sent";

    row.innerHTML = `
        <div class="message-wrapper">

            <div class="message-bubble">

                ${escapeHTML(text)}

                <span class="message-time">
                    ${getCurrentTime()}
                    <span class="message-check">✓✓</span>
                </span>

            </div>

        </div>
    `;

    chatMessages.appendChild(row);

    scrollToBottom();
}


/* =========================================
   ADD AI MESSAGE
========================================= */

function addAIMessage(text, persona) {

    const row =
        document.createElement("div");

    row.className =
        "message-row received";


    const avatar =
        document.createElement("div");

    avatar.className =
        "small-avatar";


    /* Set Krishna/Radha image */

    setAIAvatar(
        avatar,
        persona
    );


    const wrapper =
        document.createElement("div");

    wrapper.className =
        "message-wrapper";


    const senderName =
        document.createElement("div");

    senderName.className =
        "sender-name";


    /* Name */

    if (persona === "radha") {

        senderName.textContent =
            "Radha";

    } else {

        senderName.textContent =
            "Krishna";
    }


    const bubble =
        document.createElement("div");

    bubble.className =
        "message-bubble";


    bubble.innerHTML = `
        ${escapeHTML(text)}

        <span class="message-time">
            ${getCurrentTime()}
        </span>
    `;


    wrapper.appendChild(senderName);

    wrapper.appendChild(bubble);

    row.appendChild(avatar);

    row.appendChild(wrapper);

    chatMessages.appendChild(row);

    scrollToBottom();
}


/* =========================================
   TYPING INDICATOR
========================================= */

function showTyping(persona) {

    const row =
        document.createElement("div");

    row.id =
        "typingMessage";

    row.className =
        "message-row received";


    const avatar =
        document.createElement("div");

    avatar.className =
        "small-avatar";


    setAIAvatar(
        avatar,
        persona
    );


    const wrapper =
        document.createElement("div");

    wrapper.className =
        "message-wrapper";


    const senderName =
        document.createElement("div");

    senderName.className =
        "sender-name";


    const bubble =
        document.createElement("div");

    bubble.className =
        "message-bubble typing-bubble";


    if (persona === "radha") {

        senderName.textContent =
            "Radha";

        bubble.textContent =
            "Radha is typing...";

    } else {

        senderName.textContent =
            "Krishna";

        bubble.textContent =
            "Krishna is typing...";
    }


    wrapper.appendChild(senderName);

    wrapper.appendChild(bubble);

    row.appendChild(avatar);

    row.appendChild(wrapper);

    chatMessages.appendChild(row);

    scrollToBottom();
}


/* =========================================
   REMOVE TYPING
========================================= */

function removeTyping() {

    const typing =
        document.getElementById(
            "typingMessage"
        );

    if (typing) {

        typing.remove();
    }
}


/* =========================================
   SCROLL
========================================= */

function scrollToBottom() {

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


/* =========================================
   SEND MESSAGE
========================================= */

async function sendMessage() {

    const message =
        messageInput.value.trim();


    if (!message) {

        return;
    }


    /* =====================================
       CHECK WHO USER IS TALKING TO
    ===================================== */

    detectPersona(message);


    /*
     * Save the currently active persona.
     * This prevents the persona from changing
     * while Gemini is replying.
     */

    const currentPersona =
        activePersona;


    /* USER MESSAGE */

    addUserMessage(message);

    messageInput.value = "";

    messageInput.focus();


    /* TYPING */

    showTyping(
        currentPersona
    );


    try {

        const response =
            await fetch(
                "/api/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        message:
                            message,

                        persona:
                            currentPersona

                    })
                }
            );


        const data =
            await response.json();


        removeTyping();


        if (!response.ok) {

            console.error(
                "Server error:",
                data
            );


            addAIMessage(

                "Sakhi... ekta technical problem holo. Abar bolo. 🙏",

                currentPersona

            );

            return;
        }


        /* =================================
           GEMINI REPLY
        ================================= */

        addAIMessage(

            data.reply,

            data.persona ||
            currentPersona

        );


    } catch (error) {

        console.error(
            "Connection error:",
            error
        );


        removeTyping();


        addAIMessage(

            "Sakhi... connection-e ektu problem holo. Abar try koro. 💙",

            currentPersona

        );
    }
}


/* =========================================
   SEND BUTTON
========================================= */

sendButton.addEventListener(
    "click",
    sendMessage
);


/* =========================================
   ENTER KEY
========================================= */

messageInput.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter") {

            event.preventDefault();

            sendMessage();
        }
    }
);


/* =========================================
   CAMERA
========================================= */

cameraBtn.addEventListener(
    "click",
    function() {

        cameraInput.click();

    }
);


cameraInput.addEventListener(
    "change",
    function() {

        if (
            cameraInput.files.length > 0
        ) {

            addUserMessage(
                "📷 Photo selected"
            );

            /*
             * Actual image upload to Gemini
             * will be added later.
             */

        }

    }
);


/* =========================================
   MICROPHONE
========================================= */

let recognition = null;


if (
    "webkitSpeechRecognition"
    in window
) {

    recognition =
        new webkitSpeechRecognition();


    recognition.lang =
        "bn-IN";


    recognition.continuous =
        false;


    recognition.interimResults =
        false;


    recognition.onresult =
        function(event) {

            const transcript =
                event.results[0][0]
                .transcript;


            messageInput.value =
                transcript;


            messageInput.focus();

        };


    recognition.onstart =
        function() {

            micBtn.textContent =
                "🔴";

        };


    recognition.onend =
        function() {

            micBtn.textContent =
                "🎤";

        };

}


micBtn.addEventListener(
    "click",
    function() {

        if (!recognition) {

            alert(
                "Voice input is not supported in this browser."
            );

            return;
        }


        recognition.start();

    }
);


/* =========================================
   THEME
========================================= */

themeBtn.addEventListener(
    "click",
    function() {

        document.body.classList.toggle(
            "light-theme"
        );


        if (
            document.body.classList.contains(
                "light-theme"
            )
        ) {

            themeBtn.textContent =
                "🌙";

        } else {

            themeBtn.textContent =
                "🌞";
        }

    }
);


/* =========================================
   MUTE
========================================= */

let muted = false;


muteBtn.addEventListener(
    "click",
    function() {

        muted = !muted;


        muteBtn.textContent =
            muted ? "🔕" : "🔇";

    }
);


/* =========================================
   LANGUAGE
========================================= */

languageBtn.addEventListener(
    "click",
    function() {

        if (
            languageBtn
                .querySelector("span")
        ) {

            const label =
                languageBtn
                .querySelector("span");


            label.textContent =
                label.textContent === "বাংলা"
                    ? "English"
                    : "বাংলা";
        }

    }
);


/* =========================================
   NOTES
========================================= */

notesBtn.addEventListener(
    "click",
    function() {

        alert(
            "Sakhi Notes will be added here later. 📝"
        );

    }
);


/* =========================================
   INITIAL FOCUS
========================================= */

messageInput.focus();