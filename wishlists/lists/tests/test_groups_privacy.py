# Standard Library Imports
import uuid

# Django Imports
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

# Local
from lists.models import Item, Wishlist


User = get_user_model()


def _get_can_view_wishlist():
    """Dynamically import can_view_wishlist helper from lists.views or lists.models."""
    try:
        from lists.views import can_view_wishlist

        return can_view_wishlist
    except ImportError, AttributeError:
        try:
            from lists.models import can_view_wishlist

            return can_view_wishlist
        except ImportError, AttributeError:
            raise ImportError(
                "can_view_wishlist helper must be defined in lists.views or lists.models "
                "per PROJECT.md Interface Contracts."
            )


def _get_group_model():
    """Dynamically import Group model from lists.models."""
    try:
        from lists.models import Group

        return Group
    except ImportError, AttributeError:
        raise ImportError("Group model must be defined in lists.models per PROJECT.md.")


# ==============================================================================
# 1. Model Unit Tests
# ==============================================================================


class WishlistPrivacyModelTest(TestCase):
    """Unit tests verifying Wishlist privacy defaults and group association."""

    def setUp(self):
        self.owner = User.objects.create_user(username="list_owner", password="password123")

    def test_wishlist_defaults_to_private_on_creation(self):
        """CRITICAL: Wishlists MUST default to private (is_private=True) upon creation."""
        wishlist = Wishlist(owner=self.owner, title="Secret Birthday Ideas")
        # In-memory check before save
        self.assertTrue(
            wishlist.is_private,
            "Wishlist.is_private field must default to True before saving.",
        )
        wishlist.save()
        self.assertTrue(
            wishlist.is_private,
            "Wishlist.is_private field must default to True after saving.",
        )

    def test_wishlist_persists_private_default_in_database(self):
        """Ensure Wishlist.is_private=True persists across reload from SQLite database."""
        wishlist = Wishlist.objects.create(owner=self.owner, title="Database Privacy Test")
        reloaded = Wishlist.objects.get(id=wishlist.id)
        self.assertTrue(
            reloaded.is_private,
            "Wishlist reloaded from database must have is_private=True by default.",
        )

    def test_wishlist_can_be_explicitly_created_as_public(self):
        """A user can explicitly set is_private=False to create a public wishlist."""
        wishlist = Wishlist.objects.create(
            owner=self.owner,
            title="Public Wishlist",
            is_private=False,
        )
        reloaded = Wishlist.objects.get(id=wishlist.id)
        self.assertFalse(
            reloaded.is_private,
            "Wishlist should allow is_private=False when explicitly set.",
        )

    def test_wishlist_groups_many_to_many_relationship(self):
        """Wishlists can be associated with multiple groups via a ManyToManyField."""
        Group = _get_group_model()
        group1 = Group.objects.create(creator=self.owner, name="Board Gamers")
        group2 = Group.objects.create(creator=self.owner, name="Book Club")

        wishlist = Wishlist.objects.create(owner=self.owner, title="Gaming & Reading")
        wishlist.groups.add(group1, group2)

        self.assertEqual(wishlist.groups.count(), 2)
        self.assertIn(group1, wishlist.groups.all())
        self.assertIn(group2, wishlist.groups.all())

        # Verify reverse relation
        self.assertIn(wishlist, group1.wishlists.all())
        self.assertIn(wishlist, group2.wishlists.all())


class GroupModelTest(TestCase):
    """Unit tests verifying Group model fields, UUID, constraints, and methods."""

    def setUp(self):
        self.creator = User.objects.create_user(username="group_admin", password="password123")
        self.member1 = User.objects.create_user(username="member_one", password="password123")
        self.member2 = User.objects.create_user(username="member_two", password="password123")

    def test_group_fields_and_defaults(self):
        """Group model must define uuid, name, description, creator, members, created, modified."""
        Group = _get_group_model()
        group = Group.objects.create(
            creator=self.creator,
            name="Tech Enthusiasts",
            description="Discussing gadgets and software",
        )
        self.assertEqual(group.name, "Tech Enthusiasts")
        self.assertEqual(group.description, "Discussing gadgets and software")
        self.assertEqual(group.creator, self.creator)
        self.assertIsNotNone(group.created)
        self.assertIsNotNone(group.modified)
        self.assertIsInstance(group.uuid, uuid.UUID)

    def test_group_str_representation(self):
        """Group __str__ method must return the group name."""
        Group = _get_group_model()
        group = Group.objects.create(creator=self.creator, name="Board Gamers Guild")
        self.assertEqual(str(group), "Board Gamers Guild")

    def test_group_name_unique_constraint(self):
        """Group name must be unique across the application."""
        Group = _get_group_model()
        Group.objects.create(creator=self.creator, name="Duplicate Name")
        with self.assertRaises((IntegrityError, ValidationError)):
            duplicate = Group(creator=self.creator, name="Duplicate Name")
            duplicate.full_clean()
            duplicate.save()

    def test_group_members_many_to_many(self):
        """Group can have multiple members; reverse relation accessible via subscribed_groups."""
        Group = _get_group_model()
        group = Group.objects.create(creator=self.creator, name="Team Alfa")
        group.members.add(self.member1, self.member2)

        self.assertEqual(group.members.count(), 2)
        self.assertIn(self.member1, group.members.all())
        self.assertIn(self.member2, group.members.all())

        # Reverse relation
        self.assertTrue(self.member1.subscribed_groups.filter(id=group.id).exists())
        self.assertTrue(self.member2.subscribed_groups.filter(id=group.id).exists())

    def test_group_get_absolute_url(self):
        """Group get_absolute_url returns /groups/<uuid>/."""
        Group = _get_group_model()
        group = Group.objects.create(creator=self.creator, name="URL Test Group")
        expected_url = f"/groups/{group.uuid}/"
        self.assertEqual(group.get_absolute_url(), expected_url)

    def test_deleting_group_does_not_delete_wishlist(self):
        """Deleting a group unlinks it from wishlists without deleting the wishlist."""
        Group = _get_group_model()
        group = Group.objects.create(creator=self.creator, name="Temporary Group")
        wishlist = Wishlist.objects.create(owner=self.creator, title="Permanent Wishlist")
        wishlist.groups.add(group)

        group.delete()
        self.assertTrue(Wishlist.objects.filter(id=wishlist.id).exists())
        wishlist.refresh_from_db()
        self.assertEqual(wishlist.groups.count(), 0)

    def test_deleting_creator_cascades_to_group(self):
        """Deleting creator user cascades to delete created groups (on_delete=CASCADE)."""
        Group = _get_group_model()
        group = Group.objects.create(creator=self.creator, name="Creator Cascade Group")
        group_id = group.id
        self.creator.delete()
        self.assertFalse(Group.objects.filter(id=group_id).exists())


# ==============================================================================
# 2. Access Control Matrix Tests (can_view_wishlist helper)
# ==============================================================================


class CanViewWishlistAccessMatrixTest(TestCase):
    """Rigorous matrix tests for the can_view_wishlist(user, wishlist) access control helper."""

    def setUp(self):
        self.can_view_wishlist = _get_can_view_wishlist()
        Group = _get_group_model()

        # Users
        self.owner = User.objects.create_user(username="owner_user", password="password123")
        self.member = User.objects.create_user(username="group_member", password="password123")
        self.outsider = User.objects.create_user(username="outsider_user", password="password123")
        self.anonymous = None  # Django AnonymousUser simulated via unauthenticated requests / AnonymousUser()

        # Group
        self.group = Group.objects.create(creator=self.owner, name="Secret Society")
        self.group.members.add(self.owner, self.member)

        # Wishlists
        self.private_shared_list = Wishlist.objects.create(
            owner=self.owner,
            title="Private Shared List",
            is_private=True,
        )
        self.private_shared_list.groups.add(self.group)

        self.private_unshared_list = Wishlist.objects.create(
            owner=self.owner,
            title="Private Unshared List",
            is_private=True,
        )

        self.public_list = Wishlist.objects.create(
            owner=self.owner,
            title="Public List",
            is_private=False,
        )

    def test_owner_can_always_view_own_private_wishlist(self):
        """Owner can view private wishlist whether shared with groups or not."""
        self.assertTrue(self.can_view_wishlist(self.owner, self.private_unshared_list))
        self.assertTrue(self.can_view_wishlist(self.owner, self.private_shared_list))

    def test_owner_can_view_own_public_wishlist(self):
        """Owner can view own public wishlist."""
        self.assertTrue(self.can_view_wishlist(self.owner, self.public_list))

    def test_any_authenticated_user_can_view_public_wishlist(self):
        """Any authenticated user can view a public wishlist (is_private=False)."""
        self.assertTrue(self.can_view_wishlist(self.member, self.public_list))
        self.assertTrue(self.can_view_wishlist(self.outsider, self.public_list))

    def test_anonymous_user_can_view_public_wishlist(self):
        """Anonymous user (AnonymousUser or is_authenticated=False) can view a public wishlist."""
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        self.assertTrue(self.can_view_wishlist(anon, self.public_list))

    def test_group_member_can_view_private_wishlist_exposed_to_their_group(self):
        """Subscribed group member CAN view private wishlist exposed to that group."""
        self.assertTrue(self.can_view_wishlist(self.member, self.private_shared_list))

    def test_non_member_cannot_view_private_wishlist_exposed_to_group(self):
        """User NOT in the group CANNOT view private wishlist exposed to that group."""
        self.assertFalse(self.can_view_wishlist(self.outsider, self.private_shared_list))

    def test_user_in_other_group_cannot_view_private_wishlist(self):
        """User belonging to Group B cannot view private wishlist exposed only to Group A."""
        Group = _get_group_model()
        other_group = Group.objects.create(creator=self.outsider, name="Other Group")
        other_group.members.add(self.outsider)

        self.assertFalse(self.can_view_wishlist(self.outsider, self.private_shared_list))

    def test_non_owner_cannot_view_private_unshared_wishlist(self):
        """Neither members nor outsiders can view private wishlist not exposed to any group."""
        self.assertFalse(self.can_view_wishlist(self.member, self.private_unshared_list))
        self.assertFalse(self.can_view_wishlist(self.outsider, self.private_unshared_list))

    def test_anonymous_user_cannot_view_private_wishlist(self):
        """Anonymous user CANNOT view any private wishlist."""
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        self.assertFalse(self.can_view_wishlist(anon, self.private_shared_list))
        self.assertFalse(self.can_view_wishlist(anon, self.private_unshared_list))

    def test_revoking_group_exposure_immediately_revokes_member_access(self):
        """When owner removes group from wishlist, members immediately lose view access."""
        self.assertTrue(self.can_view_wishlist(self.member, self.private_shared_list))
        self.private_shared_list.groups.remove(self.group)
        self.assertFalse(self.can_view_wishlist(self.member, self.private_shared_list))

    def test_member_unsubscribing_from_group_immediately_loses_access(self):
        """When member unsubscribes from group, they immediately lose access to exposed wishlists."""
        self.assertTrue(self.can_view_wishlist(self.member, self.private_shared_list))
        self.group.members.remove(self.member)
        self.assertFalse(self.can_view_wishlist(self.member, self.private_shared_list))


# ==============================================================================
# 3. HTTP View Access Control Enforcement Tests
# ==============================================================================


class WishlistAccessControlViewTest(TestCase):
    """View-level integration tests enforcing HTTP 200 vs 403 PermissionDenied."""

    def setUp(self):
        Group = _get_group_model()

        self.owner = User.objects.create_user(username="owner", password="password123")
        self.member = User.objects.create_user(username="member", password="password123")
        self.outsider = User.objects.create_user(username="outsider", password="password123")

        self.group = Group.objects.create(creator=self.owner, name="Friends Circle")
        self.group.members.add(self.owner, self.member)

        # Private wishlist exposed to group
        self.shared_private_wishlist = Wishlist.objects.create(
            owner=self.owner,
            title="Shared Secret",
            is_private=True,
        )
        self.shared_private_wishlist.groups.add(self.group)
        self.shared_item = Item.objects.create(
            text="Shared Secret Item",
            wishlist=self.shared_private_wishlist,
        )

        # Private wishlist unshared
        self.unshared_private_wishlist = Wishlist.objects.create(
            owner=self.owner,
            title="Personal Secret",
            is_private=True,
        )
        self.unshared_item = Item.objects.create(
            text="Personal Secret Item",
            wishlist=self.unshared_private_wishlist,
        )

        # Public wishlist
        self.public_wishlist = Wishlist.objects.create(
            owner=self.owner,
            title="Public Wishlist",
            is_private=False,
        )
        self.public_item = Item.objects.create(
            text="Public Item",
            wishlist=self.public_wishlist,
        )

    def test_owner_can_view_own_private_wishlist_http_200(self):
        """Owner receives HTTP 200 and wishlist template when viewing own private wishlist."""
        self.client.force_login(self.owner)
        response = self.client.get(f"/wishlists/{self.shared_private_wishlist.uuid}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wishlist.html")
        self.assertContains(response, "Shared Secret Item")

    def test_group_member_can_view_shared_private_wishlist_http_200(self):
        """Subscribed group member receives HTTP 200 when viewing shared private wishlist."""
        self.client.force_login(self.member)
        response = self.client.get(f"/wishlists/{self.shared_private_wishlist.uuid}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shared Secret Item")

    def test_non_member_viewing_private_wishlist_returns_403(self):
        """Non-member user receives HTTP 403 PermissionDenied when viewing private wishlist."""
        self.client.force_login(self.outsider)
        response = self.client.get(f"/wishlists/{self.shared_private_wishlist.uuid}/")
        self.assertEqual(response.status_code, 403)

    def test_non_member_viewing_unshared_private_wishlist_returns_403(self):
        """User receives HTTP 403 PermissionDenied when viewing unshared private wishlist."""
        self.client.force_login(self.member)
        response = self.client.get(f"/wishlists/{self.unshared_private_wishlist.uuid}/")
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_viewing_private_wishlist_returns_403_or_redirect(self):
        """Unauthenticated user receives HTTP 403 (PermissionDenied) or redirect to login for private wishlist."""
        response = self.client.get(f"/wishlists/{self.shared_private_wishlist.uuid}/")
        self.assertIn(response.status_code, [403, 302])
        if response.status_code == 302:
            self.assertIn("/accounts/login/", response.url)

    def test_public_wishlist_accessible_by_anyone_http_200(self):
        """Public wishlist is accessible (HTTP 200) by anonymous and outsider users."""
        # Outsider user
        self.client.force_login(self.outsider)
        response = self.client.get(f"/wishlists/{self.public_wishlist.uuid}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Item")

        # Anonymous user
        self.client.logout()
        response = self.client.get(f"/wishlists/{self.public_wishlist.uuid}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Item")

    def test_item_detail_view_enforces_wishlist_privacy(self):
        """view_list_item (/wishlists/item/<uuid>/) enforces wishlist privacy rules."""
        # Owner can view item
        self.client.force_login(self.owner)
        resp = self.client.get(f"/wishlists/item/{self.shared_item.uuid}/")
        self.assertEqual(resp.status_code, 200)

        # Subscribed group member can view item
        self.client.force_login(self.member)
        resp = self.client.get(f"/wishlists/item/{self.shared_item.uuid}/")
        self.assertEqual(resp.status_code, 200)

        # Outsider gets 403 on private wishlist item
        self.client.force_login(self.outsider)
        resp = self.client.get(f"/wishlists/item/{self.shared_item.uuid}/")
        self.assertEqual(resp.status_code, 403)

        # Outsider CAN view public wishlist item
        resp = self.client.get(f"/wishlists/item/{self.public_item.uuid}/")
        self.assertEqual(resp.status_code, 200)

    def test_users_lists_view_privacy_filtering(self):
        """view_users_lists (/wishlists/lists/<user_id>/) filters wishlists based on viewer permissions."""
        # Outsider views Owner's lists
        self.client.force_login(self.outsider)
        resp = self.client.get(f"/wishlists/lists/{self.owner.id}/")
        self.assertEqual(resp.status_code, 200)
        lists_in_context = list(resp.context["lists"])
        self.assertIn(self.public_wishlist, lists_in_context)
        self.assertNotIn(self.shared_private_wishlist, lists_in_context)
        self.assertNotIn(self.unshared_private_wishlist, lists_in_context)

        # Group member views Owner's lists
        self.client.force_login(self.member)
        resp = self.client.get(f"/wishlists/lists/{self.owner.id}/")
        self.assertEqual(resp.status_code, 200)
        lists_in_context = list(resp.context["lists"])
        self.assertIn(self.public_wishlist, lists_in_context)
        self.assertIn(self.shared_private_wishlist, lists_in_context)
        self.assertNotIn(self.unshared_private_wishlist, lists_in_context)

        # Owner views their own lists (sees all of them)
        self.client.force_login(self.owner)
        resp = self.client.get(f"/wishlists/lists/{self.owner.id}/")
        self.assertEqual(resp.status_code, 200)
        lists_in_context = list(resp.context["lists"])
        self.assertIn(self.public_wishlist, lists_in_context)
        self.assertIn(self.shared_private_wishlist, lists_in_context)
        self.assertIn(self.unshared_private_wishlist, lists_in_context)


# ==============================================================================
# 4. Group Discovery, Creation & Subscription Views Tests
# ==============================================================================


class GroupDiscoveryAndSubscriptionViewTest(TestCase):
    """View tests for /groups/, /groups/create/, /groups/<uuid>/, subscribe and unsubscribe."""

    def setUp(self):
        Group = _get_group_model()
        self.user1 = User.objects.create_user(username="user_one", password="password123")
        self.user2 = User.objects.create_user(username="user_two", password="password123")

        self.group = Group.objects.create(
            creator=self.user1,
            name="Book Lovers",
            description="Discussing literature and recommendations",
        )
        self.group.members.add(self.user1)

    def test_group_list_requires_authentication(self):
        """Unauthenticated GET /groups/ redirects to login page."""
        response = self.client.get("/groups/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_group_list_view_renders_groups_and_membership_state(self):
        """Authenticated GET /groups/ displays groups, descriptions, and membership status."""
        self.client.force_login(self.user1)
        response = self.client.get("/groups/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Book Lovers")
        self.assertContains(response, "Discussing literature and recommendations")

    def test_create_group_view_requires_authentication(self):
        """Unauthenticated GET/POST /groups/create/ redirects to login."""
        response = self.client.get("/groups/create/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_create_group_get_renders_form(self):
        """Authenticated GET /groups/create/ renders group creation template."""
        self.client.force_login(self.user2)
        response = self.client.get("/groups/create/")
        self.assertEqual(response.status_code, 200)

    def test_create_group_post_creates_group_and_adds_creator_as_member(self):
        """POST /groups/create/ creates Group, assigns creator, and auto-subscribes creator."""
        Group = _get_group_model()
        self.client.force_login(self.user2)
        data = {
            "name": "Photographers Club",
            "description": "DSLR and Mirrorless photography",
        }
        response = self.client.post("/groups/create/", data=data)
        self.assertIn(response.status_code, [200, 302])

        self.assertTrue(Group.objects.filter(name="Photographers Club").exists())
        new_group = Group.objects.get(name="Photographers Club")
        self.assertEqual(new_group.creator, self.user2)
        self.assertTrue(
            new_group.members.filter(id=self.user2.id).exists(),
            "Creator must be automatically added to group members upon creation.",
        )

    def test_create_group_duplicate_name_fails_validation(self):
        """POST /groups/create/ with existing name fails validation and does not duplicate."""
        Group = _get_group_model()
        self.client.force_login(self.user2)
        initial_count = Group.objects.count()
        response = self.client.post("/groups/create/", data={"name": "Book Lovers", "description": "Duplicate"})
        self.assertEqual(Group.objects.count(), initial_count)
        self.assertIn(response.status_code, [200, 400])

    def test_create_group_empty_name_fails_validation(self):
        """POST /groups/create/ with empty name fails validation."""
        Group = _get_group_model()
        self.client.force_login(self.user2)
        initial_count = Group.objects.count()
        response = self.client.post("/groups/create/", data={"name": "", "description": "Empty"})
        self.assertEqual(Group.objects.count(), initial_count)
        self.assertIn(response.status_code, [200, 400])

    def test_group_detail_view_shows_group_details_and_members(self):
        """GET /groups/<uuid>/ renders group details, creator, member count, and shared lists."""
        self.client.force_login(self.user1)
        response = self.client.get(f"/groups/{self.group.uuid}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Book Lovers")
        self.assertContains(response, self.user1.username)

    def test_group_subscribe_post_adds_user_to_members(self):
        """POST /groups/<uuid>/subscribe/ subscribes logged-in user to group."""
        self.client.force_login(self.user2)
        self.assertFalse(self.group.members.filter(id=self.user2.id).exists())

        response = self.client.post(f"/groups/{self.group.uuid}/subscribe/")
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(self.group.members.filter(id=self.user2.id).exists())

    def test_group_unsubscribe_post_removes_user_from_members(self):
        """POST /groups/<uuid>/unsubscribe/ removes logged-in user from group members."""
        self.group.members.add(self.user2)
        self.assertTrue(self.group.members.filter(id=self.user2.id).exists())

        self.client.force_login(self.user2)
        response = self.client.post(f"/groups/{self.group.uuid}/unsubscribe/")
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(self.group.members.filter(id=self.user2.id).exists())


# ==============================================================================
# 5. Wishlist Exposure Management Tests
# ==============================================================================


class WishlistExposureManagementTest(TestCase):
    """Tests for creating wishlists with privacy default and managing group exposure."""

    def setUp(self):
        Group = _get_group_model()
        self.user = User.objects.create_user(username="alice", password="password123")
        self.other_user = User.objects.create_user(username="bob", password="password123")

        self.group1 = Group.objects.create(creator=self.user, name="Family")
        self.group2 = Group.objects.create(creator=self.user, name="Colleagues")
        self.group1.members.add(self.user, self.other_user)

    def test_new_wishlist_view_creates_private_wishlist_by_default(self):
        """Submitting POST /wishlists/new/ with title creates a private wishlist."""
        self.client.force_login(self.user)
        self.client.post("/wishlists/new/", data={"title": "Default Privacy List"})

        new_wishlist = Wishlist.objects.get(title="Default Privacy List", owner=self.user)
        self.assertTrue(
            new_wishlist.is_private,
            "New wishlist created through POST /wishlists/new/ must have is_private=True.",
        )

    def test_owner_can_expose_wishlist_to_groups(self):
        """Wishlist owner can expose wishlist to selected groups."""
        wishlist = Wishlist.objects.create(owner=self.user, title="Holiday Wishlist")
        self.assertEqual(wishlist.groups.count(), 0)

        # Expose to group1
        wishlist.groups.add(self.group1)
        self.assertEqual(wishlist.groups.count(), 1)
        self.assertIn(self.group1, wishlist.groups.all())

        # Subscribed member in group1 can now view it
        can_view = _get_can_view_wishlist()
        self.assertTrue(can_view(self.other_user, wishlist))

    def test_owner_can_unexpose_wishlist_from_group(self):
        """Removing group exposure revokes view rights for group members."""
        wishlist = Wishlist.objects.create(owner=self.user, title="Confidential")
        wishlist.groups.add(self.group1)

        can_view = _get_can_view_wishlist()
        self.assertTrue(can_view(self.other_user, wishlist))

        # Unexpose
        wishlist.groups.remove(self.group1)
        self.assertFalse(can_view(self.other_user, wishlist))

    def test_owner_can_toggle_privacy_to_public(self):
        """Owner can toggle wishlist from private to public, making it accessible to all."""
        wishlist = Wishlist.objects.create(owner=self.user, title="Secret Now Public")
        self.assertTrue(wishlist.is_private)

        wishlist.is_private = False
        wishlist.save()

        can_view = _get_can_view_wishlist()
        self.assertTrue(can_view(self.other_user, wishlist))


# ==============================================================================
# 6. Navbar Link Tests
# ==============================================================================


class GroupsNavbarLinkTest(TestCase):
    """Verify 'Groups' navigation link in lists.base.html."""

    def setUp(self):
        self.user = User.objects.create_user(username="nav_user", password="password123")

    def test_navbar_shows_groups_link_for_authenticated_users(self):
        """Authenticated users see the Groups link in navbar."""
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/groups/"')
        self.assertContains(response, "Groups")

    def test_navbar_does_not_show_groups_link_for_anonymous_users(self):
        """Unauthenticated anonymous users do NOT see the active Groups link in navbar."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # Groups nav-item should only be rendered for authenticated users
        self.assertNotContains(response, 'class="nav-link btn btn-primary btn-md m-1" role="button">Groups<')
