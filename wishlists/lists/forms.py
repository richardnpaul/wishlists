# Django
from django import forms
from django.core.exceptions import ValidationError

# Local
from .models import Item, Wishlist

EMPTY_ITEM_ERROR = "You can't have an empty wishlist item"


class WishListForm(forms.ModelForm):

    class Meta:
        model = Wishlist
        fields = ('title',)
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'placeholder': 'Enter a title for your wishlist here',
                    'class': 'form-control imput-lg'
                }
            )
        }
        error_messages = {
            'title': {'required': "You can't have an empty wishlist title"}
        }

    def save(self, as_user):
        self.instance.owner = as_user
        return super().save()


class ItemForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = ('text',)
        widgets = {
            'text': forms.TextInput(
                attrs={
                    'placeholder': 'Enter a wishlist item here',
                    'class': 'form-control input-lg',
                }
            ),
        }
        error_messages = {
            'text': {'required': EMPTY_ITEM_ERROR}
        }

    def save(self, for_list, as_user):
        self.instance.wishlist = for_list
        if not self.instance.wishlist.owner == as_user:
            raise ValidationError
        return super().save()
