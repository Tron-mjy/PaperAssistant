from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('api/upload/', views.upload_pdf, name='upload_pdf'),
    path('api/word/', views.word_lookup, name='word_lookup'),
    path('api/paragraph/', views.paragraph_explain, name='paragraph_explain'),
    path('api/ask/', views.ask_ai, name='ask_ai'),
    path('api/papers/', views.paper_list, name='paper_list'),
    path('api/paper/<int:paper_id>/delete/', views.paper_delete, name='paper_delete'),
    path('api/paper/<int:paper_id>/analysis/', views.get_analysis, name='get_analysis'),
    path('api/paper/<int:paper_id>/context/', views.get_paper_context, name='get_paper_context'),
    path('api/vocabulary/', views.vocabulary_list, name='vocabulary_list'),
    path('api/vocabulary/add/', views.vocabulary_add, name='vocabulary_add'),
    path('api/vocabulary/<int:word_id>/delete/', views.vocabulary_delete, name='vocabulary_delete'),
    path('api/vocabulary/export/', views.vocabulary_export, name='vocabulary_export'),
]
