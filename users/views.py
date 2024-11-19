from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, UserPreferencesForm
from blog.models import UserPreference
from django.contrib.auth.views import LoginView

# Create your views here.
def register(request):
    if request.method=='POST':
        form=UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username=form.cleaned_data.get('username')
            messages.success(request, f'Your account has been created. You are now able to login!')
            return redirect('login')
    else:
        form=UserRegisterForm()
    return render(request, 'users/register.html', {'form':form})

class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user

        user_preferences, created = UserPreference.objects.get_or_create(user=user)
        if not created and user_preferences.preference.count() == 0:
            return redirect('set_preferences')
        return response

@login_required
def profile(request):
    if request.method == 'POST':
        u_form=UserUpdateForm(request.POST, instance = request.user)
        p_form=ProfileUpdateForm(request.POST, request.FILES, instance = request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account details have been updated!')
            return redirect('profile')
    else:
        u_form=UserUpdateForm(instance = request.user)
        p_form=ProfileUpdateForm(instance = request.user.profile)

    context={
        'u_form':u_form,
        'p_form':p_form
    }
    return render(request, 'users/profile.html', context)
    
@login_required
def set_preferences(request):
    user_preferences, created = UserPreference.objects.get_or_create(user=request.user)

    if not created and user_preferences.preference.exists():
        return redirect('/')

    if request.method == 'POST':
        form = UserPreferencesForm(request.POST)
        if form.is_valid():
            user_preferences.preference.set(form.cleaned_data['categories'])
            user_preferences.save()
            return redirect('/')
    else:
        form = UserPreferencesForm()

    return render(request, 'users/preferences.html', {'form': form})