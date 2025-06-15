from django.urls import path
from app.security import views
from app.security.views import GoogleLoginView, GoogleLoginCallbackView

app_name = 'security'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('google/callback/', GoogleLoginCallbackView.as_view(), name='google_login_callback'),
]
