from django.test import TestCase
import pytest

from mobile_api.models import Task, User, Step
from mobile_api.views import create_step_list


class TestAdminViews(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create(user_id='vasya')
        User.objects.create(user_id='petya')
        User.objects.create(user_id='vova')

        Task.objects.create(task_id='com.app.first', launches=2, do_review=True)

    @pytest.mark.django_db
    def test_add_task(self):
        response = self.client.post('/admin/add', data={'task_id': 'com.app.second', 'launches': 3, 'do_review': True})
        assert response.status_code == 200
        assert response.json()['result'] == 'success'
        task = Task.objects.get(task_id='com.app.second')
        assert task.launches == 3

        response = self.client.post('/admin/add', data={'task_id': 'com.app.first', 'launches': 3, 'do_review': True})
        assert response.status_code == 400
        assert response.json()['result'] == 'fail'

    def add_task(self, task_id, launches, do_review):
        return Task.objects.create(task_id=task_id, launches=launches, do_review=do_review)

    @pytest.mark.django_db
    def test_list_tasks(self):
        task = self.add_task('first', 2, False)
        user = User.objects.get(user_id='vasya')

        install = create_step_list(task, user)
        install.status = Step.DONE
        install.save()

        user = User.objects.get(user_id='petya')
        create_step_list(task, user)
        user = User.objects.get(user_id='vova')
        create_step_list(task, user)

        steps = Step.objects.filter(user__user_id__in=['petya', 'vova'])
        assert steps.count() == task.num_steps * 2
        for step in steps:
            step.status = Step.DONE
            step.save()

        response = self.client.get('/admin/list')
        assert response.json() == [
            {
                'task_id': 'first',
                'launches': 2,
                'do_review': False,
                'users_started': ['vasya'],
                'users_done': ['petya', 'vova']
            }
        ]

    @pytest.mark.django_db
    def test_delete_task(self):
        self.add_task('delete', 0, False)
        response = self.client.post('/admin/delete', data={'task_id': 'delete'})
        assert response.json()['status'] == 'success'

        assert Task.objects.filter(task_id='delete').count() == 0

        response = self.client.post('/admin/delete', data={'task_id': 'delete'})
        assert response.status_code == 400


class TestUserViews(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create(user_id='vasya')
        User.objects.create(user_id='petya')
        User.objects.create(user_id='vova')

        Task.objects.create(task_id='com.app.first', launches=1, do_review=False)

    def test_list_tasks(self):
        response = self.client.post('/user/list', data={'user_id': 'vasya'})
        assert response.json() == [
            {
                'task_id': 'com.app.first',
                'price': 3,
                'status': 'todo'
            }
        ]

    def test_show_task_steps(self):
        task = Task.objects.create(task_id='com.app.second', launches=2, do_review=False)
        user = User.objects.get(user_id='vasya')
        install = create_step_list(task, user)
        install.status = Step.DONE
        install.save()
        response = self.client.post('/user/task', data={'task_id': 'com.app.second', 'user_id': 'vasya'})
        assert response.json() == [
            {
                'day': 1,
                'steps': [
                    {
                        'step': 'install',
                        'status': 'done'
                    },
                    {
                        'step': 'launch',
                        'status': 'todo'
                    }
                ]
            },
            {
                'day': 2,
                'steps': [
                    {
                        'step': 'launch',
                        'status': 'todo'
                    }
                ]
            }
        ]

    def test_show_task_steps_error(self):
        response = self.client.post('/user/task', data={'task_id': 'com.app.second', 'user_id': 'vasya'})
        assert response.status_code == 400

        response = self.client.post('/user/task', data={'task_id': 'com.app.first', 'user_id': 'petechka'})
        assert response.status_code == 400

    def test_complete_task_step(self):
        Task.objects.create(task_id='com.app.third', launches=2, do_review=True)
        response = self.client.post('/user/do',
                                    data={'task_id': 'com.app.third', 'user_id': 'vasya', 'step': 'launch'})
        assert response.status_code == 400

        response = self.client.post('/user/do',
                                    data={'task_id': 'com.app.third', 'user_id': 'vasya', 'step': 'install'})
        assert response.status_code == 200
        assert response.json() == {'completed': 'install'}

        response = self.client.post('/user/do',
                                    data={'task_id': 'com.app.third', 'user_id': 'vasya', 'step': 'launch'})
        assert response.status_code == 200
        assert response.json() == {'completed': 'launch'}

        response = self.client.post('/user/do',
                                    data={'task_id': 'com.app.third', 'user_id': 'vasya', 'step': 'install'})
        assert response.status_code == 400
        assert response.json() == {'error': 'Wrong step, expected launch, got install'}

        response = self.client.post('/user/do',
                                    data={'task_id': 'com.app.third', 'user_id': 'vasya', 'step': 'launch'})
        assert response.status_code == 200
        assert response.json() == {'completed': 'launch'}

        response = self.client.post('/user/do',
                                    data={'task_id': 'com.app.third', 'user_id': 'vasya', 'step': 'review'})
        assert response.status_code == 400

        response = self.client.post('/user/do',
                                    data={'task_id': 'com.app.third', 'user_id': 'vasya', 'step': 'launch'})
        response = self.client.post('/user/do',
                                    data={'task_id': 'com.app.third', 'user_id': 'vasya', 'step': 'review'})

        assert response.status_code == 200
        assert response.json() == {'completed': 'review'}

        response = self.client.post('/user/do',
                                    data={'task_id': 'com.app.third', 'user_id': 'vasya', 'step': 'install'})
        assert response.status_code == 400
        assert response.json() == {'error': 'User already completed all steps in task'}
