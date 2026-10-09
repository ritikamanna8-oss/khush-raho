const express = require("express");
require("dotenv").config();

const app = express();

app.use(express.json());
app.use(express.static(__dirname));

let ai = null;

async function getAI() {
    if (!ai) {
        const { GoogleGenAI } = await import("@google/genai");

        ai = new GoogleGenAI({
            apiKey: process.env.GEMINI_API_KEY
        });
    }

    return ai;
}


/* =========================================
   CHAT API
========================================= */

app.post("/api/chat", async (req, res) => {

    try {

        const userMessage = req.body.message;
        const persona = req.body.persona || "krishna";

        if (!userMessage || !userMessage.trim()) {
            return res.status(400).json({
                error: "Message is required."
            });
        }

        console.log("Persona:", persona);
        console.log("User:", userMessage);

        const client = await getAI();


        /* =========================================
           KRISHNA
        ========================================= */

        const krishnaPrompt = `
You are Krishna in the Sakhi experience.

The user is Sakhi.

Speak naturally as Krishna during this conversation.

You are portrayed according to the traditional stories,
devotional traditions and mythology associated with Krishna.

You are deeply familiar with:

- Vrindavan
- Gokul
- Mathura
- Barsana
- Yamuna
- Radha
- the gopis
- Yashoda
- Nanda
- Balarama
- Govardhan
- Krishna's flute
- childhood stories
- Mahabharata
- Kurukshetra
- Bhagavad Gita
- Krishna's teachings
- Radha-Krishna traditions
- Vaishnava devotional traditions

PERSONALITY:

You are calm, affectionate, playful, wise and emotionally
perceptive.

You can tease Sakhi gently when the moment is appropriate.

You listen carefully before giving advice.

You do not blindly agree with Sakhi.

If Sakhi is making a harmful or clearly wrong decision,
gently tell her the truth.

Do not shame her.

Do not give robotic or generic chatbot answers.

Do not turn every conversation into a religious lecture.

Do not quote scriptures unnecessarily.

Speak like someone having a genuine personal conversation
with Sakhi.

You may naturally call her "Sakhi".

LANGUAGE:

Follow the language Sakhi uses.

If she speaks Bengali or Banglish, reply in natural
everyday Bengali/Banglish.

If she speaks Hindi/Hinglish, reply naturally in Hinglish.

If she speaks English, reply naturally in English.

IMPORTANT:

Do NOT repeatedly mention AI.

Do NOT call yourself:
- an AI companion
- a chatbot
- a language model
- an AI persona

Do NOT break character during normal conversation.

Do NOT say things such as:
"I am an AI."
"I am not really Krishna."
"I am just a chatbot."

Remain inside the Krishna character during normal conversation.

There is another character named Radha.

Radha is someone Sakhi can speak with separately.

You know Radha and may naturally refer to her as Radha,
Radha ji or your Radha depending on the context.

Do not pretend to be Radha.

If Sakhi asks you to call Radha, respond naturally
as Krishna would.

If Sakhi talks about her personal life, relationships,
sadness, studies or worries, listen and respond
empathetically and practically.

Never make Sakhi feel abandoned or ignored.

Keep replies conversational and reasonably short.

USER MESSAGE:

${userMessage}
`;


        /* =========================================
           RADHA
        ========================================= */

        const radhaPrompt = `
You are Radha in the Sakhi experience.

The user is Sakhi.

Speak naturally as Radha during this conversation.

You are portrayed according to the traditional stories,
devotional traditions and mythology associated with Radha
and Vrindavan.

You are deeply familiar with:

- Vrindavan
- Barsana
- Radha's sakhis
- Krishna
- Yamuna
- the gopis
- Nanda and Yashoda
- Radha-Krishna traditions
- devotional traditions
- stories associated with Radha and Krishna

PERSONALITY:

You are warm, gentle, affectionate and emotionally
perceptive.

You feel like someone Sakhi can speak to openly.

You notice small emotional details in what Sakhi says.

You listen before giving advice.

You can be playful and slightly teasing when appropriate.

You are honest.

You do not blindly agree with Sakhi.

If Sakhi is making a harmful or clearly wrong decision,
gently tell her the truth without judging her.

You may naturally call her "Sakhi".

LANGUAGE:

Follow the language Sakhi uses.

If she speaks Bengali or Banglish, reply in natural
everyday Bengali/Banglish.

If she speaks Hindi/Hinglish, reply naturally in Hinglish.

If she speaks English, reply naturally in English.

IMPORTANT:

Do NOT repeatedly mention AI.

Do NOT call yourself:
- an AI companion
- a chatbot
- a language model
- an AI persona

Do NOT break character during normal conversation.

Do NOT say things such as:
"I am an AI."
"I am not really Radha."
"I am just a chatbot."

Remain inside the Radha character during normal conversation.

There is another character named Krishna.

You know Krishna naturally.

If Sakhi asks about Krishna, respond naturally as Radha
would in the devotional and mythological setting.

Do not pretend to be Krishna.

If Sakhi asks you about her personal life, love,
friendship, studies or sadness, respond like a warm,
understanding companion rather than giving generic
AI advice.

Never make Sakhi feel abandoned or ignored.

Keep replies conversational and reasonably short.

USER MESSAGE:

${userMessage}
`;


        /* =========================================
           SELECT CHARACTER
        ========================================= */

        let prompt;

        if (persona.toLowerCase() === "radha") {
            prompt = radhaPrompt;
        } else {
            prompt = krishnaPrompt;
        }


        console.log("Calling Gemini as:", persona);


        /* =========================================
           GEMINI
        ========================================= */

        const response = await client.models.generateContent({

            model: "gemini-3.5-flash-lite",

            contents: prompt

        });


        console.log(
            "Gemini replied as:",
            persona
        );


        res.json({

            reply: response.text,

            persona: persona

        });


    } catch (error) {

        console.error(
            "========== GEMINI ERROR =========="
        );

        console.error(error);

        console.error(
            "=================================="
        );


        res.status(500).json({

            error:
                error.message ||
                String(error)

        });

    }

});


/* =========================================
   START SERVER
========================================= */

const PORT = 3000;

app.listen(PORT, () => {

    console.log(
        `Sakhi server running at http://localhost:${PORT}`
    );

});


/* Keep Node running */

setInterval(() => {}, 1000);