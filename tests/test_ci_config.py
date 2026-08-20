import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def test_github_workflow_exists_and_configured():
    workflow_path = BASE_DIR / ".github" / "workflows" / "docker-publish.yml"
    assert workflow_path.exists(), "docker-publish.yml workflow file must exist"

    content = workflow_path.read_text(encoding="utf-8")
    assert "name: CI & Docker Publish" in content
    assert "ghcr.io" in content
    assert "linux/amd64,linux/arm64" in content
    assert "docker/build-push-action" in content
    assert "pytest" in content


def test_docker_compose_uses_ghcr_image():
    compose_path = BASE_DIR / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"

    content = compose_path.read_text(encoding="utf-8")
    assert "image: ghcr.io/phimafusion/ausgabenplaner:latest" in content
    assert "3000:3000" in content
    assert "/app/data" in content


def test_dockerfile_validity():
    dockerfile_path = BASE_DIR / "Dockerfile"
    assert dockerfile_path.exists(), "Dockerfile must exist"

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in content
    assert "EXPOSE 3000" in content
    assert 'CMD ["uvicorn", "app.main:app"' in content
    assert "ADMIN_PASSWORD" not in content
    assert "COPY tests/ ./tests/" in content
    assert "COPY pytest.ini ." in content


def test_requirements_include_test_dependencies_for_container_runner():
    req_path = BASE_DIR / "requirements.txt"
    assert req_path.exists()
    content = req_path.read_text(encoding="utf-8")
    assert "pytest" in content
    assert "httpx" in content
    assert "pytest-cov" in content
