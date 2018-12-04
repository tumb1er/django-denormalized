from django.db.models import Sum
from django.test import TestCase

from testproject.testapp import models


class CountTestCase(TestCase):
    def setUp(self):
        self.group = models.Group.objects.create()
        self.member = models.Member.objects.create(group=self.group)

    def assertMembersCount(self, group: models.Group = None):
        group = group or self.group
        group.refresh_from_db()
        expected = group.member_set.filter(active=True).count()
        self.assertEqual(group.members_count, expected)

    def assertPointsSum(self, group: models.Group = None):
        group = group or self.group
        group.refresh_from_db()
        expected = group.member_set.aggregate(s=Sum('points'))['s'] or 0
        self.assertEqual(group.points_sum, expected)

    def test_initial_value(self):
        """ After setUp group has single member."""
        self.assertMembersCount()

    def test_increment_on_new(self):
        """ Creating new member increments counter."""
        models.Member.objects.create(group=self.group)

        self.assertMembersCount()

    def test_decrement_on_delete(self):
        """ Deleting member decrements counter."""
        self.member.delete()

        self.assertMembersCount()

    def test_increment_on_change(self):
        """ Changing foreign key increments counter."""
        group = models.Group.objects.create()
        self.member.group = group

        self.member.save()

        self.assertMembersCount()

    def test_decrement_on_change(self):
        """ Changing foreign key decrements counter for old value."""
        group = models.Group.objects.create()
        self.member.group = group

        self.member.save()

        self.assertMembersCount()

    def test_denormalize(self):
        """ Count can be refreshed from db."""
        self.group.members_count = None

        self.group.member_set.denormalize()

        self.assertMembersCount()

    def test_denormalize_with_conditions(self):
        """ Count can be refreshed from db."""
        models.Member.objects.create(group=self.group, active=False)
        self.group.members_count = None

        self.group.member_set.denormalize()

        self.assertMembersCount()

    def test_increment_sum_aggregate(self):
        """ Sum is incremented properly."""
        self.member.points = 10

        self.member.save()

        self.assertPointsSum()

    def test_decrement_sum_aggregate(self):
        """ Sum is decremented properly."""
        models.Member.objects.all().update(points=10)
        models.Group.objects.all().update(points_sum=10)
        self.member.refresh_from_db()

        self.member.delete()

        self.assertPointsSum()

    def test_decrement_on_became_not_suitable(self):
        """ If object is not suitable anymore, decrement."""
        self.member.active = False

        self.member.save()

        self.assertMembersCount()

    def test_increment_on_become_suitable(self):
        """ If object became suitable, increment."""
        member = models.Member.objects.create(active=False, group=self.group)

        self.assertMembersCount()

        member.active = True
        member.save()

        self.assertMembersCount()

    def test_no_dirty_increments(self):
        """
        Increment respects operations performed in db by another processes.
        """
        group = models.Group.objects.get(pk=self.group.pk)
        models.Member.objects.create(group=group)

        models.Member.objects.create(group=self.group)

        self.assertMembersCount()

    def test_previous_state_reset_on_save(self):
        """ Save resets saved previous state for tracked object."""
        member = models.Member.objects.create(group=self.group, active=False)

        member.active = True
        member.save()

        self.assertMembersCount()

        member.active = False
        member.save()

        self.assertMembersCount()

    def test_handle_nullable_foreign_key(self):
        """ Nullable foreign key is skipped for trackers."""
        models.Member.objects.create(group=None)

        self.assertMembersCount()

    def test_foreign_key_become_null(self):
        """ If foreign key became null, decrement."""
        self.member.group = None
        self.member.save()

        self.assertMembersCount()

    def test_foreign_key_become_not_null(self):
        """ If foreign key became not null, increment."""
        member = models.Member.objects.create(group=None)

        member.group = self.group
        member.save()

        self.assertMembersCount()

    def test_collector_delete(self):
        """ Cascade delete works correctly."""
        models.Member.objects.create(active=False, group=self.group)

        self.group.delete()

        self.assertEqual(models.Group.objects.count(), 0)

    def test_save_not_affects_counters(self):
        """
        Saving fields not related to denormalized values not affects counts.
        """
        self.member.save()

        self.assertMembersCount()
