import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Satellitor.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402


def main() -> None:
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

    if not username or not password:
        return

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email or ""},
    )
    if created:
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"Created superuser '{username}'")
    else:
        # Ensure flags and password are correct on restart
        updated = False
        if email and user.email != email:
            user.email = email
            updated = True
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            updated = True
        if password:
            user.set_password(password)
            updated = True
        if updated:
            user.save()
            print(f"Updated superuser '{username}'")
        else:
            print(f"Superuser '{username}' already exists")


if __name__ == "__main__":
    main()



