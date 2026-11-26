# Standard Library Imports
from unittest import mock

# Django Imports
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings
from django.urls import reverse

# Local
from lists.forms import WishlistPrivacyForm
from lists.models import Group, InvalidInvite, Wishlist


User = get_user_model()


def make_group(creator, name="Family"):
    group = Group.objects.create(name=name, creator=creator)
    group.members.add(creator)
    return group


class InviteTokenTest(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator@example.com", password="pw")
        self.group = make_group(self.creator)

    def test_valid_token_round_trips(self):
        self.assertEqual(Group.from_invite_token(self.group.make_invite_token()), self.group)

    def test_tampered_token_is_rejected(self):
        token = self.group.make_invite_token()
        for bad in (token + "x", token[:-1], "not-a-token", f"{self.group.uuid}:1"):
            with self.subTest(bad=bad), self.assertRaises(InvalidInvite):
                Group.from_invite_token(bad)

    def test_token_for_another_version_is_rejected_after_reset(self):
        token = self.group.make_invite_token()
        self.group.reset_invite()
        with self.assertRaises(InvalidInvite):
            Group.from_invite_token(token)
        self.assertEqual(Group.from_invite_token(self.group.make_invite_token()), self.group)

    def test_expired_token_is_rejected(self):
        with mock.patch("django.core.signing.time.time", return_value=1_000_000):
            token = self.group.make_invite_token()
        with mock.patch("django.core.signing.time.time", return_value=1_000_000 + 7 * 24 * 3600 + 1):
            with self.assertRaises(InvalidInvite):
                Group.from_invite_token(token)
        with mock.patch("django.core.signing.time.time", return_value=1_000_000 + 7 * 24 * 3600 - 60):
            self.assertEqual(Group.from_invite_token(token), self.group)

    def test_token_for_deleted_group_is_rejected(self):
        token = self.group.make_invite_token()
        self.group.delete()
        with self.assertRaises(InvalidInvite):
            Group.from_invite_token(token)

    @override_settings(SECRET_KEY="a-different-secret-key-for-this-test-only-0123456789")
    def test_token_signed_with_other_key_is_rejected(self):
        with self.settings(SECRET_KEY="original-secret-key-for-this-test-only-0123456789"):
            token = self.group.make_invite_token()
        with self.assertRaises(InvalidInvite):
            Group.from_invite_token(token)


class GroupJoinViewTest(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator@example.com", password="pw")
        self.joiner = User.objects.create_user(username="joiner@example.com", password="pw")
        self.group = make_group(self.creator, name="Smiths")
        self.url = reverse("group_join", args=[self.group.make_invite_token()])

    def test_anonymous_user_is_sent_to_login_with_next(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/?next="))
        self.assertIn("join", response.url)

    def test_get_shows_confirm_page_without_joining(self):
        self.client.force_login(self.joiner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "group_join.html")
        self.assertContains(response, "Join Smiths?")
        self.assertFalse(self.group.is_member(self.joiner))

    def test_post_joins_and_redirects_to_group(self):
        self.client.force_login(self.joiner)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("group_detail", args=[self.group.uuid]))
        self.assertTrue(self.group.is_member(self.joiner))

    def test_existing_member_is_redirected_to_group(self):
        self.client.force_login(self.creator)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("group_detail", args=[self.group.uuid]))

    def test_invalid_link_shows_friendly_page_and_does_not_join(self):
        self.client.force_login(self.joiner)
        self.group.reset_invite()
        for method in (self.client.get, self.client.post):
            with self.subTest(method=method.__name__):
                response = method(self.url)
                self.assertEqual(response.status_code, 404)
                self.assertContains(response, "isn't valid", status_code=404)
        self.assertFalse(self.group.is_member(self.joiner))

    def test_creator_sees_invite_link_and_members_do_not(self):
        self.client.force_login(self.creator)
        response = self.client.get(reverse("group_detail", args=[self.group.uuid]))
        self.assertContains(response, "/groups/join/")
        self.assertIn(response.context["invite_url"].split("/groups/join/")[1].rstrip("/"), self.url)

        self.group.members.add(self.joiner)
        self.client.force_login(self.joiner)
        response = self.client.get(reverse("group_detail", args=[self.group.uuid]))
        self.assertNotContains(response, "/groups/join/")
        self.assertNotIn("invite_url", response.context)


class GroupManagementTest(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator@example.com", password="pw")
        self.member = User.objects.create_user(username="member@example.com", password="pw")
        self.group = make_group(self.creator)
        self.group.members.add(self.member)
        self.member_list = Wishlist.objects.create(owner=self.member, title="Member's list")
        self.member_list.groups.add(self.group)
        self.creator_list = Wishlist.objects.create(owner=self.creator, title="Creator's list")
        self.creator_list.groups.add(self.group)

    def creator_only_posts(self):
        return {
            "reset": (reverse("group_reset_invite", args=[self.group.uuid]), {}),
            "remove": (reverse("group_remove_member", args=[self.group.uuid, self.member.pk]), {}),
            "edit": (reverse("group_edit", args=[self.group.uuid]), {"name": "Hijacked"}),
            "delete": (reverse("group_delete", args=[self.group.uuid]), {}),
        }

    def test_non_creator_cannot_manage_group(self):
        self.client.force_login(self.member)
        for name, (url, data) in self.creator_only_posts().items():
            with self.subTest(action=name):
                self.assertEqual(self.client.post(url, data).status_code, 403)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Family")
        self.assertEqual(self.group.invite_version, 1)
        self.assertTrue(self.group.is_member(self.member))

    def test_management_actions_require_post(self):
        self.client.force_login(self.creator)
        for name, (url, _) in self.creator_only_posts().items():
            with self.subTest(action=name):
                self.assertEqual(self.client.get(url).status_code, 405)

    def test_creator_can_reset_invite(self):
        self.client.force_login(self.creator)
        self.client.post(reverse("group_reset_invite", args=[self.group.uuid]))
        self.group.refresh_from_db()
        self.assertEqual(self.group.invite_version, 2)

    def test_creator_can_rename(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("group_edit", args=[self.group.uuid]), {"name": "The Smiths", "description": "Family gifts"}
        )
        self.assertRedirects(response, reverse("group_detail", args=[self.group.uuid]))
        self.group.refresh_from_db()
        self.assertEqual((self.group.name, self.group.description), ("The Smiths", "Family gifts"))

    def test_creator_rename_with_blank_name_is_rejected(self):
        self.client.force_login(self.creator)
        response = self.client.post(reverse("group_edit", args=[self.group.uuid]), {"name": ""})
        self.assertEqual(response.status_code, 400)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Family")

    def test_creator_can_delete_group_and_lists_survive(self):
        self.client.force_login(self.creator)
        response = self.client.post(reverse("group_delete", args=[self.group.uuid]))
        self.assertRedirects(response, reverse("group_list"))
        self.assertFalse(Group.objects.filter(pk=self.group.pk).exists())
        self.assertTrue(Wishlist.objects.filter(pk=self.member_list.pk).exists())

    def test_removing_member_unshares_their_lists(self):
        self.client.force_login(self.creator)
        self.client.post(reverse("group_remove_member", args=[self.group.uuid, self.member.pk]))
        self.assertFalse(self.group.is_member(self.member))
        self.assertFalse(self.member_list.groups.exists())
        self.assertTrue(self.creator_list.groups.filter(pk=self.group.pk).exists())
        # ...and they lose access to the group's lists.
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(self.creator_list.get_absolute_url()).status_code, 403)

    def test_leaving_unshares_my_lists(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse("group_leave", args=[self.group.uuid]))
        self.assertRedirects(response, reverse("group_list"))
        self.assertFalse(self.group.is_member(self.member))
        self.assertFalse(self.member_list.groups.exists())

    def test_creator_cannot_leave_or_be_removed(self):
        self.client.force_login(self.creator)
        self.assertEqual(self.client.post(reverse("group_leave", args=[self.group.uuid])).status_code, 400)
        url = reverse("group_remove_member", args=[self.group.uuid, self.creator.pk])
        self.assertEqual(self.client.post(url).status_code, 400)
        self.assertTrue(self.group.is_member(self.creator))

    def test_removing_a_non_member_is_404(self):
        stranger = User.objects.create_user(username="stranger@example.com", password="pw")
        self.client.force_login(self.creator)
        url = reverse("group_remove_member", args=[self.group.uuid, stranger.pk])
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_non_member_cannot_leave(self):
        stranger = User.objects.create_user(username="stranger@example.com", password="pw")
        self.client.force_login(stranger)
        self.assertEqual(self.client.post(reverse("group_leave", args=[self.group.uuid])).status_code, 403)


class PrivacyFormGroupScopeTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner@example.com", password="pw")
        self.other = User.objects.create_user(username="other@example.com", password="pw")
        self.mine = make_group(self.owner, name="Mine")
        self.theirs = make_group(self.other, name="Theirs")
        self.wishlist = Wishlist.objects.create(owner=self.owner, title="List")

    def test_only_my_groups_are_offered(self):
        form = WishlistPrivacyForm(instance=self.wishlist, user=self.owner)
        self.assertEqual(list(form.fields["groups"].queryset), [self.mine])

    def test_sharing_with_a_group_i_am_not_in_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("edit_wishlist_privacy", args=[self.wishlist.uuid]),
            {"is_private": "on", "groups": [self.theirs.pk]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("groups", response.context["privacy_form"].errors)
        self.assertFalse(self.wishlist.groups.exists())


class VisibleToTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner@example.com", password="pw")
        self.member = User.objects.create_user(username="member@example.com", password="pw")
        self.stranger = User.objects.create_user(username="stranger@example.com", password="pw")
        group = make_group(self.owner)
        group.members.add(self.member)
        self.private = Wishlist.objects.create(owner=self.owner, title="Private")
        self.shared = Wishlist.objects.create(owner=self.owner, title="Shared")
        self.shared.groups.add(group)
        self.public = Wishlist.objects.create(owner=self.owner, title="Public", is_private=False)
        # A second group sharing the same list mustn't duplicate rows.
        second = make_group(self.owner, name="Second")
        second.members.add(self.member)
        self.shared.groups.add(second)

    def assertVisible(self, user, expected):
        visible = set(Wishlist.objects.visible_to(user).values_list("title", flat=True))
        self.assertEqual(visible, expected)
        self.assertEqual(Wishlist.objects.visible_to(user).count(), len(expected))
        # Must agree with the per-object check used by the detail views.
        for wishlist in Wishlist.objects.all():
            self.assertEqual(wishlist.can_view(user), wishlist.title in expected, wishlist.title)

    def test_owner_sees_all_own_lists(self):
        self.assertVisible(self.owner, {"Private", "Shared", "Public"})

    def test_group_member_sees_shared_and_public(self):
        self.assertVisible(self.member, {"Shared", "Public"})

    def test_stranger_sees_only_public(self):
        self.assertVisible(self.stranger, {"Public"})

    def test_anonymous_sees_only_public(self):
        self.assertVisible(AnonymousUser(), {"Public"})


class ListPagesTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner@example.com", password="pw", first_name="Olive")
        self.member = User.objects.create_user(username="member@example.com", password="pw", first_name="Mo")
        self.stranger = User.objects.create_user(username="stranger@example.com", password="pw", first_name="Sid")
        self.group = make_group(self.owner, name="Family")
        self.group.members.add(self.member)
        self.shared = Wishlist.objects.create(owner=self.owner, title="Olive's birthday")
        self.shared.groups.add(self.group)
        Wishlist.objects.create(owner=self.owner, title="Olive's secret list")
        Wishlist.objects.create(owner=self.stranger, title="Sid's private list")

    def test_shared_with_me_lists_group_shared_lists(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("view_my_lists"))
        self.assertEqual(list(response.context["shared_lists"]), [self.shared])
        self.assertContains(response, "Shared with me")
        self.assertContains(response, "Olive&#x27;s birthday")
        self.assertNotContains(response, "secret list")
        self.assertEqual([g.name for g in response.context["shared_lists"][0].my_groups], ["Family"])

    def test_shared_with_me_excludes_public_lists_and_my_own(self):
        Wishlist.objects.create(owner=self.stranger, title="Sid's public list", is_private=False)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("view_my_lists"))
        self.assertEqual(list(response.context["shared_lists"]), [])
        self.assertNotContains(response, "Shared with me")

    def test_view_users_only_shows_people_with_visible_lists(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("view_users"))
        self.assertEqual(list(response.context["users"]), [self.owner])
        self.assertNotContains(response, "Sid")

    def test_view_users_includes_owners_of_public_lists_and_excludes_me(self):
        Wishlist.objects.create(owner=self.stranger, title="Sid's public list", is_private=False)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("view_users"))
        self.assertEqual(list(response.context["users"]), [self.stranger])

    def test_users_lists_page_filters_and_has_no_create_form(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("view_users_lists", args=[self.owner.pk]))
        self.assertEqual(list(response.context["lists"]), [self.shared])
        self.assertContains(response, "Olive's wishlists")
        self.assertNotContains(response, "Create Wishlist")

    def test_users_lists_page_404_for_unknown_user(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("view_users_lists", args=[999999])).status_code, 404)
