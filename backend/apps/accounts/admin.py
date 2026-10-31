from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import StudentProfile, User


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False


@admin.register(User)
class OktopiUserAdmin(UserAdmin):
    inlines = (StudentProfileInline,)
    list_display = ("username", "email", "is_staff", "date_joined")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "grade_level", "school_type", "initial_level_status")
    list_filter = ("grade_level", "school_type", "initial_level_status")
