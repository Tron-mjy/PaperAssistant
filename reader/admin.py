from django.contrib import admin

from .models import Paper, Vocabulary


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ['filename', 'user', 'uploaded_at']
    search_fields = ['filename', 'user__username']
    list_filter = ['user']


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ['word', 'user', 'paper', 'created_at']
    search_fields = ['word', 'user__username']
    list_filter = ['user', 'paper']
