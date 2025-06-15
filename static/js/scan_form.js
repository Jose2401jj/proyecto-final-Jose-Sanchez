let selectedFiles = [];
let currentPatient = null;

// Función unificada para obtener el token CSRF
function getCSRFToken() {
  // Primero intenta obtener desde el meta tag
  const metaToken = document.querySelector('meta[name="csrf-token"]');
  if (metaToken) {
    return metaToken.getAttribute("content");
  }

  // Luego desde el input hidden
  const inputToken = document.querySelector("[name=csrfmiddlewaretoken]");
  if (inputToken) {
    return inputToken.value;
  }

  // Finalmente desde las cookies
  return getCookie("csrftoken");
}

// Obtener CSRF desde las cookies (mantenido como respaldo)
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (const cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(trimmed.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Validar archivos antes del procesamiento
function validarArchivos(files) {
  const maxSize = 10 * 1024 * 1024; // 10MB por archivo
  const allowedTypes = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/bmp",
    "image/tiff",
  ];

  for (let file of files) {
    if (file.size > maxSize) {
      throw new Error(
        `El archivo "${file.name}" es demasiado grande. Máximo 10MB por imagen.`
      );
    }

    if (!allowedTypes.includes(file.type.toLowerCase())) {
      throw new Error(
        `El archivo "${file.name}" no es un formato válido. Use: JPG, PNG, BMP o TIFF.`
      );
    }
  }
  return true;
}

// Búsqueda de paciente por DNI
document.getElementById("btn_buscar").addEventListener("click", function () {
  const dni = document.getElementById("dni_search").value.trim();
  if (!dni) {
    showAlert("Error", "Por favor ingrese un DNI", "error");
    document.getElementById("dni_search").focus();
    return;
  }
  buscarPacientePorDNI(dni);
});

document
  .getElementById("dni_search")
  .addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      document.getElementById("btn_buscar").click();
    }
  });

function showAlert(title, message, type) {
  Swal.fire({ title, text: message, icon: type || "info" });
}

function buscarPacientePorDNI(dni) {
  const csrfToken = getCSRFToken();
  Swal.fire({
    title: "Buscando...",
    allowOutsideClick: false,
    showConfirmButton: false,
    didOpen: () => Swal.showLoading(),
  });

  fetch(`/api/buscar-paciente/?dni=${encodeURIComponent(dni)}`, {
    method: "GET",
    headers: {
      "X-CSRFToken": csrfToken,
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((res) => {
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      return res.json();
    })
    .then((data) => {
      Swal.close();
      if (data.success) {
        mostrarPacienteEncontrado(data.paciente);
      } else {
        showAlert(
          "No encontrado",
          data.error || "DNI no encontrado",
          "warning"
        );
      }
    })
    .catch((err) => {
      Swal.close();
      console.error("Error en búsqueda:", err);
      showAlert("Error", `Error en la búsqueda: ${err.message}`, "error");
    });
}

function mostrarPacienteEncontrado(paciente) {
  currentPatient = paciente;
  document.getElementById(
    "patient_name"
  ).textContent = `${paciente.nombres} ${paciente.apellidos}`;
  document.getElementById("patient_dni").textContent = paciente.dni;
  document.getElementById("patient_age").textContent = paciente.edad
    ? paciente.edad + " años"
    : "No disponible";
  document.getElementById("patient_phone").textContent =
    paciente.telefono || "No disponible";
  document.getElementById("paciente_id_hidden").value = paciente.id;

  document.getElementById("paciente_info").style.display = "block";
  document.getElementById("analisis-form").style.display = "block";
}

// Imágenes seleccionadas
document.getElementById("imagenes").addEventListener("change", function (e) {
  selectedFiles = Array.from(e.target.files);

  try {
    validarArchivos(selectedFiles);
    mostrarPreviewImagenes(selectedFiles);
  } catch (error) {
    showAlert("Error", error.message, "error");
    // Limpiar la selección si hay error
    e.target.value = "";
    selectedFiles = [];
    document.getElementById("image_preview").innerHTML = "";
  }
});

function mostrarPreviewImagenes(files) {
  const preview = document.getElementById("image_preview");
  preview.innerHTML = "";

  files.forEach((file, index) => {
    const div = document.createElement("div");
    div.className = "preview-item";

    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => {
        div.innerHTML = `
          <img src="${e.target.result}" alt="Preview">
          <button type="button" onclick="removePreview(${index})"><i class="fas fa-times"></i></button>`;
      };
      reader.readAsDataURL(file);
    } else {
      div.innerHTML = `
        <div class="file-icon"><i class="fas fa-file-medical"></i></div>
        <button type="button" onclick="removePreview(${index})"><i class="fas fa-times"></i></button>`;
    }
    preview.appendChild(div);
  });
}

function removePreviewByName(name) {
  selectedFiles = selectedFiles.filter((f) => f.name !== name);
  const dt = new DataTransfer();
  selectedFiles.forEach((file) => dt.items.add(file));
  document.getElementById("imagenes").files = dt.files;
  mostrarPreviewImagenes(selectedFiles);
}

document
  .getElementById("analisis-form")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    if (!currentPatient)
      return showAlert("Error", "Debe buscar un paciente primero", "error");
    if (selectedFiles.length === 0)
      return showAlert("Error", "Debe seleccionar imágenes", "error");

    try {
      validarArchivos(selectedFiles);
    } catch (error) {
      return showAlert("Error", error.message, "error");
    }

    Swal.fire({
      title: "¿Proceder con el análisis?",
      html: `Se analizarán <b>${selectedFiles.length}</b> imagen(es) para <b>${currentPatient.nombres} ${currentPatient.apellidos}</b>`,
      icon: "question",
      showCancelButton: true,
      confirmButtonText: "Sí, continuar",
      cancelButtonText: "Cancelar",
    }).then((result) => {
      if (result.isConfirmed) procesarAnalisis();
    });
  });

function procesarAnalisis() {
  const formData = new FormData();
  formData.append("paciente_id", currentPatient.id);

  // Agregar cada archivo con información adicional
  selectedFiles.forEach((file, index) => {
    formData.append("imagenes", file);
    formData.append(`imagen_${index}_nombre`, file.name);
    formData.append(`imagen_${index}_tipo`, file.type);
  });

  const csrfToken = getCSRFToken();

  if (!csrfToken) {
    return showAlert(
      "Error",
      "No se pudo obtener el token de seguridad. Recargue la página.",
      "error"
    );
  }

  Swal.fire({
    title: "Analizando...",
    text: "Procesando imágenes médicas...",
    allowOutsideClick: false,
    showConfirmButton: false,
    didOpen: () => Swal.showLoading(),
  });

  // Configurar timeout más largo para el procesamiento de imágenes
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutos

  fetch("/api/procesar-analisis/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": csrfToken,
      "X-Requested-With": "XMLHttpRequest",
      // NO incluir Content-Type cuando usas FormData
    },
    signal: controller.signal,
  })
    .then((res) => {
      clearTimeout(timeoutId);

      if (!res.ok) {
        return res.text().then((text) => {
          let errorMsg = `Error HTTP ${res.status}`;
          try {
            const errorData = JSON.parse(text);
            errorMsg = errorData.error || errorMsg;
          } catch (e) {
            // Si no es JSON válido, usar el texto tal como está
            if (text.length > 0 && text.length < 200) {
              errorMsg = text;
            }
          }
          throw new Error(errorMsg);
        });
      }
      return res.json();
    })
    .then((data) => {
      Swal.close();
      console.log("Respuesta del servidor:", data); // Para debugging

      if (data.success) {
        mostrarResultados(data.resultados);
      } else {
        showAlert("Error", data.error || "Error en el análisis", "error");
      }
    })
    .catch((error) => {
      clearTimeout(timeoutId);
      Swal.close();
      console.error("Error completo:", error);

      let errorMessage = "Error de red al procesar imágenes";

      if (error.name === "AbortError") {
        errorMessage =
          "El procesamiento tomó demasiado tiempo. Intente con imágenes más pequeñas.";
      } else if (error.message) {
        errorMessage = error.message;
      }

      showAlert("Error", errorMessage, "error");
    });
}

function mostrarResultados(resultados) {
  // Información básica del paciente y análisis
  document.getElementById("result_patient_name").textContent =
    resultados.paciente;
  document.getElementById("analysis_date").textContent = resultados.fecha;
  document.getElementById("images_count").textContent =
    resultados.imagenes_procesadas;

  // Procesar múltiples resultados (puede haber varios por las múltiples imágenes)
  const todosResultados = resultados.resultados || [];

  // Consolidar diagnósticos (tomar el de mayor confianza o el primero)
  let mejorResultado = null;
  let mayorConfianza = 0;

  todosResultados.forEach((resultado) => {
    if (resultado.confianza > mayorConfianza) {
      mayorConfianza = resultado.confianza;
      mejorResultado = resultado;
    }
  });

  // Si no hay resultados, usar valores por defecto
  if (!mejorResultado && todosResultados.length > 0) {
    mejorResultado = todosResultados[0];
  }

  // Mostrar diagnóstico principal
  const diagnosisResults = document.getElementById("diagnosis_results");
  diagnosisResults.innerHTML = "";

  if (mejorResultado && mejorResultado.diagnostico) {
    const div = document.createElement("div");
    div.className = "alert alert-info";
    div.innerHTML = `
      <h6><i class="fas fa-stethoscope"></i> Diagnóstico Principal</h6>
      <strong>${mejorResultado.diagnostico}</strong>
      ${
        mejorResultado.severidad
          ? `<br><small class="text-muted">Severidad: ${mejorResultado.severidad}</small>`
          : ""
      }
    `;
    diagnosisResults.appendChild(div);
  }

  // Mostrar hallazgos consolidados
  const findingsList = document.getElementById("main_findings");
  findingsList.innerHTML = "";

  // Recopilar todos los hallazgos únicos
  const todosHallazgos = new Set();
  todosResultados.forEach((resultado) => {
    if (resultado.hallazgos && Array.isArray(resultado.hallazgos)) {
      resultado.hallazgos.forEach((h) => todosHallazgos.add(h));
    }
  });

  // Mostrar hallazgos únicos
  Array.from(todosHallazgos).forEach((hallazgo) => {
    const li = document.createElement("li");
    li.innerHTML = `<i class="fas fa-check-circle text-success me-2"></i> ${hallazgo}`;
    findingsList.appendChild(li);
  });

  // Mostrar confianza (del mejor resultado)
  const confidenceFill = document.getElementById("confidence_fill");
  const confidenceText = document.getElementById("confidence_text");
  const porcentaje = mejorResultado ? mejorResultado.confianza || 0 : 0;
  confidenceFill.style.width = `${porcentaje}%`;
  confidenceText.textContent = `Confianza: ${porcentaje}%`;

  if (porcentaje >= 80) {
    confidenceFill.style.background =
      "linear-gradient(90deg, #059669, #34d399)";
  } else if (porcentaje >= 60) {
    confidenceFill.style.background =
      "linear-gradient(90deg, #d97706, #fbbf24)";
  } else {
    confidenceFill.style.background =
      "linear-gradient(90deg, #dc2626, #f87171)";
  }

  // Mostrar recomendaciones (del mejor resultado)
  const recomendaciones = mejorResultado
    ? mejorResultado.recomendaciones || ""
    : "";
  document.getElementById("recommendations").textContent = recomendaciones;

  // Preparar imágenes para mostrar
  const imagenesParaMostrar = [];
  todosResultados.forEach((resultado, index) => {
    // Imagen original
    if (resultado.imagen_url) {
      imagenesParaMostrar.push({
        url: resultado.imagen_url,
        tipo: `Imagen Original ${index + 1}`,
        categoria: "original",
      });
    }

    // Imagen procesada
    if (resultado.procesada_url) {
      imagenesParaMostrar.push({
        url: resultado.procesada_url,
        tipo: `Imagen Procesada ${index + 1}`,
        categoria: "procesada",
      });
    }

    // GradCAM
    if (resultado.gradcam_url) {
      imagenesParaMostrar.push({
        url: resultado.gradcam_url,
        tipo: `GradCAM ${index + 1}`,
        categoria: "gradcam",
      });
    }
  });

  mostrarImagenesResultado(imagenesParaMostrar);

  // Mostrar sección de resultados
  const section = document.getElementById("resultados_section");
  section.style.display = "block";
  section.scrollIntoView({ behavior: "smooth" });

  // Guardar ID del diagnóstico
  window.currentAnalysisId = resultados.diagnostico_id;

  console.log("Resultados procesados:", {
    totalImagenes: imagenesParaMostrar.length,
    diagnosticoId: resultados.diagnostico_id,
    mejorResultado: mejorResultado,
  });
}
function mostrarImagenesResultado(imagenes) {
  const container = document.getElementById("imagenes_resultado_container");
  container.innerHTML = "";

  if (!imagenes || imagenes.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; color:gray;">
        <p style="font-size: 1.2rem;">No hay imágenes para mostrar</p>
      </div>`;
    return;
  }

  imagenes.forEach((img, idx) => {
    const div = document.createElement("div");
    div.className = "card";

    const categoria = img.categoria || "imagen";
    let badgeClass = "badge";
    if (categoria === "original") badgeClass += " original";
    else if (categoria === "procesada") badgeClass += " procesada";
    else if (categoria === "gradcam") badgeClass += " gradcam";

    div.innerHTML = `
      <div style="position: relative;">
        <img src="${img.url}" alt="${img.tipo}" class="card-img"
             onclick="abrirModalImagen('${img.url}', '${img.tipo}')"
             onerror="this.src='https://via.placeholder.com/400x220?text=Imagen+no+disponible'">
        <span class="${badgeClass}">${categoria}</span>
      </div>
      <div style="padding: 0.5rem 1rem;">
        <h4 style="font-size: 1rem; margin: 0 0 0.25rem;">${img.tipo}</h4>
        <small style="color: #666;">Imagen ${idx + 1}</small>
      </div>
    `;

    container.appendChild(div);
  });
}
let scale = 1.5; // Comienza con un zoom inicial
let isDragging = false;
let startX, startY;
let scrollLeft, scrollTop;
function abrirModalImagen(src) {
  const modal = document.getElementById("modalImagen");
  const img = document.getElementById("modalImagenVista");
  const container = document.getElementById("modalZoomContainer");

  img.src = src;
  scale = 1.5; // Zoom inicial
  img.style.transform = `scale(${scale})`;
  modal.style.display = "flex";

  // Centrar imagen después de un pequeño delay
  setTimeout(() => {
    container.scrollLeft =
      (img.clientWidth * scale - container.clientWidth) / 2;
    container.scrollTop =
      (img.clientHeight * scale - container.clientHeight) / 2;
  }, 100);
}

function cerrarModalImagen() {
  const modal = document.getElementById("modalImagen");
  modal.style.display = "none";
}

// Zoom scroll
document
  .getElementById("modalZoomContainer")
  .addEventListener("wheel", function (e) {
    e.preventDefault();
    const img = document.getElementById("modalImagenVista");
    const zoomSpeed = 0.1;
    scale += e.deltaY < 0 ? zoomSpeed : -zoomSpeed;
    scale = Math.max(1, Math.min(scale, 5)); // Limita el zoom entre 1x y 5x
    img.style.transform = `scale(${scale})`;
  });

// Drag para mover
const container = document.getElementById("modalZoomContainer");

container.addEventListener("mousedown", (e) => {
  isDragging = true;
  container.style.cursor = "grabbing";
  startX = e.pageX;
  startY = e.pageY;
  scrollLeft = container.scrollLeft;
  scrollTop = container.scrollTop;
});

container.addEventListener("mouseup", () => {
  isDragging = false;
  container.style.cursor = "grab";
});

container.addEventListener("mousemove", (e) => {
  if (!isDragging) return;
  e.preventDefault();
  const x = e.pageX - startX;
  const y = e.pageY - startY;
  container.scrollLeft = scrollLeft - x;
  container.scrollTop = scrollTop - y;
});

container.addEventListener("mouseleave", () => {
  isDragging = false;
  container.style.cursor = "grab";
});

// Listener global para abrir el modal desde las imágenes procesadas
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("imagen-procesada")) {
    abrirModalImagen(e.target.src);
  }
});
// function generarPDF(diagnosticoId) {
//   Swal.fire({
//     title: 'Generando PDF...',
//     text: 'Esto puede tardar unos segundos',
//     allowOutsideClick: false,
//     didOpen: () => {
//       Swal.showLoading();
//     }
//   });

//   setTimeout(() => {
//     Swal.close();
//     window.location.href = `/pdf_report/?id=${diagnosticoId}`;
//   }, 1500);
// }
