/**
 * AI Content Generation Page
 *
 * BUSINESS CONTEXT:
 * Allows instructors to generate course content using AI.
 * Supports generating quizzes, slides, exercises, and syllabus.
 * Uses course-generator service (port 8002) for AI-powered content creation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tab-based interface for different content types
 * - Real-time generation with loading states
 * - Preview generated content before saving
 * - Integration with course-generator backend service
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/templates/DashboardLayout';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import { Heading } from '../../../components/atoms/Heading';
import { Spinner } from '../../../components/atoms/Spinner';
import { useAuth } from '../../../hooks/useAuth';
import { trainingProgramService } from '../../../services';
import styles from './ContentGenerationPage.module.css';

/**
 * Content type options
 */
type ContentType = 'quiz' | 'slides' | 'exercise' | 'syllabus';

/**
 * AI Content Generation Page Component
 *
 * WHY THIS APPROACH:
 * - Tab-based UI for different content types
 * - Clear separation of generation workflows
 * - Preview before committing to course
 * - Placeholder for future AI integration
 */
export const ContentGenerationPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<ContentType>('quiz');
  const [selectedProgram, setSelectedProgram] = useState<string>('');

  // Quiz generation state
  const [quizTopic, setQuizTopic] = useState('');
  const [quizDifficulty, setQuizDifficulty] = useState<'beginner' | 'intermediate' | 'advanced'>('intermediate');
  const [questionCount, setQuestionCount] = useState(5);

  // Slides generation state
  const [slidesTopic, setSlidesTopic] = useState('');
  const [slideCount, setSlideCount] = useState(10);

  // Exercise generation state
  const [exerciseTopic, setExerciseTopic] = useState('');
  const [exerciseType, setExerciseType] = useState<'coding' | 'written' | 'project'>('coding');

  // Syllabus generation state
  const [syllabusTopic, setSyllabusTopic] = useState('');
  const [courseDuration, setCourseDuration] = useState(4);

  /**
   * Fetch instructor's programs for selection
   */
  const { data: programs, isLoading: loadingPrograms } = useQuery({
    queryKey: ['trainingPrograms', 'instructor', user?.id],
    queryFn: async () => {
      if (!user?.id) return { data: [] };
      return trainingProgramService.getInstructorPrograms(user.id);
    },
    enabled: !!user?.id,
  });

  /**
   * Generate content mutation (placeholder)
   */
  const generateMutation = useMutation({
    mutationFn: async (params: { type: ContentType; data: any }) => {
      // TODO: Integrate with course-generator service
      // For now, simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      return { success: true, content: 'Generated content will appear here' };
    },
  });

  /**
   * Handle content generation
   */
  const handleGenerate = () => {
    if (!selectedProgram) {
      alert('Please select a training program first');
      return;
    }

    let data: any = {};

    switch (activeTab) {
      case 'quiz':
        if (!quizTopic) {
          alert('Please enter a quiz topic');
          return;
        }
        data = { topic: quizTopic, difficulty: quizDifficulty, questionCount };
        break;
      case 'slides':
        if (!slidesTopic) {
          alert('Please enter a slides topic');
          return;
        }
        data = { topic: slidesTopic, slideCount };
        break;
      case 'exercise':
        if (!exerciseTopic) {
          alert('Please enter an exercise topic');
          return;
        }
        data = { topic: exerciseTopic, type: exerciseType };
        break;
      case 'syllabus':
        if (!syllabusTopic) {
          alert('Please enter a course topic');
          return;
        }
        data = { topic: syllabusTopic, duration: courseDuration };
        break;
    }

    generateMutation.mutate({ type: activeTab, data });
  };

  /**
   * Render active tab content
   */
  const renderTabContent = () => {
    switch (activeTab) {
      case 'quiz':
        return (
          <div className={styles['generation-form']}>
            <Heading level="h3" gutterBottom>
              Generate Quiz Questions
            </Heading>
            <p className={styles['description']}>
              AI will generate multiple-choice quiz questions based on your topic and difficulty level.
            </p>

            <div className={styles['form-group']}>
              <label htmlFor="quizTopic" className={styles['form-label']}>
                Quiz Topic
              </label>
              <input
                id="quizTopic"
                type="text"
                value={quizTopic}
                onChange={(e) => setQuizTopic(e.target.value)}
                className={styles['form-input']}
                placeholder="e.g., Python List Comprehensions, Neural Networks Basics"
              />
            </div>

            <div className={styles['form-row']}>
              <div className={styles['form-group']}>
                <label htmlFor="quizDifficulty" className={styles['form-label']}>
                  Difficulty Level
                </label>
                <select
                  id="quizDifficulty"
                  value={quizDifficulty}
                  onChange={(e) => setQuizDifficulty(e.target.value as any)}
                  className={styles['form-select']}
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>

              <div className={styles['form-group']}>
                <label htmlFor="questionCount" className={styles['form-label']}>
                  Number of Questions
                </label>
                <input
                  id="questionCount"
                  type="number"
                  value={questionCount}
                  onChange={(e) => setQuestionCount(Number(e.target.value))}
                  className={styles['form-input']}
                  min="1"
                  max="20"
                />
              </div>
            </div>
          </div>
        );

      case 'slides':
        return (
          <div className={styles['generation-form']}>
            <Heading level="h3" gutterBottom>
              Generate Presentation Slides
            </Heading>
            <p className={styles['description']}>
              AI will generate PowerPoint-style slides with key concepts, examples, and visuals.
            </p>

            <div className={styles['form-group']}>
              <label htmlFor="slidesTopic" className={styles['form-label']}>
                Presentation Topic
              </label>
              <input
                id="slidesTopic"
                type="text"
                value={slidesTopic}
                onChange={(e) => setSlidesTopic(e.target.value)}
                className={styles['form-input']}
                placeholder="e.g., Introduction to Machine Learning, Docker Fundamentals"
              />
            </div>

            <div className={styles['form-group']}>
              <label htmlFor="slideCount" className={styles['form-label']}>
                Number of Slides
              </label>
              <input
                id="slideCount"
                type="number"
                value={slideCount}
                onChange={(e) => setSlideCount(Number(e.target.value))}
                className={styles['form-input']}
                min="5"
                max="50"
              />
            </div>
          </div>
        );

      case 'exercise':
        return (
          <div className={styles['generation-form']}>
            <Heading level="h3" gutterBottom>
              Generate Lab Exercise
            </Heading>
            <p className={styles['description']}>
              AI will generate hands-on exercises with instructions, starter code, and solution.
            </p>

            <div className={styles['form-group']}>
              <label htmlFor="exerciseTopic" className={styles['form-label']}>
                Exercise Topic
              </label>
              <input
                id="exerciseTopic"
                type="text"
                value={exerciseTopic}
                onChange={(e) => setExerciseTopic(e.target.value)}
                className={styles['form-input']}
                placeholder="e.g., Build a REST API, Create a React Component"
              />
            </div>

            <div className={styles['form-group']}>
              <label htmlFor="exerciseType" className={styles['form-label']}>
                Exercise Type
              </label>
              <select
                id="exerciseType"
                value={exerciseType}
                onChange={(e) => setExerciseType(e.target.value as any)}
                className={styles['form-select']}
              >
                <option value="coding">Coding Exercise</option>
                <option value="written">Written Assignment</option>
                <option value="project">Project-Based</option>
              </select>
            </div>
          </div>
        );

      case 'syllabus':
        return (
          <div className={styles['generation-form']}>
            <Heading level="h3" gutterBottom>
              Generate Course Syllabus
            </Heading>
            <p className={styles['description']}>
              AI will generate a complete course syllabus with modules, lessons, and learning objectives.
            </p>

            <div className={styles['form-group']}>
              <label htmlFor="syllabusTopic" className={styles['form-label']}>
                Course Topic
              </label>
              <input
                id="syllabusTopic"
                type="text"
                value={syllabusTopic}
                onChange={(e) => setSyllabusTopic(e.target.value)}
                className={styles['form-input']}
                placeholder="e.g., Full Stack Web Development, Data Science Fundamentals"
              />
            </div>

            <div className={styles['form-group']}>
              <label htmlFor="courseDuration" className={styles['form-label']}>
                Course Duration (weeks)
              </label>
              <input
                id="courseDuration"
                type="number"
                value={courseDuration}
                onChange={(e) => setCourseDuration(Number(e.target.value))}
                className={styles['form-input']}
                min="1"
                max="52"
              />
            </div>
          </div>
        );
    }
  };

  return (
    <DashboardLayout>
      <div className={styles['content-gen-page']}>
        {/* Page Header */}
        <div className={styles['page-header']}>
          <div className={styles['header-content']}>
            <Heading level="h1" gutterBottom>
              AI Content Generator
            </Heading>
            <p className={styles['header-description']}>
              Generate quizzes, slides, exercises, and syllabi using AI. Select a training program and choose the type of content you want to create.
            </p>
          </div>
          <Button variant="secondary" onClick={() => navigate('/instructor/programs')}>
            Back to Programs
          </Button>
        </div>

        {/* Program Selection */}
        <Card variant="outlined" padding="medium" className={styles['program-selector']}>
          <div className={styles['form-group']}>
            <label htmlFor="program" className={styles['form-label']}>
              Select Training Program
            </label>
            {loadingPrograms ? (
              <Spinner size="small" />
            ) : (
              <select
                id="program"
                value={selectedProgram}
                onChange={(e) => setSelectedProgram(e.target.value)}
                className={styles['form-select']}
              >
                <option value="">-- Select a program --</option>
                {programs?.data.map((program) => (
                  <option key={program.id} value={program.id}>
                    {program.title}
                  </option>
                ))}
              </select>
            )}
          </div>
        </Card>

        {/* Content Generation Tabs */}
        <Card variant="outlined" padding="large">
          {/* Tab Navigation */}
          <div className={styles['tabs']}>
            <button
              className={`${styles['tab']} ${activeTab === 'quiz' ? styles['tab-active'] : ''}`}
              onClick={() => setActiveTab('quiz')}
            >
              Quiz Questions
            </button>
            <button
              className={`${styles['tab']} ${activeTab === 'slides' ? styles['tab-active'] : ''}`}
              onClick={() => setActiveTab('slides')}
            >
              Presentation Slides
            </button>
            <button
              className={`${styles['tab']} ${activeTab === 'exercise' ? styles['tab-active'] : ''}`}
              onClick={() => setActiveTab('exercise')}
            >
              Lab Exercise
            </button>
            <button
              className={`${styles['tab']} ${activeTab === 'syllabus' ? styles['tab-active'] : ''}`}
              onClick={() => setActiveTab('syllabus')}
            >
              Course Syllabus
            </button>
          </div>

          {/* Tab Content */}
          <div className={styles['tab-content']}>
            {renderTabContent()}

            {/* Generation Button */}
            <div className={styles['generate-actions']}>
              <Button
                variant="primary"
                size="large"
                onClick={handleGenerate}
                disabled={generateMutation.isPending || !selectedProgram}
              >
                {generateMutation.isPending ? (
                  <>
                    <Spinner size="small" />
                    Generating Content...
                  </>
                ) : (
                  'Generate with AI'
                )}
              </Button>
            </div>

            {/* Results Preview */}
            {generateMutation.isSuccess && (
              <div className={styles['results-preview']}>
                <Heading level="h4" gutterBottom>
                  Generated Content Preview
                </Heading>
                <div className={styles['preview-content']}>
                  <p>✨ AI content generation completed successfully!</p>
                  <p className={styles['placeholder-text']}>
                    Preview of generated content will be displayed here. This will include:
                  </p>
                  <ul>
                    <li>Generated questions, slides, or exercises</li>
                    <li>Edit and refine options</li>
                    <li>Save to course button</li>
                  </ul>
                  <p className={styles['coming-soon']}>
                    🚀 Full AI integration with course-generator service coming in Phase 6
                  </p>
                </div>
                <div className={styles['preview-actions']}>
                  <Button variant="secondary">
                    Regenerate
                  </Button>
                  <Button variant="primary">
                    Save to Course
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Feature Info */}
        <Card variant="outlined" padding="medium" className={styles['info-card']}>
          <Heading level="h4" gutterBottom>
            💡 AI-Powered Content Generation
          </Heading>
          <p>
            Our AI content generator uses advanced language models to create high-quality educational content tailored to your training program. Features include:
          </p>
          <ul className={styles['feature-list']}>
            <li><strong>Quiz Generator:</strong> Multiple-choice, true/false, and short-answer questions</li>
            <li><strong>Slide Creator:</strong> Professional presentation slides with diagrams and examples</li>
            <li><strong>Exercise Builder:</strong> Hands-on coding labs with starter code and solutions</li>
            <li><strong>Syllabus Designer:</strong> Complete course structure with learning objectives</li>
          </ul>
        </Card>
      </div>
    </DashboardLayout>
  );
};
