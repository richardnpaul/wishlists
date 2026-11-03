# Django Imports
from django.contrib.auth.models import User
from django.test import TestCase

# Local
from ..forms import WishListForm
from ..models import Item, Wishlist


class HomePageTest(TestCase):
    def test_uses_home_template(self):
        response = self.client.get("/")
        self.assertTemplateUsed(response, "home.html")

    def test_home_page_uses_wishlist_form(self):
        response = self.client.get("/")
        self.assertIsInstance(response.context["wishlist_form"], WishListForm)


class NewListTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="newlistuser", password="password")
        self.client.force_login(self.user)

    def test_can_save_post_request(self):
        self.client.post("/wishlists/new/", data={"title": "List no.1"})
        self.assertEqual(Wishlist.objects.count(), 1)
        new_wishlist = Wishlist.objects.first()
        self.assertEqual(new_wishlist.title, "List no.1")
        self.assertEqual(new_wishlist.owner, self.user)

    def test_redirects_after_post(self):
        response = self.client.post("/wishlists/new/", data={"title": "List no.1"})
        new_wishlist = Wishlist.objects.first()
        self.assertRedirects(response, f"/wishlists/{new_wishlist.uuid}/edit/")

    def test_for_invalid_input_renders_new_list_template(self):
        response = self.client.post("/wishlists/new/", data={"title": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new_list.html")

    def test_for_invalid_input_passes_form_to_template(self):
        response = self.client.post("/wishlists/new/", data={"title": ""})
        self.assertIsInstance(response.context["wishlist_form"], WishListForm)

    def test_invalid_list_items_arent_saved(self):
        self.client.post("/wishlists/new/", data={"title": ""})
        self.assertEqual(Wishlist.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)

    def test_unauthenticated_user_redirected(self):
        self.client.logout()
        response = self.client.post("/wishlists/new/", data={"title": "List no.1"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


class ListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="listviewuser", password="password")
        self.other_user = User.objects.create_user(username="otheruser", password="password")

    def test_displays_only_items_for_that_list(self):
        correct_wishlist = Wishlist.objects.create(owner=self.user, title="Correct List")
        Item.objects.create(text="Christmas wish no.1", wishlist=correct_wishlist)
        Item.objects.create(text="Christmas wish no.2", wishlist=correct_wishlist)

        other_wishlist = Wishlist.objects.create(owner=self.other_user, title="Other List")
        Item.objects.create(text="Other Christmas wishlist item no.1", wishlist=other_wishlist)
        Item.objects.create(text="Other Christmas wishlist item no.2", wishlist=other_wishlist)

        response = self.client.get(f"/wishlists/{correct_wishlist.uuid}/")

        self.assertContains(response, "Christmas wish no.1")
        self.assertContains(response, "Christmas wish no.2")
        self.assertNotContains(response, "Other Christmas wishlist item no.1")
        self.assertNotContains(response, "Other Christmas wishlist item no.2")

    def test_uses_wishlist_template(self):
        wishlist = Wishlist.objects.create(owner=self.user, title="My List")
        response = self.client.get(f"/wishlists/{wishlist.uuid}/")
        self.assertTemplateUsed(response, "wishlist.html")

    def test_passes_correct_wishlist_to_template(self):
        Wishlist.objects.create(owner=self.user, title="List 1")
        correct_wishlist = Wishlist.objects.create(owner=self.user, title="List 2")
        response = self.client.get(f"/wishlists/{correct_wishlist.uuid}/")
        self.assertEqual(response.context["wishlist"], correct_wishlist)

    def test_can_save_a_post_request_to_create_list_item(self):
        self.client.force_login(self.user)
        correct_wishlist = Wishlist.objects.create(owner=self.user, title="Wishlist")
        self.client.post(
            f"/wishlists/{correct_wishlist.uuid}/item/create/",
            data={"text": "New item for existing wishlist"},
        )

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, "New item for existing wishlist")
        self.assertEqual(new_item.wishlist, correct_wishlist)
