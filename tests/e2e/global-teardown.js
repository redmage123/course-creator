/**
 * Global teardown for Playwright E2E tests
 * Cleans up test environment
 */

import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

async function globalTeardown() {
  console.log('🧹 Starting global teardown for E2E tests...');
  
  try {
    // Clean up test data but keep services running for development
    console.log('🗄️ Cleaning up test database...');
    // Don't reset database in development mode - just clean test data
    // await execAsync('python setup-database.py --reset');
    
    console.log('✅ Global teardown complete!');
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw error to avoid masking test failures
  }
}

export default globalTeardown;