
from io import BytesIO

import pytest
from PIL import Image

from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def make_image(color=(100, 100, 100), size=(32, 32), image_format="PNG"):
    image = Image.new("RGB", size, color)
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    buffer.seek(0)
    return buffer


def make_pattern_image():
    image = Image.new("RGB", (32, 32), "black")
    for x in range(16, 32):
        for y in range(32):
            image.putpixel((x, y), (255, 255, 255))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def read_result(response):
    assert response.status_code == 200
    assert response.mimetype == "image/png"

    image = Image.open(BytesIO(response.data))
    image.load()
    return image.convert("RGB")


def process(client, operation, image=None, filename="sample.png", **fields):
    if image is None:
        image = make_pattern_image()

    data = {
        "image": (image, filename),
        "operation": operation,
        **fields,
    }

    return client.post(
        "/api/process",
        data=data,
        content_type="multipart/form-data",
    )


def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["service"] == "PixelLab"


@pytest.mark.parametrize(
    "operation",
    ["grayscale", "blur", "sharpen", "edges", "brightness", "sepia"],
)
def test_all_operations_return_png(client, operation):
    response = process(client, operation, brightness="120")

    result = read_result(response)

    assert result.size == (32, 32)


def test_grayscale_removes_color(client):
    response = process(
        client,
        "grayscale",
        image=make_image((200, 50, 20)),
    )

    pixel = read_result(response).getpixel((10, 10))

    assert pixel[0] == pixel[1] == pixel[2]


def test_blur_changes_a_sharp_boundary(client):
    response = process(client, "blur", image=make_pattern_image())

    result = read_result(response)

    assert result.getpixel((15, 16)) != (0, 0, 0)



def test_sharpen_processes_a_pattern(client):
    image = Image.new("RGB", (32, 32), (120, 120, 120))

    for x in range(32):
        for y in range(32):
            value = 80 + ((x * 17 + y * 13) % 90)
            image.putpixel((x, y), (value, value, value))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    original = image.copy()
    response = process(client, "sharpen", image=buffer)
    result = read_result(response)

    assert result.size == original.size
    assert list(result.getdata()) != list(original.getdata())



def test_edge_detection_finds_edges(client):
    response = process(client, "edges", image=make_pattern_image())

    result = read_result(response)

    assert max(max(pixel) for pixel in result.getdata()) > 0


def test_brightness_can_be_reduced(client):
    response = process(
        client,
        "brightness",
        image=make_image((100, 100, 100)),
        brightness="50",
    )

    pixel = read_result(response).getpixel((10, 10))

    assert all(45 <= channel <= 55 for channel in pixel)


def test_brightness_can_be_increased(client):
    response = process(
        client,
        "brightness",
        image=make_image((100, 100, 100)),
        brightness="150",
    )

    pixel = read_result(response).getpixel((10, 10))

    assert all(145 <= channel <= 155 for channel in pixel)


def test_sepia_adds_warm_tones(client):
    response = process(
        client,
        "sepia",
        image=make_image((128, 128, 128)),
    )

    red, green, blue = read_result(response).getpixel((10, 10))

    assert red > green > blue


def test_jpeg_upload_is_supported(client):
    response = process(
        client,
        "grayscale",
        image=make_image((120, 80, 40), image_format="JPEG"),
        filename="photo.jpg",
    )

    result = read_result(response)

    assert result.size == (32, 32)


def test_download_has_meaningful_filename(client):
    response = process(
        client,
        "grayscale",
        filename="sunset.png",
    )

    assert "sunset_grayscale.png" in response.headers["Content-Disposition"]


def test_missing_image_is_rejected(client):
    response = client.post(
        "/api/process",
        data={"operation": "grayscale"},
    )

    assert response.status_code == 400
    assert "error" in response.json


def test_missing_operation_is_rejected(client):
    response = client.post(
        "/api/process",
        data={"image": (make_image(), "sample.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400


def test_invalid_operation_is_rejected(client):
    response = process(client, "not-a-real-operation")

    assert response.status_code == 400


def test_unsupported_extension_is_rejected(client):
    response = process(
        client,
        "grayscale",
        filename="sample.gif",
    )

    assert response.status_code == 400


def test_corrupted_image_is_rejected(client):
    response = process(
        client,
        "grayscale",
        image=BytesIO(b"this is not a real image"),
        filename="corrupted.png",
    )

    assert response.status_code == 400


@pytest.mark.parametrize("brightness", ["", "abc", "19", "201", "-10"])
def test_invalid_brightness_is_rejected(client, brightness):
    response = process(
        client,
        "brightness",
        brightness=brightness,
    )

    assert response.status_code == 400


def test_upload_over_size_limit_is_rejected(client):
    oversized_file = BytesIO(b"x" * (8 * 1024 * 1024 + 1))

    response = process(
        client,
        "grayscale",
        image=oversized_file,
        filename="large.png",
    )

    
def test_pipeline_failure_demo():
    assert False, "Intentional failure to verify CI/CD pipeline"


    assert response.status_code == 413
    assert "error" in response.json
