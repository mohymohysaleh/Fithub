import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


# --- ENUMS ---
class Role(models.TextChoices):
  CLIENT = "CLIENT", "Client"
  COACH = "COACH", "Coach"
  ADMIN = "ADMIN", "Admin"


class SubscriptionStatus(models.TextChoices):
  ACTIVE = "ACTIVE", "Active"
  PAUSED = "PAUSED", "Paused"
  CANCELLED = "CANCELLED", "Cancelled"


class PlanStatus(models.TextChoices):
  ACTIVE = "ACTIVE", "Active"
  ARCHIVED = "ARCHIVED", "Archived"


class CheckInStatus(models.TextChoices):
  PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
  REVIEWED = "REVIEWED", "Reviewed"


# --- CUSTOM USER MANAGER ---
class UserManager(BaseUserManager):

  def create_user(self, email, password=None, **extra_fields):
    if not email:
      raise ValueError("The Email field must be set")
    email = self.normalize_email(email)
    user = self.model(email=email, **extra_fields)
    user.set_password(password)
    user.save(using=self._db)
    return user

  def create_superuser(self, email, password=None, **extra_fields):
    extra_fields.setdefault("role", Role.ADMIN)
    extra_fields.setdefault("is_staff", True)
    extra_fields.setdefault("is_superuser", True)
    return self.create_user(email, password, **extra_fields)


# --- 1. USERS TABLE ---
class User(AbstractBaseUser, PermissionsMixin):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  email = models.EmailField(unique=True, max_length=255)
  password_hash = models.CharField(max_length=255)
  role = models.CharField(
      max_length=20, choices=Role.choices, default=Role.CLIENT
  )
  first_name = models.CharField(max_length=100)
  last_name = models.CharField(max_length=100)
  created_at = models.DateTimeField(auto_now_add=True)

  is_active = models.BooleanField(default=True)
  is_staff = models.BooleanField(default=False)

  objects = UserManager()

  USERNAME_FIELD = "email"
  REQUIRED_FIELDS = ["first_name", "last_name"]

  def set_password(self, raw_password):
    super().set_password(raw_password)
    self.password_hash = self.password

  class Meta:
    db_table = "users"


# --- 2. COACH PROFILES TABLE ---
class CoachProfile(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.OneToOneField(
      User, on_delete=models.CASCADE, related_name="coachProfile"
  )
  bio = models.TextField(blank=True, null=True)
  max_client_capacity = models.IntegerField(default=20)
  specialization = models.CharField(max_length=255, blank=True, null=True)
  rating = models.DecimalField(
      max_digits=3, decimal_places=2, blank=True, null=True
  )

  class Meta:
    db_table = "coach_profiles"


# --- 3. CLIENT PROFILES TABLE ---
class ClientProfile(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.OneToOneField(
      User, on_delete=models.CASCADE, related_name="clientProfile"
  )
  coach = models.ForeignKey(
      CoachProfile,
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name="clients",
  )
  goal = models.CharField(max_length=255, blank=True, null=True)
  height = models.DecimalField(
      max_digits=5, decimal_places=2, blank=True, null=True
  )
  current_weight = models.DecimalField(
      max_digits=5, decimal_places=2, blank=True, null=True
  )
  medical_notes = models.TextField(blank=True, null=True)
  subscription_status = models.CharField(
      max_length=20,
      choices=SubscriptionStatus.choices,
      default=SubscriptionStatus.ACTIVE,
  )

  class Meta:
    db_table = "client_profiles"


# --- 4. EXERCISES TABLE ---
class Exercise(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=255)
  target_muscle = models.CharField(max_length=100)
  video_url = models.CharField(max_length=500, blank=True, null=True)
  instructions = models.TextField(blank=True, null=True)

  class Meta:
    db_table = "exercises"


# --- 5. WORKOUT PLANS TABLE ---
class WorkoutPlan(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  client = models.ForeignKey(
      ClientProfile, on_delete=models.CASCADE, related_name="workoutPlans"
  )
  coach = models.ForeignKey(
      CoachProfile, on_delete=models.CASCADE, related_name="workoutPlans"
  )
  title = models.CharField(max_length=255)
  phase_number = models.IntegerField(default=1)
  status = models.CharField(
      max_length=20, choices=PlanStatus.choices, default=PlanStatus.ACTIVE
  )

  class Meta:
    db_table = "workout_plans"


# --- 6. WORKOUT SESSIONS TABLE ---
class WorkoutSession(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  workout_plan = models.ForeignKey(
      WorkoutPlan, on_delete=models.CASCADE, related_name="sessions"
  )
  day_name = models.CharField(max_length=100)

  class Meta:
    db_table = "workout_sessions"


# --- 7. WORKOUT SESSION EXERCISES (JUNCTION) TABLE ---
class WorkoutSessionExercise(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  workout_session = models.ForeignKey(
      WorkoutSession, on_delete=models.CASCADE, related_name="exercises"
  )
  exercise = models.ForeignKey(
      Exercise, on_delete=models.CASCADE, related_name="sessionExercises"
  )
  target_sets = models.IntegerField()
  target_reps = models.CharField(max_length=50)
  target_rpe = models.IntegerField(blank=True, null=True)

  class Meta:
    db_table = "workout_session_exercises"


# --- 8. NUTRITION PLANS TABLE ---
class NutritionPlan(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  client = models.ForeignKey(
      ClientProfile, on_delete=models.CASCADE, related_name="nutritionPlans"
  )
  coach = models.ForeignKey(
      CoachProfile, on_delete=models.CASCADE, related_name="nutritionPlans"
  )
  target_calories = models.IntegerField()
  target_protein_g = models.IntegerField()
  target_carbs_g = models.IntegerField()
  target_fats_g = models.IntegerField()
  notes = models.TextField(blank=True, null=True)

  class Meta:
    db_table = "nutrition_plans"


# --- 9. CHECK-INS TABLE ---
class CheckIn(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  client = models.ForeignKey(
      ClientProfile, on_delete=models.CASCADE, related_name="checkIns"
  )
  submitted_date = models.DateField(auto_now_add=True)
  weight = models.DecimalField(max_digits=5, decimal_places=2)
  sleep_quality_score = models.IntegerField()
  stress_level_score = models.IntegerField()
  client_notes = models.TextField(blank=True, null=True)
  progress_photos = models.JSONField(blank=True, null=True)
  coach_feedback = models.TextField(blank=True, null=True)
  status = models.CharField(
      max_length=30,
      choices=CheckInStatus.choices,
      default=CheckInStatus.PENDING_REVIEW,
  )

  class Meta:
    db_table = "check_ins"


# --- 10. MESSAGES TABLE ---
class Message(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  sender = models.ForeignKey(
      User, on_delete=models.CASCADE, related_name="sentMessages"
  )
  recipient = models.ForeignKey(
      User, on_delete=models.CASCADE, related_name="receivedMessages"
  )
  content = models.TextField()
  attachment_url = models.CharField(max_length=500, blank=True, null=True)
  sent_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    db_table = "messages"