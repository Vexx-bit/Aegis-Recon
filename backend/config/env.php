<?php
/**
 * Environment Configuration Loader
 * Loads environment variables from .env file
 */

/**
 * Load environment variables from .env file
 */
function loadEnv($filePath = null) {
    if ($filePath === null) {
        $filePath = __DIR__ . '/../../.env';
    }
    
    if (!file_exists($filePath)) {
        error_log('Warning: .env file not found at ' . $filePath);
        return false;
    }
    
    $lines = file($filePath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    
    foreach ($lines as $line) {
        // Skip comments
        if (strpos(trim($line), '#') === 0) {
            continue;
        }
        
        // Parse KEY=VALUE
        if (strpos($line, '=') !== false) {
            list($key, $value) = explode('=', $line, 2);
            $key = trim($key);
            $value = trim($value);
            
            // Remove quotes if present
            $value = trim($value, '"\'');
            
            // Set environment variable
            putenv("$key=$value");
            $_ENV[$key] = $value;
            $_SERVER[$key] = $value;
        }
    }
    
    return true;
}

// Auto-load environment variables
loadEnv();
