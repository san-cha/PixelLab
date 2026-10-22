
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

OPERATIONS = {
    "grayscale",
    "blur",
    "sharpen",
    "edges",
    "brightness",
    "sepia",
}


def process_image(image, operation, brightness=100):
    if operation not in OPERATIONS:
        raise ValueError("Unsupported processing operation.")

    image = ImageOps.exif_transpose(image).convert("RGB")

    if operation == "grayscale":
        return ImageOps.grayscale(image).convert("RGB")

    if operation == "blur":
        return image.filter(ImageFilter.GaussianBlur(radius=2.5))

    if operation == "sharpen":
        return image.filter(
            ImageFilter.UnsharpMask(radius=2, percent=180, threshold=3)
        )

    if operation == "edges":
        return image.filter(ImageFilter.FIND_EDGES).convert("RGB")

    if operation == "brightness":
        if isinstance(brightness, bool) or not isinstance(brightness, int):
            raise ValueError("Brightness must be an integer.")
        if not 20 <= brightness <= 200:
            raise ValueError("Brightness must be between 20 and 200.")
        return ImageEnhance.Brightness(image).enhance(brightness / 100)

    if operation == "sepia":
        grayscale = ImageOps.grayscale(image)
        return ImageOps.colorize(
            grayscale,
            black="#2b2118",
            white="#f4dfb5",
        ).convert("RGB")

    raise ValueError("Unsupported processing operation.")
#img proc