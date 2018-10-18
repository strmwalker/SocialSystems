from django.db import models


# Create your models here.

class Task(models.Model):
    task_id = models.CharField(primary_key=True, max_length=20)
    launches = models.PositiveIntegerField(null=False)
    do_review = models.BooleanField(null=False)

    @property
    def json(self) -> dict:
        return {
            'task_id': self.task_id,
            'launches': self.launches,
            'do_review': self.do_review
        }

    @property
    def price(self) -> int:
        price = 2  # install
        price += 1 * self.launches  # launches
        if self.do_review:
            price += 4  # review
        return price

    @property
    def num_steps(self) -> int:
        steps = 1  # install
        steps += self.launches  # launches
        if self.do_review:
            steps += 1
        if self.launches >= 7:
            steps += 1  # free launch on 7th day to review
        return steps


class User(models.Model):
    user_id = models.CharField(primary_key=True, max_length=20)


class Step(models.Model):
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    day = models.PositiveIntegerField()

    # Okay, this will be ordered as stated: install -> launch -> review
    # we could use numeric codes, but this is more clear in terms of raw queries
    INSTALL = 'I'
    LAUNCH = 'L'
    REVIEW = 'R'
    STEP_CHOICES = (
        (INSTALL, 'install'),
        (LAUNCH, 'launch'),
        (REVIEW, 'review')
    )
    step = models.CharField(max_length=1, choices=STEP_CHOICES)

    TODO = 'TD'
    DONE = 'DN'
    STATUS_CHOICES = (
        (TODO, 'todo'),
        (DONE, 'done')
    )
    status = models.CharField(max_length=2, choices=STEP_CHOICES, default=TODO)

    class Meta:
        ordering = ['day', 'step']

