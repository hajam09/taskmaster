from django.contrib import auth
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect
from django.shortcuts import render

from accounts.forms import LoginForm
from accounts.forms import RegistrationForm
from taskmaster.operations import emailOperations


def login(request):
    if not request.session.session_key:
        request.session.save()

    if request.method == "POST":
        uniqueVisitorId = request.session.session_key

        if cache.get(uniqueVisitorId) is not None and cache.get(uniqueVisitorId) > 3:
            cache.set(uniqueVisitorId, cache.get(uniqueVisitorId), 600)

            messages.error(
                request, 'Your account has been temporarily locked out because of too many failed login attempts.'
            )
            return redirect('accounts:login')

        form = LoginForm(request, request.POST)

        if form.is_valid():
            cache.delete(uniqueVisitorId)
            return redirect('jira:dashboard')

        if cache.get(uniqueVisitorId) is None:
            cache.set(uniqueVisitorId, 1)
        else:
            cache.incr(uniqueVisitorId, 1)

    else:
        form = LoginForm(request)

    context = {
        "form": form
    }
    return render(request, 'accounts/login.html', context)


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            newUser = form.save()
            emailOperations.sendEmailToActivateAccount(request, newUser)

            messages.info(
                request, 'We\'ve sent you an activation link. Please check your email.'
            )
            return redirect('accounts:login')
    else:
        form = RegistrationForm()

    context = {
        "form": form
    }
    return render(request, 'accounts/registration.html', context)


def logout(request):
    auth.logout(request)

    previousUrl = request.META.get('HTTP_REFERER')
    if previousUrl:
        return redirect(previousUrl)

    return redirect('accounts:login')
