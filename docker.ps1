param(
  [ValidateSet("build","up","down","logs","ps","migrate","makesuper","shell","collectstatic","makemigrations")]
  [string]$cmd = "up"
)

switch ($cmd) {
  "build" { docker compose build }
  "up" { docker compose up -d --build }
  "down" { docker compose down }
  "logs" { docker compose logs -f --tail=200 web }
  "ps" { docker compose ps }
  "migrate" { docker compose exec web python Satellitor/manage.py migrate }
  "makesuper" {
    $mUser = if ($env:DJANGO_SUPERUSER_USERNAME) { $env:DJANGO_SUPERUSER_USERNAME } else { "admin" }
    $mPass = if ($env:DJANGO_SUPERUSER_PASSWORD) { $env:DJANGO_SUPERUSER_PASSWORD } else { "admin" }
    $mEmail = if ($env:DJANGO_SUPERUSER_EMAIL) { $env:DJANGO_SUPERUSER_EMAIL } else { "admin@example.com" }
    docker compose exec -e DJANGO_SUPERUSER_USERNAME=$mUser -e DJANGO_SUPERUSER_PASSWORD=$mPass -e DJANGO_SUPERUSER_EMAIL=$mEmail web python Satellitor/create_superuser.py
  }
  "shell" { docker compose exec web python Satellitor/manage.py shell }
  "collectstatic" { docker compose exec web python Satellitor/manage.py collectstatic --noinput }
  "makemigrations" { docker compose exec web python Satellitor/manage.py makemigrations }
}



