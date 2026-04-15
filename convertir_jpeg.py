"""
convertir_jpeg.py
-----------------
Script del pipeline Fotos-Premium.
Convierte las imágenes PNG escaladas (Real-ESRGAN) a JPEG de alta calidad
con perfil de color sRGB embebido.

Uso desde el agente:
    python convertir_jpeg.py --input_dir "...\\escaladas" --output_dir "...\\jpeg"
"""

import os
import sys
import argparse
from PIL import Image, ImageCms

def obtener_perfil_srgb():
    """
    Devuelve un perfil ICC sRGB usando Pillow ImageCms.
    Este perfil garantiza que los JPEG sean reconocidos como sRGB
    por Photoshop, Lightroom, navegadores y bancos de imágenes.
    """
    return ImageCms.createProfile("sRGB")

def convertir_a_jpg(ruta_png: str, ruta_dest: str) -> str:
    """
    Convierte una imagen PNG a JPEG con perfil sRGB embebido.

    Args:
        ruta_png:   Ruta completa al archivo PNG de entrada.
        ruta_dest:  Carpeta donde se guardará el JPEG resultante.

    Returns:
        Ruta completa del archivo JPEG generado.
    """
    img = Image.open(ruta_png)

    # Paso 1: Aplanar transparencia si existe (PNG con canal Alpha o paleta)
    if img.mode in ("RGBA", "P", "LA"):
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        fondo.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = fondo
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Paso 2: Convertir al espacio de color sRGB y embeber el perfil ICC
    perfil_srgb = obtener_perfil_srgb()
    img_con_perfil = ImageCms.profileToProfile(
        img,
        ImageCms.ImageCmsProfile(perfil_srgb),  # origen: sRGB (asumimos fuente sRGB)
        ImageCms.ImageCmsProfile(perfil_srgb),  # destino: sRGB embebido
        renderingIntent=ImageCms.Intent.PERCEPTUAL,
        outputMode="RGB"
    )

    # Paso 3: Construir nombre del archivo de salida
    nombre_base = os.path.splitext(os.path.basename(ruta_png))[0]
    nombre_jpeg = nombre_base + ".jpg"
    ruta_salida = os.path.join(ruta_dest, nombre_jpeg)

    # Paso 4: Guardar como JPEG con máxima calidad
    # - quality=95:     balance entre peso y calidad visual impecable
    # - subsampling=0:  4:4:4 – sin pérdida de detalle en color (modo profesional)
    # - icc_profile:    embebe el perfil sRGB en los metadatos EXIF del JPEG
    img_con_perfil.save(
        ruta_salida,
        format="JPEG",
        quality=95,
        subsampling=0,
        icc_profile=ImageCms.ImageCmsProfile(perfil_srgb).tobytes()
    )

    return ruta_salida


def procesar_carpeta(input_dir: str, output_dir: str):
    """
    Convierte todos los PNG de una carpeta a JPEG sRGB.
    """
    os.makedirs(output_dir, exist_ok=True)

    extensiones_validas = (".png", ".jpg", ".jpeg")
    pngs = [f for f in os.listdir(input_dir) if f.lower().endswith(extensiones_validas)]
    if not pngs:
        print(f"[AVISO] No se encontraron archivos PNG en: {input_dir}")
        return

    total = len(pngs)
    for idx, archivo in enumerate(pngs, 1):
        ruta_png = os.path.join(input_dir, archivo)
        print(f"[{idx}/{total}] Convirtiendo: {archivo} ...")
        ruta_jpeg = convertir_a_jpg(ruta_png, output_dir)
        size_mb = os.path.getsize(ruta_jpeg) / (1024 * 1024)
        print(f"         -> Guardado: {os.path.basename(ruta_jpeg)} ({size_mb:.2f} MB)")

    print(f"\n[OK] {total} imagenes convertidas a JPEG sRGB en: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convierte PNGs escalados a JPEG con perfil sRGB embebido."
    )
    parser.add_argument(
        "--input_dir",
        required=True,
        help="Carpeta con los PNG escalados (Real-ESRGAN output)"
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Carpeta de destino para los JPEG resultantes"
    )
    args = parser.parse_args()
    procesar_carpeta(args.input_dir, args.output_dir)
