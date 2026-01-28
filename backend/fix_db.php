<?php
require_once __DIR__ . '/config/database.php';

try {
    $db = getDatabaseConnection();
    echo "Connected to database.\n";
    
    // Add columns if they don't exist
    $columns = [
        "ALTER TABLE scans ADD COLUMN IF NOT EXISTS finished_at DATETIME NULL",
        "ALTER TABLE scans ADD COLUMN IF NOT EXISTS results JSON NULL",
        "ALTER TABLE scans MODIFY COLUMN status VARCHAR(50) DEFAULT 'queued'"
    ];
    
    foreach ($columns as $sql) {
        if ($db->query($sql)) {
            echo "Executed: $sql\n";
        } else {
            echo "Error: " . $db->error . "\n";
        }
    }
    
    echo "Database schema updated successfully.\n";
    $db->close();
    
} catch (Exception $e) {
    echo "Critical Error: " . $e->getMessage() . "\n";
    exit(1);
}
