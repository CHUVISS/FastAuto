$ErrorActionPreference = "Stop"
Set-PSDebug -Trace 1

Set-Location "$PSScriptRoot\.."
$env:PYTHONPATH = (Get-Location).Path

python scripts/wait_for_db.py
alembic upgrade head
python scripts/initial_data.py

# Dev-only demo listings; safe in any env (the script no-ops outside local).
if (($null -eq $env:ENVIRONMENT) -or ($env:ENVIRONMENT -eq "local")) {
    python -m scripts.seed_dev_listings
}
