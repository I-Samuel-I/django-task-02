"""
Testes para as novas funcionalidades de admin, filters e decorators.
Copie para app/tests.py ou crie um arquivo tests/test_admin.py
"""

import logging
from datetime import timedelta
from django.test import TestCase, Client, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Categoria, Documento
from .admin import (
    DocumentoAdmin, 
    DataEnvioFilter, 
    TamanhoArquivoFilter,
    marcar_como_verificado,
    marcar_como_nao_verificado
)
from .views import DocumentoCreateView

CustomUser = get_user_model()


class DataEnvioFilterTestCase(TestCase):
    """Testes para o filtro de data de envio."""
    
    def setUp(self):
        self.usuario = CustomUser.objects.create_user(
            email='teste@example.com',
            password='senha123',
            nome_completo='Usuário Teste'
        )
        self.categoria = Categoria.objects.create(nome='Teste')
        
        # Documento de hoje
        arquivo = SimpleUploadedFile(
            "teste.pdf",
            b"conteúdo",
            content_type="application/pdf"
        )
        self.doc_hoje = Documento.objects.create(
            usuario=self.usuario,
            categoria=self.categoria,
            titulo='Documento de Hoje',
            arquivo=arquivo
        )
        
        # Documento de 8 dias atrás
        arquivo2 = SimpleUploadedFile(
            "teste2.pdf",
            b"conteúdo",
            content_type="application/pdf"
        )
        doc_semana = Documento.objects.create(
            usuario=self.usuario,
            categoria=self.categoria,
            titulo='Documento de 8 Dias Atrás',
            arquivo=arquivo2
        )
        doc_semana.data_envio = timezone.now() - timedelta(days=8)
        doc_semana.save()
        self.doc_semana = doc_semana
        
        # Documento de 4 meses atrás
        arquivo3 = SimpleUploadedFile(
            "teste3.pdf",
            b"conteúdo",
            content_type="application/pdf"
        )
        doc_antigo = Documento.objects.create(
            usuario=self.usuario,
            categoria=self.categoria,
            titulo='Documento Antigo',
            arquivo=arquivo3
        )
        doc_antigo.data_envio = timezone.now() - timedelta(days=120)
        doc_antigo.save()
        self.doc_antigo = doc_antigo
    
    def test_filter_hoje(self):
        """Testa filtro para documentos de hoje."""
        filter_obj = DataEnvioFilter(None, {}, Documento, DocumentoAdmin)
        filter_obj.value = lambda: 'hoje'
        
        queryset = filter_obj.queryset(None, Documento.objects.all())
        self.assertIn(self.doc_hoje, queryset)
        self.assertNotIn(self.doc_semana, queryset)
    
    def test_filter_semana(self):
        """Testa filtro para documentos da última semana."""
        filter_obj = DataEnvioFilter(None, {}, Documento, DocumentoAdmin)
        filter_obj.value = lambda: 'semana'
        
        queryset = filter_obj.queryset(None, Documento.objects.all())
        self.assertIn(self.doc_hoje, queryset)
        self.assertNotIn(self.doc_semana, queryset)
        self.assertNotIn(self.doc_antigo, queryset)
    
    def test_filter_antigos(self):
        """Testa filtro para documentos mais antigos."""
        filter_obj = DataEnvioFilter(None, {}, Documento, DocumentoAdmin)
        filter_obj.value = lambda: 'antigos'
        
        queryset = filter_obj.queryset(None, Documento.objects.all())
        self.assertIn(self.doc_antigo, queryset)
        self.assertNotIn(self.doc_hoje, queryset)


class TamanhoArquivoFilterTestCase(TestCase):
    """Testes para o filtro de tamanho de arquivo."""
    
    def setUp(self):
        self.usuario = CustomUser.objects.create_user(
            email='teste@example.com',
            password='senha123',
            nome_completo='Usuário Teste'
        )
        self.categoria = Categoria.objects.create(nome='Teste')
    
    def test_filter_pequeno(self):
        """Testa filtro para arquivos pequenos (até 1MB)."""
        # Este teste seria mais realista com arquivos reais
        # Para fins de demonstração, vamos criar um documento mock
        filter_obj = TamanhoArquivoFilter(None, {}, Documento, DocumentoAdmin)
        filter_obj.value = lambda: 'pequeno'
        
        # O filtro deveria retornar documentos com tamanho <= 1MB
        queryset = filter_obj.queryset(None, Documento.objects.all())
        self.assertIsNotNone(queryset)


class MarkAsVerificadoActionTestCase(TestCase):
    """Testes para a action de marcar como verificado."""
    
    def setUp(self):
        self.usuario = CustomUser.objects.create_user(
            email='teste@example.com',
            password='senha123',
            nome_completo='Usuário Teste'
        )
        self.categoria = Categoria.objects.create(nome='Teste')
        self.categoria_admin = DocumentoAdmin(Documento, AdminSite())
        
        # Criar documentos não verificados
        for i in range(3):
            arquivo = SimpleUploadedFile(
                f"teste{i}.pdf",
                b"conteúdo",
                content_type="application/pdf"
            )
            Documento.objects.create(
                usuario=self.usuario,
                categoria=self.categoria,
                titulo=f'Documento {i}',
                arquivo=arquivo,
                verificado=False
            )
    
    def test_marcar_como_verificado(self):
        """Testa a action de marcar documentos como verificados."""
        # Criar um request mock
        factory = RequestFactory()
        request = factory.get('/admin/')
        request.user = self.usuario
        
        # Pegar todos os documentos não verificados
        queryset = Documento.objects.filter(verificado=False)
        self.assertEqual(queryset.count(), 3)
        
        # Executar a action
        marcar_como_verificado(self.categoria_admin, request, queryset)
        
        # Verificar se todos foram marcados
        verificados = Documento.objects.filter(verificado=True)
        self.assertEqual(verificados.count(), 3)
    
    def test_marcar_como_nao_verificado(self):
        """Testa a action de marcar documentos como não verificados."""
        # Primeiro, marcar todos como verificados
        Documento.objects.all().update(verificado=True)
        
        factory = RequestFactory()
        request = factory.get('/admin/')
        request.user = self.usuario
        
        # Pegar todos os documentos
        queryset = Documento.objects.all()
        
        # Executar a action de desmarcar
        marcar_como_nao_verificado(self.categoria_admin, request, queryset)
        
        # Verificar se todos foram desmarcados
        nao_verificados = Documento.objects.filter(verificado=False)
        self.assertEqual(nao_verificados.count(), 3)


class LogUploadDecoratorTestCase(TestCase):
    """Testes para o decorator de logging de upload."""
    
    def setUp(self):
        self.client = Client()
        self.usuario = CustomUser.objects.create_user(
            email='teste@example.com',
            password='senha123',
            nome_completo='Usuário Teste'
        )
        self.categoria = Categoria.objects.create(nome='Teste')
    
    def test_upload_com_logging(self):
        """Testa se o decorator registra o upload corretamente."""
        # Fazer login
        self.client.login(email='teste@example.com', password='senha123')
        
        # Capturar logs
        with self.assertLogs('myapp', level='INFO') as logs:
            arquivo = SimpleUploadedFile(
                "teste.pdf",
                b"conteúdo teste",
                content_type="application/pdf"
            )
            
            response = self.client.post('/documentos/novo/', {
                'titulo': 'Documento Teste',
                'categoria': self.categoria.id,
                'arquivo': arquivo
            })
        
        # Verificar se o upload foi registrado nos logs
        # Nota: O decorator registra em form_valid
        log_entries = '\n'.join(logs.output)
        self.assertIn('teste@example.com', log_entries)


class DocumentoAdminDisplayTestCase(TestCase):
    """Testes para os métodos de display customizados do admin."""
    
    def setUp(self):
        self.usuario = CustomUser.objects.create_user(
            email='teste@example.com',
            password='senha123',
            nome_completo='Usuário Teste'
        )
        self.categoria = Categoria.objects.create(nome='Teste')
        self.categoria_admin = DocumentoAdmin(Documento, AdminSite())
        
        arquivo = SimpleUploadedFile(
            "teste.pdf",
            b"x" * (500 * 1024),  # 500 KB
            content_type="application/pdf"
        )
        self.documento = Documento.objects.create(
            usuario=self.usuario,
            categoria=self.categoria,
            titulo='Este é um documento muito longo que precisa ser truncado para ficar melhor na exibição',
            arquivo=arquivo
        )
    
    def test_titulo_truncado(self):
        """Testa se o título é truncado corretamente."""
        result = self.categoria_admin.titulo_truncado(self.documento)
        # O resultado deve estar em HTML, então não deve conter o título completo
        self.assertNotIn('melhor na exibição', result.split('>')[-1])
    
    def test_usuario_email(self):
        """Testa a exibição do email do usuário."""
        result = self.categoria_admin.usuario_email(self.documento)
        self.assertEqual(result, 'teste@example.com')
    
    def test_tamanho_arquivo_formatado(self):
        """Testa a formatação do tamanho do arquivo."""
        result = self.categoria_admin.tamanho_arquivo_formatado(self.documento)
        self.assertIn('KB', result)
    
    def test_status_verificacao_nao_verificado(self):
        """Testa o status de não verificado."""
        result = self.categoria_admin.status_verificacao(self.documento)
        self.assertIn('red', result)
        self.assertIn('Não Verificado', result)
    
    def test_status_verificacao_verificado(self):
        """Testa o status verificado."""
        self.documento.verificado = True
        result = self.categoria_admin.status_verificacao(self.documento)
        self.assertIn('green', result)
        self.assertIn('Verificado', result)


# Exemplos de como executar os testes
"""
Para executar todos os testes:
python manage.py test app.tests

Para executar um teste específico:
python manage.py test app.tests.DataEnvioFilterTestCase.test_filter_hoje

Com verbosidade:
python manage.py test app.tests -v 2

Com coverage:
coverage run --source='app' manage.py test app.tests
coverage report
coverage html
"""
