import gradio as gr
import os
import subprocess
import time
import shutil
import tempfile
import glob

# Configuración de carpetas
BASE_DIR = r"c:\Users\casti\.gemini\Agentes\Real-ESRGAN"
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
SCRIPT_PATH = os.path.join(BASE_DIR, "inference_realesrgan.py")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def upscale_batch(files, scale_factor):
    if not files:
        return None, None, "Por favor, sube al menos una imagen (o selecciona una carpeta)."
    
    # Creamos un directorio temporal para alojar las imágenes de entrada
    temp_input_dir = tempfile.mkdtemp(prefix="realesr_in_")
    
    # Copiamos todos los archivos subidos al directorio temporal
    for file_obj in files:
        file_path = file_obj if isinstance(file_obj, str) else file_obj.name
        # Preservar el nombre base original en lo posible
        base_name = os.path.basename(file_path)
        dest_path = os.path.join(temp_input_dir, base_name)
        shutil.copy(file_path, dest_path)
    
    timestamp = int(time.time())
    factor = scale_factor.replace("x", "")
    
    # Creamos una subcarpeta específica para este lote en outputs
    batch_output_dir = os.path.join(OUTPUT_DIR, f"lote_{factor}x_{timestamp}")
    os.makedirs(batch_output_dir, exist_ok=True)
    
    # Comando para ejecutar Real-ESRGAN sobre TODA la carpeta a la vez
    command = [
        "python", 
        SCRIPT_PATH,
        "-i", temp_input_dir,
        "-o", batch_output_dir,
        "--outscale", factor,
        "-n", "RealESRGAN_x4plus"
    ]
    
    try:
        # Ejecutamos el script de renderizado por lotes
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        # Leemos los resultados generados
        generated_files = glob.glob(os.path.join(batch_output_dir, "*.*"))
        
        if not generated_files:
            return None, None, f"Error: no se generaron archivos.\nDetalles: {stderr}"
            
        return generated_files, generated_files, f"¡Listo! Se renderizaron {len(generated_files)} imágenes exitosamente."
        
    except Exception as e:
        return None, None, f"Error técnico: {e}"
    finally:
        # Limpiamos los archivos temporales de entrada para no llenar el disco duro
        try:
            shutil.rmtree(temp_input_dir)
        except:
            pass

# Interfaz Gradio
with gr.Blocks(title="Estudio de Renderizado Multi-Imágenes") as demo:
    gr.Markdown("# 🔍 Estudio de Escalado 4K/8K (Real-ESRGAN)")
    gr.Markdown("Transforma tus fotos generadas en imágenes Ultra HD de alta resolución. ¡Ahora puedes procesar múltiples archivos o carpetas completas de una vez!")
    
    with gr.Row():
        with gr.Column():
            # gr.File soporta subir múltiples imágenes, o arrastrar una carpeta que contenga imágenes
            input_files = gr.File(
                label="Sube tus fotos, o arrastra una carpeta aquí", 
                file_count="multiple",
                type="filepath" # En Gradio antiguo
            )
            scale_dropdown = gr.Dropdown(
                choices=["2x", "4x", "8x"], 
                value="4x", 
                label="Factor de Escalado (Resolución final deseada)"
            )
            btn = gr.Button("✨ EMPREzar RENDERIZADO POR LOTES", variant="primary")
        
        with gr.Column():
            status = gr.Textbox(label="Estado del Renderizado")
            output_gallery = gr.Gallery(label="Fotos Renderizadas", columns=2, object_fit="contain", height="auto")
            output_files = gr.File(label="Descargar Archivos Originales (o búscalas en la carpeta outputs)")

    btn.click(
        fn=upscale_batch,
        inputs=[input_files, scale_dropdown],
        outputs=[output_gallery, output_files, status]
    )

    gr.Markdown("---")
    gr.Markdown("💡 **Tip de Flujo de Trabajo:** Las imágenes procesadas se organizarán automáticamente en subcarpetas dentro de `IA-Tools\Real-ESRGAN\outputs`. Recuerda que cálculos en **8x** exigirán mucha potencia computacional y podrían tardar un poco más.")

if __name__ == "__main__":
    demo.launch(server_port=8897, allowed_paths=[OUTPUT_DIR], inbrowser=True)

