# Django Imports
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.forms.models import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_safe

# Third-party Imports
from accounts.forms import LoginForm

# Local
from .forms import ArchiveItemForm, BoughtItemForm, GroupForm, ItemForm, WishListForm, WishlistPrivacyForm
from .models import Group, Item, Wishlist, can_view_wishlist


@require_safe
def home_page(request):
    return render(
        request,
        "home.html",
        {"wishlist_form": WishListForm(), "login_form": LoginForm()},
    )


@require_safe
def view_list(request, wishlist_uuid):
    wishlist = get_object_or_404(Wishlist, uuid=wishlist_uuid)
    if not can_view_wishlist(request.user, wishlist):
        raise PermissionDenied
    return render(request, "wishlist.html", {"wishlist": wishlist, "login_form": LoginForm()})


@login_required
@require_POST
def archive_list(request, wishlist_uuid):
    wishlist = get_object_or_404(Wishlist, uuid=wishlist_uuid)
    if wishlist.owner != request.user:
        raise PermissionDenied
    if not wishlist.archived:
        wishlist.archived = True
        wishlist.save()
    return redirect("view_my_lists")


@login_required
@require_safe
def view_my_lists(request):
    lists = Wishlist.objects.filter(owner=request.user).all()
    return render(
        request,
        "lists.html",
        {"lists": lists, "wishlist_form": WishListForm(), "login_form": LoginForm()},
    )


@login_required
@require_safe
def view_users_lists(request, user_id):
    all_lists = Wishlist.objects.filter(owner=user_id, archived=False).all()
    lists = [w for w in all_lists if can_view_wishlist(request.user, w)]
    return render(
        request,
        "lists.html",
        {"lists": lists, "wishlist_form": WishListForm(), "login_form": LoginForm()},
    )


@login_required
@require_safe
def view_users(request):
    users = User.objects.filter(is_active=True, is_superuser=False, is_staff=False).all()
    wishlists = Wishlist.objects.all()
    return render(
        request,
        "view_users.html",
        {"users": users, "wishlists": wishlists, "login_form": LoginForm()},
    )


@require_safe
def view_list_item(request, item_uuid):
    item = get_object_or_404(Item, uuid=item_uuid)
    wishlist = item.wishlist
    if not can_view_wishlist(request.user, wishlist):
        raise PermissionDenied
    return render(
        request,
        "item_view.html",
        {"item": item, "wishlist": wishlist, "login_form": LoginForm()},
    )


@login_required
def edit_list_item(request, item_uuid):
    item = get_object_or_404(Item, uuid=item_uuid)
    wishlist = item.wishlist
    if wishlist.owner != request.user:
        raise PermissionDenied
    if request.method == "POST":
        item_form = ItemForm(data=request.POST, instance=item)
        if item_form.is_valid():
            item_form.save(for_list=wishlist, as_user=request.user)
            return redirect(item)
    else:
        item_form = ItemForm(instance=item)
    return render(
        request,
        "edit_item_view.html",
        {
            "item": item,
            "form": item_form,
            "wishlist": wishlist,
            "login_form": LoginForm(),
        },
    )


@login_required
@require_POST
def save_list_item(request, item_uuid):
    item = get_object_or_404(Item, uuid=item_uuid)
    wishlist = item.wishlist
    if wishlist.owner != request.user:
        raise PermissionDenied
    form = ItemForm(data=request.POST, instance=item)
    if form.is_valid():
        form.save(for_list=wishlist, as_user=request.user)
    return redirect(item)


@login_required
@require_POST
def buy_list_item(request, item_uuid):
    item = get_object_or_404(Item, uuid=item_uuid)
    wishlist = item.wishlist
    if not can_view_wishlist(request.user, wishlist):
        raise PermissionDenied
    if not item.gifter and request.user != wishlist.owner:
        item.gifter = request.user
        item.save()
        return redirect(item)
    else:
        return redirect(wishlist)


@login_required
@require_POST
def return_list_item(request, item_uuid):
    item = get_object_or_404(Item, uuid=item_uuid)
    if item.gifter != request.user:
        raise PermissionDenied
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
        Item,
        fields=("text", "url", "price", "priority", "notes", "archived"),
        form=ArchiveItemForm,
        extra=0,
    )

    formset = ArchiveItemFormSet(queryset=item_qs)

    if request.method == "POST":
        formset = ArchiveItemFormSet(request.POST, queryset=item_qs)
        if formset.is_valid():
            for form in formset:
                form.save(as_user=request.user)
            return redirect("archive_bought_items")
        else:
            return render(
                request,
                "archive_bought_items.html",
                {"formset": formset, "login_form": LoginForm()},
            )

    return render(
        request,
        "archive_bought_items.html",
        {"formset": formset, "login_form": LoginForm()},
    )


@login_required
def view_all_bought_items(request):
    item_qs = Item.objects.filter(gifter=request.user, archived=False).order_by("wishlist").all()

    BoughtItemFormSet = modelformset_factory(
        Item,
        fields=("text", "url", "notes", "ordered", "delivered", "wrapped"),
        form=BoughtItemForm,
        extra=0,
    )

    formset = BoughtItemFormSet(queryset=item_qs)

    if request.method == "POST":
        formset = BoughtItemFormSet(request.POST, queryset=item_qs)
        if formset.is_valid():
            for form in formset:
                form.save(as_user=request.user)
            return redirect("bought_items")
        else:
            return render(
                request,
                "bought_items.html",
                {"formset": formset, "login_form": LoginForm()},
            )

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
            return render(
                request,
                "new_list.html",
                {"wishlist_form": form, "login_form": LoginForm()},
            )
        wishlist = Wishlist.objects.get(title=request.POST["title"], owner=request.user)
        return redirect(f"/wishlists/{wishlist.uuid}/edit/")
    return render(
        request,
        "new_list.html",
        {"wishlist_form": WishListForm(), "login_form": LoginForm()},
    )


@login_required
def edit_list(request, wishlist_uuid):
    wishlist = get_object_or_404(Wishlist, uuid=wishlist_uuid)
    if wishlist.owner != request.user:
        raise PermissionDenied
    form = ItemForm()
    if request.method == "POST":
        form = ItemForm(data=request.POST)
        if form.is_valid():
            form.save(for_list=wishlist, as_user=request.user)
            return redirect(f"/wishlists/{wishlist.uuid}/edit/")
    return render(
        request,
        "edit_wishlist.html",
        {"wishlist": wishlist, "form": form, "login_form": LoginForm()},
    )


@login_required
@require_POST
def create_list_item(request, wishlist_uuid):
    wishlist = get_object_or_404(Wishlist, uuid=wishlist_uuid)
    if wishlist.owner != request.user:
        raise PermissionDenied
    form = ItemForm(data=request.POST)

    if form.is_valid():
        form.save(for_list=wishlist, as_user=request.user)
        return redirect(f"/wishlists/{wishlist.uuid}/edit/")

    return render(
        request,
        "edit_wishlist.html",
        {"wishlist": wishlist, "form": form, "login_form": LoginForm()},
        status=400,
    )


@login_required
@require_safe
def group_list(request):
    query = request.GET.get("q", "").strip()
    groups_qs = Group.objects.annotate(member_count=Count("members")).order_by("name")
    if query:
        groups_qs = groups_qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
    user_group_ids = set(request.user.subscribed_groups.values_list("id", flat=True))
    return render(
        request,
        "group_list.html",
        {
            "groups": groups_qs,
            "query": query,
            "user_group_ids": user_group_ids,
            "login_form": LoginForm(),
        },
    )


@login_required
def group_create(request):
    if request.method == "POST":
        form = GroupForm(data=request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            group.members.add(request.user)
            return redirect("group_detail", group_uuid=group.uuid)
        return render(
            request,
            "group_create.html",
            {"form": form, "login_form": LoginForm()},
            status=400,
        )
    return render(
        request,
        "group_create.html",
        {"form": GroupForm(), "login_form": LoginForm()},
    )


@login_required
@require_safe
def group_detail(request, group_uuid):
    group = get_object_or_404(Group, uuid=group_uuid)
    is_member = group.members.filter(id=request.user.id).exists()
    all_shared = group.wishlists.filter(archived=False).all()
    shared_wishlists = [w for w in all_shared if can_view_wishlist(request.user, w)]
    user_wishlists = Wishlist.objects.filter(owner=request.user, archived=False).all()
    return render(
        request,
        "group_detail.html",
        {
            "group": group,
            "is_member": is_member,
            "shared_wishlists": shared_wishlists,
            "user_wishlists": user_wishlists,
            "login_form": LoginForm(),
        },
    )


@login_required
@require_POST
def group_subscribe(request, group_uuid):
    group = get_object_or_404(Group, uuid=group_uuid)
    group.members.add(request.user)
    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect("group_detail", group_uuid=group.uuid)


@login_required
@require_POST
def group_unsubscribe(request, group_uuid):
    group = get_object_or_404(Group, uuid=group_uuid)
    group.members.remove(request.user)
    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect("group_detail", group_uuid=group.uuid)


@login_required
def edit_wishlist_privacy(request, wishlist_uuid):
    wishlist = get_object_or_404(Wishlist, uuid=wishlist_uuid)
    if wishlist.owner != request.user:
        raise PermissionDenied
    if request.method == "POST":
        form = WishlistPrivacyForm(data=request.POST, instance=wishlist, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("view_list", wishlist_uuid=wishlist.uuid)
    else:
        form = WishlistPrivacyForm(instance=wishlist, user=request.user)
    return render(
        request,
        "edit_wishlist_privacy.html",
        {
            "wishlist": wishlist,
            "privacy_form": form,
            "login_form": LoginForm(),
        },
    )
