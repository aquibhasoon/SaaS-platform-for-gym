from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import TrainerPermission, User
from attendance.models import Attendance
from members.models import Member
from memberships.models import Membership, MembershipPlan, Payment
from trainers.models import TrainerMemberAssignment


class V1CoreBusinessTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="TestPassword123!",
            role="owner",
            is_active=True,
        )

        self.member_user = User.objects.create_user(
            username="member",
            password="TestPassword123!",
            role="member",
            is_active=True,
        )

        self.member = Member.objects.create(
            user=self.member_user,
            first_name="Test",
            last_name="Member",
            phone="9876543210",
            email="member@test.com",
            status="active",
            approval_status="approved",
        )

        self.plan = MembershipPlan.objects.create(
            name="Monthly Plan",
            duration_months=1,
            price=Decimal("1000.00"),
        )

    def test_member_created(self):
        self.assertEqual(
            Member.objects.count(),
            1,
        )

        self.assertEqual(
            self.member.full_name,
            "Test Member",
        )

    def test_member_id_generated(self):
        self.assertTrue(
            self.member.member_id.startswith("GYM"),
        )

    def test_member_is_approved(self):
        self.assertTrue(
            self.member.is_approved,
        )

    def test_membership_creation(self):
        membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
        )

        self.assertEqual(
            membership.member,
            self.member,
        )

    def test_membership_total_paid(self):
        membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
            amount=Decimal("1000.00"),
        )

        Payment.objects.create(
            membership=membership,
            amount=Decimal("400.00"),
            payment_method="cash",
        )

        self.assertEqual(
            membership.total_paid,
            Decimal("400.00"),
        )

    def test_membership_balance_due(self):
        membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
            amount=Decimal("1000.00"),
        )

        Payment.objects.create(
            membership=membership,
            amount=Decimal("400.00"),
            payment_method="cash",
        )

        self.assertEqual(
            membership.balance_due,
            Decimal("600.00"),
        )

    def test_membership_fully_paid(self):
        membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
            amount=Decimal("1000.00"),
        )

        Payment.objects.create(
            membership=membership,
            amount=Decimal("1000.00"),
            payment_method="cash",
        )

        self.assertTrue(
            membership.fully_paid,
        )

    def test_payment_receipt_number_generated(self):
        membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
            amount=Decimal("1000.00"),
        )

        payment = Payment.objects.create(
            membership=membership,
            amount=Decimal("500.00"),
            payment_method="cash",
        )

        self.assertTrue(
            payment.receipt_number.startswith("REC"),
        )

    def test_attendance_created(self):
        attendance = Attendance.objects.create(
            member=self.member,
            check_in=timezone.now(),
            check_in_date=timezone.localdate(),
        )

        self.assertEqual(
            attendance.member,
            self.member,
        )

    def test_attendance_member_relation(self):
        Attendance.objects.create(
            member=self.member,
            check_in=timezone.now(),
            check_in_date=timezone.localdate(),
        )

        self.assertEqual(
            self.member.attendance_records.count(),
            1,
        )

    def test_plan_price(self):
        self.assertEqual(
            self.plan.price,
            Decimal("1000.00"),
        )

    def test_membership_plan_relation(self):
        membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
        )

        self.assertEqual(
            membership.plan,
            self.plan,
        )

    def test_payment_membership_relation(self):
        membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
        )

        payment = Payment.objects.create(
            membership=membership,
            amount=Decimal("500.00"),
            payment_method="cash",
        )

        self.assertEqual(
            payment.membership,
            membership,
        )


class SecurityIntegrationTests(TestCase):

    def setUp(self):

        # -------------------------------------------------------------
        # Owner
        # -------------------------------------------------------------

        self.owner = User.objects.create_user(
            username="security_owner",
            password="TestPassword123!",
            role="owner",
            is_active=True,
        )

        # -------------------------------------------------------------
        # Trainer
        # -------------------------------------------------------------

        self.trainer = User.objects.create_user(
            username="security_trainer",
            password="TestPassword123!",
            role="trainer",
            is_active=True,
        )

        TrainerPermission.objects.create(
            user=self.trainer,
            can_view_members=True,
            can_add_members=True,
            can_edit_members=True,
            can_delete_members=True,
            can_view_attendance=True,
            can_scan_attendance=True,
            can_edit_attendance=True,
            can_view_memberships=True,
            can_create_memberships=True,
            can_renew_memberships=True,
            can_view_payments=True,
            can_add_payments=True,
            can_view_workouts=True,
            can_manage_workouts=True,
            can_view_progress=True,
            can_manage_progress=True,
            can_view_reports=True,
        )

        # -------------------------------------------------------------
        # Second trainer
        # -------------------------------------------------------------

        self.other_trainer = User.objects.create_user(
            username="security_other_trainer",
            password="TestPassword123!",
            role="trainer",
            is_active=True,
        )

        TrainerPermission.objects.create(
            user=self.other_trainer,
            can_view_members=True,
            can_add_members=True,
            can_edit_members=True,
            can_delete_members=True,
            can_view_attendance=True,
            can_scan_attendance=True,
            can_edit_attendance=True,
            can_view_memberships=True,
            can_create_memberships=True,
            can_renew_memberships=True,
            can_view_payments=True,
            can_add_payments=True,
            can_view_workouts=True,
            can_manage_workouts=True,
            can_view_progress=True,
            can_manage_progress=True,
            can_view_reports=True,
        )

        # -------------------------------------------------------------
        # Member user
        # -------------------------------------------------------------

        self.member_user = User.objects.create_user(
            username="security_member",
            password="TestPassword123!",
            role="member",
            is_active=True,
        )

        # -------------------------------------------------------------
        # Main member
        # -------------------------------------------------------------

        self.member = Member.objects.create(
            user=self.member_user,
            first_name="Security",
            last_name="Member",
            phone="9876543210",
            email="securitymember@test.com",
            status="active",
            approval_status="approved",
        )

        # -------------------------------------------------------------
        # Second member
        # -------------------------------------------------------------

        self.other_member = Member.objects.create(
            first_name="Other",
            last_name="Member",
            phone="9876543211",
            email="othermember@test.com",
            status="active",
            approval_status="approved",
        )

        # -------------------------------------------------------------
        # Active trainer/member assignment
        # -------------------------------------------------------------

        self.assignment = TrainerMemberAssignment.objects.create(
            trainer=self.trainer,
            member=self.member,
            assigned_by=self.owner,
            is_active=True,
        )

        # -------------------------------------------------------------
        # Membership plan
        # -------------------------------------------------------------

        self.plan = MembershipPlan.objects.create(
            name="Security Test Plan",
            duration_months=1,
            price=Decimal("1000.00"),
        )

        # -------------------------------------------------------------
        # Membership
        # -------------------------------------------------------------

        self.membership = Membership.objects.create(
            member=self.member,
            plan=self.plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
            amount=Decimal("1000.00"),
        )

    # =================================================================
    # Member authorization
    # =================================================================

    def test_trainer_only_accesses_assigned_members(self):
        from trainers.authorization import accessible_members

        members = accessible_members(
            self.trainer,
        )

        self.assertIn(
            self.member,
            members,
        )

        self.assertNotIn(
            self.other_member,
            members,
        )

    def test_unassigned_trainer_has_no_member_access(self):
        from trainers.authorization import accessible_members

        members = accessible_members(
            self.other_trainer,
        )

        self.assertNotIn(
            self.member,
            members,
        )

        self.assertNotIn(
            self.other_member,
            members,
        )

    def test_inactive_assignment_is_not_accessible(self):
        from trainers.authorization import accessible_members

        self.assignment.is_active = False
        self.assignment.save(
            update_fields=[
                "is_active",
            ]
        )

        members = accessible_members(
            self.trainer,
        )

        self.assertNotIn(
            self.member,
            members,
        )

    def test_owner_can_access_all_members(self):
        from trainers.authorization import accessible_members

        members = accessible_members(
            self.owner,
        )

        self.assertIn(
            self.member,
            members,
        )

        self.assertIn(
            self.other_member,
            members,
        )

    def test_trainer_can_access_assigned_member(self):
        from trainers.authorization import trainer_can_access_member

        self.assertTrue(
            trainer_can_access_member(
                self.trainer,
                self.member,
            )
        )

    def test_trainer_cannot_access_unassigned_member(self):
        from trainers.authorization import trainer_can_access_member

        self.assertFalse(
            trainer_can_access_member(
                self.trainer,
                self.other_member,
            )
        )

    def test_owner_can_access_any_member(self):
        from trainers.authorization import trainer_can_access_member

        self.assertTrue(
            trainer_can_access_member(
                self.owner,
                self.member,
            )
        )

        self.assertTrue(
            trainer_can_access_member(
                self.owner,
                self.other_member,
            )
        )

    # =================================================================
    # HTTP member authorization
    # =================================================================

    def test_trainer_can_open_assigned_member(self):
        self.client.force_login(
            self.trainer,
        )

        response = self.client.get(
            reverse(
                "members:detail",
                kwargs={
                    "member_id": self.member.member_id,
                },
            ),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_trainer_cannot_open_unassigned_member(self):
        self.client.force_login(
            self.trainer,
        )

        response = self.client.get(
            reverse(
                "members:detail",
                kwargs={
                    "member_id": self.other_member.member_id,
                },
            ),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_owner_can_open_any_member(self):
        self.client.force_login(
            self.owner,
        )

        response = self.client.get(
            reverse(
                "members:detail",
                kwargs={
                    "member_id": self.other_member.member_id,
                },
            ),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    # =================================================================
    # Trainer permission tests
    # =================================================================

    def test_trainer_without_permission_is_denied(self):
        trainer = User.objects.create_user(
            username="no_member_permission",
            password="TestPassword123!",
            role="trainer",
            is_active=True,
        )

        TrainerPermission.objects.create(
            user=trainer,
            can_view_members=False,
        )

        self.client.force_login(
            trainer,
        )

        response = self.client.get(
            reverse("members:list"),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response["Location"],
            "/",
        )

    def test_missing_trainer_permission_record_is_denied(self):
        trainer = User.objects.create_user(
            username="missing_permission",
            password="TestPassword123!",
            role="trainer",
            is_active=True,
        )

        self.client.force_login(
            trainer,
        )

        response = self.client.get(
            reverse("members:list"),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response["Location"],
            "/",
        )

    def test_member_role_cannot_open_staff_members(self):
        self.client.force_login(
            self.member_user,
        )

        response = self.client.get(
            reverse("members:list"),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response["Location"],
            "/",
        )

    # =================================================================
    # Payment permission tests
    # =================================================================

    def test_trainer_without_payment_permission_cannot_view_payments(self):
        trainer = User.objects.create_user(
            username="payment_view_denied",
            password="TestPassword123!",
            role="trainer",
            is_active=True,
        )

        TrainerPermission.objects.create(
            user=trainer,
            can_view_payments=False,
        )

        self.client.force_login(
            trainer,
        )

        response = self.client.get(
            reverse("payments:list"),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_trainer_without_payment_add_permission_cannot_add_payment(self):
        trainer = User.objects.create_user(
            username="payment_add_denied",
            password="TestPassword123!",
            role="trainer",
            is_active=True,
        )

        TrainerPermission.objects.create(
            user=trainer,
            can_view_payments=True,
            can_add_payments=False,
        )

        self.client.force_login(
            trainer,
        )

        response = self.client.get(
            reverse(
                "payments:create",
                kwargs={
                    "membership_id": self.membership.id,
                },
            ),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    # =================================================================
    # Owner permission bypass
    # =================================================================

    def test_owner_can_view_members_without_trainer_permission(self):
        self.client.force_login(
            self.owner,
        )

        response = self.client.get(
            reverse("members:list"),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_owner_can_view_payments_without_trainer_permission(self):
        self.client.force_login(
            self.owner,
        )

        response = self.client.get(
            reverse("payments:list"),
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            200,
        )