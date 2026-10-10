$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = "C:\Users\abhis\AppData\Local\Programs\Python\Python311\python.exe"
$frontendDir = Join-Path $root "frontend"

if ($args.Count -eq 0) {
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$root`" && `"$backend`" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$frontendDir`" && npm.cmd run dev -- --hostname 0.0.0.0 --port 3000"
    Write-Host ""
    Write-Host "FreightRate Predictor is starting..."
    Write-Host "Backend:  http://localhost:8000/docs"
    Write-Host "Frontend: http://localhost:3000"
} else {
    & $backend $args
}
