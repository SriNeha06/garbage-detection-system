import io
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Minimal OpenCV compatibility layer for environments where cv2
# wheel is unavailable (e.g., Windows ARM Python).

COLOR_RGB2BGR = 1
LINE_AA = 16
FONT_HERSHEY_SIMPLEX = 0
INTER_AREA = 3
IMWRITE_JPEG_QUALITY = 1


def cvtColor(image_array, code):
    if code != COLOR_RGB2BGR:
        raise ValueError("Unsupported color conversion code")
    # Swap channels RGB <-> BGR
    return image_array[:, :, ::-1].copy()


def rectangle(img, pt1, pt2, color, thickness=1):
    x1, y1 = pt1
    x2, y2 = pt2
    pil = Image.fromarray(img[:, :, ::-1])  # BGR -> RGB
    draw = ImageDraw.Draw(pil)
    rgb = (int(color[2]), int(color[1]), int(color[0]))
    if thickness < 0:
        draw.rectangle([x1, y1, x2, y2], fill=rgb)
    else:
        for i in range(max(1, thickness)):
            draw.rectangle([x1 - i, y1 - i, x2 + i, y2 + i], outline=rgb)
    out = np.array(pil)[:, :, ::-1]  # RGB -> BGR
    img[:] = out
    return img


def getTextSize(text, font_face, font_scale, thickness):
    # Approximation sufficient for overlay layout.
    width = int(len(text) * 10 * max(0.4, font_scale))
    height = int(18 * max(0.4, font_scale))
    baseline = max(1, int(3 * max(0.4, font_scale)))
    return (width, height), baseline


def putText(img, text, org, font_face, font_scale, color, thickness=1, lineType=LINE_AA):
    x, y = org
    pil = Image.fromarray(img[:, :, ::-1])  # BGR -> RGB
    draw = ImageDraw.Draw(pil)
    rgb = (int(color[2]), int(color[1]), int(color[0]))
    try:
        font_size = max(12, int(20 * max(0.4, font_scale)))
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    draw.text((x, y - 14), text, fill=rgb, font=font)
    out = np.array(pil)[:, :, ::-1]  # RGB -> BGR
    img[:] = out
    return img


def addWeighted(src1, alpha, src2, beta, gamma, dst=None):
    blended = np.clip(src1.astype(np.float32) * alpha + src2.astype(np.float32) * beta + gamma, 0, 255).astype(np.uint8)
    if dst is not None:
        dst[:] = blended
        return dst
    return blended


def resize(image_array, dsize, interpolation=INTER_AREA):
    width, height = dsize
    pil = Image.fromarray(image_array[:, :, ::-1])  # BGR -> RGB
    pil = pil.resize((width, height), Image.Resampling.BILINEAR)
    return np.array(pil)[:, :, ::-1]  # RGB -> BGR


def imencode(fmt, image_array, params=None):
    fmt = fmt.lower().strip(".")
    if fmt in ("jpg", "jpeg"):
        pil_format = "JPEG"
    elif fmt == "png":
        pil_format = "PNG"
    elif fmt == "webp":
        pil_format = "WEBP"
    else:
        raise ValueError(f"Unsupported image format: {fmt}")

    pil = Image.fromarray(image_array[:, :, ::-1])  # BGR -> RGB
    buffer = io.BytesIO()
    save_kwargs = {}
    if params:
        # Handle [IMWRITE_JPEG_QUALITY, quality]
        if len(params) >= 2 and params[0] == IMWRITE_JPEG_QUALITY and pil_format == "JPEG":
            save_kwargs["quality"] = int(params[1])
    pil.save(buffer, format=pil_format, **save_kwargs)
    data = np.frombuffer(buffer.getvalue(), dtype=np.uint8)
    return True, data
