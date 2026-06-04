from __future__ import annotations

import pytest

from app.core.config import Settings, parse_cors

pytestmark = pytest.mark.unit

_SAFE = "a_secure_key_not_in_insecure_set_1234"

_PROD_SAFE = {
    "ENVIRONMENT": "production",
    "SECRET_KEY": _SAFE,
    "REFRESH_SECRET_KEY": _SAFE,
    "FIRST_SUPERUSER_PASSWORD": _SAFE,
    "MINIO_ACCESS_KEY": _SAFE,
    "MINIO_SECRET_KEY": _SAFE,
    "BACKEND_CORS_ORIGINS": "https://example.com",
}


def _make(**kwargs):
    return Settings(**{"_env_file": None, **kwargs})


def test_settings_defaults_in_local_env():
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
    )
    assert s.ENVIRONMENT == "local"


def test_settings_warns_on_default_secrets_in_local():
    with pytest.warns(UserWarning):
        _make(
            ENVIRONMENT="local",
            SECRET_KEY="changethis",
            REFRESH_SECRET_KEY=_SAFE,
            FIRST_SUPERUSER_PASSWORD=_SAFE,
            MINIO_ACCESS_KEY=_SAFE,
            MINIO_SECRET_KEY=_SAFE,
        )


def test_settings_raises_on_default_secrets_in_production():
    with pytest.raises(ValueError):
        _make(
            ENVIRONMENT="production",
            SECRET_KEY="changethis",
            REFRESH_SECRET_KEY=_SAFE,
            FIRST_SUPERUSER_PASSWORD=_SAFE,
            MINIO_ACCESS_KEY=_SAFE,
            MINIO_SECRET_KEY=_SAFE,
            BACKEND_CORS_ORIGINS="https://example.com",
        )


def test_settings_requires_cors_in_production():
    with pytest.raises(ValueError, match="CORS"):
        _make(
            ENVIRONMENT="production",
            SECRET_KEY=_SAFE,
            REFRESH_SECRET_KEY=_SAFE,
            FIRST_SUPERUSER_PASSWORD=_SAFE,
            MINIO_ACCESS_KEY=_SAFE,
            MINIO_SECRET_KEY=_SAFE,
            BACKEND_CORS_ORIGINS="",
        )


@pytest.mark.parametrize("quality", [0, 96])
def test_settings_validates_jpeg_quality_out_of_range(quality):
    with pytest.raises(ValueError):
        _make(
            SECRET_KEY=_SAFE,
            REFRESH_SECRET_KEY=_SAFE,
            FIRST_SUPERUSER_PASSWORD=_SAFE,
            MINIO_ACCESS_KEY=_SAFE,
            MINIO_SECRET_KEY=_SAFE,
            IMAGE_JPEG_QUALITY=quality,
        )


@pytest.mark.parametrize("quality", [1, 95])
def test_settings_validates_jpeg_quality_boundary_ok(quality):
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        IMAGE_JPEG_QUALITY=quality,
    )
    assert s.IMAGE_JPEG_QUALITY == quality


def test_sqlalchemy_database_uri_uses_pgbouncer_when_enabled():
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        USE_PGBOUNCER=True,
    )
    assert "pgbouncer" in str(s.sqlalchemy_database_uri)


def test_async_scheme_reflects_db_driver():
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        DB_DRIVER="psycopg",
    )
    assert "postgresql+psycopg" in str(s.sqlalchemy_database_uri)


def test_ollama_url_explicit_overrides_backend():
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        OLLAMA_BASE_URL="http://custom:11434",
        AI_BACKEND="docker",
    )
    assert s.ollama_url == "http://custom:11434"


def test_ollama_url_for_local_backend():
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        AI_BACKEND="local",
        OLLAMA_BASE_URL="",
    )
    assert s.ollama_url == s.OLLAMA_LOCAL_URL


def test_ollama_url_for_docker_backend():
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        AI_BACKEND="docker",
        OLLAMA_BASE_URL="",
    )
    assert s.ollama_url == s.OLLAMA_DOCKER_URL


def test_image_max_pixels_computed_from_mp():
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        IMAGE_MAX_PIXELS_MP=30,
    )
    assert s.image_max_pixels == 30_000_000


def test_allowed_image_types_list_parses_csv():
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        ALLOWED_IMAGE_TYPES="image/jpeg,image/png",
    )
    assert s.allowed_image_types_list == ["image/jpeg", "image/png"]


def test_parse_cors_handles_string_csv():
    result = parse_cors("a,b")
    assert result == ["a", "b"]


def test_parse_cors_handles_list():
    result = parse_cors(["x", "y"])
    assert result == ["x", "y"]


def test_all_cors_origins_strips_trailing_slash():
    s = _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        BACKEND_CORS_ORIGINS="https://test.com/",
    )
    assert "https://test.com" in s.all_cors_origins
    assert "https://test.com/" not in s.all_cors_origins


def _sentry_settings(**overrides):
    return _make(
        SECRET_KEY=_SAFE,
        REFRESH_SECRET_KEY=_SAFE,
        FIRST_SUPERUSER_PASSWORD=_SAFE,
        MINIO_ACCESS_KEY=_SAFE,
        MINIO_SECRET_KEY=_SAFE,
        **overrides,
    )


def test_sentry_defaults_are_off_and_safe():
    s = _sentry_settings()
    assert s.SENTRY_DSN == ""
    assert s.SENTRY_TRACES_SAMPLE_RATE == 0.0
    assert s.SENTRY_PROFILES_SAMPLE_RATE == 0.0
    assert s.SENTRY_SEND_DEFAULT_PII is False


@pytest.mark.parametrize("rate", [0.0, 0.1, 0.5, 1.0])
def test_sentry_traces_sample_rate_valid_range(rate):
    s = _sentry_settings(SENTRY_TRACES_SAMPLE_RATE=rate)
    assert s.SENTRY_TRACES_SAMPLE_RATE == rate


@pytest.mark.parametrize("rate", [-0.1, 1.1, 2.0])
def test_sentry_traces_sample_rate_rejects_out_of_range(rate):
    with pytest.raises(ValueError, match="sample rate"):
        _sentry_settings(SENTRY_TRACES_SAMPLE_RATE=rate)


@pytest.mark.parametrize("rate", [-0.5, 1.01])
def test_sentry_profiles_sample_rate_rejects_out_of_range(rate):
    with pytest.raises(ValueError, match="sample rate"):
        _sentry_settings(SENTRY_PROFILES_SAMPLE_RATE=rate)


def test_sentry_send_default_pii_allowed_in_local():
    # Local env must NOT enforce the PII guard — devs may want PII when
    # reproducing a user issue locally.
    s = _sentry_settings(SENTRY_SEND_DEFAULT_PII=True)
    assert s.SENTRY_SEND_DEFAULT_PII is True


def test_sentry_send_default_pii_rejected_in_production():
    with pytest.raises(ValueError, match="SENTRY_SEND_DEFAULT_PII"):
        _make(**_PROD_SAFE, SENTRY_SEND_DEFAULT_PII=True)


def test_sentry_send_default_pii_false_is_fine_in_production():
    s = _make(**_PROD_SAFE, SENTRY_SEND_DEFAULT_PII=False)
    assert s.SENTRY_SEND_DEFAULT_PII is False
