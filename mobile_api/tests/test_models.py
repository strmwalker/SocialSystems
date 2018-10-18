from unittest import TestCase

import pytest

from mobile_api.models import Task, User, Step
from mobile_api.views import create_step_list


class TestTask(TestCase):

    def test_json(self):
        task = Task(task_id='foo', launches=3, do_review=True)
        self.assertEqual(task.json,
                         {
                             'task_id': 'foo',
                             'launches': 3,
                             'do_review': True
                         })

    def test_price(self):
        task = Task(task_id='foo', launches=1, do_review=False)
        self.assertEqual(task.price, 3)

        task = Task(task_id='foo', launches=2, do_review=False)
        self.assertEqual(task.price, 4)

        task = Task(task_id='foo', launches=7, do_review=True)
        self.assertEqual(task.price, 13)

        task = Task(task_id='foo', launches=5, do_review=True)
        self.assertEqual(task.price, 11)

    def test_num_steps(self):
        task = Task(task_id='foo', launches=1, do_review=False)
        self.assertEqual(task.num_steps, 2)

        task = Task(task_id='foo', launches=2, do_review=False)
        self.assertEqual(task.num_steps, 3)

        task = Task(task_id='foo', launches=7, do_review=True)
        self.assertEqual(task.num_steps, 9)

        task = Task(task_id='foo', launches=5, do_review=True)
        self.assertEqual(task.num_steps, 8)


class TestStep(TestCase):

    @pytest.mark.django_db
    def test_ordering(self):
        task = Task.objects.create(task_id='foo', launches=2, do_review=True)
        user = User.objects.create(user_id='bar')
        create_step_list(task, user)

        steps = Step.objects.all()
        days = [step.day for step in steps]
        self.assertEqual(days, [1, 1, 2, 7, 7])
        actions = [step.step for step in steps]
        self.assertEqual(actions, [Step.INSTALL, Step.LAUNCH, Step.LAUNCH, Step.LAUNCH, Step.REVIEW])

        task = Task.objects.create(task_id='bar', launches=5, do_review=True)
        create_step_list(task, user)
        steps = Step.objects.filter(task=task, user=user)
        days = [step.day for step in steps]
        self.assertEqual(days, [1, 1, 2, 3, 4, 5, 7, 7])
