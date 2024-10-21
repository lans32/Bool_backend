from django.db import models
from django.contrib.auth.models import User

class OperationManager(models.Manager):
    def get_one_operation(self, operation_id):
        return self.get(id=operation_id)

class Operation(models.Model):
    STATUS_CHOICES = [
        ("a", "Active"), 
        ("d", "Deleted")
    ]
    name = models.CharField(max_length=255)
    operator_name = models.TextField()
    description = models.TextField()
    photo = models.URLField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=7, default='a')
    value_0 = models.BooleanField(default=False)
    value_A = models.BooleanField(default=False)
    value_B = models.BooleanField(default=False)
    value_AB = models.BooleanField(default=False)

    objects = OperationManager()

    def __str__(self):
        return self.name

class AskManager(models.Manager):
    def get_one_ask(self, ask_id):
        return self.get(id=ask_id)

    def get_total_asks(self, ask):
        return AskOperation.objects.filter(ask=ask).count()

    def get_total_operations(self, ask):
        return AskOperation.objects.filter(ask=ask).count()


class Ask(models.Model):
    STATUS_CHOICES = [
        ('dr', "Draft"),
        ('del', "Deleted"), 
        ('f', "Formed"), 
        ('c', "Completed"), 
        ('r', "Rejected")
    ]
    first_operand = models.BooleanField(default=False)
    status = models.CharField(choices=STATUS_CHOICES, max_length=9, default='dr')
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(User, related_name='asks_created', on_delete=models.SET_NULL, null=True)
    moderator = models.ForeignKey(User, related_name='asks_moderated', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator'], condition=models.Q(status='draft'), name='unique_draft_per_user')
        ]

    objects = AskManager()

    def __str__(self):
        return str(self.id)

class AskOperation(models.Model):
    ask = models.ForeignKey(Ask, on_delete=models.CASCADE)
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE)
    second_operand = models.BooleanField(default=False)
    result = models.BooleanField(null=True, default=None)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ask', 'operation'], name='unique_ask_operation')
        ]
    
    def calculate_result(self):
        first_operand = self.ask.first_operand
        second_operand = self.second_operand

        if first_operand == 0 and second_operand == 0:
            self.result = self.operation.value_0
        elif first_operand == 1 and second_operand == 0:
            self.result = self.operation.value_A
        elif first_operand == 0 and second_operand == 1:
            self.result = self.operation.value_B
        elif first_operand == 1 and second_operand == 1:
            self.result = self.operation.value_AB

        self.save()