
from django.views.generic import ListView, DetailView  
from app.core.models import InformePDF


class ReportListView(ListView):
    model = InformePDF
    template_name = 'dashboard/report/report_list.html'
    context_object_name = 'reports'
    
class ReportDetailView(DetailView  ):
    model = InformePDF
    template_name = 'dashboard/report/report_detail.html'
    context_object_name = 'report'
    
    def get_queryset(self):
        return InformePDF.objects.filter(id=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.get_queryset().first()
        print(context)
        return context