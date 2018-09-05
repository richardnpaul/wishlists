# Django
from django import forms

from lists.models import Item, Wishlist

class NewItemForm(forms.models.ModelForm):

    class Meta:
        model = Item
        fields = ('text',)
        widgets = {
            'text': forms.fields.TextInput(
                attrs={
                    'placeholder': 'Enter a wishlist item here',
                }
            ),
        }