from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from .models import Categoria, CustomUser, Documento


class TamanhoArquivoFilter(admin.SimpleListFilter):
    title = 'Tamanho do Arquivo'
    parameter_name = 'tamanho'

    def lookups(self, request, model_admin):
        return [
            ('pequeno', 'Até 1MB'),
            ('medio', '1MB a 2MB'),
            ('grande', 'Acima de 2MB'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'pequeno':
            return queryset.filter(arquivo__size__lte=1 * 1024 * 1024)
        if self.value() == 'medio':
            return queryset.filter(arquivo__size__gt=1 * 1024 * 1024, arquivo__size__lte=2 * 1024 * 1024)
        if self.value() == 'grande':
            return queryset.filter(arquivo__size__gt=2 * 1024 * 1024)
        return queryset


class DataEnvioFilter(admin.SimpleListFilter):
    title = 'Data de Envio'
    parameter_name = 'data_envio'

    def lookups(self, request, model_admin):
        return [
            ('hoje', 'Hoje'),
            ('semana', 'Últimos 7 dias'),
            ('mes', 'Último mês'),
            ('trimestre', 'Últimos 3 meses'),
            ('antigos', 'Mais de 3 meses'),
        ]

    def queryset(self, request, queryset):
        agora = timezone.now()
        
        if self.value() == 'hoje':
            inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(data_envio__gte=inicio_dia)
        
        elif self.value() == 'semana':
            semana_atras = agora - timedelta(days=7)
            return queryset.filter(data_envio__gte=semana_atras)
        
        elif self.value() == 'mes':
            mes_atras = agora - timedelta(days=30)
            return queryset.filter(data_envio__gte=mes_atras)
        
        elif self.value() == 'trimestre':
            trimestre_atras = agora - timedelta(days=90)
            return queryset.filter(data_envio__gte=trimestre_atras)
        
        elif self.value() == 'antigos':
            trimestre_atras = agora - timedelta(days=90)
            return queryset.filter(data_envio__lt=trimestre_atras)
        
        return queryset


@admin.action(description='Marcar como Verificados')
def marcar_como_verificado(modeladmin, request, queryset):
    quantidade = queryset.update(verificado=True)
    modeladmin.message_user(
        request, 
        f"{quantidade} documento(s) marcado(s) como verificado(s)."
    )


@admin.action(description='Marcar como Não Verificados')
def marcar_como_nao_verificado(modeladmin, request, queryset):
    quantidade = queryset.update(verificado=False)
    modeladmin.message_user(
        request, 
        f"{quantidade} documento(s) marcado(s) como não verificado(s)."
    )


class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 1
    fields = ('titulo', 'usuario', 'data_envio', 'verificado')
    readonly_fields = ('data_envio',)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'quantidade_documentos')
    search_fields = ('nome',)
    inlines = [DocumentoInline]
    
    def quantidade_documentos(self, obj):
        count = obj.documento_set.count()
        return count
    quantidade_documentos.short_description = 'Documentos'


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    
    list_display = ('titulo_truncado', 'usuario_email', 'categoria', 'data_envio_formatada', 'tamanho_arquivo_formatado', 'status_verificacao')
    list_filter = ('categoria', DataEnvioFilter, TamanhoArquivoFilter, 'verificado')
    search_fields = ('titulo', 'usuario__email', 'usuario__nome_completo')
    readonly_fields = ('data_envio', 'tamanho_arquivo')
    actions = [marcar_como_verificado, marcar_como_nao_verificado]
    
    fieldsets = (
        ('Informações do Documento', {
            'fields': ('titulo', 'categoria', 'arquivo')
        }),
        ('Informações do Usuário', {
            'fields': ('usuario',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('data_envio', 'tamanho_arquivo', 'verificado'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'data_envio'
    ordering = ('-data_envio',)
    
    def titulo_truncado(self, obj):
        titulo = obj.titulo[:50] + '...' if len(obj.titulo) > 50 else obj.titulo
        return titulo
    titulo_truncado.short_description = 'Título'
    
    def usuario_email(self, obj):
        return obj.usuario.email
    usuario_email.short_description = 'Usuário'
    
    def data_envio_formatada(self, obj):
        return obj.data_envio.strftime('%d/%m/%Y %H:%M')
    data_envio_formatada.short_description = 'Data de Envio'
    
    def tamanho_arquivo_formatado(self, obj):
        try:
            size = obj.arquivo.size
            if size < 1024:
                return f'{size} B'
            elif size < 1024 * 1024:
                return f'{size / 1024:.2f} KB'
            else:
                return f'{size / (1024 * 1024):.2f} MB'
        except:
            return '-'
    tamanho_arquivo_formatado.short_description = 'Tamanho'
    
    def status_verificacao(self, obj):
        status = 'Verificado' if obj.verificado else 'Não verificado'
        return status
    status_verificacao.short_description = 'Status'
    
    def tamanho_arquivo(self, obj):
        try:
            size = obj.arquivo.size
            if size < 1024:
                return f'{size} bytes'
            elif size < 1024 * 1024:
                return f'{size / 1024:.2f} KB'
            else:
                return f'{size / (1024 * 1024):.2f} MB'
        except:
            return '-'
    tamanho_arquivo.short_description = 'Tamanho'
    
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            import logging
            logger = logging.getLogger('myapp')
            logger.info(
                f"[ADMIN] Documento '{obj.titulo}' alterado por {request.user.email}"
            )


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'nome_completo', 'is_staff', 'is_active')
    search_fields = ('email', 'nome_completo')
