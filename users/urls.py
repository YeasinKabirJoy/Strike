from django.urls import path,include
from .views import profile
urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('profile/', profile,name='profile'),
    path('profile/<str:username>/', profile,name='user-profile'),

]
