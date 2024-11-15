from django import forms
from .models import GroupMessage


class GroupChatInputForm(forms.ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['message']

        widgets = {
            'message': forms.TextInput(attrs={'class': 'form-control'}),
        }