from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from app.core.models import Paciente
from app.core.form.form_pacient import PacienteForm

class PacienteListView(ListView):
    model = Paciente
    template_name = 'dashboard/paciente/pacient_list.html'
    context_object_name = 'pacientes'


class PacienteCreateView(CreateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'dashboard/paciente/pacient_form.html'
    success_url = reverse_lazy('core:pacient_list')


class PacienteUpdateView(UpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'dashboard/paciente/pacient_form.html'
    success_url = reverse_lazy('core:pacient_list')


class PacienteDeleteView(DeleteView):
    model = Paciente
    success_url = reverse_lazy('core:pacient_list')