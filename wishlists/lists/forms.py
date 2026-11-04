# Django Imports
from django import forms

# Local
from .models import Group, Item, Wishlist


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
        if "is_private" in self.data:
            val = self.data.get("is_private")
            self.instance.is_private = val in (True, "true", "True", "on", "1", 1)
        else:
            self.instance.is_private = True
        return super().save()


class GroupForm(forms.ModelForm):
    name = forms.CharField(
        max_length=128,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter a group name here",
                "class": "form-control input-lg",
            }
        ),
        error_messages={"required": "Group name is required"},
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Enter group description (optional)",
                "class": "form-control",
                "rows": 3,
            }
        ),
    )

    class Meta:
        model = Group
        fields = ("name", "description")


class WishlistPrivacyForm(forms.ModelForm):
    is_private = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_is_private"}),
        label="Private Wishlist",
        help_text="Private wishlists are visible only to you and members of groups you share with.",
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="Expose to Groups",
        help_text="Select which groups can view this wishlist.",
    )

    class Meta:
        model = Wishlist
        fields = ("is_private", "groups")

    def __init__(self, *args, **kwargs):
        kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = Group.objects.all().order_by("name")


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
