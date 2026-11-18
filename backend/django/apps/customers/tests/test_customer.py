from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.customers.models import Customer


User = get_user_model()


class CustomerTests(APITestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.helper = User.objects.create_user(
            username="helper", phone="0722222222",
            password="Secret123", role="SALES_HELPER",
        )
        self.agent = User.objects.create_user(
            username="agent", phone="0733333333",
            password="Secret123", role="FIELD_AGENT",
        )

    def test_create_customer_auto_code(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/customers/",
            {"name": "Acme", "phone": "0744444444", "customer_type": "RESELLER"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        c = Customer.objects.get(phone="0744444444")
        self.assertTrue(c.code.startswith("CUST"))

    def test_duplicate_phone_rejected(self):
        Customer.objects.create(
            code="CUST-0001", name="A", phone="0755555555",
            customer_type="RETAIL",
        )
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/customers/",
            {"name": "B", "phone": "0755555555", "customer_type": "RETAIL"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_invalid_phone_rejected(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/customers/",
            {"name": "Bad", "phone": "12345", "customer_type": "RETAIL"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_helper_cannot_set_credit_limit(self):
        self.client.force_authenticate(self.helper)
        res = self.client.post(
            "/api/customers/",
            {
                "name": "X", "phone": "0766666666",
                "customer_type": "RESELLER", "credit_limit": 5000,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_walkin_singleton(self):
        self.client.force_authenticate(self.boss)
        r1 = self.client.get("/api/customers/walk-in/")
        r2 = self.client.get("/api/customers/walk-in/")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.data["id"], r2.data["id"])

    def test_helper_cannot_delete_customer(self):
        c = Customer.objects.create(
            code="CUST-0002", name="X", phone="0777777777",
            customer_type="RETAIL",
        )
        self.client.force_authenticate(self.helper)
        res = self.client.delete(f"/api/customers/{c.pk}/")
        self.assertEqual(res.status_code, 403)

    def test_boss_can_delete_customer(self):
        c = Customer.objects.create(
            code="CUST-0003", name="X", phone="0788888888",
            customer_type="RETAIL",
        )
        self.client.force_authenticate(self.boss)
        res = self.client.delete(f"/api/customers/{c.pk}/")
        self.assertEqual(res.status_code, 204)

    def test_search_and_filter(self):
        Customer.objects.create(
            code="CUST-0004", name="Nakuru Motors",
            phone="0799999999", customer_type="RESELLER",
        )
        Customer.objects.create(
            code="CUST-0005", name="Walk Customer",
            phone="0788888889", customer_type="RETAIL",
        )
        self.client.force_authenticate(self.boss)
        res = self.client.get("/api/customers/?customer_type=RESELLER")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["name"], "Nakuru Motors")

    def test_customer_contacts_and_route_assignments_routes_resolve(self):
        self.client.force_authenticate(self.boss)
        contacts = self.client.get("/api/customers/contacts/?customer=1")
        assignments = self.client.get("/api/customers/route-assignments/?customer=1")

        self.assertEqual(contacts.status_code, 200)
        self.assertEqual(assignments.status_code, 200)