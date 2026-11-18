from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.inventory.models import StockLocation


User = get_user_model()


class FieldAgentTransferLocationTests(APITestCase):
	def setUp(self):
		self.agent = User.objects.create_user(
			username="field-agent", phone="0712345678",
			password="Secret123", role="FIELD_AGENT",
		)
		other_agent = User.objects.create_user(
			username="other-agent", phone="0712345679",
			password="Secret123", role="FIELD_AGENT",
		)
		self.assigned_location = StockLocation.objects.create(
			name="Agent Van", location_type=StockLocation.Type.FIELD,
			assigned_agent=self.agent,
		)
		self.shop_location = StockLocation.objects.create(
			name="Main Shop", location_type=StockLocation.Type.SHOP,
		)
		StockLocation.objects.create(
			name="Other Agent Van", location_type=StockLocation.Type.FIELD,
			assigned_agent=other_agent,
		)
		self.warehouse_location = StockLocation.objects.create(
			name="Warehouse", location_type=StockLocation.Type.WAREHOUSE,
		)
		self.client.force_authenticate(user=self.agent)

	def test_field_agent_can_select_assigned_and_shop_locations(self):
		response = self.client.get("/api/inventory/locations/")

		self.assertEqual(response.status_code, 200)
		locations = response.data.get("results", response.data)
		self.assertCountEqual(
			[location["id"] for location in locations],
			[self.assigned_location.id, self.shop_location.id],
		)

	def test_field_agent_cannot_transfer_to_an_unassigned_warehouse(self):
		response = self.client.post(
			"/api/inventory/transfers/",
			{
				"from_location": self.shop_location.id,
				"to_location": self.warehouse_location.id,
				"items": [{"product_id": 1, "quantity": "1"}],
			},
			format="json",
		)

		self.assertEqual(response.status_code, 403)
