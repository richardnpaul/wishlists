# Django Imports
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.forms.models import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_safe

# Third-party Imports
from accounts.forms import LoginForm

# Local
from .forms import ArchiveItemForm, BoughtItemForm, ItemForm, WishListForm
from .models import Item, Wishlist


@require_safe
def home_page(request):
    return render(request, "home.html", {"wishlist_form": WishListForm(), "login_form": LoginForm()})


@require_safe
def view_list(request, wishlist_uuid):
    wishlist = Wishlist.objects.get(uuid=wishlist_uuid)
    return render(request, "wishlist.html", {"wishlist": wishlist, "login_form": LoginForm()})


@login_required
@require_POST
def archive_list(request, wishlist_uuid):
    wishlist = Wishlist.objects.get(uuid=wishlist_uuid)
    if not request.user.is_authenticated:
        return redirect("/accounts/login/")
    if request.user == wishlist.owner:
        if not wishlist.archived:
            wishlist.archived = True
            wishlist.save()
        return redirect("view_my_lists")
    return redirect("view_my_lists")


@login_required
@require_safe
def view_my_lists(request):
    lists = Wishlist.objects.filter(owner=request.user).all()
    return render(request, "lists.html", {"lists": lists, "wishlist_form": WishListForm(), "login_form": LoginForm()})


@login_required
@require_safe
def view_users_lists(request, user_id):
    lists = Wishlist.objects.filter(owner=user_id, archived=False).all()
    return render(request, "lists.html", {"lists": lists, "login_form": LoginForm()})


@login_required
@require_safe
def view_users(request):
    users = User.objects.filter(is_active=True, is_superuser=False, is_staff=False).all()
    wishlists = Wishlist.objects.all()
    return render(request, "view_users.html", {"users": users, "wishlists": wishlists, "login_form": LoginForm()})


@require_safe
def view_list_item(request, item_uuid):
    item = Item.objects.get(uuid=item_uuid)
    wishlist = Wishlist.objects.filter(item__uuid=item_uuid).first()
    return render(request, "item_view.html", {"item": item, "wishlist": wishlist, "login_form": LoginForm()})


@login_required
def edit_list_item(request, item_uuid):
    item = get_object_or_404(Item, uuid=item_uuid)
    wishlist = Wishlist.objects.filter(item__uuid=item_uuid).first()
    item_form = ItemForm(instance=item)
    if request.POST:
        if item_form.is_valid():
            item_form.save(request.POST)
            return redirect(item)
    return render(
        request,
        "edit_item_view.html",
        {"item": item, "form": item_form, "wishlist": wishlist, "login_form": LoginForm()},
    )


@login_required
@require_POST
def save_list_item(request, item_uuid):
    item = Item.objects.get(uuid=item_uuid)
    wishlist = Wishlist.objects.filter(item__uuid=item_uuid).first()
    if request.user == wishlist.owner:
        form = ItemForm(data=request.POST, instance=item)
        if form.is_valid():
            form.save(for_list=wishlist, as_user=request.user)
        else:
            return redirect(item)
    return redirect(item)


@login_required
@require_POST
def buy_list_item(request, item_uuid):
    item = Item.objects.get(uuid=item_uuid)
    wishlist = Wishlist.objects.filter(item__uuid=item_uuid).first()
    if not item.gifter and not request.user == wishlist.owner:
        item.gifter = request.user
        item.save()
        return redirect(item)
    else:
        return redirect(wishlist)


@login_required
@require_POST
def return_list_item(request, item_uuid):
    item = Item.objects.get(uuid=item_uuid)
    if item.gifter == request.user:
        item.gifter = None
        item.archived = False
        item.ordered = False
        item.delivered = False
        item.wrapped = False
        item.save()
    return redirect(item)


@login_required
def archive_bought_items(request):
    item_qs = Item.objects.filter(gifter=request.user).all()

    ArchiveItemFormSet = modelformset_factory(
        Item, fields=("text", "url", "price", "priority", "notes", "archived"), form=ArchiveItemForm, extra=0
    )

    formset = ArchiveItemFormSet(queryset=item_qs)

    if request.method == "POST":
        formset = ArchiveItemFormSet(request.POST, queryset=item_qs)
        if formset.is_valid():
            for form in formset:
                form.save(as_user=request.user)
            return redirect("archive_bought_items")
        else:
            return render(request, "archive_bought_items.html", {"formset": formset, "login_form": LoginForm()})

    return render(request, "archive_bought_items.html", {"formset": formset, "login_form": LoginForm()})


@login_required
def view_all_bought_items(request):
    item_qs = Item.objects.filter(gifter=request.user, archived=False).order_by("wishlist").all()

    BoughtItemFormSet = modelformset_factory(
        Item, fields=("text", "url", "notes", "ordered", "delivered", "wrapped"), form=BoughtItemForm, extra=0
    )

    formset = BoughtItemFormSet(queryset=item_qs)

    if request.method == "POST":
        formset = BoughtItemFormSet(request.POST, queryset=item_qs)
        if formset.is_valid():
            for form in formset:
                form.save(as_user=request.user)
            return redirect("bought_items")
        else:
            return render(request, "bought_items.html", {"formset": formset, "login_form": LoginForm()})

    return render(request, "bought_items.html", {"formset": formset, "login_form": LoginForm()})


@login_required
@require_safe
def return_bought_items(request):
    items = Item.objects.filter(gifter=request.user, archived=False).order_by("wishlist").all()
    return render(request, "return_bought_items.html", {"items": items, "login_form": LoginForm()})


@login_required
def new_list(request):
    if request.POST:
        form = WishListForm(data=request.POST)
        if form.is_valid():
            form.save(as_user=request.user)
        else:
            return render(request, "new_list.html", {"wishlist_form": form, "login_form": LoginForm()})
        wishlist = Wishlist.objects.get(title=request.POST["title"], owner=request.user)
        return redirect(f"/wishlists/{wishlist.uuid}/edit/")
    return render(request, "new_list.html", {"wishlist_form": WishListForm(), "login_form": LoginForm()})


@login_required
def edit_list(request, wishlist_uuid):
    wishlist = Wishlist.objects.get(uuid=wishlist_uuid)
    form = ItemForm()

    if not request.user.is_authenticated:
        return redirect("/accounts/login/")
    if not wishlist.owner == request.user:
        return redirect("/accounts/login/")
    if request.POST:
        form = ItemForm(data=request.POST)
        if form.is_valid():
            form.save(for_list=wishlist, as_user=request.user)
            return redirect(f"/wishlists/{wishlist.uuid}/edit/")
    return render(request, "edit_wishlist.html", {"wishlist": wishlist, "form": form, "login_form": LoginForm()})


@login_required
@require_POST
def create_list_item(request, wishlist_uuid):
    wishlist = Wishlist.objects.get(uuid=wishlist_uuid)
    form = ItemForm(data=request.POST)

    if form.is_valid():
        form.save(for_list=wishlist, as_user=request.user)
        return redirect(f"/wishlists/{wishlist.uuid}/edit/")

    return render(request, "edit_wishlist.html", {"wishlist": wishlist, "form": form, "login_form": LoginForm()})