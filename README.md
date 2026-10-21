# PixelLab — Image Processing Studio

PixelLab is a web-based image processing application built with Python, Flask, and Pillow. Users can upload images, apply different image-processing operations, preview the results, and download the processed images.

The project demonstrates containerization and automated CI/CD using Docker, GitHub Actions, and GitHub Container Registry (GHCR).

## Features

- Upload JPG, JPEG, and PNG images
- Preview original and processed images
- Apply six image-processing operations:
  - Grayscale
  - Blur
  - Sharpen
  - Edge detection
  - Brightness adjustment
  - Sepia
- Download processed images as PNG files
- Validate uploaded files and processing parameters
- Enforce an 8 MB upload limit
- Run automated tests using pytest
- Build and publish Docker images automatically through GitHub Actions

## Technology Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Flask
- **Image Processing:** Pillow
- **Testing:** pytest
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions
- **Container Registry:** GitHub Container Registry (GHCR)
- **Version Control:** Git and GitHub

## Architecture

1. The user uploads an image through the web interface.
2. The Flask backend validates the file and selected operation.
3. Pillow processes the image in memory.
4. The processed image is returned for preview and download.
5. pytest verifies application functionality and input validation.
6. GitHub Actions runs the tests whenever code is pushed to `main` or a pull request targets `main`.
7. If tests pass on a push to `main`, the workflow builds the Docker image and publishes it to GHCR.

## Run Locally

### Prerequisites

- Python 3.13
- Docker Desktop

### Run with Docker Compose

Clone the repository:

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/PixelLab.git
cd PixelLab
```

Build and start the application:

```bash
docker compose up --build -d
```

Open the application:

http://localhost:5000

Check the service health:

```bash
curl http://localhost:5000/api/health
```

Expected response:

```json
{
  "service": "PixelLab",
  "status": "ok"
}
```

Stop the application:

```bash
docker compose down
```

### Run Tests

Create and activate a virtual environment, then install development dependencies:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies and run the test suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

## CI/CD Pipeline

The GitHub Actions workflow is located at `.github/workflows/ci-cd.yml`.

- **Continuous Integration:** Installs dependencies and runs the automated test suite.
- **Build:** Runs only after the test job succeeds.
- **Publish:** On successful pushes to `main`, publishes the Docker image to GHCR.
- **Pull requests:** Run tests without publishing an image.

If the test job fails, the dependent build-and-publish job is skipped.

### Published Docker Image

Registry: `ghcr.io/YOUR-GITHUB-USERNAME/pixellab`

Available tags:

- `latest` — the most recently published successful image.
- `sha-<commit-hash>` — identifies the image built from a specific commit.

Pull the image:

```bash
docker pull ghcr.io/YOUR-GITHUB-USERNAME/pixellab:latest
```

The published image is a container artifact. The workflow does not deploy the application to a cloud server; the application can run locally using Docker Desktop.

## Security and Validation

- Limits uploaded files to 8 MB.
- Accepts only supported image formats and validates actual image content.
- Rejects corrupted images and invalid processing parameters.
- Processes images in memory without storing user uploads permanently.
- Runs the application as a non-root user inside the container.
- Uses GitHub's automatically provided `GITHUB_TOKEN` for registry publishing.

## Project Structure

```text
PixelLab/
├── app/
│   ├── __init__.py
│   ├── image_processing.py
│   ├── static/
│   │   ├── app.js
│   │   └── style.css
│   └── templates/
│       └── index.html
├── tests/
│   └── test_app.py
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── .dockerignore
├── .gitignore
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── requirements-dev.txt
└── run.py
```

## Learning Outcomes

This project demonstrates web application development, image processing, automated testing, Docker containerization, version control, CI/CD workflow design, and container image publishing. It also demonstrates how automated tests can prevent a failed build from being published.

## Future Improvements

- Use a production WSGI server for container execution.
- Add image-processing options and configurable parameters.
- Add test coverage reporting and image vulnerability scanning.
- Improve accessibility and automated frontend testing.
