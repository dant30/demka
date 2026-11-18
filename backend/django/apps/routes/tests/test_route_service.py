from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import User
from apps.customers.models import Customer, CustomerRouteAssignment
from apps.routes.models import Route, RouteChangeLog
from apps.routes.services import RouteService


class RouteServiceTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.agent1 = User.objects.create_user(
            username="agent1", phone="0722222222",
            password="Secret123", role="FIELD_AGENT",
        )
        self.agent2 = User.objects.create_user(
            username="agent2", phone="0733333333",
            password="Secret123", role="FIELD_AGENT",
        )

    def test_create_with_schedule(self):
        route = RouteService.create(
            {
                "name": "Route A", "code": "ra",
                "default_agent": self.agent1,
                "schedule_days": [0, 2, 4],  # Mon, Wed, Fri
            },
            self.boss,
        )
        self.assertEqual(route.code, "RA")
        self.assertEqual(
            sorted(route.schedules.values_list("day_of_week", flat=True)),
            [0, 2, 4],
        )

    def test_create_with_agent_instance(self):
        route = RouteService.create(
            {"name": "Route B", "code": "RB", "default_agent": self.agent1},
            self.boss,
        )
        self.assertEqual(route.default_agent, self.agent1)

    def test_change_agent_logs_audit(self):
        route = RouteService.create(
            {"name": "Route A", "code": "RA", "default_agent": self.agent1},
            self.boss,
        )
        RouteService.change_default_agent(
            route.pk, self.agent2.pk, self.boss, "Agent 1 on leave",
        )
        route.refresh_from_db()
        self.assertEqual(route.default_agent_id, self.agent2.pk)

        log = RouteChangeLog.objects.get(route=route)
        self.assertEqual(log.change_type, "REASSIGN_AGENT")
        self.assertEqual(log.previous_agent_id, self.agent1.pk)
        self.assertEqual(log.new_agent_id, self.agent2.pk)
        self.assertEqual(log.reason, "Agent 1 on leave")

    def test_change_agent_requires_reason(self):
        from core.exceptions.domain import ValidationError
        route = RouteService.create(
            {"name": "Route A", "code": "RA"}, self.boss,
        )
        with self.assertRaises(ValidationError):
            RouteService.change_default_agent(
                route.pk, self.agent2.pk, self.boss, "",
            )

    def test_reassign_customers(self):
        r1 = RouteService.create({"name": "A", "code": "RA"}, self.boss)
        r2 = RouteService.create({"name": "B", "code": "RB"}, self.boss)

        c1 = Customer.objects.create(
            code="CUST-0001", name="Shop A", phone="0700000001",
            customer_type="RETAIL",
        )
        c2 = Customer.objects.create(
            code="CUST-0002", name="Shop B", phone="0700000002",
            customer_type="RETAIL",
        )
        from django.utils import timezone
        today = timezone.now().date()
        CustomerRouteAssignment.objects.create(
            customer=c1, route=r1, assigned_from=today,
        )
        CustomerRouteAssignment.objects.create(
            customer=c2, route=r1, assigned_from=today,
        )

        result = RouteService.reassign_customers(
            route_id=r1.pk, customer_ids=[c1.pk], target_route_id=r2.pk,
            user=self.boss, reason="Better coverage",
        )
        self.assertEqual(result["moved"], 1)
        # c1 now open-assigned to r2
        self.assertTrue(
            CustomerRouteAssignment.objects.filter(
                customer=c1, route=r2, assigned_to__isnull=True,
            ).exists()
        )
        # c1's old r1 assignment closed
        self.assertFalse(
            CustomerRouteAssignment.objects.filter(
                customer=c1, route=r1, assigned_to__isnull=True,
            ).exists()
        )

    def test_deactivate_refuses_with_open_runs(self):
        from core.exceptions.domain import ConflictError
        route = RouteService.create(
            {"name": "A", "code": "RA", "default_agent": self.agent1}, self.boss,
        )
        from apps.inventory.models import StockLocation
        from django.utils import timezone
        van = StockLocation.objects.create(
            name="Van", location_type="FIELD", assigned_agent=self.agent1,
        )
        from apps.routes.services import RouteRunService
        RouteRunService.create(
            {
                "route": route.pk, "stock_location": van.pk,
                "run_date": timezone.now().date(),
            },
            self.boss,
        )
        with self.assertRaises(ConflictError):
            RouteService.deactivate(route.pk, self.boss, "No longer needed")