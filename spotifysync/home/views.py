from django.shortcuts import render, redirect

# Create your views here.


def front(request):
    return render(request, 'home/front.html')


def home(request):
    return redirect('/room/')
