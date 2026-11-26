# Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch
from django.forms.models import modelformset_factory
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe

# Third-party Imports
from accounts.forms import LoginForm

# Local
from .forms import ArchiveItemForm, BoughtItemForm, GroupForm, ItemForm, WishListForm, WishlistPrivacyForm
from .models import Group, InvalidInvite, Item, Wishlist, can_view_wishlist


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
    lists = Wishlist.objects.filter(owner=request.user)
    # Lists shared with me through my groups (public lists elsewhere aren't "shared with me").
    shared_lists = (
        Wishlist.objects.filter(archived=False, groups__members=request.user)
        .exclude(owner=request.user)
        .select_related("owner")
        .prefetch_related(Prefetch("groups", queryset=request.user.subscribed_groups.all(), to_attr="my_groups"))
        .order_by("owner__first_name", "title")
        .distinct()
    )
    return render(
        request,
        "lists.html",
        {
            "lists": lists,
            "shared_lists": shared_lists,
            "wishlist_form": WishListForm(),
            "login_form": LoginForm(),
        },
    )


@login_required
@require_safe
def view_users_lists(request, user_id):
    list_owner = get_object_or_404(User, pk=user_id)
    lists = Wishlist.objects.visible_to(request.user).filter(owner=list_owner, archived=False)
    return render(
        request,
        "lists.html",
        {"lists": lists, "list_owner": list_owner, "login_form": LoginForm()},
    )


@login_required
@require_safe
def view_users(request):
    # Only people with at least one list the viewer can see, so the page doesn't reveal who has an account.
    visible_lists = Wishlist.objects.visible_to(request.user).filter(archived=False)
    users = (
        User.objects.filter(is_active=True, is_superuser=False, is_staff=False, wishlist_owner__in=visible_lists)
        .exclude(pk=request.user.pk)
        .distinct()
        .order_by("first_name", "last_name")
    )
    return render(
        request,
        "view_users.html",
        {"users": users, "login_form": LoginForm()},
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
        form = WishListForm(data=request.POST, owner=request.user)
        if not form.is_valid():
            return render(
                request,
                "new_list.html",
                {"wishlist_form": form, "login_form": LoginForm()},
            )
        wishlist = form.save(as_user=request.user)
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


def _group_for_member(request, group_uuid):
    """Return the group, or 403 if the current user isn't a member. Groups are invite-only."""
    group = get_object_or_404(Group, uuid=group_uuid)
    if not group.is_member(request.user):
        raise PermissionDenied
    return group


def _group_for_creator(request, group_uuid):
    group = get_object_or_404(Group, uuid=group_uuid)
    if not group.is_creator(request.user):
        raise PermissionDenied
    return group


@login_required
@require_safe
def group_list(request):
    groups = request.user.subscribed_groups.annotate(member_count=Count("members")).order_by("name")
    return render(
        request,
        "group_list.html",
        {"groups": groups, "login_form": LoginForm()},
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
    group = _group_for_member(request, group_uuid)
    is_creator = group.is_creator(request.user)
    context = {
        "group": group,
        "is_creator": is_creator,
        "members": group.members.order_by("first_name", "last_name", "username"),
        "shared_wishlists": group.wishlists.filter(archived=False).select_related("owner").order_by("title"),
        "login_form": LoginForm(),
    }
    if is_creator:
        context["invite_url"] = request.build_absolute_uri(reverse("group_join", args=[group.make_invite_token()]))
        context["invite_max_age_days"] = settings.GROUP_INVITE_MAX_AGE // (60 * 60 * 24)
        context["edit_form"] = GroupForm(instance=group)
    return render(request, "group_detail.html", context)


@login_required
def group_join(request, token):
    try:
        group = Group.from_invite_token(token)
    except InvalidInvite:
        return render(request, "group_join.html", {"invalid": True, "login_form": LoginForm()}, status=404)
    if group.is_member(request.user):
        return redirect("group_detail", group_uuid=group.uuid)
    if request.method == "POST":
        group.members.add(request.user)
        return redirect("group_detail", group_uuid=group.uuid)
    return render(
        request,
        "group_join.html",
        {"group": group, "token": token, "login_form": LoginForm()},
    )


@login_required
@require_POST
def group_leave(request, group_uuid):
    group = _group_for_member(request, group_uuid)
    if group.is_creator(request.user):
        # A group must keep its creator; they delete it instead.
        return HttpResponseBadRequest("The group creator can't leave the group; delete it instead.")
    group.remove_member(request.user)
    return redirect("group_list")


@login_required
@require_POST
def group_remove_member(request, group_uuid, user_id):
    group = _group_for_creator(request, group_uuid)
    member = get_object_or_404(group.members, pk=user_id)
    if member == group.creator:
        return HttpResponseBadRequest("The group creator can't be removed.")
    group.remove_member(member)
    return redirect("group_detail", group_uuid=group.uuid)


@login_required
@require_POST
def group_reset_invite(request, group_uuid):
    group = _group_for_creator(request, group_uuid)
    group.reset_invite()
    return redirect("group_detail", group_uuid=group.uuid)


@login_required
@require_POST
def group_edit(request, group_uuid):
    group = _group_for_creator(request, group_uuid)
    form = GroupForm(data=request.POST, instance=group)
    if form.is_valid():
        form.save()
        return redirect("group_detail", group_uuid=group.uuid)
    return render(
        request,
        "group_create.html",
        {"form": form, "group": group, "login_form": LoginForm()},
        status=400,
    )


@login_required
@require_POST
def group_delete(request, group_uuid):
    group = _group_for_creator(request, group_uuid)
    group.delete()
    return redirect("group_list")


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
