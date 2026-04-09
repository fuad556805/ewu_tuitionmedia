from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from accounts.models import User
from posts.models import Post
import logging
import requests
import json

logger = logging.getLogger(__name__)


@login_required
def guru_page(request):
    return render(request, 'guru/guru.html')


@login_required
def guru_ask(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data = json.loads(request.body)
    user_message = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    tutors = User.objects.filter(role='tutor', banned=False).values(
        'first_name', 'last_name', 'subjects', 'location', 'university', 'college'
    )
    tutor_list = [
        {
            'name': f"{t['first_name']} {t['last_name']}",
            'subjects': t['subjects'],
            'location': t['location'],
            'education': t.get('university') or t.get('college', ''),
        }
        for t in tutors
    ]

    active_posts = Post.objects.filter(status='active').values(
        'subject', 'location', 'budget', 'schedule', 'student__first_name'
    )
    post_list = [
        {
            'subject': p['subject'],
            'location': p['location'],
            'budget': p['budget'],
            'schedule': p['schedule'],
        }
        for p in active_posts
    ]

    system_prompt = (
        f"You are Guru, a smart AI assistant for TuitionMedia — Bangladesh's tuition matching platform.\n"
        f"Available tutors: {json.dumps(tutor_list)}\n"
        f"Active posts: {json.dumps(post_list)}\n"
        f"Current user: {request.user.get_full_name()} ({request.user.role})\n"
        f"Respond in a warm mix of Bangla and English. Be helpful and concise (under 150 words). "
        f"For matching: suggest specific tutors or posts by name with reasons. "
        f"For general questions: give helpful advice about tuition, studying, platform usage."
    )

    # ── 1. GROQ (try first) ──────────────────────────────────────────
    groq_keys = [k for k in [
        getattr(settings, 'GROQ_API_KEY', ''),
        getattr(settings, 'GROQ_API_KEY_2', ''),
    ] if k]

    groq_models = [
        'llama-3.3-70b-versatile',
        'llama-3.1-8b-instant',
        'mixtral-8x7b-32768',
    ]

    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        messages.append({"role": h['role'], "content": h['content']})
    messages.append({"role": "user", "content": user_message})

    for groq_key in groq_keys:
        for model in groq_models:
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 512,
                        "temperature": 0.7,
                    },
                    timeout=30,
                )
                result = response.json()
                if response.status_code == 200 and 'choices' in result:
                    reply = result['choices'][0]['message']['content']
                    logger.info("Groq success: %s", model)
                    return JsonResponse({'reply': reply})

                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.warning("Groq model %s failed (%s): %s", model, response.status_code, error_msg)

            except Exception as exc:
                logger.error("Groq model %s exception: %s", model, exc)

    # ── 2. GEMINI (fallback) ─────────────────────────────────────────
    gemini_keys = [k for k in [
        getattr(settings, 'GEMINI_API_KEY_2', ''),
        getattr(settings, 'GEMINI_API_KEY', ''),
    ] if k]

    gemini_models = [
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
    ]

    contents = []
    for h in history[-10:]:
        role = 'user' if h['role'] == 'user' else 'model'
        contents.append({'role': role, 'parts': [{'text': h['content']}]})
    contents.append({'role': 'user', 'parts': [{'text': user_message}]})

    gemini_payload = {
        'system_instruction': {'parts': [{'text': system_prompt}]},
        'contents': contents,
        'generationConfig': {'maxOutputTokens': 512, 'temperature': 0.7},
    }

    for gemini_key in gemini_keys:
        for model in gemini_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            try:
                response = requests.post(url, json=gemini_payload, timeout=30)
                result = response.json()
                if response.status_code == 200 and 'candidates' in result:
                    reply = result['candidates'][0]['content']['parts'][0]['text']
                    logger.info("Gemini success: %s", model)
                    return JsonResponse({'reply': reply})

                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.warning("Gemini model %s failed (%s): %s", model, response.status_code, error_msg)

            except Exception as exc:
                logger.error("Gemini model %s exception: %s", model, exc)

    # ── 3. সব fail ──────────────────────────────────────────────────
    logger.error("All Groq and Gemini keys/models failed.")
    return JsonResponse({'reply': 'দুঃখিত, AI সেবা সাময়িকভাবে বন্ধ আছে। Please try again later.'})
