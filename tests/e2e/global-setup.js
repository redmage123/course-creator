/**
 * Global setup for Playwright E2E tests
 * Starts backend services and prepares test environment
 */

import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

async function globalSetup() {
  console.log('🚀 Starting global setup for E2E tests...');
  
  try {
    // Check if services are already running
    console.log('📋 Checking service status...');
    const { stdout } = await execAsync('./app-control.sh status');
    console.log('Service status:', stdout);
    
    // Start services if not running
    if (stdout.includes('not running') || stdout.includes('stopped')) {
      console.log('🔧 Starting backend services...');
      await execAsync('./app-control.sh start');
      console.log('✅ Backend services started');
      
      // Wait for services to be ready
      console.log('⏳ Waiting for services to initialize...');
      await new Promise(resolve => setTimeout(resolve, 10000));
    } else {
      console.log('✅ Backend services already running');
    }
    
    // Setup test database
    console.log('🗄️ Setting up test database...');
    await execAsync('python setup-database.py');
    console.log('✅ Test database ready');
    
    // Create test admin user
    console.log('👤 Creating test admin user...');
    try {
      await execAsync('python create-admin.py');
      console.log('✅ Test admin user created');
    } catch (error) {
      // Admin might already exist
      console.log('ℹ️ Admin user already exists or creation failed:', error.message);
    }
    
    console.log('🎉 Global setup complete!');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  }
}

export default globalSetup;