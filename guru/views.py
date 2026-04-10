from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from accounts.models import User
from posts.models import Post
from tuitions.models import Tuition, TuitionRequest
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
    f"You are Guru — the smart AI companion of TuitionMedia, Bangladesh's premier tuition matching platform.\n"
    f"You are like a knowledgeable elder brother/sister (বড় ভাই/আপু) to the user — helpful, warm, and intelligent.\n\n"

    f"## WHO YOU ARE\n"
    f"- You are NOT just a matching bot. You are a full AI assistant who happens to specialize in TuitionMedia.\n"
    f"- You can talk about anything: studies, life, career, general knowledge, fun topics — anything.\n"
    f"- You always try your best to give a correct, thoughtful answer.\n"
    f"- If you are unsure, you say so honestly but still try to help.\n\n"

    f"## TUITIONMEDIA PLATFORM (Know this well)\n"
    f"- Flow: Students create tuition posts → Tutors browse and apply → Student selects a tutor.\n"
    f"- Commission: TuitionMedia takes 30% from tutors ONLY, from the FIRST month's payment only. No recurring charge.\n"
    f"- Students pay ZERO commission, ever.\n\n"

    f"## CURRENT PLATFORM DATA\n"
    f"Registered Tutors: {json.dumps(tutor_list, ensure_ascii=False)}\n"
    f"Active Tuition Posts: {json.dumps(post_list, ensure_ascii=False)}\n"
    f"Current User: {request.user.get_full_name()} | Role: {request.user.role}\n\n"

    f"## HOW TO RESPOND\n"
    f"Step 1 — Understand what the user wants:\n"
    f"  - Tutor/post matching? → Use the platform data above to suggest 1–3 specific matches with reasons.\n"
    f"  - Platform question? → Explain clearly using platform rules above.\n"
    f"  - Anything else (study tips, career, general talk, fun)? → Answer freely and naturally.\n"
    f"Step 2 — Always give a complete, helpful answer. Never refuse or redirect unnecessarily.\n"
    f"Step 3 — If matching: always mention name + reason. If general: be natural and conversational.\n\n"

    f"## LANGUAGE & TONE\n"
    f"- Warm Banglish (Bengali + English mix) — like talking to a smart friend.\n"
    f"- Use আপনি for formal context, তুমি only if the user is clearly casual/young.\n"
    f"- Keep replies concise — under 180 words unless detail is truly needed.\n"
    f"- No robotic language. Be natural, warm, and human.\n"
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


# ═══════════════════════════════════════════════════════════
#  ADMIN GURU
# ═══════════════════════════════════════════════════════════

def _admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@_admin_required
def admin_guru_page(request):
    return render(request, 'guru/admin_guru.html')


@_admin_required
def admin_guru_ask(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data = json.loads(request.body)
    user_message = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    # ── Gather all site statistics ──────────────────────────
    total_students     = User.objects.filter(role='student').count()
    total_tutors       = User.objects.filter(role='tutor').count()
    banned_users       = User.objects.filter(banned=True).count()
    pending_profiles   = User.objects.filter(profile_approved=False).count()

    total_posts        = Post.objects.count()
    active_posts       = Post.objects.filter(status='active').count()
    pending_posts      = Post.objects.filter(status='pending_approval').count()
    rejected_posts     = Post.objects.filter(status='rejected').count()

    total_requests     = TuitionRequest.objects.count()
    pending_requests   = TuitionRequest.objects.filter(status='pending').count()
    accepted_requests  = TuitionRequest.objects.filter(status='accepted').count()

    active_tuitions    = Tuition.objects.filter(status='active').count()
    completed_tuitions = Tuition.objects.filter(status='completed').count()
    cancelled_tuitions = Tuition.objects.filter(status='cancelled').count()

    all_paid_tuitions  = list(Tuition.objects.filter(salary__gt=0))
    total_commission   = sum(t.commission for t in all_paid_tuitions)
    paid_commission    = sum(t.commission for t in all_paid_tuitions if t.commission_status == 'paid')
    pending_commission = sum(t.commission for t in all_paid_tuitions if t.commission_status in ('pending', 'proof_uploaded'))
    proof_uploaded     = Tuition.objects.filter(commission_status='proof_uploaded').count()

    recent_users = list(
        User.objects.exclude(role='admin').order_by('-date_joined').values(
            'first_name', 'last_name', 'role', 'phone', 'date_joined'
        )[:10]
    )
    recent_users_fmt = [
        f"{u['first_name']} {u['last_name']} ({u['role']}) — joined {u['date_joined'].strftime('%d %b %Y')}"
        for u in recent_users
    ]

    recent_tuitions = list(
        Tuition.objects.select_related('tutor', 'student').order_by('-created_at')[:8]
    )
    recent_tuitions_fmt = [
        f"{t.tutor.get_full_name()} teaches {t.student.get_full_name()} | {t.subject} | salary: {t.salary} BDT | commission: {t.commission} BDT ({t.commission_status})"
        for t in recent_tuitions
    ]

    system_prompt = (
        f"You are Admin Guru — the intelligent AI assistant exclusively for the TuitionMedia admin dashboard.\n"
        f"You have FULL access to all platform data and statistics. You are like a smart data analyst + ops assistant for the admin.\n\n"

        f"## PLATFORM OVERVIEW (Live Data)\n"
        f"### Users\n"
        f"- Total Students: {total_students}\n"
        f"- Total Tutors: {total_tutors}\n"
        f"- Banned Users: {banned_users}\n"
        f"- Pending Profile Approvals: {pending_profiles}\n\n"

        f"### Posts\n"
        f"- Total Posts: {total_posts}\n"
        f"- Active Posts: {active_posts}\n"
        f"- Pending Approval: {pending_posts}\n"
        f"- Rejected: {rejected_posts}\n\n"

        f"### Tuition Requests\n"
        f"- Total Requests: {total_requests}\n"
        f"- Pending: {pending_requests}\n"
        f"- Accepted: {accepted_requests}\n\n"

        f"### Tuitions\n"
        f"- Active Tuitions: {active_tuitions}\n"
        f"- Completed: {completed_tuitions}\n"
        f"- Cancelled: {cancelled_tuitions}\n\n"

        f"### Financials (Commission)\n"
        f"- Total Commission (all time): {total_commission} BDT\n"
        f"- Paid Commission: {paid_commission} BDT\n"
        f"- Pending Commission: {pending_commission} BDT\n"
        f"- Proof Uploaded (awaiting confirmation): {proof_uploaded}\n\n"

        f"### Recent Users (last 10 joined)\n"
        f"{chr(10).join(recent_users_fmt) or 'None'}\n\n"

        f"### Recent Tuitions\n"
        f"{chr(10).join(recent_tuitions_fmt) or 'None'}\n\n"

        f"## YOUR ROLE\n"
        f"- Answer any admin question about the platform: stats, trends, specific users/tuitions, pending actions.\n"
        f"- Give actionable insights: e.g. 'X profiles need approval', 'Y BDT commission pending'.\n"
        f"- If asked about something not in the data, say so honestly.\n"
        f"- You can also advise on platform management best practices.\n\n"

        f"## LANGUAGE\n"
        f"- Respond in Banglish (Bengali + English mix) by default.\n"
        f"- Be concise, professional, and data-driven.\n"
        f"- Use numbers and facts from the live data above.\n"
    )

    # ── Reuse same LLM fallback chain ───────────────────────
    groq_keys = [k for k in [
        getattr(settings, 'GROQ_API_KEY', ''),
        getattr(settings, 'GROQ_API_KEY_2', ''),
    ] if k]

    groq_models = ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768']

    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        messages.append({"role": h['role'], "content": h['content']})
    messages.append({"role": "user", "content": user_message})

    for groq_key in groq_keys:
        for model in groq_models:
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": messages, "max_tokens": 600, "temperature": 0.5},
                    timeout=30,
                )
                result = response.json()
                if response.status_code == 200 and 'choices' in result:
                    return JsonResponse({'reply': result['choices'][0]['message']['content']})
            except Exception as exc:
                logger.error("Admin Guru Groq %s error: %s", model, exc)

    gemini_keys = [k for k in [
        getattr(settings, 'GEMINI_API_KEY_2', ''),
        getattr(settings, 'GEMINI_API_KEY', ''),
    ] if k]

    gemini_models = ['gemini-2.0-flash', 'gemini-2.0-flash-lite']
    contents = []
    for h in history[-10:]:
        role = 'user' if h['role'] == 'user' else 'model'
        contents.append({'role': role, 'parts': [{'text': h['content']}]})
    contents.append({'role': 'user', 'parts': [{'text': user_message}]})

    for gemini_key in gemini_keys:
        for model in gemini_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            try:
                response = requests.post(
                    url,
                    json={
                        'system_instruction': {'parts': [{'text': system_prompt}]},
                        'contents': contents,
                        'generationConfig': {'maxOutputTokens': 600, 'temperature': 0.5},
                    },
                    timeout=30,
                )
                result = response.json()
                if response.status_code == 200 and 'candidates' in result:
                    return JsonResponse({'reply': result['candidates'][0]['content']['parts'][0]['text']})
            except Exception as exc:
                logger.error("Admin Guru Gemini %s error: %s", model, exc)

    return JsonResponse({'reply': 'দুঃখিত, AI সেবা সাময়িকভাবে বন্ধ আছে।'})
