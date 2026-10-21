from unittest.mock import MagicMock, patch

from celery import shared_task
from celery.app.trace import build_tracer

from core.apps.tenants.tasks import provision_tenant_schema
from core.config.celery import celery_app
from core.config.celery.base import restore_schema_context, switch_schema_context


@shared_task(bind=True, ignore_result=True)
def dummy_parameter_task(self, tenant_id: str):
    return f"processed-{tenant_id}"


@shared_task(bind=True, ignore_result=True)
def dummy_failing_task(self):
    raise ValueError("forced failure for retry test")


class TestTenantAwareCeleryTasks:
    def test_tenant_aware_task_attributes(self):
        """Verify default 3x retry attributes on tasks."""
        assert dummy_parameter_task.autoretry_for == (Exception,)
        assert dummy_parameter_task.max_retries == 3
        assert dummy_parameter_task.default_retry_delay == 60

    def test_schema_name_stripped_before_task_execution(self):
        """Verify _schema_name is stripped from kwargs before task execution."""
        tracer = build_tracer(
            dummy_parameter_task.name, dummy_parameter_task, app=celery_app
        )
        kwargs = {"tenant_id": "test-uuid-123", "_schema_name": "public"}

        res = tracer("test-task-uuid-1", (), kwargs, request={})
        assert res.retval == "processed-test-uuid-123"

    def test_provision_tenant_schema_signature(self):
        """Verify provision_tenant_schema has explicit tenant_id signature."""
        import inspect

        sig = inspect.signature(provision_tenant_schema)
        params = list(sig.parameters.keys())
        # Bound tasks have 'self' bound at runtime, signature shows tenant_id
        assert "tenant_id" in params

    @patch("django.db.connection.set_schema_to_public")
    def test_switch_schema_context_public(self, mock_set_public):
        """Verify switch_schema_context correctly handles public schema without querying tenant model."""
        task = MagicMock()
        kwargs = {"tenant_id": "123", "_schema_name": "public"}

        with patch("django.db.connection.schema_name", "some_other_tenant"):
            switch_schema_context(task, kwargs)

        assert "_schema_name" not in kwargs
        mock_set_public.assert_called_once()

    @patch("django.db.connection.set_schema_to_public")
    @patch("django.db.connection.set_schema")
    def test_restore_schema_context(self, mock_set_schema, mock_set_public):
        """Verify restore_schema_context correctly restores previous schema."""
        task = MagicMock()
        task._old_schema = ("public", True)

        with patch("django.db.connection.schema_name", "tenant_a"):
            restore_schema_context(task)

        mock_set_public.assert_called_once()
        mock_set_schema.assert_not_called()

    def test_task_autoretry_on_failure(self):
        """Verify Celery task triggers retry on unhandled exception."""
        with patch.object(
            dummy_failing_task, "retry", wraps=dummy_failing_task.retry
        ) as mock_retry:
            try:
                dummy_failing_task.apply()
            except Exception:
                pass
            assert mock_retry.called
            assert mock_retry.call_count >= 1
