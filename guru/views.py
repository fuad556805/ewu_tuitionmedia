from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from accounts.models import User
from posts.models import Post
import requests
import json


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

    # Build context
    tutors = User.objects.filter(role='tutor', banned=False).values('first_name', 'last_name', 'subjects', 'location', 'education')
    tutor_list = [{'name': f"{t['first_name']} {t['last_name']}", 'subjects': t['subjects'],
                   'location': t['location'], 'education': t['education']} for t in tutors]

    active_posts = Post.objects.filter(status='active').values('subject', 'location', 'budget', 'schedule', 'student__first_name')
    post_list = [{'subject': p['subject'], 'location': p['location'],
                  'budget': p['budget'], 'schedule': p['schedule']} for p in active_posts]

    system_prompt = f"""You are Guru, a smart AI assistant for TuitionMedia — Bangladesh's tuition matching platform.
Available tutors: {json.dumps(tutor_list)}
Active posts: {json.dumps(post_list)}
Current user: {request.user.get_full_name()} ({request.user.role})
Respond in a warm mix of Bangla and English. Be helpful and concise (under 150 words).
For matching: suggest specific tutors or posts by name with reasons.
For general questions: give helpful advice about tuition, studying, platform usage."""

    messages_payload = []
    for h in history[-10:]:
        messages_payload.append({'role': h['role'], 'content': h['content']})
    messages_payload.append({'role': 'user', 'content': user_message})

    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': settings.ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 512,
                'system': system_prompt,
                'messages': messages_payload,
            },
            timeout=30
        )
        result = response.json()
        reply = result['content'][0]['text']
        return JsonResponse({'reply': reply})
    except Exception as e:
        return JsonResponse({'reply': 'দুঃখিত, এই মুহূর্তে সংযোগ সমস্যা হচ্ছে। Please try again.'})
