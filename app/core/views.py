from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth, TruncDay, ExtractMonth
from datetime import datetime, timedelta
from .models import Paciente, Diagnostico, ResultadoIA, DoctorProfile
from django.utils import timezone
from django.db.models import Q

from app.core.form.form_pacient import PacienteForm

# Create your views here.

def home(request):
    return render(request, 'core/home.html')

 
@login_required
def dashboard(request):
    total_escaneos = Diagnostico.objects.count()
    total_pacientes = Paciente.objects.count()
    pacientes = Paciente.objects.all()
    escaneos_recientes = Diagnostico.objects.select_related('paciente').order_by('-fecha_diagnostico')[:5]  # los 5 más recientes
    #pendientes = Resonancia.objects.filter(estado='pendiente').count()  # Ajusta si usas otro campo
    precision = "98%"  # O cámbialo a algo dinámico si tienes métricas reales

    context = {
        'total_escaneos': total_escaneos,
        'pacientes': pacientes,
        'escaneos_recientes': escaneos_recientes,
        'total_pacientes': total_pacientes,
        'pendientes': 10,
        'precision': precision,
    }
    return render(request, 'dashboard/index.html', context)



def scan_list(request):
    Diagnosticos = Diagnostico.objects.all()
    context = {
        'diagnostico': Diagnosticos
    }
    return render(request, 'dashboard/scan/scan.html', context)


@login_required
def statistics_view(request):
    # Definir meses en español
    months_esp = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

    # Obtener el doctor actual
    doctor = request.user.doctorprofile
    
    # Fecha actual y rangos de tiempo
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    six_months_ago = now - timedelta(days=180)

    # Total de pacientes únicos atendidos
    total_pacientes = Diagnostico.objects.filter(
        doctor=doctor
    ).values('paciente').distinct().count()

    # Total de diagnósticos
    total_diagnosticos = Diagnostico.objects.filter(
        doctor=doctor
    ).count()

    # Calcular el porcentaje de casos de neumonía
    total_resultados = ResultadoIA.objects.filter(
        imagen__diagnostico__doctor=doctor
    ).count()
    
    casos_neumonia = ResultadoIA.objects.filter(
        imagen__diagnostico__doctor=doctor
    ).exclude(
        tipo_diagnostico='normal'
    ).count()

    total_neumonia = round((casos_neumonia / total_resultados * 100) if total_resultados > 0 else 0, 1)

    # Porcentaje de diagnósticos validados
    total_validados = Diagnostico.objects.filter(
        doctor=doctor,
        estado='validado'
    ).count()
    
    porcentaje_validados = round((total_validados / total_diagnosticos * 100) if total_diagnosticos > 0 else 0, 1)

    # Precisión del diagnóstico por mes del año actual
    current_year = now.year
    accuracy_by_month = []
    
    for month in range(1, now.month + 1):
        # Obtener diagnósticos del mes
        diagnostics = Diagnostico.objects.filter(
            doctor=doctor,
            fecha_diagnostico__year=current_year,
            fecha_diagnostico__month=month
        )
        
        total = diagnostics.count()
        validated = diagnostics.filter(estado='validado').count()
        
        # Obtener diagnósticos correctos
        correct = 0
        for diag in diagnostics.filter(estado='validado'):
            # Obtener el último ResultadoIA para este diagnóstico
            resultado = ResultadoIA.objects.filter(
                imagen__diagnostico=diag
            ).order_by('-fecha_procesamiento').first()
            
            # Un diagnóstico se considera correcto si:
            # 1. Está validado
            # 2. Tiene un ResultadoIA
            if resultado:
                # Si el diagnóstico está validado, consideramos que el modelo acertó
                correct += 1
        
        if total > 0:
            accuracy = (correct / total) * 100
            accuracy_by_month.append({
                'month': months_esp[month - 1],
                'accuracy': round(accuracy, 1),
                'total': total,
                'validated': validated,
                'correct': correct
            })

    # Diagnósticos por mes (últimos 6 meses)
    monthly_diagnostics = (
        Diagnostico.objects
        .filter(doctor=doctor, fecha_diagnostico__gte=six_months_ago)
        .annotate(month=TruncMonth('fecha_diagnostico'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Formatear datos mensuales
    monthly_data = []
    for entry in monthly_diagnostics:
        monthly_data.append({
            'month': months_esp[entry['month'].month - 1],
            'count': entry['count']
        })

    # Distribución de tipos de neumonía
    type_distribution = (
        ResultadoIA.objects
        .filter(imagen__diagnostico__doctor=doctor)
        .values('tipo_diagnostico')
        .annotate(count=Count('id'))
    )

    # Formatear datos de tipos
    type_mapping = {
        'normal': 'Normal',
        'neumonia_viral': 'Viral',
        'neumonia_bacteriana': 'Bacteriana',
        'otros': 'Otros'
    }
    
    type_data = []
    for entry in type_distribution:
        type_data.append({
            'type': type_mapping.get(entry['tipo_diagnostico'], entry['tipo_diagnostico']),
            'count': entry['count']
        })

    # Diagnósticos del mes actual por día
    current_month_diagnostics = (
        Diagnostico.objects
        .filter(
            doctor=doctor,
            fecha_diagnostico__year=now.year,
            fecha_diagnostico__month=now.month
        )
        .annotate(day=TruncDay('fecha_diagnostico'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    # Crear lista de todos los días del mes con sus diagnósticos
    first_day = now.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    days_in_month = (last_day.day + 1)
    
    daily_data = []
    diagnostics_dict = {d['day'].day: d['count'] for d in current_month_diagnostics}
    
    for day in range(1, days_in_month):
        daily_data.append({
            'day': day,
            'count': diagnostics_dict.get(day, 0)
        })

    # Estadísticas del mes actual
    total_mes_actual = sum(d['count'] for d in daily_data)
    dias_transcurridos = now.day
    promedio_diario = round(total_mes_actual / dias_transcurridos, 1) if dias_transcurridos > 0 else 0
    
    # Comparación con el mes anterior
    total_mes_anterior = Diagnostico.objects.filter(
        doctor=doctor,
        fecha_diagnostico__year=last_month_start.year,
        fecha_diagnostico__month=last_month_start.month
    ).count()
    
    dias_mes_anterior = last_month_start.day
    promedio_anterior = round(total_mes_anterior / dias_mes_anterior, 1) if dias_mes_anterior > 0 else 0
    
    variacion_promedio = round(((promedio_diario - promedio_anterior) / promedio_anterior * 100) if promedio_anterior > 0 else 0, 1)

    context = {
        'monthly_data': monthly_data,
        'type_data': type_data,
        'accuracy_data': accuracy_by_month,
        'total_pacientes': total_pacientes,
        'total_diagnosticos': total_diagnosticos,
        'total_neumonia': total_neumonia,
        'porcentaje_validados': porcentaje_validados,
        'daily_data': daily_data,
        'total_mes_actual': total_mes_actual,
        'promedio_diario': promedio_diario,
        'variacion_promedio': variacion_promedio,
        'doctor': doctor,
        'now': now
    }

    return render(request, 'dashboard/Statistics/statistics.html', context)
