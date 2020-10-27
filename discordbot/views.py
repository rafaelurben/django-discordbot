from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from discordbot.models import AmongUsGame

import json

# Create your views here.

@require_POST
@csrf_exempt
def amongus_tracker_post(request):
    try:
        data = dict(json.loads(json.loads(request.body)))
        id = int(data["id"])

        if AmongUsGame.objects.filter(id=id).exists():
            game = AmongUsGame.objects.get(id=id)
            return JsonResponse(game.post_data(data))
        else:
            return JsonResponse({"error": "id-not-found", "error_message": "Game with this ID not found!"})
    except Exception as e:
        return JsonResponse({"error": "invalid-data", "error_message": str(e)})
