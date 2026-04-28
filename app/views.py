import logging
import time

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView

from .decorators import log_upload_usuario_method
from .forms import DocumentoForm
from .models import Documento

logger = logging.getLogger('myapp')


def log_request_duration(view_func):
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        response = view_func(request, *args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"View {view_func.__name__}: {duration:.3f}s")
        return response
    return wrapper


@method_decorator(log_upload_usuario_method, name='form_valid')
class DocumentoCreateView(LoginRequiredMixin, CreateView):
    model = Documento
    form_class = DocumentoForm
    template_name = 'documentos/form.html'
    success_url = reverse_lazy('lista_documentos')

    def form_valid(self, form):
        documento = form.save(commit=False)
        documento.usuario = self.request.user
        documento.save()
        messages.success(self.request, "Documento enviado com sucesso!")
        logger.info(f"Documento '{documento.arquivo.name}' enviado por {self.request.user.email}")
        return super().form_valid(form)


@method_decorator(log_request_duration, name='dispatch')
class DocumentoListView(LoginRequiredMixin, ListView):
    model = Documento
    template_name = 'documentos/lista.html'
    context_object_name = 'documentos'

    def get_queryset(self):
        return Documento.objects.filter(usuario=self.request.user)

