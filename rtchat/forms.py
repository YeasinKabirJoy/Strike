from django import forms
from .models import GroupMessage,ChatGroup


class GroupChatInputForm(forms.ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['message']

        widgets = {
            'message': forms.TextInput(attrs={'class': 'form-control'}),
        }


class GroupCreationForm(forms.ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['groupchat_name']
        widgets = {
            'groupchat_name': forms.TextInput(attrs={'class': 'form-control','placeholder':'Group Name'}),
        }