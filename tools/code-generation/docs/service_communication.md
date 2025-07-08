# Service Communication Patterns

## course-management

### Consumers:
- **user-management**: Requires user authentication for course operations (auth_dep)
- **course-generator**: Calls generator service to create course content (api_call)
- **content-storage**: Stores course materials and media files (storage_dep)

## course-generator

### Dependencies:
- **course-management**: Calls generator service to create course content (api_call)

### Consumers:
- **user-management**: Requires authentication for course generation (auth_dep)
- **content-storage**: Stores generated course content and assets (storage_dep)

## content-storage

### Dependencies:
- **course-management**: Stores course materials and media files (storage_dep)
- **course-generator**: Stores generated course content and assets (storage_dep)

### Consumers:
- **user-management**: Optional authentication for file access control (auth_dep)

## user-management

### Dependencies:
- **course-management**: Requires user authentication for course operations (auth_dep)
- **course-generator**: Requires authentication for course generation (auth_dep)
- **content-storage**: Optional authentication for file access control (auth_dep)

