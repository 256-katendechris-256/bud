from django.http import Http404
from django.shortcuts import render, get_object_or_404

from apps.books.models import Book
from apps.reading.models import UserBook


def app_shell(request):
    return render(request, 'index.html')


def login_page(request):
    return render(request, 'login.html')


def signup_page(request):
    return render(request, 'signup.html')


def dashboard(request):
    return render(request, 'dashboard.html')


def books_page(request):
    return render(request, 'books.html')


def books_reader_page(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if not book.file:
        raise Http404("No PDF file uploaded for this book.")
    start_page = 0
    if request.user.is_authenticated:
        ub = UserBook.objects.filter(user=request.user, book=book).first()
        if ub:
            start_page = ub.current_page
    return render(request, 'reader.html', {'book': book, 'start_page': start_page})
