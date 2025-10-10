import os
from uuid import uuid4

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nome_completo = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome_completo']

    def __str__(self):
        return self.email


class Categoria(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


def validar_tamanho_arquivo(arquivo):
    if arquivo.size > 2 * 1024 * 1024:  # 2 MB
        raise ValidationError("O arquivo excede o tamanho máximo de 2MB!")


def validar_tipo_arquivo(arquivo):
    ext_permitidas = ['pdf', 'jpg', 'jpeg', 'png']
    ext = arquivo.name.split('.')[-1].lower()
    if ext not in ext_permitidas:
        raise ValidationError("Tipo de arquivo não permitido! Permitidos: PDF, JPG, PNG.")


def upload_path_usuario(instance, filename):
    ext = filename.split('.')[-1]
    novo_nome = f"{uuid4().hex}.{ext}"
    return os.path.join('uploads', f'usuario_{instance.usuario.id}', novo_nome)


class DocumentoManager(models.Manager):
    def verificados(self):
        return self.filter(verificado=True)


class Documento(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    titulo = models.CharField(max_length=200)
    arquivo = models.FileField(
        upload_to=upload_path_usuario,
        validators=[validar_tamanho_arquivo, validar_tipo_arquivo]
    )
    data_envio = models.DateTimeField(auto_now_add=True)
    verificado = models.BooleanField(default=False)

    objects = DocumentoManager()

    def __str__(self):
        return f"{self.titulo} - {self.usuario.email}"
