from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager

class NewUserManager(UserManager):
    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self.db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(("email адрес"), unique=True)
    password = models.CharField(verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        verbose_name=('groups')
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text=('Specific permissions for this user.'),
        verbose_name=('user permissions')
    )

    USERNAME_FIELD = 'email'

    objects = NewUserManager()

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
    description = models.TextField(null=True)
    photo = models.URLField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=7, default='a')
    value_0 = models.BooleanField(default=False, null=True)
    value_A = models.BooleanField(default=False, null=True)
    value_B = models.BooleanField(default=False, null=True)
    value_AB = models.BooleanField(default=False, null=True)

    objects = OperationManager()

    def __str__(self):
        return self.name

class AskManager(models.Manager):
    def get_one_ask(self, ask_id):
        return self.get(id=ask_id)

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
    first_operand = models.BooleanField(default=False, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=9, default='dr')
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(CustomUser, related_name='asks_created', on_delete=models.PROTECT)
    moderator = models.ForeignKey(CustomUser, related_name='asks_moderated', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator'], condition=models.Q(status='dr'), name='unique_draft_per_user')
        ]

    objects = AskManager()

    def __str__(self):
        return str(self.id)

class AskOperation(models.Model):
    ask = models.ForeignKey(Ask, on_delete=models.CASCADE)
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE)
    second_operand = models.BooleanField(default=False, null=True)
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