import logging

from core.apps.users import get_user_model

LOGGER = logging.getLogger(__name__)


def create_system_user_callback(sender, **kwargs):
    """
    post_migrate signal handler to ensure the system user is provisioned.
    Runs once after the users app migrations are applied.
    """
    User = get_user_model()
    if hasattr(User, "create_system_user"):
        try:
            system_user = User.create_system_user()
            LOGGER.info(f"System user verified/provisioned: {system_user.username}")
            return system_user
        except Exception as e:
            LOGGER.warning(f"Failed to create system user during post_migrate: {e}")
            return None
    return None
