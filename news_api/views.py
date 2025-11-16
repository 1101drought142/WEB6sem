import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from main.models import News


@method_decorator(csrf_exempt, name='dispatch')
class NewsListCreateView(View):
    """API endpoint для получения списка новостей и создания новой новости"""
    
    def get(self, request):
        """Обработка GET запроса - получение списка новостей"""
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

    def post(self, request):
        """Обработка POST запроса - создание новой новости"""
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


@method_decorator(csrf_exempt, name='dispatch')
class NewsDetailUpdateDeleteView(View):
    """API endpoint для получения, обновления и удаления конкретной новости"""
    
    def get(self, request, pk):
        """Обработка GET запроса - получение детальной информации о новости"""
        news = get_object_or_404(News, pk=pk)
        return JsonResponse({
            'id': news.id,
            'name': news.name,
            'slug': news.slug,
            'description': news.description
        })

    def put(self, request, pk):
        """Обработка PUT запроса - обновление новости"""
        news = get_object_or_404(News, pk=pk)
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

    def delete(self, request, pk):
        """Обработка DELETE запроса - удаление новости"""
        news = get_object_or_404(News, pk=pk)
        news.delete()
        return JsonResponse({'status': 'deleted'}, status=204)
