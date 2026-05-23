from django.shortcuts import render,redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .forms import ProfileEditForm
from django.db.models import Q
# Create your views here.
User = get_user_model()

def profile(request,username=None):
    if username and request.user.username != username:
        user_profile = User.objects.get(username=username).profile
    else:
        user_profile = request.user.profile

    context = {
        'profile':user_profile
    }
    return render(request,'users/profile.html',context)


@login_required
def profile_edit(request):
    user_profile = request.user.profile
    form = ProfileEditForm(instance=user_profile)
    if request.method == 'POST':
        form = ProfileEditForm(data=request.POST,instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    context = {
        'profile':user_profile,
        'form':form
    }

    return render(request,'users/profile-edit.html',context)


def search_users(request):
    if request.htmx:
        query = request.POST.get('search', '').strip()

        results = User.objects.filter(
            Q(username__icontains=query) | Q(profile__name__icontains=query)
        ).exclude(id=request.user.id).select_related('profile')

        context = {
            'results':results
        }
        return render(request,'snippet/search-item.html',context)

    return render(request, 'users/search.html')