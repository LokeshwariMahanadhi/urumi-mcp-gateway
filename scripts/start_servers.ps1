# Starts the three MCP servers, each in its own window.
$root = Split-Path -Parent $PSScriptRoot

foreach ($name in "woocommerce", "currency", "utilities") {
    $command = "cd '$root'; .\.venv\Scripts\Activate.ps1; python -m servers.$name.server"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $command
}