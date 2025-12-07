#!/usr/bin/env python
"""
Quick setup script for safety monitoring system
"""
import subprocess
import sys
import os

def run_command(cmd, cwd=None):
    """Run a shell command"""
    print(f"\n🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        return False
    return True

def main():
    print("=" * 60)
    print("🛡️  Safety Monitoring System - Setup")
    print("=" * 60)
    
    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(project_root, 'smart_cotton_system')
    frontend_dir = os.path.join(project_root, 'frontend', 'smart-cotton')
    
    # Backend setup
    print("\n📦 Setting up Django backend...")
    
    if not run_command('python manage.py makemigrations safety', cwd=backend_dir):
        sys.exit(1)
    
    if not run_command('python manage.py migrate safety', cwd=backend_dir):
        sys.exit(1)
    
    if not run_command('python manage.py init_safety', cwd=backend_dir):
        print("⚠️  Warning: Could not initialize sample data")
    
    # Frontend setup
    print("\n📦 Setting up Next.js frontend...")
    print("ℹ️  Make sure you have run 'npm install' in frontend/smart-cotton")
    
    # Check if .env.local exists
    env_local = os.path.join(frontend_dir, '.env.local')
    if not os.path.exists(env_local):
        print("\n📝 Creating .env.local file...")
        with open(env_local, 'w') as f:
            f.write("NEXT_PUBLIC_API_URL=http://localhost:8000\n")
        print("✅ Created .env.local")
    
    # Check if backend .env exists
    backend_env = os.path.join(backend_dir, '.env')
    if not os.path.exists(backend_env):
        print("\n📝 Creating backend .env file...")
        with open(backend_env, 'w') as f:
            f.write("GEMINI_API_KEY=your_api_key_here\n")
        print("✅ Created .env (please add your Gemini API key)")
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("\n1. Backend (in smart_cotton_system/):")
    print("   python manage.py runserver")
    print("\n2. Frontend (in frontend/smart-cotton/):")
    print("   npm run dev")
    print("\n3. Access dashboard:")
    print("   http://localhost:3000/safety-monitoring")
    print("\n4. Test API:")
    print("   curl http://localhost:8000/api/safety/workers/live_status/")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
