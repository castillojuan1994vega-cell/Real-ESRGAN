import os
import subprocess
import time
import argparse
from PIL import Image, ImageCms

def obtener_perfil_srgb():
    """Devuelve un perfil ICC sRGB estándar."""
    return ImageCms.createProfile("sRGB")

def convertir_a_jpg_pro(ruta_fuente, ruta_final):
    """
    Convierte una imagen (normalmente PNG escalado) a JPEG con perfil sRGB embebido,
    calidad 95 y muestreo 4:4:4 (profesional).
    """
    img = Image.open(ruta_fuente)
    
    # Aplanar si hay transparencia
    if img.mode in ("RGBA", "P", "LA"):
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        fondo.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = fondo
    elif img.mode != "RGB":
        img = img.convert("RGB")

    perfil_srgb = obtener_perfil_srgb()
    # Aplicar perfil sRGB
    img_con_perfil = ImageCms.profileToProfile(
        img,
        ImageCms.ImageCmsProfile(perfil_srgb),
        ImageCms.ImageCmsProfile(perfil_srgb),
        renderingIntent=ImageCms.Intent.PERCEPTUAL,
        outputMode="RGB"
    )

    # Guardado profesional
    img_con_perfil.save(
        ruta_final,
        format="JPEG",
        quality=95,
        subsampling=0,
        icc_profile=ImageCms.ImageCmsProfile(perfil_srgb).tobytes()
    )

def main():
    parser = argparse.ArgumentParser(description="Procesado maestro: Escalado + Conversión sRGB + Limpieza.")
    parser.add_argument("--project_dir", required=True, help="Ruta de la carpeta del proyecto (ej: .../Hidroponia_Urbana_2026)")
    parser.add_argument("--prefix", help="Prefijo de los archivos (opcional, se deduce del nombre de la carpeta si no se da)")
    parser.add_argument("--tiles", type=int, default=400, help="Tamaño de tile para evitar Out of Memory en GPU (default 400)")
    
    args = parser.parse_args()
    
    project_dir = args.project_dir
    orig_dir = os.path.join(project_dir, "originales")
    esc_dir = os.path.join(project_dir, "escaladas")
    jpeg_dir = os.path.join(project_dir, "jpeg")
    
    # Asegurar carpetas
    os.makedirs(esc_dir, exist_ok=True)
    os.makedirs(jpeg_dir, exist_ok=True)
    
    # Deducir prefijo si no existe
    if not args.prefix:
        project_name = os.path.basename(project_dir.strip("\\/"))
        prefix = f"{project_name}_v"
    else:
        prefix = args.prefix
    
    # Rutas de herramientas
    python_exe = r"C:\Users\casti\.gemini\Agentes\Real-ESRGAN\.venv\Scripts\python.exe"
    inference_script = r"C:\Users\casti\.gemini\Agentes\Real-ESRGAN\inference_realesrgan.py"
    
    # Buscar archivos en 'originales'
    files = [f for f in os.listdir(orig_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not files:
        print(f"[ERROR] No hay archivos en {orig_dir}")
        return

    print(f"--- Iniciando PROCESADO MAESTRO para {len(files)} imagenes ---")
    print(f"Proyecto: {os.path.basename(project_dir)}")
    
    # Ordenar por numero si sigue el patron _vN
    try:
        files.sort(key=lambda x: int(x.split('_v')[-1].split('.')[0]) if '_v' in x else x)
    except:
        files.sort()

    for idx, filename in enumerate(files, 1):
        input_path = os.path.join(orig_dir, filename)
        
        # Nombre base sin extension
        base_name = os.path.splitext(filename)[0]
        # Real-ESRGAN añade _out por defecto o nosotros lo buscaremos
        escalada_path = os.path.join(esc_dir, f"{base_name}_out.png")
        final_jpg = os.path.join(jpeg_dir, f"{base_name}.jpg")

        if os.path.exists(final_jpg):
            print(f"[{idx}/{len(files)}] {base_name}.jpg YA EXISTE. Saltando.")
            continue

        print(f"\n--- [{idx}/{len(files)}] Escalando: {filename} ---")
        start_t = time.time()
        
        # 1. ESCALADO (PNG intermedio lossless)
        cmd_upscale = [
            python_exe, inference_script,
            "-n", "RealESRGAN_x4plus",
            "-i", input_path,
            "-o", esc_dir,
            "--outscale", "4",
            "-t", str(args.tiles),
            "--ext", "png",
            "--fp32"
        ]
        
        result = subprocess.run(cmd_upscale, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f" ERROR en escalado: {result.stderr}")
            continue
            
        # 2. CONVERSIÓN A JPEG sRGB PROFESIONAL
        if os.path.exists(escalada_path):
            try:
                print(f" [{idx}/{len(files)}] Convirtiendo a JPEG sRGB (Calidad Profesional)...")
                convertir_a_jpg_pro(escalada_path, final_jpg)
                
                # 3. LIMPIEZA (Borrar PNG intermedio)
                os.remove(escalada_path)
                
                elapsed = time.time() - start_t
                size_mb = os.path.getsize(final_jpg) / (1024 * 1024)
                print(f" [OK] Completo en {elapsed:.1f}s | {size_mb:.2f} MB")
            except Exception as e:
                print(f" ERROR en conversion: {e}")
        else:
            print(f" ERROR: No se genero el archivo {escalada_path}")

    print("\n--- ¡PROCESADO MAESTRO COMPLETADO! ---")
    print(f"Todas las imagenes estan en: {jpeg_dir}")

if __name__ == "__main__":
    main()
