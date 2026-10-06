# Powershell launcher script using project Python 3.11 environment
$PythonExe = "C:\Users\abhis\AppData\Local\Programs\Python\Python311\python.exe"
if ($args.Count -eq 0) {
    & $PythonExe main.py
} else {
    & $PythonExe $args
}
