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

    url = forms.URLField(max_length=500, required=False, widget=forms.URLInput(
        attrs={
            'placeholder': 'Enter a the website address to a wishlist item here',
            'class': 'form-control',
        }))
    price = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control'}))
    notes = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'class': 'form-control'}))

    class Meta:
        model = Item
        fields = ('text', 'url', 'price', 'priority', 'notes')
        widgets = {
            'text': forms.TextInput(
                attrs={
                    'placeholder': 'Enter a wishlist item here',
                    'class': 'form-control',
                }
            ),
            'priority': forms.Select(
                attrs={
                    'class': 'form-check-input'
                }
            )
        }
        error_messages = {
            'text': {'required': EMPTY_ITEM_ERROR},
            'priority': {
                'required': 'A priority must be submitted. Defaults to medium'
            },
        }

    def save(self, for_list, as_user):
        self.instance.wishlist = for_list
        if not self.instance.wishlist.owner == as_user:
            raise ValidationError
        return super(ItemForm, self).save()


class BoughtItemForm(forms.ModelForm):

    archived = forms.BooleanField(required=False, widget=forms.CheckboxInput(
        attrs={'class': 'form-control-sm form-check-input m-0'}
    ))

    class Meta:
        model = Item
        fields = ('text', 'archived',)
        exclude = ['url', 'price', 'priority', 'notes', 'created',
                    'modified', 'uuid', 'wishlist']
        widgets = {
            'text': forms.TextInput(attrs={'readonly':'readonly'}),
            'archived': forms.CheckboxInput()
        }

    def save(self, as_user):
        self.instance.item = self.cleaned_data['id']
        if not self.instance.item.gifter == as_user:
            raise ValidationError
        return super(BoughtItemForm, self).save()

