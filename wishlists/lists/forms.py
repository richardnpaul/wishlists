# Django Imports
from django import forms

# Local
from .models import Item, Wishlist


EMPTY_ITEM_ERROR = "You can't have an empty wishlist item"


class WishListForm(forms.ModelForm):
    class Meta:
        model = Wishlist
        fields = ("title",)
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Enter a title for your wishlist here",
                    "class": "form-control input-lg",
                }
            )
        }
        error_messages = {"title": {"required": "You can't have an empty wishlist title"}}

    def save(self, as_user):
        self.instance.owner = as_user
        return super().save()


class ItemForm(forms.ModelForm):
    url = forms.URLField(
        max_length=500,
        required=False,
        widget=forms.URLInput(
            attrs={
                "placeholder": "Enter a the website address to a wishlist item here",
                "class": "form-control",
            }
        ),
    )
    price = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    priority = forms.ChoiceField(
        choices=Item.PRIORITY_CHOICES,
        initial="3",
        required=False,
        widget=forms.Select(attrs={"class": "form-check-input"}),
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control"}))

    class Meta:
        model = Item
        fields = ("text", "url", "price", "priority", "notes")
        widgets = {
            "text": forms.TextInput(
                attrs={
                    "placeholder": "Enter a wishlist item here",
                    "class": "form-control",
                }
            ),
        }
        error_messages = {
            "text": {"required": EMPTY_ITEM_ERROR},
        }

    def clean_priority(self):
        return self.cleaned_data.get("priority") or "3"

    def save(self, for_list, as_user):
        self.instance.wishlist = for_list
        if not self.instance.wishlist.owner == as_user:
            raise forms.ValidationError
        return super(ItemForm, self).save()


class ArchiveItemForm(forms.ModelForm):
    archived = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-control-sm form-check-input m-0"}),
    )

    class Meta:
        model = Item
        fields = ("text", "archived")
        exclude = [
            "url",
            "price",
            "priority",
            "notes",
            "created",
            "modified",
            "uuid",
            "wishlist",
            "ordered",
            "delivered",
            "wrapped",
        ]
        widgets = {
            "text": forms.TextInput(attrs={"readonly": "readonly"}),
            "archived": forms.CheckboxInput(),
        }

    def save(self, as_user):
        self.instance.item = self.cleaned_data["id"]
        if not self.instance.item.gifter == as_user:
            raise forms.ValidationError
        return super(ArchiveItemForm, self).save()


class BoughtItemForm(forms.ModelForm):
    text = forms.CharField(required=False)
    url = forms.URLField(required=False)
    notes = forms.CharField(required=False)

    ordered = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-control-sm form-check-input m-0"}),
    )
    delivered = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-control-sm form-check-input m-0"}),
    )
    wrapped = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-control-sm form-check-input m-0"}),
    )

    class Meta:
        model = Item
        fields = ["text", "url", "notes", "ordered", "delivered", "wrapped"]
        exclude = [
            "price",
            "priority",
            "created",
            "modified",
            "uuid",
            "wishlist",
            "archived",
        ]
        widgets = {
            "text": forms.TextInput(attrs={"readonly": "readonly"}),
            "url": forms.Textarea(attrs={"readonly": "readonly"}),
            "notes": forms.Textarea(attrs={"readonly": "readonly"}),
            "ordered": forms.CheckboxInput(),
            "delivered": forms.CheckboxInput(),
            "wrapped": forms.CheckboxInput(),
        }

    def save(self, as_user):
        self.instance.item = self.cleaned_data["id"]
        if not self.instance.item.gifter == as_user:
            raise forms.ValidationError
        return super(BoughtItemForm, self).save()
