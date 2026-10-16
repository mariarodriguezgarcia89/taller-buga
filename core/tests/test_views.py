from django.urls import reverse


def test_dashboard_requires_login(client, db):
    response = client.get(reverse("core:dashboard"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


def test_dashboard_loads_for_logged_in_user(client, django_user_model):
    user = django_user_model.objects.create_user(username="maria", password="test-pass-123")
    client.force_login(user)
    response = client.get(reverse("core:dashboard"))
    assert response.status_code == 200