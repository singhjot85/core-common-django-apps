from core.apps.crm import get_customer_preference_type_model
from core.seeder.base import BaseMeta, BaseSeeder


class CustomerPreferenceTypeSeeder(BaseSeeder):
    """Production seeder for customer preference type definitions."""

    class Meta(BaseMeta):
        model = get_customer_preference_type_model()
        fields = ["code", "label", "data_type", "default_value", "values"]
        depends_on = []
        is_fixture = True
        relation_map = {}
