# Course Creator Platform Architecture

## Service Dependency Graph

### Services

#### user-management
- **Type**: authentication
- **Port**: 8000
- **Description**: User registration, authentication, and profile management
- **Responsibilities**: User authentication, Authorization, Profile management, Role-based access control

#### course-generator
- **Type**: content_generation
- **Port**: 8001
- **Description**: AI-powered course content generation
- **Responsibilities**: Course content generation, Template management, AI prompt processing

#### course-management
- **Type**: business_logic
- **Port**: 8004
- **Description**: Course lifecycle and enrollment management
- **Responsibilities**: Course CRUD operations, Enrollment management, Progress tracking

#### content-storage
- **Type**: data_storage
- **Port**: 8003
- **Description**: File storage and content management
- **Responsibilities**: File upload/download, Media processing, Storage management

### Dependencies

- **course-management** → **user-management**
  - Type: auth_dep
  - Description: Requires user authentication for course operations
  - Required: True

- **course-generator** → **user-management**
  - Type: auth_dep
  - Description: Requires authentication for course generation
  - Required: True

- **course-management** → **course-generator**
  - Type: api_call
  - Description: Calls generator service to create course content
  - Required: True

- **course-management** → **content-storage**
  - Type: storage_dep
  - Description: Stores course materials and media files
  - Required: True

- **course-generator** → **content-storage**
  - Type: storage_dep
  - Description: Stores generated course content and assets
  - Required: True

- **content-storage** → **user-management**
  - Type: auth_dep
  - Description: Optional authentication for file access control
  - Required: False

