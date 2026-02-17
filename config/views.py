from django.shortcuts import render


def app_shell(request):
    return render(request, 'index.html')


def login_page(request):
    return render(request, 'login.html')


def signup_page(request):
    return render(request, 'signup.html')


def dashboard(request):
    return render(request, 'dashboard.html')
