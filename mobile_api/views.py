# Create your views here.
from django.db.models import Count, Q
from django.http import JsonResponse, HttpRequest
from django.urls import reverse

from mobile_api.models import Task, User, Step

# region admin interface
def get_task(request: HttpRequest):

    task_id = request.GET.get('task_id')
    task = Task.objects.get(task_id=task_id)
    return JsonResponse(status=200, data=task.json)


def admin_add_task(request: HttpRequest):
    task_id = request.POST.get('task_id')
    launches = request.POST.get('launches')
    do_review = request.POST.get('do_review')

    try:
        task = Task.objects.create(task_id=task_id, launches=launches, do_review=do_review)
    except Exception:
        # fixme: concrete exception
        return JsonResponse(status=400, data={'result': 'fail'})
    return JsonResponse(status=200, data={'result': 'success'})


def admin_delete_task(request: HttpRequest):
    task_id = request.POST.get('task_id')

    try:
        task = Task.objects.get(task_id=task_id)
    except Task.DoesNotExist:
        return JsonResponse(data={'status': 'Fail. Task does not exist'}, status=400)

    task.delete()
    return JsonResponse(status=200, data={'status': 'success'})


def get_started(task: Task):
    # Users who completed between one and all steps in task
    users = User.objects\
        .annotate(completed_steps=Count('step', filter=Q(step__status=Step.DONE, step__task=task)))\
        .filter(completed_steps__lt=task.num_steps, completed_steps__gt=0)

    return users


def get_done(task: Task):
    # Users who completed all steps in task
    users = User.objects\
        .annotate(completed_steps=Count('step', filter=Q(step_status=Step.DONE, step__task=task)))\
        .filter(completed_steps=task.num_steps)

    return users


def admin_list_tasks(request: HttpRequest):
    tasks = Task.objects.all()

    admin_list = []
    for task in tasks:
        started = get_started(task)
        users_started = [user.user_id for user in started]

        done = get_done(task)
        users_done = [user.user_id for user in done]

        if not users_started and not users_done:
            continue
        admin_list.append(task.json.update(users_started=users_started, users_done=users_done))

    return JsonResponse(data=admin_list)


def create_step_list(task: Task, user: User) -> Step:
    install = Step.objects.create(task=task, user=user, step=Step.INSTALL, day=1)
    for launch in range(task.launches):
        Step.objects.create(task=task, user=user, step=Step.LAUNCH, day=launch+1)
    if task.do_review:
        if task.launches < 7:
            Step.objects.create(task=task, user=user, step=Step.LAUNCH, day=7)
        Step.objects.create(task=task, user=user, step=Step.REVIEW, day=7)

    return install


def user_list_tasks(request: HttpRequest):
    user_id = request.POST.get('user_id')
    user, _ = User.objects.get_or_create(user_id=user_id)

    tasks = Task.objects.all()
    user_task_list = [task.json.update(price=task.price) for task in tasks]
    return JsonResponse(data=user_task_list)


def user_show_task_steps(request: HttpRequest):
    user_id = request.POST.get('user_id')
    task_id = request.POST.get('task_id')

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return JsonResponse(status=400, data={
            'error': 'User does not exist',
            'registration_link': reverse(user_list_tasks(request))
        })

    task = Task.objects.get(task_id=task_id)

    steps = Step.objects.filter(user=user, task=task)
    # get days
    days = set([step.day for step in steps])  # can't figure out how get distinct list
    result = []
    for day in days:
        d = {'day': day}
        day_steps_qs = steps.filter(day=day)
        day_steps = [{'step': step.step, 'status': step.status} for step in day_steps_qs]
        d['steps'] = day_steps
        result.append(d)

    return JsonResponse(status=200, data=result)


def user_complete_task_step(request: HttpRequest):
    task_id = request.POST.get('task_id')
    user_id = request.POST.get('user_id')
    step = request.POST.get('step')
    try:
        task = Task.objects.get(task_id=task_id)
    except Task.DoesNotExist:
        return JsonResponse(status=400, data={'error': 'Task does not exist'})

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return JsonResponse(status=400, data={'error': 'User does not exist'})

    todo = Step.objects.filter(user=user, task=task, status=Step.TODO)
    if not todo:
        done = Step.objects.filter(user=user, task=task, status=Step.DONE).len()
        if task.num_steps <= done:
            return JsonResponse(status=400, data={'error': 'User already completed all steps in task'})
        else:
            todo = create_step_list(task, user)

    if todo.step != step:
        return JsonResponse(status=400, data={'error': 'Wrong step'})

    todo.status = Step.DONE
    todo.save()

    return JsonResponse(status=200, data={'completed': step})
