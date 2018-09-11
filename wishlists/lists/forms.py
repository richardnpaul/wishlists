# Django
from django import forms

# Local
from .models import Item

EMPTY_ITEM_ERROR = "You can't have an empty wishlist item"


class ItemForm(forms.models.ModelForm):

    class Meta:
        model = Item
        fields = ('text',)
        widgets = {
            'text': forms.fields.TextInput(
                attrs={
                    'placeholder': 'Enter a wishlist item here',
                    'class': 'form-control input-lg',
                }
            ),
        }
        error_messages = {
            'text': {'required': EMPTY_ITEM_ERROR}
        }

    def save(self, for_list):
        self.instance.wishlist = for_list
        return super().save()
