#!/usr/bin/env python3

import sys
sys.path.append('/home/bbrelin/course-creator/lab-containers')

try:
    from main import get_docker_client, DynamicImageBuilder
    print("Imports successful")
    
    # Test the docker client
    client = get_docker_client()
    print(f"Docker client: {client}")
    print(f"Type: {type(client)}")
    
    # Test if the error happens when we try to use it like a Docker client
    try:
        print("Testing .images access...")
        images = client.images
        print("This should not print!")
    except AttributeError as e:
        print(f"Expected error: {e}")
    
    # Test the actual function that's failing
    print("Testing DynamicImageBuilder.build_lab_image...")
    
    import asyncio
    async def test_build():
        try:
            result = await DynamicImageBuilder.build_lab_image(
                lab_type="python",
                course_id="test_course",
                lab_config={},
                custom_dockerfile=None
            )
            print(f"Build result: {result}")
        except Exception as e:
            import traceback
            print(f"Build error: {e}")
            print("Traceback:")
            print(traceback.format_exc())
    
    asyncio.run(test_build())
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print("Traceback:")
    print(traceback.format_exc())