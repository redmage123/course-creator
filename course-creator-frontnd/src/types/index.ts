export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: 'student' | 'instructor' | 'admin';
  avatar_url?: string;
  bio?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Course {
  id: string;
  title: string;
  description: string;
  instructor_id: string;
  instructor?: User;
  category: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_duration?: number;
  price: number;
  is_published: boolean;
  thumbnail_url?: string;
  created_at: string;
  updated_at: string;
  lessons_count?: number;
  students_count?: number;
}

export interface Lesson {
  id: string;
  course_id: string;
  title: string;
  description?: string;
  content?: string;
  lesson_order: number;
  duration_minutes: number;
  is_published: boolean;
  lesson_type: 'video' | 'text' | 'quiz' | 'assignment';
  created_at: string;
}

export interface Enrollment {
  id: string;
  student_id: string;
  course_id: string;
  course?: Course;
  enrollment_date: string;
  status: 'active' | 'completed' | 'dropped';
  progress_percentage: number;
  last_accessed?: string;
  completed_at?: string;
}
