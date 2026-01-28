<?php
/**
 * Database Initialization Script
 * Run this script once to set up the database and tables
 */

require_once __DIR__ . '/config/env.php';
require_once __DIR__ . '/config/database.php';

echo "=============================================================\n";
echo "Aegis Recon - Database Initialization\n";
echo "=============================================================\n\n";

try {
    echo "[1] Testing database connection...\n";
    
    // Try to connect
    $db = getDatabaseConnection();
    echo "    ✓ Database connection successful\n\n";
    
    echo "[2] Creating tables...\n";
    
    // Initialize database tables
    if (initializeDatabase()) {
        echo "    ✓ Tables created successfully\n\n";
    } else {
        echo "    ✗ Failed to create tables\n\n";
        exit(1);
    }
    
    echo "[3] Verifying table structure...\n";
    
    // Verify scans table
    $result = $db->query("DESCRIBE scans");
    if ($result && $result->num_rows > 0) {
        echo "    ✓ 'scans' table verified\n";
        echo "    Columns:\n";
        while ($row = $result->fetch_assoc()) {
            echo "      - {$row['Field']} ({$row['Type']})\n";
        }
    }
    
    echo "\n[4] Creating logs directory...\n";
    $logsDir = __DIR__ . '/logs';
    if (!is_dir($logsDir)) {
        mkdir($logsDir, 0755, true);
        echo "    ✓ Logs directory created: $logsDir\n";
    } else {
        echo "    ✓ Logs directory already exists\n";
    }
    
    echo "\n=============================================================\n";
    echo "Database initialization completed successfully!\n";
    echo "=============================================================\n\n";
    
    echo "Next steps:\n";
    echo "1. Copy .env.example to .env and configure your settings\n";
    echo "2. Set your API_KEY in the .env file\n";
    echo "3. Test the API endpoints using the documentation\n\n";
    
    $db->close();
    
} catch (Exception $e) {
    echo "\n✗ ERROR: " . $e->getMessage() . "\n";
    echo "\nPlease check:\n";
    echo "- MySQL/MariaDB is running\n";
    echo "- Database credentials in .env are correct\n";
    echo "- User has permissions to create databases and tables\n\n";
    exit(1);
}
