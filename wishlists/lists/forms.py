# Django
from django import forms

# Local
from .models import Item

EMPTY_ITEM_ERROR = "You can't have an empty wishlist item"


class ItemForm(forms.ModelForm):

    url = forms.URLField(required=False, widget=forms.URLInput(
        attrs={
            'placeholder': 'Enter a the website address to a wishlist item here',
            'class': 'form-control',
        }))
    price = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control'}))
    number = forms.DecimalField(initial=1, widget=forms.NumberInput(
        attrs={'class': 'form-control'}))

    class Meta:
        model = Item
        fields = ('text', 'url', 'price', 'number', 'priority')
        widgets = {
            'text': forms.TextInput(
                attrs={
                    'placeholder': 'Enter a wishlist item here',
                    'class': 'form-control',
                }
            ),
            'priority': forms.Select(
                attrs={
                    'class': 'form-check-input '
                }
            )
        }
        error_messages = {
            'text': {'required': EMPTY_ITEM_ERROR},
            'number': {'required': 'A desired number needs to be selected. Defaults to 1'},
            'priority': {'required': 'A priority must be submitted. Defaults to medium'},
        }

    def save(self, for_list):
        self.instance.wishlist = for_list
        return super().save()
