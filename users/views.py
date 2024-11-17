from django.shortcuts import render
from django.contrib.auth import get_user_model
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