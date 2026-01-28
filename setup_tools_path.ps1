# Aegis Recon - Add Tools to PATH (Current Session)
# Run this in your PowerShell to enable Ruby and Perl

Write-Host "=== Adding Tools to PATH ===" -ForegroundColor Cyan
Write-Host ""

# Add Ruby to PATH
$rubyPath = "C:\Ruby34-x64\bin"
if (Test-Path $rubyPath) {
    $env:PATH = "$rubyPath;$env:PATH"
    Write-Host "✓ Added Ruby to PATH: $rubyPath" -ForegroundColor Green
} else {
    Write-Host "✗ Ruby not found at: $rubyPath" -ForegroundColor Red
}

# Add Perl to PATH
$perlPath = "C:\Strawberry\perl\bin"
if (Test-Path $perlPath) {
    $env:PATH = "$perlPath;$env:PATH"
    Write-Host "✓ Added Perl to PATH: $perlPath" -ForegroundColor Green
} else {
    Write-Host "✗ Perl not found at: $perlPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Verifying Tools ===" -ForegroundColor Cyan

# Test Ruby
try {
    $rubyVersion = ruby --version 2>&1
    Write-Host "✓ Ruby: $rubyVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Ruby: Still not working" -ForegroundColor Red
}

# Test Perl
try {
    $perlVersion = perl --version 2>&1 | Select-String "This is perl"
    Write-Host "✓ Perl: $perlVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Perl: Still not working" -ForegroundColor Red
}

# Test Nmap
try {
    $nmapVersion = nmap --version 2>&1 | Select-String "Nmap version"
    Write-Host "✓ Nmap: $nmapVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Nmap: Not working" -ForegroundColor Red
}

# Test Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python: Not working" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== All Set! ===" -ForegroundColor Green
Write-Host "You can now run scans with full tool support!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install tool dependencies (see below)" -ForegroundColor Gray
Write-Host "2. Run a test scan" -ForegroundColor Gray
Write-Host ""
Write-Host "Install dependencies:" -ForegroundColor Cyan
Write-Host "  cd tools\WhatWeb" -ForegroundColor Gray
Write-Host "  gem install bundler" -ForegroundColor Gray
Write-Host "  bundle install" -ForegroundColor Gray
