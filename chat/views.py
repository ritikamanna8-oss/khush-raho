
import json
import os
import urllib.request
import urllib.error

from dotenv import load_dotenv

from django.conf import settings
from django.db import transaction
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .models import ChatMessage


load_dotenv(settings.BASE_DIR / ".env")

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
acknowledge her feelings first and give useful guidance when appropriate.

Do not blindly agree with everything.
Do not over-explain.
Do not repeatedly say:
"How are you?"
"Tell me more."
"I'm here for you."

SPEAKER:

If Sakhi explicitly addresses Krishna, Krishna responds.
If Sakhi explicitly addresses Radha, Radha responds.
If nobody is explicitly addressed, choose Krishna or Radha naturally.
Do not always choose Krishna.
Do not always choose Radha.
Both may respond only when genuinely appropriate.

OUTPUT:

Start the response with exactly one of:

Krishna:
Radha:

Or, when both genuinely need to speak:

Krishna:
...
Radha:
...

Keep responses natural and reasonably short.
"""


def get_recent_history(user, before_message=None):
    queryset = ChatMessage.objects.filter(user=user)

    # When editing, use only the conversation before that message.
    if before_message is not None:
        queryset = queryset.filter(
            created_at__lt=before_message.created_at
        )

    messages = list(queryset.order_by("-created_at", "-id")[:4])
    messages.reverse()

    history = ""

    for item in messages:
        history += (
            f"Sakhi: {item.message}\n"
            f"{item.reply}\n\n"
        )

    return history


def build_prompt(user, message, before_message=None):
    history = get_recent_history(
        user,
        before_message=before_message
    )

    return f"""
{SYSTEM_PROMPT}

RECENT CONVERSATION:

{history}

NEW MESSAGE FROM SAKHI:

{message}
"""


def parse_gemini_stream_line(line):
    line = line.strip()

    if line.startswith("data:"):
        line = line[5:].strip()

    if not line or line == "[DONE]":
        return None

    try:
        data = json.loads(line)
        candidates = data.get("candidates", [])

        if not candidates:
            return None

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        if not parts:
            return None

        return "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict)
        )

    except (json.JSONDecodeError, TypeError, AttributeError):
        return None


def get_speaker(reply):
    lower_reply = reply.strip().lower()

    if (
        lower_reply.startswith("radha:")
        and "\nkrishna:" in lower_reply
    ):
        return "both"

    if (
        lower_reply.startswith("krishna:")
        and "\nradha:" in lower_reply
    ):
        return "both"

    if lower_reply.startswith("radha:"):
        return "radha"

    return "krishna"


def get_primary_persona(speaker):
    return "radha" if speaker == "radha" else "krishna"


def call_gemini_once(prompt):
    """Generate a complete reply for the edit operation."""

    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini API key is not configured.")

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{GEMINI_MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 400
        }
    }

    request_data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    candidates = result.get("candidates", [])

    if not candidates:
        raise RuntimeError(
            "Gemini returned no reply. Please try editing again."
        )

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )

    reply = "".join(
        part.get("text", "")
        for part in parts
        if isinstance(part, dict)
    ).strip()

    if not reply:
        raise RuntimeError("Gemini returned an empty reply.")

    return reply


@login_required
@require_POST
def chat_view(request):
    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()

        if not message:
            return JsonResponse(
                {"error": "Message is empty."},
                status=400
            )

        if len(message) > 10000:
            return JsonResponse(
                {"error": "Message is too long."},
                status=400
            )

        if not GEMINI_API_KEY:
            return JsonResponse(
                {"error": "Gemini API key is not configured."},
                status=500
            )

        prompt = build_prompt(request.user, message)

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{GEMINI_MODEL}:streamGenerateContent"
            "?alt=sse"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 250
            }
        }

        request_data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
                "Accept": "text/event-stream"
            },
            method="POST"
        )

        response = urllib.request.urlopen(req, timeout=60)

        def generate():
            full_reply = ""

            try:
                while True:
                    raw_line = response.readline()

                    if not raw_line:
                        break

                    line = raw_line.decode(
                        "utf-8",
                        errors="ignore"
                    ).strip()

                    if not line:
                        continue

                    chunk = parse_gemini_stream_line(line)

                    if not chunk:
                        continue

                    full_reply += chunk

                    yield (
                        json.dumps(
                            {
                                "type": "chunk",
                                "text": chunk
                            },
                            ensure_ascii=False
                        ) + "\n"
                    )

                clean_reply = full_reply.strip()

                if not clean_reply:
                    yield json.dumps({
                        "type": "error",
                        "error": "Gemini returned an empty reply."
                    }) + "\n"
                    return

                speaker = get_speaker(clean_reply)

                saved_message = ChatMessage.objects.create(
                    user=request.user,
                    message=message,
                    reply=clean_reply,
                    persona=get_primary_persona(speaker)
                )

                yield (
                    json.dumps({
                        "type": "done",
                        "speaker": speaker,
                        "message_id": saved_message.id
                    }) + "\n"
                )

            except Exception:
                yield json.dumps({
                    "type": "error",
                    "error": "The reply could not be completed. Please try again."
                }) + "\n"

            finally:
                response.close()

        streaming_response = StreamingHttpResponse(
            generate(),
            content_type="application/x-ndjson"
        )
        streaming_response["Cache-Control"] = "no-cache"
        streaming_response["X-Accel-Buffering"] = "no"
        return streaming_response

    except urllib.error.HTTPError as error:
        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        return JsonResponse(
            {
                "error": "Gemini API error.",
                "details": error_body
            },
            status=500
        )

    except Exception as error:
        return JsonResponse(
            {
                "error": "Something went wrong.",
                "details": str(error)
            },
            status=500
        )


@login_required
def chat_history_view(request):
    messages = (
        ChatMessage.objects
        .filter(user=request.user)
        .order_by("created_at", "id")
    )

    history = [
        {
            "id": item.id,
            "message": item.message,
            "reply": item.reply,
            "persona": item.persona,
            "created_at": item.created_at.isoformat(),
        }
        for item in messages
    ]

    return JsonResponse({"history": history})


@login_required
@require_POST
def edit_message_view(request, message_id):
    try:
        data = json.loads(request.body)
        new_message = data.get("message", "").strip()

    except (json.JSONDecodeError, AttributeError, TypeError):
        return JsonResponse(
            {"error": "Invalid request."},
            status=400
        )

    if not new_message:
        return JsonResponse(
            {"error": "Message cannot be empty."},
            status=400
        )

    if len(new_message) > 10000:
        return JsonResponse(
            {"error": "Message is too long."},
            status=400
        )

    if not GEMINI_API_KEY:
        return JsonResponse(
            {"error": "Gemini API key is not configured."},
            status=500
        )

    chat_message = get_object_or_404(
        ChatMessage,
        id=message_id,
        user=request.user
    )

    try:
        # Generate the replacement reply before changing the database.
        # If Gemini fails, the old message and reply remain intact.
        prompt = build_prompt(
            request.user,
            new_message,
            before_message=chat_message
        )

        new_reply = call_gemini_once(prompt)
        speaker = get_speaker(new_reply)

        with transaction.atomic():
            chat_message.message = new_message
            chat_message.reply = new_reply
            chat_message.persona = get_primary_persona(speaker)
            chat_message.save(
                update_fields=["message", "reply", "persona"]
            )

        return JsonResponse({
            "success": True,
            "id": chat_message.id,
            "message": chat_message.message,
            "reply": chat_message.reply,
            "persona": chat_message.persona,
            "speaker": speaker,
        })

    except urllib.error.HTTPError as error:
        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        return JsonResponse(
            {
                "error": "Gemini API error while editing.",
                "details": error_body
            },
            status=500
        )

    except Exception as error:
        return JsonResponse(
            {
                "error": "Could not update the message and reply.",
                "details": str(error)
            },
            status=500
        )


@login_required
@require_POST
def delete_message_view(request, message_id):
    with transaction.atomic():
        chat_message = get_object_or_404(
            ChatMessage.objects.select_for_update(),
            id=message_id,
            user=request.user
        )
        chat_message.delete()

    return JsonResponse({
        "success": True,
        "deleted_id": message_id
    })