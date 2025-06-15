from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from app.security.mixins.mixins import PermissionMixin
from app.core.models import Diagnostico, ResultadoIA
from django.urls import reverse_lazy

class RevisionManualView(LoginRequiredMixin, PermissionMixin, View):
    """Vista para la revisión manual de resultados de IA"""
    permission_required = 'core.view_resultadoia'
    template_name = 'dashboard/scan/revision_manual.html'

    def get(self, request, diagnostico_id=None):
        if diagnostico_id:
            # Vista de detalle de un diagnóstico específico
            diagnostico = get_object_or_404(Diagnostico.objects.select_related(
                'paciente',
                'doctor'
            ).prefetch_related(
                'imagenes',
                'imagenes__resultado_ia'
            ), id=diagnostico_id)

            context = {
                'diagnostico': diagnostico,
                'title': f'Revisión de Diagnóstico #{diagnostico_id}',
                'section': 'revision_manual'
            }
            return render(request, self.template_name, context)
        else:
            # Vista de lista de diagnósticos
            diagnosticos = Diagnostico.objects.select_related(
                'paciente',
                'doctor'
            ).prefetch_related(
                'imagenes',
                'imagenes__resultado_ia'
            ).order_by('-fecha_diagnostico')

            context = {
                'diagnosticos': diagnosticos,
                'title': 'Revisión Manual de Resultados',
                'section': 'revision_manual'
            }
            return render(request, self.template_name, context)

class ValidarResultadoView(LoginRequiredMixin, PermissionMixin, View):
    """Vista para validar o rechazar un resultado específico"""
    permission_required = 'core.change_resultadoia'

    def post(self, request, diagnostico_id):
        diagnostico = get_object_or_404(Diagnostico, id=diagnostico_id)
        accion = request.POST.get('accion')
        observaciones = request.POST.get('observaciones', '')

        if accion == 'validar':
            diagnostico.estado = 'validado'
            mensaje = 'Diagnóstico validado correctamente'
        elif accion == 'rechazar':
            diagnostico.estado = 'rechazado'
            mensaje = 'Diagnóstico rechazado'
        else:
            messages.error(request, 'Acción no válida')
            return redirect('core:revision_manual')

        diagnostico.observaciones_medicas = observaciones
        diagnostico.doctor = request.user.doctorprofile if hasattr(request.user, 'doctorprofile') else None
        diagnostico.save()

        messages.success(request, mensaje)
        return redirect('core:revision_manual')
