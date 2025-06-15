import os
import numpy as np
import cv2
import tensorflow as tf
import tempfile
import time
from django.conf import settings
from keras import models
from keras_preprocessing import image
from PIL import Image, ImageEnhance

# Cargar el modelo una sola vez
MODEL_PATH = os.path.join(settings.BASE_DIR, 'static/model/inceptionv3.h5')
model = models.load_model(MODEL_PATH)

# Etiquetas del modelo (para clasificación multiclase)
CLASES = {
    0: "Normal",
    1: "Neumonía Bacteriana",
    2: "Neumonía Viral"
}

def _validar_imagen(img_array):
    """Verifica si la imagen tiene buen contraste, y si es en escala de grises"""
    if img_array.std() < 20 or img_array.mean() > 230:
        return False, "Imagen demasiado clara o sin contraste"

    is_grayscale_like = np.allclose(img_array[..., 0], img_array[..., 1], atol=15) and \
                        np.allclose(img_array[..., 1], img_array[..., 2], atol=15)

    if not is_grayscale_like:
        return False, "La imagen no parece una radiografía de tórax"

    return True, None

def _procesar_imagen(ruta_imagen):
    """
    Procesa la imagen original aplicando mejoras de contraste y normalización
    
    Returns:
        str: Ruta absoluta del archivo de imagen procesada
    """
    try:
        # Abrir imagen con PIL
        img = Image.open(ruta_imagen)
        
        # Convertir a RGB si no lo está
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar a 150x150 (tamaño del modelo)
        img = img.resize((150, 150), Image.Resampling.LANCZOS)
        
        # Aplicar mejoras de imagen
        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # Ajustar brillo ligeramente
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # Crear directorio temporal para imagen procesada
        temp_dir = tempfile.mkdtemp()
        base_name = os.path.splitext(os.path.basename(ruta_imagen))[0]
        procesada_filename = f"procesada_{base_name}.jpeg"
        procesada_path = os.path.join(temp_dir, procesada_filename)
        
        # Guardar imagen procesada
        img.save(procesada_path, 'JPEG', quality=95)
        
        print(f"Imagen procesada guardada en: {procesada_path}")
        return procesada_path
        
    except Exception as e:
        print(f"Error procesando imagen: {str(e)}")
        return None

def _generar_gradcam(model, input_array, pred_class, ruta_imagen, is_binary=False):
    """
    Genera GradCAM y retorna la ruta absoluta del archivo generado
    
    Returns:
        str: Ruta absoluta del archivo GradCAM generado
    """
    try:
        last_conv_layer = model.get_layer("mixed10")
        grad_model = tf.keras.models.Model([model.input], [last_conv_layer.output, model.output])

        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(input_array)
            loss = predictions[:, 0] if is_binary else predictions[:, pred_class]
            grads = tape.gradient(loss, conv_outputs)

        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        conv_outputs = conv_outputs[0]
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)
        heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
        heatmap = heatmap.numpy()

        heatmap_resized = cv2.resize(heatmap, (150, 150))
        heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap_resized), cv2.COLORMAP_JET)

        img_original = cv2.imread(ruta_imagen)
        if img_original is None:
            print(f"No se pudo leer la imagen original: {ruta_imagen}")
            return None

        img_original = cv2.resize(img_original, (150, 150))
        superimposed_img = cv2.addWeighted(img_original, 0.6, heatmap_colored, 0.4, 0)

        # Crear directorio temporal para GradCAM
        temp_dir = tempfile.mkdtemp()
        base_name = os.path.splitext(os.path.basename(ruta_imagen))[0]
        gradcam_filename = f"gradcam_{base_name}.jpeg"
        gradcam_path = os.path.join(temp_dir, gradcam_filename)
        
        # Guardar GradCAM
        success = cv2.imwrite(gradcam_path, superimposed_img)
        
        if success:
            print(f"GradCAM guardado en: {gradcam_path}")
            return gradcam_path
        else:
            print(f"Error al guardar GradCAM en: {gradcam_path}")
            return None

    except Exception as e:
        print(f"Error generando Grad-CAM: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def _determinar_areas_afectadas(pred_class, is_binary=False):
    """Determina las áreas típicamente afectadas según el diagnóstico"""
    if is_binary:
        if pred_class == 1:
            return "Campos pulmonares con opacidades"
        else:
            return "Sin áreas de opacidad significativa"
    else:
        areas_por_clase = {
            0: "Sin áreas de opacidad significativa",
            1: "Lóbulos pulmonares con consolidación bacteriana",
            2: "Infiltrados intersticiales difusos"
        }
        return areas_por_clase.get(pred_class, "Áreas por determinar")

def _generar_coordenadas_roi(pred_class, is_binary=False):
    """Genera coordenadas aproximadas de región de interés"""
    # Estas son coordenadas ejemplo - en un sistema real vendrían del GradCAM
    if is_binary and pred_class == 1:
        return [[30, 40, 120, 110]]  # [x1, y1, x2, y2]
    elif not is_binary and pred_class > 0:
        return [[25, 35, 125, 115]]
    else:
        return []

def analizar_imagen_neumonia(ruta_imagen):
    """
    Analiza una imagen de rayos X para detectar neumonía
    
    Args:
        ruta_imagen (str): Ruta absoluta de la imagen a analizar
    
    Returns:
        dict: Resultado completo del análisis con todas las rutas de archivos generados
    """
    print(f"=== INICIANDO ANÁLISIS DE IMAGEN ===")
    print(f"Ruta de imagen: {ruta_imagen}")
    
    start_time = time.time()
    
    try:
        # Cargar y validar imagen
        img = image.load_img(ruta_imagen, target_size=(150, 150))
        img_array = image.img_to_array(img).astype('float32')
        print(f"Imagen cargada exitosamente: {img_array.shape}")
        
    except Exception as e:
        print(f"Error al cargar imagen: {str(e)}")
        return {
            'diagnostico': "Error al procesar la imagen",
            'confianza': 0,
            'hallazgos': 'Formato de imagen inválido',
            'recomendaciones': 'Verifica el archivo',
            'imagen_procesada_path': None,
            'gradcam_path': None,
            'tipo_diagnostico': 'error',
            'areas_afectadas': None,
            'coordenadas_roi': [],
            'tiempo_procesamiento': 0
        }

    # Validaciones de imagen
    es_valida, motivo = _validar_imagen(img_array)
    if not es_valida:
        print(f"Imagen no válida: {motivo}")
        return {
            'diagnostico': "Imagen no válida para diagnóstico",
            'confianza': 0,
            'hallazgos': motivo,
            'recomendaciones': 'Sube una radiografía de tórax clara',
            'imagen_procesada_path': None,
            'gradcam_path': None,
            'tipo_diagnostico': 'invalida',
            'areas_afectadas': None,
            'coordenadas_roi': [],
            'tiempo_procesamiento': round(time.time() - start_time, 2)
        }

    try:
        # Procesar imagen
        print("Procesando imagen...")
        imagen_procesada_path = _procesar_imagen(ruta_imagen)
        
        # Preparar imagen para predicción
        img_array_norm = np.expand_dims(img_array, axis=0) / 255.0
        print("Realizando predicción con IA...")
        pred = model.predict(img_array_norm, verbose=0)
        
        # Determinar si es modelo binario o multiclase
        is_binary = pred.shape[1] == 1
        print(f"Modelo {'binario' if is_binary else 'multiclase'} detectado")

        if is_binary:
            pred_class = 1 if pred[0][0] > 0.5 else 0
            confianza = float(pred[0][0]) if pred_class == 1 else 1 - float(pred[0][0])
            resultado = "Neumonía" if pred_class == 1 else "Normal"
            tipo_diagnostico = "neumonia" if pred_class == 1 else "normal"
        else:
            pred_class = np.argmax(pred[0])
            confianza = float(pred[0][pred_class])
            resultado = CLASES.get(pred_class, "Desconocido")
            tipo_diagnostico = "normal" if pred_class == 0 else "neumonia"

        print(f"Predicción: {resultado} (Confianza: {confianza:.2%})")

        # Generar GradCAM
        print("Generando GradCAM...")
        gradcam_path = _generar_gradcam(model, img_array_norm, pred_class, ruta_imagen, is_binary)
        
        # Determinar áreas afectadas y coordenadas
        areas_afectadas = _determinar_areas_afectadas(pred_class, is_binary)
        coordenadas_roi = _generar_coordenadas_roi(pred_class, is_binary)
        
        tiempo_procesamiento = round(time.time() - start_time, 2)
        
        resultado_final = {
            'diagnostico': resultado,
            'confianza': round(confianza * 100, 2),
            'hallazgos': f'La imagen presenta características consistentes con: {resultado}',
            'recomendaciones': 'Consultar con un especialista para confirmación diagnóstica' if resultado != 'Normal' else 'Imagen sin hallazgos patológicos evidentes',
            'imagen_procesada_path': imagen_procesada_path,  # RUTA ABSOLUTA
            'gradcam_path': gradcam_path,  # RUTA ABSOLUTA
            'tipo_diagnostico': tipo_diagnostico,
            'areas_afectadas': areas_afectadas,
            'coordenadas_roi': coordenadas_roi,
            'tiempo_procesamiento': tiempo_procesamiento
        }
        
        print(f"=== ANÁLISIS COMPLETADO ===")
        print(f"Resultado: {resultado_final}")
        
        return resultado_final

    except Exception as e:
        print(f"Error durante el análisis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'diagnostico': "Error en el análisis",
            'confianza': 0,
            'hallazgos': f'Error durante el procesamiento: {str(e)}',
            'recomendaciones': 'Intentar nuevamente con otra imagen',
            'imagen_procesada_path': None,
            'gradcam_path': None,
            'tipo_diagnostico': 'error',
            'areas_afectadas': None,
            'coordenadas_roi': [],
            'tiempo_procesamiento': round(time.time() - start_time, 2)
        }