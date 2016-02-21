#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_lifter
----------------------------------

Tests for `lifter` module.
"""

import random
import sys
import unittest
import mock

import lifter
from lifter import tiny


class TestObject(object):
    def __init__(self, name, **kwargs):
        self.name = name
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.name

class TestBase(unittest.TestCase):
    PARENTS = [
        TestObject(name='parent_1'),
        TestObject(name='parent_2'),
    ]
    OBJECTS = [
        TestObject(name='test_1', order=2, a=1, parent=PARENTS[0], label='alabama', surname='Mister T'),
        TestObject(name='test_2', order=3, a=1, parent=PARENTS[0], label='arkansas', surname='Colonel'),
        TestObject(name='test_3', order=1, a=2, parent=PARENTS[1], label='texas', surname='Lincoln'),
        TestObject(name='test_4', order=4, a=2, parent=PARENTS[1], label='washington', surname='clint'),
    ]

    DICTS = [o.__dict__ for o in OBJECTS]

    def setUp(self):
        self.manager = lifter.load(self.OBJECTS, queryset_class=tiny.TinyQuerySet)
        self.dict_manager = lifter.load(self.DICTS, queryset_class=tiny.TinyQuerySet)

class TestQueries(TestBase):

    def test_default_order(self):
        self.assertEqual(list(self.manager.all()), self.OBJECTS)
        self.assertEqual(list(self.dict_manager.all()), self.DICTS)

    def test_can_get_using_attribute(self):
        self.assertEqual(self.manager.get(tiny.q.name == 'test_1'), self.OBJECTS[0])
        self.assertEqual(self.dict_manager.get(tiny.q.name == 'test_1'), self.DICTS[0])

    def test_can_filter(self):
        self.assertEqual(self.manager.filter(tiny.q.a == 1), self.OBJECTS[:2])

    def test_queryset_is_lazy(self):
        with mock.patch('lifter.tiny.TinyQuerySet._fetch_all') as fetch:
            qs = self.manager.all().filter(tiny.q.order == 3)
            fetch.assert_not_called()
            self.assertEqual(qs._data, [])

        self.assertEqual(qs, [self.OBJECTS[1]])

        with mock.patch('lifter.tiny.TinyQuerySet._fetch_all') as fetch:
            self.assertEqual(qs, [self.OBJECTS[1]])
            self.assertEqual(qs, [self.OBJECTS[1]])
            self.assertEqual(qs, [self.OBJECTS[1]])
            fetch.assert_not_called()


    def test_can_combine_filters(self):
        self.assertEqual(self.manager.filter((tiny.q.a == 1) & (tiny.q.name == 'test_2')), self.OBJECTS[1:2])
        self.assertEqual(self.manager.filter(tiny.q.a == 1).filter(tiny.q.name == 'test_2'), self.OBJECTS[1:2])

        self.assertEqual(self.dict_manager.filter((tiny.q.a == 1) & (tiny.q.name == 'test_2')), self.DICTS[1:2])
        self.assertEqual(self.dict_manager.filter(tiny.q.a == 1).filter(tiny.q.name == 'test_2'), self.DICTS[1:2])

    def test_can_exclude(self):
        self.assertEqual(self.manager.exclude(tiny.q.a == 1), self.OBJECTS[2:])
        self.assertEqual(self.dict_manager.exclude(tiny.q.a == 1), self.DICTS[2:])

    def test_can_combine_exclude(self):
        self.assertEqual(self.manager.exclude(tiny.q.a == 1).exclude(tiny.q.name == 'test_4'), self.OBJECTS[2:3])
        self.assertEqual(self.manager.exclude((tiny.q.a == 2) & (tiny.q.name == 'test_4')), self.OBJECTS[:3])

        self.assertEqual(self.dict_manager.exclude(tiny.q.a == 1).exclude(tiny.q.name == 'test_4'), self.DICTS[2:3])
        self.assertEqual(self.dict_manager.exclude((tiny.q.a == 2) & (tiny.q.name == 'test_4')), self.DICTS[:3])

    def test_related_lookups(self):
        self.assertEqual(self.manager.filter(tiny.q.parent.name == 'parent_1'), self.OBJECTS[:2])
        self.assertEqual(self.manager.exclude(tiny.q.parent.name == 'parent_1'), self.OBJECTS[2:])
        self.assertEqual(self.manager.get((tiny.q.parent.name == 'parent_1') & (tiny.q.order == 2)), self.OBJECTS[0])

        self.assertEqual(self.dict_manager.filter(tiny.q.parent.name == 'parent_1'), self.DICTS[:2])
        self.assertEqual(self.dict_manager.exclude(tiny.q.parent.name == 'parent_1'), self.DICTS[2:])
        self.assertEqual(self.dict_manager.get((tiny.q.parent.name == 'parent_1') & (tiny.q.order == 2)), self.DICTS[0])


    def test_exception_raised_on_missing_attr(self):
        with self.assertRaises(ValueError):
            list(self.manager.filter(tiny.q.x == "y"))
        with self.assertRaises(ValueError):
            list(self.dict_manager.filter(tiny.q.x == "y"))

    def test_can_count(self):
        self.assertEqual(self.manager.filter(tiny.q.a == 1).count(), 2)

        self.assertEqual(self.dict_manager.filter(tiny.q.a == 1).count(), 2)

    def test_first(self):
        self.assertIsNone(self.manager.filter(tiny.q.a == 123).first())
        self.assertIsNotNone(self.manager.filter(tiny.q.a == 1).first())

        self.assertIsNone(self.dict_manager.filter(tiny.q.a == 123).first())
        self.assertIsNotNone(self.dict_manager.filter(tiny.q.a == 1).first())

    def test_last(self):
        self.assertIsNone(self.manager.filter(tiny.q.a == 123).last())
        self.assertIsNotNone(self.manager.filter(tiny.q.a == 1).last())

        self.assertIsNone(self.dict_manager.filter(tiny.q.a == 123).last())
        self.assertIsNotNone(self.dict_manager.filter(tiny.q.a == 1).last())

    def test_ordering(self):
        self.assertEqual(self.manager.order_by(tiny.p.order, tiny.Order.ASC)[:2], [self.OBJECTS[2], self.OBJECTS[0]])
        self.assertEqual(self.manager.order_by(tiny.p.order, tiny.Order.DESC)[:2], [self.OBJECTS[3], self.OBJECTS[1]])

        self.assertEqual(self.dict_manager.order_by(tiny.p.order, tiny.Order.ASC)[:2], [self.DICTS[2], self.DICTS[0]])
        self.assertEqual(self.dict_manager.order_by(tiny.p.order, tiny.Order.DESC)[:2], [self.DICTS[3], self.DICTS[1]])

    def test_random_ordering(self):
        is_py3 = sys.version_info >= (3, 2)

        random.seed(0)
        random_ordered_0 = self.dict_manager.order_by('?')[:2]
        if is_py3:
            self.assertEqual(random_ordered_0, [self.DICTS[3], self.DICTS[1]])
        else:
            self.assertEqual(random_ordered_0, [self.DICTS[3], self.DICTS[2]])
        random.seed(1)
        random_ordered_1 = self.dict_manager.order_by('?')[:2]
        if is_py3:
            self.assertEqual(random_ordered_1, [self.DICTS[1], self.DICTS[2]])
        else:
            self.assertEqual(random_ordered_1, [self.DICTS[0], self.DICTS[2]])

        self.assertNotEqual(random_ordered_0, random_ordered_1)

    def test_exists(self):
        self.assertFalse(self.manager.filter(tiny.q.a == 123).exists())
        self.assertTrue(self.manager.filter(tiny.q.a == 1).exists())

        self.assertFalse(self.dict_manager.filter(tiny.q.a == 123).exists())
        self.assertTrue(self.dict_manager.filter(tiny.q.a == 1).exists())

    def test_get_raise_exception_on_multiple_objects_returned(self):
        with self.assertRaises(lifter.MultipleObjectsReturned):
            self.manager.get(tiny.q.a == 1)

        with self.assertRaises(lifter.MultipleObjectsReturned):
            self.dict_manager.get(tiny.q.a == 1)

    def test_get_raise_exception_on_does_not_exist(self):
        with self.assertRaises(lifter.DoesNotExist):
            self.manager.get(tiny.q.a == 123)

        with self.assertRaises(lifter.DoesNotExist):
            self.dict_manager.get(tiny.q.a == 123)

    def test_can_filter_using_callable(self):
        self.assertEqual(self.manager.filter(tiny.q.order.test(lambda v: v in [1, 3])), [self.OBJECTS[1], self.OBJECTS[2]])

        self.assertEqual(self.dict_manager.filter(tiny.q.order.test(lambda v: v in [1, 3])), [self.DICTS[1], self.DICTS[2]])

    def test_values(self):
        expected = [
            {'order': 2},
            {'order': 3},
        ]
        self.assertEqual(self.manager.filter(tiny.q.a == 1).values(tiny.p.order), expected)
        self.assertEqual(self.dict_manager.filter(tiny.q.a == 1).values(tiny.p.order), expected)

        expected = [
            {'order': 2, 'a': 1},
            {'order': 3, 'a': 1},
        ]
        self.assertEqual(self.manager.filter(tiny.q.a == 1).values(tiny.p.order, tiny.p.a), expected)
        self.assertEqual(self.dict_manager.filter(tiny.q.a == 1).values(tiny.p.order, tiny.p.a), expected)

    def test_values_list(self):
        expected = [2, 3]
        self.assertEqual(self.manager.filter(tiny.q.a == 1).values_list(tiny.p.order, flat=True), expected)
        self.assertEqual(self.dict_manager.filter(tiny.q.a == 1).values_list(tiny.p.order, flat=True), expected)

        expected = [
            (2, 1),
            (3, 1),
        ]
        self.assertEqual(self.manager.filter(tiny.q.a == 1).values_list(tiny.p.order, tiny.p.a), expected)
        self.assertEqual(self.dict_manager.filter(tiny.q.a == 1).values_list(tiny.p.order, tiny.p.a), expected)

    def test_distinct(self):
        self.assertEqual(self.manager.values_list(tiny.p.a, flat=True), [1, 1, 2, 2])
        self.assertEqual(self.manager.values_list(tiny.p.a, flat=True).distinct(), [1, 2])
        self.assertEqual(self.manager.values_list(tiny.p.parent, flat=True).distinct(), self.PARENTS)
    #
    # def test_can_check_nested_iterables(self):
    #     users = [
    #         {
    #             'name': 'Kurt',
    #             'tags': [
    #                 {'name': 'nice'},
    #                 {'name': 'friendly'},
    #             ]
    #         },
    #         {
    #             'name': 'Bill',
    #             'tags': [
    #                 {'name': 'friendly'},
    #             ]
    #         },
    #     ]
    #     manager = lifter.load(users)
    #     self.assertNotIn(users[1], manager.filter(tags__name='nice'))
    #     self.assertRaises(ValueError, manager.filter, tags__x='y')
    #
    #     companies = [
    #         {
    #             'name': 'blackbooks',
    #             'employees': [
    #                 {
    #                     'name': 'Manny',
    #                     'tags': [
    #                         {'name': 'nice'},
    #                         {'name': 'friendly'},
    #                     ]
    #                 }
    #             ]
    #         },
    #         {
    #             'name': 'community',
    #             'employees': [
    #                 {
    #                     'name': 'Britta',
    #                     'tags': [
    #                         {'name': 'activist'},
    #                     ]
    #                 }
    #             ]
    #         }
    #     ]
    #     manager = lifter.load(companies)
    #     self.assertNotIn(companies[1], manager.filter(employees__tags__name='friendly'))
#
# class TestLookups(TestBase):
#     def test_gt(self):
#         self.assertEqual(self.manager.filter(order=lifter.lookups.gt(3)), [self.OBJECTS[3]])
#
#     def test_gte(self):
#         self.assertEqual(self.manager.filter(order=lifter.lookups.gte(3)), [self.OBJECTS[1], self.OBJECTS[3]])
#
#     def test_lt(self):
#         self.assertEqual(self.manager.filter(order=lifter.lookups.lt(3)), [self.OBJECTS[0], self.OBJECTS[2]])
#
#     def test_lte(self):
#         self.assertEqual(self.manager.filter(order=lifter.lookups.lte(3)), [self.OBJECTS[0], self.OBJECTS[1], self.OBJECTS[2]])
#
#     def test_startswith(self):
#         self.assertEqual(self.manager.filter(label=lifter.lookups.startswith('a')), [self.OBJECTS[0], self.OBJECTS[1]])
#
#     def test_endswith(self):
#         self.assertEqual(self.manager.filter(label=lifter.lookups.endswith('s')), [self.OBJECTS[1], self.OBJECTS[2]])
#
#     def test_value_in(self):
#         self.assertEqual(self.manager.filter(label=lifter.lookups.value_in(['alabama', 'arkansas'])), [self.OBJECTS[0], self.OBJECTS[1]])
#
#     def test_range(self):
#         self.assertEqual(self.manager.filter(order=lifter.lookups.value_range(2, 3)), [self.OBJECTS[0], self.OBJECTS[1]])
#
#     def test_istartswith(self):
#         self.assertEqual(self.manager.filter(surname=lifter.lookups.istartswith('c')), [self.OBJECTS[1], self.OBJECTS[3]])
#
#     def test_iendswith(self):
#         self.assertEqual(self.manager.filter(surname=lifter.lookups.iendswith('t')), [self.OBJECTS[0], self.OBJECTS[3]])
#
#     def test_contains(self):
#         self.assertEqual(self.manager.filter(surname=lifter.lookups.contains('Lin')), [self.OBJECTS[2]])
#
#     def test_icontains(self):
#         self.assertEqual(self.manager.filter(surname=lifter.lookups.icontains('lin')), [self.OBJECTS[2], self.OBJECTS[3]])
#
# class TestAggregation(TestBase):
#     def test_sum(self):
#         self.assertEqual(self.manager.aggregate(lifter.Sum('a')), {'a__sum': 6})
#         self.assertEqual(self.manager.aggregate(total=lifter.Sum('a')), {'total': 6})
#
#     def test_min(self):
#         self.assertEqual(self.manager.aggregate(lifter.Min('a')), {'a__min': 1})
#
#     def test_max(self):
#         self.assertEqual(self.manager.aggregate(lifter.Max('a')), {'a__max': 2})
#
#     def test_avg(self):
#         self.assertEqual(self.manager.aggregate(lifter.Avg('a')), {'a__avg': 1.5})
#
#     def test_flat(self):
#         self.assertEqual(self.manager.aggregate(lifter.Avg('a'), flat=True), [1.5])

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())