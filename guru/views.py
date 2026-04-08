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

    contents = []
    for h in history[-10:]:
        role = 'user' if h['role'] == 'user' else 'model'
        contents.append({'role': role, 'parts': [{'text': h['content']}]})
    contents.append({'role': 'user', 'parts': [{'text': user_message}]})

    # Collect all configured API keys (primary + secondary)
    api_keys = [k for k in [
        settings.GEMINI_API_KEY,
        getattr(settings, 'GEMINI_API_KEY_2', ''),
    ] if k]

    if not api_keys:
        logger.error("No Gemini API keys configured.")
        return JsonResponse({'reply': 'দুঃখিত, AI সেবা সাময়িকভাবে বন্ধ আছে। Please try again later.'})

    models = [
        'gemini-2.5-flash-lite',
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
    ]

    payload = {
        'system_instruction': {'parts': [{'text': system_prompt}]},
        'contents': contents,
        'generationConfig': {
            'maxOutputTokens': 512,
            'temperature': 0.7,
        },
    }

    last_error = None
    for api_key in api_keys:
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = requests.post(url, json=payload, timeout=30)
                result = response.json()

                if response.status_code == 200 and 'candidates' in result:
                    reply = result['candidates'][0]['content']['parts'][0]['text']
                    return JsonResponse({'reply': reply})

                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.warning("Gemini key#%d model %s failed (%s): %s", api_keys.index(api_key) + 1, model, response.status_code, error_msg)
                last_error = error_msg

            except Exception as exc:
                logger.error("Gemini key#%d model %s exception: %s", api_keys.index(api_key) + 1, model, exc)
                last_error = str(exc)

    logger.error("All Gemini keys and models failed. Last error: %s", last_error)
    return JsonResponse({'reply': 'দুঃখিত, AI সেবা সাময়িকভাবে বন্ধ আছে। Please try again later.'})
