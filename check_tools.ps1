# Aegis Recon - Tool Installation Checker

Write-Host "=== Aegis Recon Tool Checker ===" -ForegroundColor Cyan
Write-Host ""

# Check Nmap
Write-Host "Checking Nmap..." -ForegroundColor Yellow
try {
    $nmap = nmap --version 2>&1 | Select-String "Nmap version"
    Write-Host "✓ Nmap: $nmap" -ForegroundColor Green
} catch {
    Write-Host "✗ Nmap: NOT FOUND" -ForegroundColor Red
    Write-Host "  Install from: https://nmap.org/download.html" -ForegroundColor Gray
}

# Check Ruby
Write-Host "Checking Ruby..." -ForegroundColor Yellow
try {
    $ruby = ruby --version 2>&1
    Write-Host "✓ Ruby: $ruby" -ForegroundColor Green
} catch {
    Write-Host "✗ Ruby: NOT FOUND" -ForegroundColor Red
    Write-Host "  Install from: https://rubyinstaller.org/" -ForegroundColor Gray
}

# Check Perl
Write-Host "Checking Perl..." -ForegroundColor Yellow
try {
    $perl = perl --version 2>&1 | Select-String "This is perl"
    Write-Host "✓ Perl: $perl" -ForegroundColor Green
} catch {
    Write-Host "✗ Perl: NOT FOUND" -ForegroundColor Red
    Write-Host "  Install from: https://strawberryperl.com/" -ForegroundColor Gray
}

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $python = python --version 2>&1
    Write-Host "✓ Python: $python" -ForegroundColor Green
} catch {
    Write-Host "✗ Python: NOT FOUND" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Tool Files ===" -ForegroundColor Cyan

# Check WhatWeb
$whatweb = "E:\Xampp\htdocs\Aegis Recon\tools\WhatWeb\whatweb"
if (Test-Path $whatweb) {
    Write-Host "✓ WhatWeb: Found" -ForegroundColor Green
} else {
    Write-Host "✗ WhatWeb: NOT FOUND at $whatweb" -ForegroundColor Red
}

# Check Nikto
$nikto = "E:\Xampp\htdocs\Aegis Recon\tools\nikto\program\nikto.pl"
if (Test-Path $nikto) {
    Write-Host "✓ Nikto: Found" -ForegroundColor Green
} else {
    Write-Host "✗ Nikto: NOT FOUND at $nikto" -ForegroundColor Red
}

# Check theHarvester
$harvester = "E:\Xampp\htdocs\Aegis Recon\tools\theHarvester\theHarvester.py"
if (Test-Path $harvester) {
    Write-Host "✓ theHarvester: Found" -ForegroundColor Green
} else {
    Write-Host "✗ theHarvester: NOT FOUND at $harvester" -ForegroundColor Red
}

# Check Sublist3r
$sublist3r = "E:\Xampp\htdocs\Aegis Recon\tools\Sublist3r\sublist3r.py"
if (Test-Path $sublist3r) {
    Write-Host "✓ Sublist3r: Found" -ForegroundColor Green
} else {
    Write-Host "✗ Sublist3r: NOT FOUND at $sublist3r" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Install missing tools to get full scan capabilities!" -ForegroundColor Yellow
Write-Host ""
Write-Host "See: docs\INSTALL_SCANNING_TOOLS.md for installation guide" -ForegroundColor Gray
