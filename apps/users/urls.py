from django.urls import path,include
from .views import profile,profile_edit,search_users
urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('profile/', profile,name='profile'),
    path('profile/edit/', profile_edit,name='profile-edit'),
    path('profile/<str:username>/', profile,name='user-profile'),
    path('serach/user', search_users,name='user-search'),

]
