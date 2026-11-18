from django.test import SimpleTestCase


class HealthCheckTests(SimpleTestCase):
    def test_health_endpoint_returns_ok(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})

    def test_health_endpoint_only_accepts_get(self):
        response = self.client.post("/api/health/")

        self.assertEqual(response.status_code, 405)