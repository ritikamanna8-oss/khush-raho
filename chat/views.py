import json
import os
import urllib.request
import urllib.error

from dotenv import load_dotenv

from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import ChatMessage


load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-3.5-flash-lite"


SYSTEM_PROMPT = """
You are an AI companion inside a private group chat called "Khush Raho".

Members:
Sakhi — the user
Krishna
Radha

KRISHNA:
calm, warm, practical, patient, emotionally intelligent,
honest, respectful and gently playful.

RADHA:
warm, affectionate, emotionally expressive, gentle,
caring, attentive and respectfully playful.

IMPORTANT:

Always speak respectfully to Sakhi.

In Bengali or Banglish ALWAYS use:
tumi
tomar
tomake

NEVER use:
tui
tor
toke

Match Sakhi's language naturally.

Banglish -> natural Banglish.
Bengali -> Bengali.
English -> English.
Mixed language -> natural mixed language.

Use the recent conversation to understand context.

If Sakhi is sad or emotionally upset:
acknowledge her feelings first and then give useful guidance when appropriate.

Do not blindly agree with everything.

Do not over-explain.

Do not repeatedly say:
"How are you?"
"Tell me more."
"I'm here for you."

SPEAKER:

If Sakhi explicitly addresses Krishna,
Krishna responds.

If Sakhi explicitly addresses Radha,
Radha responds.

If nobody is explicitly addressed,
choose Krishna or Radha naturally based on the context.

Do not always choose Krishna.
Do not always choose Radha.

Both may respond only when genuinely appropriate.

OUTPUT:

Start the response with exactly one of:

Krishna:
Radha:

or, when both genuinely need to speak:

Krishna:
...
Radha:
...

Keep responses natural and reasonably short.
"""


def get_recent_history(user):

    messages = list(
        ChatMessage.objects
        .filter(user=user)
        .order_by("-created_at")[:4]
    )

    messages.reverse()

    history = ""

    for item in messages:

        history += (
            f"Sakhi: {item.message}\n"
            f"{item.reply}\n\n"
        )

    return history


def build_prompt(user, message):

    history = get_recent_history(user)

    return f"""
{SYSTEM_PROMPT}

RECENT CONVERSATION:

{history}

NEW MESSAGE FROM SAKHI:

{message}
"""


def parse_gemini_stream_line(line):

    line = line.strip()

    if not line:
        return None

    if line.startswith("data:"):

        line = line[5:].strip()

    if not line:
        return None

    try:

        data = json.loads(line)

        candidates = data.get(
            "candidates",
            []
        )

        if not candidates:
            return None

        content = candidates[0].get(
            "content",
            {}
        )

        parts = content.get(
            "parts",
            []
        )

        if not parts:
            return None

        text = parts[0].get(
            "text",
            ""
        )

        return text

    except json.JSONDecodeError:

        return None


@login_required
@csrf_exempt
@require_POST
def chat_view(request):

    try:

        data = json.loads(
            request.body
        )

        message = data.get(
            "message",
            ""
        ).strip()

        if not message:

            return JsonResponse(
                {
                    "error":
                    "Message is empty."
                },
                status=400
            )

        if not GEMINI_API_KEY:

            return JsonResponse(
                {
                    "error":
                    "Gemini API key is not configured."
                },
                status=500
            )


        prompt = build_prompt(
            request.user,
            message
        )


        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/"
            + GEMINI_MODEL
            + ":streamGenerateContent"
            "?alt=sse"
        )


        payload = {

            "contents": [

                {
                    "parts": [

                        {
                            "text": prompt
                        }

                    ]
                }

            ],

            "generationConfig": {

                "temperature": 0.7,

                "maxOutputTokens": 250

            }

        }


        request_data = json.dumps(
            payload
        ).encode("utf-8")


        req = urllib.request.Request(

            url,

            data=request_data,

            headers={

                "Content-Type":
                    "application/json",

                "x-goog-api-key":
                    GEMINI_API_KEY,

                "Accept":
                    "text/event-stream"

            },

            method="POST"
        )


        response = urllib.request.urlopen(
            req,
            timeout=60
        )


        def generate():

            full_reply = ""

            try:

                while True:

                    raw_line = (
                        response
                        .readline()
                    )


                    if not raw_line:
                        break


                    line = (
                        raw_line
                        .decode(
                            "utf-8",
                            errors="ignore"
                        )
                        .strip()
                    )


                    if not line:
                        continue


                    chunk = (
                        parse_gemini_stream_line(
                            line
                        )
                    )


                    if not chunk:
                        continue


                    full_reply += chunk


                    # Send each piece
                    # immediately to browser

                    yield (
                        json.dumps(
                            {
                                "type":
                                    "chunk",

                                "text":
                                    chunk
                            },
                            ensure_ascii=False
                        )
                        + "\n"
                    )


                # --------------------------------
                # DETERMINE PRIMARY SPEAKER
                # --------------------------------

                clean_reply = (
                    full_reply.strip()
                )

                lower_reply = (
                    clean_reply.lower()
                )


                if (
                    lower_reply.startswith(
                        "radha:"
                    )
                    and
                    "\nkrishna:" in
                    lower_reply
                ):

                    speaker = "both"


                elif (
                    lower_reply.startswith(
                        "krishna:"
                    )
                    and
                    "\nradha:" in
                    lower_reply
                ):

                    speaker = "both"


                elif lower_reply.startswith(
                    "radha:"
                ):

                    speaker = "radha"


                else:

                    speaker = "krishna"


                # --------------------------------
                # SAVE CHAT
                # --------------------------------

                primary_persona = (
                    "radha"
                    if speaker == "radha"
                    else "krishna"
                )


                ChatMessage.objects.create(

                    user=request.user,

                    message=message,

                    reply=clean_reply,

                    persona=primary_persona

                )


                # --------------------------------
                # FINAL EVENT
                # --------------------------------

                yield (
                    json.dumps(
                        {
                            "type":
                                "done",

                            "speaker":
                                speaker
                        }
                    )
                    + "\n"
                )


            finally:

                response.close()


        streaming_response = (
            StreamingHttpResponse(
                generate(),
                content_type=
                    "application/x-ndjson"
            )
        )


        streaming_response[
            "Cache-Control"
        ] = "no-cache"


        streaming_response[
            "X-Accel-Buffering"
        ] = "no"


        return streaming_response


    except urllib.error.HTTPError as error:

        error_body = (
            error.read()
            .decode(
                "utf-8",
                errors="ignore"
            )
        )


        return JsonResponse(

            {
                "error":
                    "Gemini API error.",

                "details":
                    error_body
            },

            status=500
        )


    except Exception as error:

        return JsonResponse(

            {
                "error":
                    "Something went wrong.",

                "details":
                    str(error)
            },

            status=500
        )