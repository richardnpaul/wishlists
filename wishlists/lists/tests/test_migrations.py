# Django Imports
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class CleanGroupMembershipsMigrationTest(TransactionTestCase):
    migrate_from = ("lists", "0017_group_invite_version")
    migrate_to = ("lists", "0018_clean_group_memberships")

    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate([target])
        return executor.loader.project_state([target]).apps

    def setUp(self):
        apps = self.migrate(self.migrate_from)
        User = apps.get_model("auth", "User")
        Group = apps.get_model("lists", "Group")
        Wishlist = apps.get_model("lists", "Wishlist")

        self.creator = User.objects.create(username="creator@example.com")
        self.member = User.objects.create(username="member@example.com")
        self.outsider = User.objects.create(username="outsider@example.com")

        # Group whose creator was never added as a member.
        self.group = Group.objects.create(name="Family", creator=self.creator)
        self.group.members.add(self.member)

        self.member_list = Wishlist.objects.create(owner_id=self.member.pk, title="Member list")
        self.member_list.groups.add(self.group)
        # Shared with a group its owner isn't in — allowed by the old privacy form.
        self.outsider_list = Wishlist.objects.create(owner_id=self.outsider.pk, title="Outsider list")
        self.outsider_list.groups.add(self.group)

    def tearDown(self):
        self.migrate(("lists", "0018_clean_group_memberships"))

    def test_creator_added_and_stray_links_removed(self):
        apps = self.migrate(self.migrate_to)
        Group = apps.get_model("lists", "Group")
        Wishlist = apps.get_model("lists", "Wishlist")

        group = Group.objects.get(pk=self.group.pk)
        self.assertTrue(group.members.filter(pk=self.creator.pk).exists())
        self.assertTrue(group.members.filter(pk=self.member.pk).exists())

        self.assertTrue(Wishlist.objects.get(pk=self.member_list.pk).groups.filter(pk=group.pk).exists())
        self.assertFalse(Wishlist.objects.get(pk=self.outsider_list.pk).groups.exists())

    def test_rerunning_is_a_no_op(self):
        self.migrate(self.migrate_to)
        self.migrate(self.migrate_from)  # reverse is a no-op
        apps = self.migrate(self.migrate_to)
        Group = apps.get_model("lists", "Group")
        self.assertEqual(Group.objects.get(pk=self.group.pk).members.count(), 2)
