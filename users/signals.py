from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save,sender=User)
def create_profile(sender,instance,created,**kwargs):
    user = instance
    if created:
        Profile.objects.create(
            user=user,
        )
    # else:
    #     profile = user.profile
    #     profile.email = user.email
    #     profile.save()


# @receiver(post_save,sender=Profile)
# def update_user(sender,instance,created,**kwargs):
#     profile = instance
#     user = profile.user
#     if not created and profile.email != user.email:
#         user.email = profile.email
#         user.save()