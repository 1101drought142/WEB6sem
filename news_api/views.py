import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from main.models import News

@csrf_exempt
def api_news_list_create(request):
    if request.method == 'GET':
        name_filter = request.GET.get('name')
        ordering = request.GET.get('ordering')

        news = News.objects.all()

        if name_filter:
            news = news.filter(name__icontains=name_filter)

        if ordering:
            news = news.order_by(ordering)

        data = [
            {
                'id': n.id,
                'name': n.name,
                'slug': n.slug,
                'description': n.description
            } for n in news
        ]
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            body = json.loads(request.body)
            name = body.get('name')
            slug = body.get('slug')
            description = body.get('description')

            if not all([name, slug, description]):
                return HttpResponseBadRequest('Нет всех полей')

            news = News.objects.create(name=name, slug=slug, description=description)
            return JsonResponse({
                'id': news.id,
                'name': news.name,
                'slug': news.slug,
                'description': news.description
            }, status=201)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

@csrf_exempt
def api_news_detail_update_delete(request, pk):
    try:
        news = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return HttpResponseNotFound('News not found')

    if request.method == 'GET':
        return JsonResponse({
            'id': news.id,
            'name': news.name,
            'slug': news.slug,
            'description': news.description
        })

    elif request.method == 'PUT':
        try:
            body = json.loads(request.body)
            news.name = body.get('name', news.name)
            news.slug = body.get('slug', news.slug)
            news.description = body.get('description', news.description)
            news.save()
            return JsonResponse({
                'id': news.id,
                'name': news.name,
                'slug': news.slug,
                'description': news.description
            })
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

    elif request.method == 'DELETE':
        news.delete()
        return JsonResponse({'status': 'deleted'}, status=204)

    else:
        return HttpResponseNotAllowed(['GET', 'PUT', 'DELETE'])
