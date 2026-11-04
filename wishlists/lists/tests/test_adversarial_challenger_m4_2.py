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


class SearchAndDiscoveryBoundaryTest(TestCase):
    """Adversarial stress-testing of group search and discovery boundaries."""

    def setUp(self):
        self.user = User.objects.create_user(username="search_user", password="password123")
        self.client.force_login(self.user)
        self.g1 = Group.objects.create(
            name="Django Architects",
            description="Discussing Django and Python architecture",
            creator=self.user,
        )
        self.g2 = Group.objects.create(
            name="Frontend Wizards",
            description="React, Vue, and CSS styling tricks",
            creator=self.user,
        )
        self.g3 = Group.objects.create(
            name="Rustaceans",
            description="High performance systems programming",
            creator=self.user,
        )

    def test_empty_search_query_returns_all_groups(self):
        """Empty search query ?q= returns all groups."""
        response = self.client.get(reverse("group_list") + "?q=")
        self.assertEqual(response.status_code, 200)
        groups = list(response.context["groups"])
        self.assertEqual(len(groups), 3)

    def test_whitespace_search_query_returns_all_groups(self):
        """Whitespace query ?q=   is stripped and returns all groups."""
        response = self.client.get(reverse("group_list") + "?q=   ")
        self.assertEqual(response.status_code, 200)
        groups = list(response.context["groups"])
        self.assertEqual(len(groups), 3)

    def test_case_insensitive_search_match_in_name(self):
        """Search query matches group name case-insensitively."""
        for query in ("django", "DJANGO", "dJaNgO", "architect"):
            with self.subTest(query=query):
                response = self.client.get(reverse("group_list") + f"?q={query}")
                self.assertEqual(response.status_code, 200)
                groups = list(response.context["groups"])
                self.assertEqual(len(groups), 1)
                self.assertEqual(groups[0].name, "Django Architects")

    def test_case_insensitive_search_match_in_description(self):
        """Search query matches group description case-insensitively."""
        for query in ("python", "PYTHON", "PyThOn"):
            with self.subTest(query=query):
                response = self.client.get(reverse("group_list") + f"?q={query}")
                self.assertEqual(response.status_code, 200)
                groups = list(response.context["groups"])
                self.assertEqual(len(groups), 1)
                self.assertEqual(groups[0].name, "Django Architects")

    def test_search_partial_substring_match(self):
        """Partial substring match in name or description."""
        response = self.client.get(reverse("group_list") + "?q=Wiz")
        self.assertEqual(response.status_code, 200)
        groups = list(response.context["groups"])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].name, "Frontend Wizards")

    def test_search_no_match_returns_empty_and_friendly_message(self):
        """Query with no matches returns empty queryset and alert in template."""
        response = self.client.get(reverse("group_list") + "?q=NonexistentGroupKeywordXYZ")
        self.assertEqual(response.status_code, 200)
        groups = list(response.context["groups"])
        self.assertEqual(len(groups), 0)
        self.assertContains(response, "No groups found.")

    def test_search_special_characters_do_not_crash(self):
        """Adversarial search queries with SQL/regex characters do not cause 500 errors."""
        adversarial_queries = [
            "%",
            "_",
            "'",
            "'' OR 1=1 --",
            '<script>alert("xss")</script>',
            "\\",
            "; DROP TABLE lists_group; --",
            "$@#!^&*()",
        ]
        for query in adversarial_queries:
            with self.subTest(query=query):
                response = self.client.get(reverse("group_list"), {"q": query})
                self.assertEqual(
                    response.status_code,
                    200,
                    f"Query {query} resulted in status code {response.status_code}",
                )

    def test_search_unicode_characters(self):
        """Unicode characters in search query execute cleanly."""
        Group.objects.create(name="Équipe de Recherche", description="Recherche et développement", creator=self.user)
        response = self.client.get(reverse("group_list"), {"q": "Équipe"})
        self.assertEqual(response.status_code, 200)
        groups = list(response.context["groups"])
        self.assertEqual(len(groups), 1)

    def test_nonexistent_group_uuid_returns_404(self):
        """Accessing nonexistent group UUID returns 404."""
        nonexistent_uuid = uuid.uuid4()
        response = self.client.get(reverse("group_detail", kwargs={"group_uuid": nonexistent_uuid}))
        self.assertEqual(response.status_code, 404)

    def test_invalid_uuid_returns_404(self):
        """Accessing malformed UUID path returns 404."""
        response = self.client.get("/groups/not-a-valid-uuid/")
        self.assertEqual(response.status_code, 404)

    def test_subscribe_nonexistent_uuid_returns_404(self):
        """Subscribing to nonexistent group UUID returns 404."""
        nonexistent_uuid = uuid.uuid4()
        response = self.client.post(reverse("group_subscribe", kwargs={"group_uuid": nonexistent_uuid}))
        self.assertEqual(response.status_code, 404)

    def test_unsubscribe_nonexistent_uuid_returns_404(self):
        """Unsubscribing from nonexistent group UUID returns 404."""
        nonexistent_uuid = uuid.uuid4()
        response = self.client.post(reverse("group_unsubscribe", kwargs={"group_uuid": nonexistent_uuid}))
        self.assertEqual(response.status_code, 404)


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

    def test_group_list_membership_badges_and_buttons(self):
        """Group list renders 'Subscribed' and 'Unsubscribe' for members, and 'Subscribe' for non-members."""
        # Owner is member of self.group
        self.client.force_login(self.owner)
        response = self.client.get(reverse("group_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="badge badge-success mb-1">Subscribed</span>')
        self.assertContains(response, "Unsubscribe")

        # Visitor is NOT a member
        self.client.force_login(self.visitor)
        response = self.client.get(reverse("group_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<span class="badge badge-success mb-1">Subscribed</span>')
        self.assertContains(response, "Subscribe")

    def test_group_detail_membership_badges_and_actions(self):
        """Group detail renders 'Member' and 'Leave Group' for members, and 'Join Group' for non-members."""
        # Member view
        self.client.force_login(self.owner)
        url = reverse("group_detail", kwargs={"group_uuid": self.group.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Member")
        self.assertContains(response, "Leave Group")

        # Non-member view
        self.client.force_login(self.visitor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Leave Group")
        self.assertContains(response, "Join Group")

    def test_group_detail_shared_wishlist_filtering(self):
        """Group detail page only displays shared wishlists that the requesting user has permission to see."""
        # Expose both private and public lists to the group
        self.private_list.groups.add(self.group)
        self.public_list.groups.add(self.group)

        # Visitor is NOT in group yet: private_list is accessible via group? Only if visitor is in group!
        # Since visitor is not in group, can_view_wishlist for private_list is False!
        self.client.force_login(self.visitor)
        url = reverse("group_detail", kwargs={"group_uuid": self.group.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Public list is visible
        self.assertContains(response, self.public_list.title)
        # Private list should NOT be visible to visitor because visitor is not a member of the group!
        self.assertNotContains(response, self.private_list.title)

        # Once visitor joins the group:
        self.group.members.add(self.visitor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Now private list IS visible because visitor is a member of the exposed group
        self.assertContains(response, self.private_list.title)

    def test_xss_protection_in_group_rendering(self):
        """XSS payloads in group name and description are safely escaped by templates."""
        xss_group = Group.objects.create(
            name='<script id="xss-test">alert("xss")</script>',
            description='<img src=x onerror="alert(1)">',
            creator=self.owner,
        )
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

    def test_group_subscribe_idempotent(self):
        """Subscribing to a group multiple times does not raise error and keeps user as member."""
        url = reverse("group_subscribe", kwargs={"group_uuid": self.group.uuid})
        response1 = self.client.post(url)
        self.assertEqual(response1.status_code, 302)
        self.assertTrue(self.group.members.filter(id=self.user.id).exists())

        # Second subscribe
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(self.group.members.filter(id=self.user.id).count(), 1)

    def test_group_unsubscribe_idempotent(self):
        """Unsubscribing when not a member does not raise error."""
        url = reverse("group_unsubscribe", kwargs={"group_uuid": self.group.uuid})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.group.members.filter(id=self.user.id).exists())

    def test_group_subscribe_next_url_valid_local_redirect(self):
        """POST next param with local URL redirects to that local URL."""
        url = reverse("group_subscribe", kwargs={"group_uuid": self.group.uuid})
        response = self.client.post(url, data={"next": "/groups/"})
        self.assertRedirects(response, "/groups/")

    def test_privacy_form_invalid_group_pk_rejected(self):
        """POSTing invalid/non-existent group PK fails form validation."""
        wishlist = Wishlist.objects.create(owner=self.user, title="My Valid List")
        form = WishlistPrivacyForm(data={"is_private": True, "groups": [999999]}, instance=wishlist)
        self.assertFalse(form.is_valid())
        self.assertIn("groups", form.errors)
