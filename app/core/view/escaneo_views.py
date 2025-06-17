import os
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.views import View
import tempfile
from app.core.models import Diagnostico, ImagenDiagnostico, Paciente, ResultadoIA, InformePDF
from neumscan.services.analisis_imagen import analizar_imagen_neumonia
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from PIL import Image
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView
from app.security.mixins.mixins import PermissionMixin

class AnalisisImagenView(View):
    """Vista principal para mostrar el formulario de análisis"""
    def get(self, request):
        return render(request, 'dashboard/scan/scan_form.html')


from django.shortcuts import redirect
from django.contrib import messages
import os

class DiagnosticoDeleteView(PermissionMixin, DeleteView):
    model = Diagnostico
    success_url = reverse_lazy('core:scan_list')
    permission_required = 'core.delete_diagnostico'

    def get(self, request, *args, **kwargs):
        try:
            diagnostico = self.get_object()

            # Eliminar archivos asociados
            for imagen in diagnostico.imagenes.all():
                if imagen.imagen_original and os.path.isfile(imagen.imagen_original.path):
                    os.remove(imagen.imagen_original.path)
                if imagen.imagen_procesada and os.path.isfile(imagen.imagen_procesada.path):
                    os.remove(imagen.imagen_procesada.path)
                if imagen.gradcam and os.path.isfile(imagen.gradcam.path):
                    os.remove(imagen.gradcam.path)

            # Eliminar informe PDF si existe
            try:
                informe = diagnostico.informepdf
                if informe and informe.archivo_pdf and os.path.isfile(informe.archivo_pdf.path):
                    os.remove(informe.archivo_pdf.path)
            except InformePDF.DoesNotExist:
                pass

            diagnostico.delete()
            messages.success(request, 'Diagnóstico eliminado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el diagnóstico: {str(e)}')

        return redirect('core:scan_list')


class BuscarPacienteAPIView(View):
    """API para buscar paciente por DNI"""
    def get(self, request):
        dni = request.GET.get('dni', '').strip()
        
        if not dni:
            return JsonResponse({
                'success': False,
                'error': 'DNI es requerido'
            })
        
        try:
            # Buscar paciente en la base de datos
            paciente = Paciente.objects.get(dni=dni)
            
            return JsonResponse({
                'success': True,
                'paciente': {
                    'id': paciente.id,
                    'nombres': paciente.nombres,
                    'apellidos': paciente.apellidos,
                    'dni': paciente.dni,
                    'edad': paciente.edad(),
                    'sexo': paciente.get_sexo_display(),
                    'telefono': paciente.contacto,
                    'direccion': paciente.direccion,
                    'historial_clinico': paciente.historial_clinico[:100] + '...' if len(paciente.historial_clinico) > 100 else paciente.historial_clinico
                }
            })
        except Paciente.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'No se encontró ningún paciente con DNI: {dni}'
            })


@method_decorator(csrf_exempt, name='dispatch')
class ProcesarAnalisisAPIView(View):
    def post(self, request):
        try:
            paciente_id = request.POST.get('paciente_id')
            imagenes = request.FILES.getlist('imagenes')

            if not paciente_id:
                return JsonResponse({'success': False, 'error': 'ID de paciente es requerido'})

            if not imagenes:
                return JsonResponse({'success': False, 'error': 'Debe seleccionar al menos una imagen'})

            try:
                paciente = Paciente.objects.get(id=paciente_id)
            except Paciente.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Paciente no encontrado'})

            # Crear diagnóstico
            diagnostico = Diagnostico.objects.create(
                paciente=paciente,
                doctor=request.user.doctorprofile if hasattr(request.user, 'doctorprofile') else None,
                estado='validado',
                observaciones_medicas='Análisis de neumonía por IA'
            )

            resultados_procesados = []

            for idx, imagen in enumerate(imagenes):
                try:
                    if not self._validar_archivo(imagen):
                        print(f"Imagen {idx + 1} no válida: {imagen.name}")
                        continue

                    # Guardar imagen temporalmente
                    temp_path = self._guardar_imagen_temporal(imagen)
                    print(f"Imagen temporal guardada en: {temp_path}")

                    # Analizar imagen con IA
                    resultado_ia = analizar_imagen_neumonia(temp_path)
                    print(f"Resultado IA: {resultado_ia}")

                    if resultado_ia['confianza'] > 0:
                        # Guardar imagen original en el modelo ImagenDiagnostico
                        imagen_diagnostico = ImagenDiagnostico.objects.create(
                            diagnostico=diagnostico,
                            imagen_original=imagen
                        )
                        print(f"ImagenDiagnostico creada con ID: {imagen_diagnostico.id}")

                        # Guardar imagen procesada si existe
                        imagen_procesada_path = resultado_ia.get('imagen_procesada_path')
                        if imagen_procesada_path and os.path.exists(imagen_procesada_path):
                            print(f"Guardando imagen procesada desde: {imagen_procesada_path}")
                            try:
                                with open(imagen_procesada_path, 'rb') as f:
                                    procesada_content = ContentFile(f.read())
                                    nombre_procesada = f'procesada_{imagen_diagnostico.id}_{idx + 1}.jpeg'
                                    imagen_diagnostico.imagen_procesada.save(
                                        nombre_procesada,
                                        procesada_content,
                                        
                                    )
                                print(f"Imagen procesada guardada como: {nombre_procesada}")
                            except Exception as e:
                                print(f"Error al guardar imagen procesada: {str(e)}")
                        else:
                            print(f"No se encontró imagen procesada en: {imagen_procesada_path}")

                        # Guardar imagen GradCAM si existe
                        gradcam_path = resultado_ia.get('gradcam_path')
                        if gradcam_path:
                            # Convertir ruta relativa a ruta absoluta
                            if gradcam_path.startswith('/media/'):
                                # Remover /media/ y construir ruta completa
                                gradcam_path_abs = os.path.join(settings.MEDIA_ROOT, gradcam_path.lstrip('/media/'))
                            elif gradcam_path.startswith('media/'):
                                # Construir ruta completa desde MEDIA_ROOT
                                gradcam_path_abs = os.path.join(settings.MEDIA_ROOT, gradcam_path.lstrip('media/'))
                            else:
                                gradcam_path_abs = gradcam_path
                            
                            print(f"Buscando GradCAM en ruta absoluta: {gradcam_path_abs}")
                            
                            if os.path.exists(gradcam_path_abs):
                                print(f"Guardando GradCAM desde: {gradcam_path_abs}")
                                try:
                                    with open(gradcam_path_abs, 'rb') as f:
                                        gradcam_content = ContentFile(f.read())
                                        nombre_gradcam = f'gradcam_{imagen_diagnostico.id}_{idx + 1}.jpeg'
                                        imagen_diagnostico.gradcam.save(
                                            nombre_gradcam,
                                            gradcam_content,
                                            save=False  # No guardar aún
                                        )
                                    print(f"GradCAM guardado como: {nombre_gradcam}")
                                except Exception as e:
                                    print(f"Error al guardar GradCAM: {str(e)}")
                            else:
                                print(f"No se encontró GradCAM en ruta absoluta: {gradcam_path_abs}")
                                # Intentar buscar en diferentes ubicaciones
                                possible_paths = [
                                    gradcam_path,
                                    os.path.join(os.getcwd(), gradcam_path.lstrip('/')),
                                    os.path.join(os.getcwd(), 'media', gradcam_path.split('/')[-1]),
                                    os.path.join(tempfile.gettempdir(), gradcam_path.split('/')[-1])
                                ]
                                
                                for possible_path in possible_paths:
                                    print(f"Intentando: {possible_path}")
                                    if os.path.exists(possible_path):
                                        print(f"¡Encontrado GradCAM en: {possible_path}!")
                                        try:
                                            with open(possible_path, 'rb') as f:
                                                gradcam_content = ContentFile(f.read())
                                                nombre_gradcam = f'gradcam_{imagen_diagnostico.id}_{idx + 1}.jpeg'
                                                imagen_diagnostico.gradcam.save(
                                                    nombre_gradcam,
                                                    gradcam_content,
                                                    save=False
                                                )
                                            print(f"GradCAM guardado como: {nombre_gradcam}")
                                            break
                                        except Exception as e:
                                            print(f"Error al guardar GradCAM desde {possible_path}: {str(e)}")
                        else:
                            print("No se proporcionó ruta de GradCAM")

                        # Guardar el objeto con todas las imágenes
                        imagen_diagnostico.save()
                        print(f"ImagenDiagnostico guardado completamente")

                        # Limpiar archivos temporales generados por IA
                        if imagen_procesada_path and os.path.exists(imagen_procesada_path):
                            try:
                                os.remove(imagen_procesada_path)
                                print(f"Archivo temporal procesado eliminado: {imagen_procesada_path}")
                            except Exception as e:
                                print(f"Error al eliminar archivo procesado: {str(e)}")

                        if gradcam_path and os.path.exists(gradcam_path):
                            try:
                                os.remove(gradcam_path)
                                print(f"Archivo temporal GradCAM eliminado: {gradcam_path}")
                            except Exception as e:
                                print(f"Error al eliminar archivo GradCAM: {str(e)}")

                        # Determinar severidad
                        severidad = self._determinar_severidad(resultado_ia['diagnostico'])

                        # Crear resultado de IA
                        resultado_ia_obj = ResultadoIA.objects.create(
                            imagen=imagen_diagnostico,
                            diagnostico_principal=resultado_ia['diagnostico'],
                            tipo_diagnostico=resultado_ia.get('tipo_diagnostico', 'otros'),
                            confianza=resultado_ia['confianza'],
                            hallazgos=resultado_ia['hallazgos'],
                            recomendaciones=resultado_ia['recomendaciones'],
                            areas_afectadas=resultado_ia.get('areas_afectadas'),
                            severidad=severidad,
                            coordenadas_roi=resultado_ia.get('coordenadas_roi'),
                            tiempo_procesamiento=resultado_ia.get('tiempo_procesamiento')
                        )
                        print(f"ResultadoIA creado con ID: {resultado_ia_obj.id}")

                        # Refrescar el objeto para obtener las URLs actualizadas
                        imagen_diagnostico.refresh_from_db()

                        resultados_procesados.append({
                            'imagen_id': imagen_diagnostico.id,
                            'diagnostico': resultado_ia['diagnostico'],
                            'confianza': resultado_ia['confianza'],
                            'hallazgos': resultado_ia['hallazgos'],
                            'recomendaciones': resultado_ia['recomendaciones'],
                            'severidad': severidad,
                            'imagen_url': imagen_diagnostico.imagen_original.url if imagen_diagnostico.imagen_original else None,
                            'procesada_url': imagen_diagnostico.imagen_procesada.url if imagen_diagnostico.imagen_procesada else None,
                            'gradcam_url': imagen_diagnostico.gradcam.url if imagen_diagnostico.gradcam else None
                        })

                    # Eliminar archivo temporal original
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                            print(f"Archivo temporal original eliminado: {temp_path}")
                        except Exception as e:
                            print(f"Error al eliminar archivo temporal: {str(e)}")

                except Exception as e:
                    print(f"Error procesando imagen {idx + 1}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue

            if resultados_procesados:
                # *** GENERAR PDF AUTOMÁTICAMENTE DESPUÉS DEL ANÁLISIS ***
                try:
                    resultados_ia = ResultadoIA.objects.filter(imagen__diagnostico=diagnostico)

                    informe_pdf = self._generar_pdf_informe(diagnostico, resultados_ia)

                    print(f"PDF generado exitosamente: {informe_pdf.archivo_pdf.url}")
                except Exception as e:
                    print(f"Error al generar PDF: {str(e)}")
                    # Continuar aunque falle la generación del PDF

                respuesta_datos = {
                    'paciente': f"{paciente.nombres} {paciente.apellidos}",
                    'fecha': diagnostico.fecha_diagnostico.strftime('%d/%m/%Y %H:%M'),
                    'imagenes_procesadas': len(resultados_procesados),
                    'resultados': resultados_procesados,
                    'diagnostico_id': diagnostico.id,
                    'pdf_url': informe_pdf.archivo_pdf.url if 'informe_pdf' in locals() else None
                }

                return JsonResponse({'success': True, 'resultados': respuesta_datos})
            else:
                diagnostico.estado = 'error'
                diagnostico.save()
                return JsonResponse({'success': False, 'error': 'No se pudieron procesar las imágenes correctamente'})

        except Exception as e:
            print(f"Error general en ProcesarAnalisisAPIView: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'Error interno del servidor: {str(e)}'})

    def _validar_archivo(self, archivo):
        extensiones_validas = ['.jpg', '.jpeg', '.png']
        nombre_archivo = archivo.name.lower()
        if not any(nombre_archivo.endswith(ext) for ext in extensiones_validas):
            return False
        try:
            Image.open(archivo).verify()  # Validación real de imagen
            archivo.seek(0)  # Resetear puntero después de .verify()
            return True
        except:
            return False

    def _guardar_imagen_temporal(self, imagen):
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, imagen.name)
        with open(temp_path, 'wb+') as destination:
            for chunk in imagen.chunks():
                destination.write(chunk)
        return temp_path

    def _determinar_severidad(self, diagnostico):
        diagnostico_lower = diagnostico.lower()
        if diagnostico_lower == 'normal':
            return 'Sin alteraciones'
        elif 'bacteriana' in diagnostico_lower:
            return 'Moderada a severa'
        elif 'viral' in diagnostico_lower:
            return 'Leve a moderada'
        else:
            return 'Por determinar'

    def _generar_pdf_informe(self, diagnostico, resultado_ia):
        """
        Generar PDF del informe automáticamente después del análisis.
        Usa los datos directamente desde `resultado_ia`.
        """
        try:
            # Verificar si ya existe un informe
            informe_existente = InformePDF.objects.filter(diagnostico=diagnostico).first()
            if informe_existente:
                print(f"Ya existe un informe PDF para el diagnóstico {diagnostico.id}")
                return informe_existente

            print(f"Generando PDF para diagnóstico {diagnostico.id}")

            # Obtener las imágenes relacionadas con el diagnóstico
            imagenes = ImagenDiagnostico.objects.filter(diagnostico=diagnostico)
            imagenes_info = []

            # Construir rutas absolutas para las imágenes
            for img in imagenes:
                # Obtener rutas absolutas
                original_path = img.imagen_original.path if img.imagen_original else None
                procesada_path = img.imagen_procesada.path if img.imagen_procesada else None
                gradcam_path = img.gradcam.path if img.gradcam else None

                # Convertir rutas a formato URL para WeasyPrint
                imagen_data = {
                    'original': 'file:///' + original_path.replace('\\', '/') if original_path else None,
                    'procesada': 'file:///' + procesada_path.replace('\\', '/') if procesada_path else None,
                    'gradcam': 'file:///' + gradcam_path.replace('\\', '/') if gradcam_path else None
                }
                imagenes_info.append(imagen_data)
            
            print(f"Imágenes preparadas para PDF: {imagenes_info}")
            
            context = {
                'diagnostico': diagnostico,
                'imagenes_info': imagenes_info,
                'resultados_ia': resultado_ia,
            }

            # Renderizar HTML con la plantilla PDF
            html_string = render_to_string('dashboard/report/pdf_template.html', context)

            # Crear PDF en un archivo temporal
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                HTML(string=html_string).write_pdf(temp_file.name)

            # Guardar archivo en modelo InformePDF
            informe = InformePDF.objects.create(diagnostico=diagnostico)
            with open(temp_file.name, 'rb') as pdf_file:
                nombre_archivo = f'informe_diagnostico_{diagnostico.id}_{diagnostico.fecha_diagnostico.strftime("%Y%m%d_%H%M%S")}.pdf'
                informe.archivo_pdf.save(nombre_archivo, ContentFile(pdf_file.read()))

            # Eliminar archivo temporal
            os.remove(temp_file.name)

            print(f"PDF guardado como: {informe.archivo_pdf.name}")
            return informe

        except Exception as e:
            print(f"Error al generar PDF para diagnóstico {diagnostico.id}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e



def generar_pdf_informe_manual(request, diagnostico_id):

    diagnostico = get_object_or_404(Diagnostico, id=diagnostico_id)

    

    # Verificar si ya existe un informe
    informe_existente = InformePDF.objects.filter(diagnostico=diagnostico).first()
    if informe_existente:
        return HttpResponse(informe_existente.archivo_pdf.url)

    try:
        # Usar el método de la clase para generar el PDF
        view_instance = ProcesarAnalisisAPIView()
        informe = view_instance._generar_pdf_informe(diagnostico)
        return HttpResponse(informe.archivo_pdf.url)
    except Exception as e:
        return HttpResponse(f'Error al generar PDF: {str(e)}', status=500)