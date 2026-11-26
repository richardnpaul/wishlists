# Standard Library Imports
import uuid

# Django Imports
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

# Local
from lists.forms import GroupForm, WishListForm, WishlistPrivacyForm
from lists.models import Group, Wishlist


User = get_user_model()


class GroupFormAdversarialTest(TestCase):
    """Adversarial stress-testing of GroupForm."""

    def setUp(self):
        self.user = User.objects.create_user(username="group_creator", password="password123")

    def test_group_form_blank_name_rejected(self):
        """Blank group name must fail form validation with required error."""
        form = GroupForm(data={"name": "", "description": "Valid description"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertEqual(form.errors["name"], ["Group name is required"])

    def test_group_form_whitespace_only_name_rejected(self):
        """Whitespace-only group name must be rejected."""
        form = GroupForm(data={"name": "     ", "description": "Whitespace test"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_group_form_name_boundary_128_chars_allowed(self):
        """Exactly 128 characters must be accepted as maximum allowed length."""
        max_name = "A" * 128
        form = GroupForm(data={"name": max_name, "description": "Boundary 128 chars"})
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")

    def test_group_form_name_boundary_129_chars_rejected(self):
        """129 characters exceeds max_length=128 and must be rejected."""
        too_long = "A" * 129
        form = GroupForm(data={"name": too_long, "description": "Boundary 129 chars"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_group_form_duplicate_name_rejected(self):
        """Duplicate group name must fail validation against existing database records."""
        Group.objects.create(name="Unique Hackers", creator=self.user)
        form = GroupForm(data={"name": "Unique Hackers", "description": "Another hacker group"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_group_form_empty_description_allowed(self):
        """Description is optional and blank description must be valid."""
        form = GroupForm(data={"name": "No Description Group", "description": ""})
        self.assertTrue(form.is_valid())

    def test_group_form_large_description_allowed(self):
        """Large description text (e.g. 5000 characters) must be accepted."""
        large_desc = "Lorem ipsum " * 400
        form = GroupForm(data={"name": "Large Desc Group", "description": large_desc})
        self.assertTrue(form.is_valid())

    def test_group_form_special_characters_in_name(self):
        """Special characters in group name must be accepted by the form."""
        special_name = "C++ & Python Devs #1 (2026) <Special>"
        form = GroupForm(data={"name": special_name, "description": "Dev group"})
        self.assertTrue(form.is_valid())


class WishListFormPrivacyAdversarialTest(TestCase):
    """Adversarial stress-testing of WishListForm privacy defaults and handling."""

    def setUp(self):
        self.user = User.objects.create_user(username="list_tester", password="password123")

    def test_wishlist_form_omitted_is_private_strictly_defaults_to_true(self):
        """CRITICAL: WishListForm MUST default is_private to True when omitted from POST data."""
        form = WishListForm(data={"title": "Private Default List"})
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")
        wishlist = form.save(as_user=self.user)
        self.assertTrue(
            wishlist.is_private,
            "Wishlist.is_private must be True when omitted from POST data",
        )
        # Verify persistence in database
        reloaded = Wishlist.objects.get(id=wishlist.id)
        self.assertTrue(reloaded.is_private)

    def test_wishlist_form_explicit_true_values(self):
        """Various representations of truthy is_private must save as True."""
        for i, val in enumerate((True, "true", "True", "on", "1", 1)):
            with self.subTest(val=val):
                form = WishListForm(data={"title": f"True List {i}_{val}", "is_private": val})
                self.assertTrue(form.is_valid())
                wishlist = form.save(as_user=self.user)
                self.assertTrue(wishlist.is_private)

    def test_wishlist_form_explicit_false_values(self):
        """Falsy representations of is_private must save as False."""
        for i, val in enumerate((False, "false", "False", "0", 0, "")):
            with self.subTest(val=val):
                form = WishListForm(data={"title": f"False List {i}_{val}", "is_private": val})
                self.assertTrue(form.is_valid())
                wishlist = form.save(as_user=self.user)
                self.assertFalse(
                    wishlist.is_private,
                    f"Expected is_private=False for {val}, got {wishlist.is_private}",
                )

    def test_wishlist_form_blank_title_rejected(self):
        """Blank title must be rejected."""
        form = WishListForm(data={"title": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_wishlist_form_title_boundary_128_chars_allowed(self):
        """Exactly 128 characters title must be valid."""
        max_title = "W" * 128
        form = WishListForm(data={"title": max_title})
        self.assertTrue(form.is_valid())
        wishlist = form.save(as_user=self.user)
        self.assertEqual(wishlist.title, max_title)

    def test_wishlist_form_title_boundary_129_chars_rejected(self):
        """129 characters title must be rejected."""
        too_long = "W" * 129
        form = WishListForm(data={"title": too_long})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


class WishlistPrivacyFormAdversarialTest(TestCase):
    """Adversarial stress-testing of WishlistPrivacyForm."""

    def setUp(self):
        self.user = User.objects.create_user(username="privacy_owner", password="password123")
        self.wishlist = Wishlist.objects.create(owner=self.user, title="Privacy Matrix List", is_private=True)
        self.g1 = Group.objects.create(name="Beta Group", creator=self.user)
        self.g2 = Group.objects.create(name="Alpha Group", creator=self.user)
        self.g3 = Group.objects.create(name="Gamma Group", creator=self.user)
        self.user.subscribed_groups.add(self.g1, self.g2, self.g3)

    def test_privacy_form_groups_queryset_alphabetical_order(self):
        """Groups queryset must be ordered alphabetically by name."""
        form = WishlistPrivacyForm(instance=self.wishlist)
        names = list(form.fields["groups"].queryset.values_list("name", flat=True))
        self.assertEqual(names, ["Alpha Group", "Beta Group", "Gamma Group"])

    def test_privacy_form_toggle_to_public_and_back(self):
        """Toggle is_private to False, then back to True."""
        # Uncheck private (omitted or False)
        form = WishlistPrivacyForm(data={"is_private": False}, instance=self.wishlist)
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")
        form.save()
        self.wishlist.refresh_from_db()
        self.assertFalse(self.wishlist.is_private)

        # Re-check private
        form = WishlistPrivacyForm(data={"is_private": True}, instance=self.wishlist)
        self.assertTrue(form.is_valid())
        form.save()
        self.wishlist.refresh_from_db()
        self.assertTrue(self.wishlist.is_private)

    def test_privacy_form_multiple_groups_selection(self):
        """Selecting multiple groups exposes wishlist to exactly those groups."""
        form = WishlistPrivacyForm(
            data={"is_private": True, "groups": [self.g1.pk, self.g3.pk]},
            instance=self.wishlist,
        )
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")
        form.save()
        self.wishlist.refresh_from_db()
        associated_pks = set(self.wishlist.groups.values_list("pk", flat=True))
        self.assertEqual(associated_pks, {self.g1.pk, self.g3.pk})

    def test_privacy_form_empty_groups_clears_associations(self):
        """Submitting no groups clears all existing group associations."""
        self.wishlist.groups.add(self.g1, self.g2)
        self.assertEqual(self.wishlist.groups.count(), 2)

        form = WishlistPrivacyForm(
            data={"is_private": True, "groups": []},
            instance=self.wishlist,
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.wishlist.refresh_from_db()
        self.assertEqual(self.wishlist.groups.count(), 0)

    def test_privacy_form_user_kwarg_handled_gracefully(self):
        """WishlistPrivacyForm handles user kwarg gracefully without unexpected keyword error."""
        form = WishlistPrivacyForm(instance=self.wishlist, user=self.user)
        self.assertIsNotNone(form)


class WishlistPrivacyViewSecurityTest(TestCase):
    """View-level security and boundary tests for edit_wishlist_privacy view."""

    def setUp(self):
        self.owner = User.objects.create_user(username="list_owner_sec", password="password123")
        self.attacker = User.objects.create_user(username="attacker_sec", password="password123")
        self.wishlist = Wishlist.objects.create(owner=self.owner, title="Confidential List", is_private=True)
        self.group = Group.objects.create(name="Confidential Group", creator=self.owner)
        self.group.members.add(self.owner)

    def test_anonymous_user_redirected_to_login(self):
        """Unauthenticated user accessing privacy edit page is redirected to login."""
        url = reverse("edit_wishlist_privacy", kwargs={"wishlist_uuid": self.wishlist.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_non_owner_forbidden_on_get(self):
        """Non-owner authenticated user GETting privacy edit page receives HTTP 403."""
        self.client.force_login(self.attacker)
        url = reverse("edit_wishlist_privacy", kwargs={"wishlist_uuid": self.wishlist.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_non_owner_forbidden_on_post(self):
        """Non-owner authenticated user attempting to POST privacy changes receives HTTP 403."""
        self.client.force_login(self.attacker)
        url = reverse("edit_wishlist_privacy", kwargs={"wishlist_uuid": self.wishlist.uuid})
        response = self.client.post(url, data={"is_private": False})
        self.assertEqual(response.status_code, 403)
        self.wishlist.refresh_from_db()
        self.assertTrue(self.wishlist.is_private, "Attacker must NOT alter wishlist privacy")

    def test_owner_can_get_and_post_privacy(self):
        """Owner can view privacy form and successfully update privacy and groups."""
        self.client.force_login(self.owner)
        url = reverse("edit_wishlist_privacy", kwargs={"wishlist_uuid": self.wishlist.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # POST update: make public and add group
        post_response = self.client.post(
            url,
            data={"is_private": "", "groups": [self.group.pk]},
        )
        self.assertRedirects(post_response, reverse("view_list", kwargs={"wishlist_uuid": self.wishlist.uuid}))
        self.wishlist.refresh_from_db()
        self.assertFalse(self.wishlist.is_private)
        self.assertIn(self.group, self.wishlist.groups.all())

    def test_nonexistent_wishlist_returns_404(self):
        """Nonexistent wishlist UUID returns 404."""
        self.client.force_login(self.owner)
        fake_uuid = uuid.uuid4()
        url = reverse("edit_wishlist_privacy", kwargs={"wishlist_uuid": fake_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class GroupUrlBoundaryTest(TestCase):
    """Malformed and unknown group URLs."""

    def setUp(self):
        self.user = User.objects.create_user(username="search_user", password="password123")
        self.client.force_login(self.user)

    def test_nonexistent_group_uuid_returns_404(self):
        response = self.client.get(reverse("group_detail", kwargs={"group_uuid": uuid.uuid4()}))
        self.assertEqual(response.status_code, 404)

    def test_invalid_uuid_returns_404(self):
        response = self.client.get("/groups/not-a-valid-uuid/")
        self.assertEqual(response.status_code, 404)

    def test_leave_nonexistent_uuid_returns_404(self):
        response = self.client.post(reverse("group_leave", kwargs={"group_uuid": uuid.uuid4()}))
        self.assertEqual(response.status_code, 404)

    def test_search_query_is_ignored_and_only_own_groups_listed(self):
        """There's no public directory any more: ?q= can't surface other people's groups."""
        other = User.objects.create_user(username="someone_else", password="password123")
        Group.objects.create(name="Django Architects", creator=other).members.add(other)
        response = self.client.get(reverse("group_list") + "?q=django")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["groups"]), [])
        self.assertNotContains(response, "Django Architects")


class TemplateAndUIVerificationTest(TestCase):
    """Template and UI element stress-testing."""

    def setUp(self):
        self.owner = User.objects.create_user(username="template_owner", password="password123")
        self.visitor = User.objects.create_user(username="template_visitor", password="password123")
        self.private_list = Wishlist.objects.create(
            owner=self.owner,
            title="Owner Secret List",
            is_private=True,
        )
        self.public_list = Wishlist.objects.create(
            owner=self.owner,
            title="Owner Public List",
            is_private=False,
        )
        self.group = Group.objects.create(
            name="UI Verification Group",
            description="Testing template badges and buttons",
            creator=self.owner,
        )
        self.group.members.add(self.owner)

    def test_navbar_unauthenticated_does_not_contain_groups_link(self):
        """Unauthenticated requests must NOT see the 'Groups' navigation button."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'href="/groups/"')
        self.assertNotContains(response, ">Groups<")
        # Ensure login dropdown is present
        self.assertContains(response, "Login")

    def test_navbar_authenticated_contains_groups_link(self):
        """Authenticated requests MUST see the 'Groups' navigation button."""
        self.client.force_login(self.visitor)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("group_list"))
        self.assertContains(response, "Groups")

    def test_private_badge_rendered_on_private_wishlist(self):
        """Private wishlist renders secondary 'Private' badge and NOT 'Public' badge."""
        self.client.force_login(self.owner)
        url = reverse("view_list", kwargs={"wishlist_uuid": self.private_list.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="badge badge-secondary">Private</span>')
        self.assertNotContains(response, '<span class="badge badge-info">Public</span>')

    def test_public_badge_rendered_on_public_wishlist(self):
        """Public wishlist renders info 'Public' badge and NOT 'Private' badge."""
        self.client.force_login(self.visitor)
        url = reverse("view_list", kwargs={"wishlist_uuid": self.public_list.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="badge badge-info">Public</span>')
        self.assertNotContains(response, '<span class="badge badge-secondary">Private</span>')

    def test_owner_sees_privacy_and_edit_buttons(self):
        """Wishlist owner sees 'Privacy & Sharing' and 'Edit' buttons on wishlist view."""
        self.client.force_login(self.owner)
        url = reverse("view_list", kwargs={"wishlist_uuid": self.public_list.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Privacy & Sharing")
        self.assertContains(response, reverse("edit_wishlist_privacy", kwargs={"wishlist_uuid": self.public_list.uuid}))
        self.assertContains(response, reverse("edit_list", kwargs={"wishlist_uuid": self.public_list.uuid}))

    def test_non_owner_does_not_see_privacy_nor_edit_buttons(self):
        """Non-owner viewer does NOT see 'Privacy & Sharing' nor 'Edit' buttons."""
        self.client.force_login(self.visitor)
        url = reverse("view_list", kwargs={"wishlist_uuid": self.public_list.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Privacy & Sharing")
        self.assertNotContains(
            response, reverse("edit_wishlist_privacy", kwargs={"wishlist_uuid": self.public_list.uuid})
        )
        self.assertNotContains(response, reverse("edit_list", kwargs={"wishlist_uuid": self.public_list.uuid}))

    def test_group_list_shows_only_my_groups(self):
        """Group list shows groups I'm in, and nothing to non-members."""
        self.client.force_login(self.owner)
        response = self.client.get(reverse("group_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "UI Verification Group")

        self.client.force_login(self.visitor)
        response = self.client.get(reverse("group_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "UI Verification Group")
        self.assertNotContains(response, "Subscribe")

    def test_group_detail_membership_badges_and_actions(self):
        """Creator sees Delete (not Leave); a member sees Leave; a non-member is refused."""
        url = reverse("group_detail", kwargs={"group_uuid": self.group.uuid})

        self.client.force_login(self.owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Member")
        self.assertContains(response, "Delete Group")
        self.assertNotContains(response, "Leave Group")

        self.group.members.add(self.visitor)
        self.client.force_login(self.visitor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leave Group")
        self.assertNotContains(response, "Delete Group")
        self.assertNotContains(response, "Join Group")

        self.group.members.remove(self.visitor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_group_detail_shared_wishlist_filtering(self):
        """Only members can see a group's page; members see every list shared with it."""
        self.private_list.groups.add(self.group)
        self.public_list.groups.add(self.group)
        url = reverse("group_detail", kwargs={"group_uuid": self.group.uuid})

        self.client.force_login(self.visitor)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.group.members.add(self.visitor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_list.title)
        self.assertContains(response, self.private_list.title)

    def test_xss_protection_in_group_rendering(self):
        """XSS payloads in group name and description are safely escaped by templates."""
        xss_group = Group.objects.create(
            name='<script id="xss-test">alert("xss")</script>',
            description='<img src=x onerror="alert(1)">',
            creator=self.owner,
        )
        xss_group.members.add(self.owner)
        self.client.force_login(self.owner)

        # In group list
        response = self.client.get(reverse("group_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<script id="xss-test">')
        self.assertContains(response, escape('<script id="xss-test">alert("xss")</script>'))

        # In group detail
        detail_url = reverse("group_detail", kwargs={"group_uuid": xss_group.uuid})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<script id="xss-test">')
        self.assertNotContains(response, '<img src=x onerror="alert(1)">')


class GroupViewsAndRedirectionAdversarialTest(TestCase):
    """Stress testing group views, creation errors, and redirection logic."""

    def setUp(self):
        self.user = User.objects.create_user(username="group_view_user", password="password123")
        self.other_user = User.objects.create_user(username="other_view_user", password="password123")
        self.client.force_login(self.user)
        self.group = Group.objects.create(name="Existing Group", creator=self.other_user)

    def test_group_create_duplicate_name_returns_400_with_form_errors(self):
        """POSTing a duplicate group name to group_create returns HTTP 400 with form error."""
        response = self.client.post(
            reverse("group_create"),
            data={"name": "Existing Group", "description": "Duplicate test"},
        )
        self.assertEqual(response.status_code, 400)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_privacy_form_invalid_group_pk_rejected(self):
        """POSTing invalid/non-existent group PK fails form validation."""
        wishlist = Wishlist.objects.create(owner=self.user, title="My Valid List")
        form = WishlistPrivacyForm(data={"is_private": True, "groups": [999999]}, instance=wishlist)
        self.assertFalse(form.is_valid())
        self.assertIn("groups", form.errors)
