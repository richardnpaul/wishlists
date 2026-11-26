from django.db import migrations


def clean_group_memberships(apps, schema_editor):
    """Bring existing rows in line with the invite-only group rules.

    - Every group's creator is a member.
    - A wishlist is only shared with groups its owner belongs to.
    Idempotent: re-running changes nothing.
    """
    Group = apps.get_model("lists", "Group")
    Wishlist = apps.get_model("lists", "Wishlist")

    creators_added = 0
    for group in Group.objects.all():
        if not group.members.filter(pk=group.creator_id).exists():
            group.members.add(group.creator_id)
            creators_added += 1

    links_removed = 0
    for wishlist in Wishlist.objects.filter(groups__isnull=False).distinct():
        stray = wishlist.groups.exclude(members=wishlist.owner_id)
        count = stray.count()
        if count:
            wishlist.groups.remove(*stray)
            links_removed += count

    if creators_added or links_removed:
        print(
            f"\n    clean_group_memberships: added {creators_added} creator(s) to their groups, "
            f"removed {links_removed} wishlist/group link(s) where the owner wasn't a member"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("lists", "0017_group_invite_version"),
    ]

    operations = [
        migrations.RunPython(clean_group_memberships, migrations.RunPython.noop),
    ]
