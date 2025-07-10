#!/usr/bin/env python3
"""
Generate a secure JWT secret key for the course creator platform
"""
import secrets
import string
import base64
import os

def generate_jwt_secret():
    """Generate a cryptographically secure JWT secret key"""
    
    print("JWT Secret Key Generator")
    print("=" * 40)
    
    # Method 1: Random bytes (most secure)
    random_bytes = secrets.token_bytes(64)  # 64 bytes = 512 bits
    base64_key = base64.b64encode(random_bytes).decode('utf-8')
    
    print("\n1. Base64 encoded random key (512 bits):")
    print(f"   {base64_key}")
    
    # Method 2: Random hex string
    hex_key = secrets.token_hex(32)  # 32 bytes = 256 bits
    print(f"\n2. Hex encoded random key (256 bits):")
    print(f"   {hex_key}")
    
    # Method 3: Random alphanumeric string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    secure_key = ''.join(secrets.choice(alphabet) for _ in range(64))
    print(f"\n3. Alphanumeric + symbols key (64 characters):")
    print(f"   {secure_key}")
    
    # Method 4: UUID-based key (less secure but human-readable)
    import uuid
    uuid_key = f"course-creator-{uuid.uuid4()}-{uuid.uuid4()}"
    print(f"\n4. UUID-based key (human-readable):")
    print(f"   {uuid_key}")
    
    print("\n" + "=" * 40)
    print("RECOMMENDATIONS:")
    print("- Use option 1 (Base64) for maximum security")
    print("- Use option 3 for good security with readability")
    print("- Never use option 4 in production")
    print("- Store the key securely and never commit to version control")
    
    return base64_key

if __name__ == "__main__":
    recommended_key = generate_jwt_secret()
    
    print(f"\n🔐 RECOMMENDED KEY FOR YOUR .cc_env FILE:")
    print(f"JWT_SECRET_KEY={recommended_key}")
    
    # Optionally update the .cc_env file
    response = input("\nWould you like to update your .cc_env file with the recommended key? (y/N): ")
    if response.lower() in ['y', 'yes']:
        try:
            # Read current .cc_env file
            with open('.cc_env', 'r') as f:
                content = f.read()
            
            # Replace the JWT_SECRET_KEY line
            lines = content.split('\n')
            updated_lines = []
            key_updated = False
            
            for line in lines:
                if line.strip().startswith('JWT_SECRET_KEY='):
                    updated_lines.append(f'JWT_SECRET_KEY={recommended_key}')
                    key_updated = True
                    print(f"✅ Updated JWT_SECRET_KEY in .cc_env")
                else:
                    updated_lines.append(line)
            
            # If key wasn't found, add it
            if not key_updated:
                updated_lines.append('')
                updated_lines.append('# JWT Configuration')
                updated_lines.append(f'JWT_SECRET_KEY={recommended_key}')
                print(f"✅ Added JWT_SECRET_KEY to .cc_env")
            
            # Write back to file
            with open('.cc_env', 'w') as f:
                f.write('\n'.join(updated_lines))
            
            print("✅ .cc_env file updated successfully!")
            print("⚠️  Remember to restart your services: ./app-control.sh restart")
            
        except Exception as e:
            print(f"❌ Error updating .cc_env file: {e}")
            print(f"Please manually add this line to your .cc_env file:")
            print(f"JWT_SECRET_KEY={recommended_key}")
    else:
        print("\n📝 To use this key, add this line to your .cc_env file:")
        print(f"JWT_SECRET_KEY={recommended_key}")