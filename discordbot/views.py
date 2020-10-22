from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from discordbot.models import AmongUsGame

import json

# Create your views here.

@require_POST
@csrf_exempt
def amongus_tracker_post(request, id):
    data = json.loads(json.loads(request.body))
    print(data, type(data))
    if AmongUsGame.objects.filter(id=id).exists():
        game = AmongUsGame.objects.get(id=id)
        return JsonResponse(game.post_data(data))
    else:
        return JsonResponse({"error": "Game with this ID not found!"})
