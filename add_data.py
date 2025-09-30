import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare.settings')

django.setup()

from main.models import News

news_mock = {
    1: {
        "name": "Тестовая новость 1",
        "slug": "test_news_1",
        "desc": "<p style='color:red'>Описание тестовой новости 1</p>"
    },
    2: {
        "name": "Тестовая новость 2",
        "slug": "test_news_2",
        "desc": "Описание тестовой новости 2"
    },
    3: {
        "name": "Тестовая новость 3",
        "slug": "test_news_3",
        "desc": "Описание тестовой новости 3"
    }
}

for item in news_mock.values():
    name = item["name"]
    desc = item["desc"]
    slug = item["slug"]

    news = News.objects.create(
        name=name,
        slug=slug,
        description=desc
    )