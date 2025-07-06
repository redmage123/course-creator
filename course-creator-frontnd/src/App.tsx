import React, { useState } from 'react';

function App() {
  const [currentPage, setCurrentPage] = useState<string>('home');

  console.log('App rendering, currentPage:', currentPage);

  // Simple navigation function with proper TypeScript typing
  const navigateTo = (page: string) => {
    console.log('Navigating to:', page);
    setCurrentPage(page);
  };

  // Courses page component
  const CoursesPage = () => (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Available Courses</h1>
          <button 
            onClick={() => navigateTo('home')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            ← Back to Home
          </button>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Course 1 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="w-full h-48 bg-gradient-to-br from-blue-100 to-indigo-200 rounded-lg mb-4 flex items-center justify-center">
              <span className="text-blue-600 font-bold text-lg">Web Development</span>
            </div>
            <h3 className="text-xl font-semibold mb-2">Introduction to Web Development</h3>
            <p className="text-gray-600 mb-4">Learn HTML, CSS, and JavaScript basics</p>
            <div className="flex justify-between items-center">
              <span className="text-2xl font-bold text-blue-600">$99</span>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                Enroll Now
              </button>
            </div>
          </div>

          {/* Course 2 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="w-full h-48 bg-gradient-to-br from-green-100 to-emerald-200 rounded-lg mb-4 flex items-center justify-center">
              <span className="text-green-600 font-bold text-lg">React Mastery</span>
            </div>
            <h3 className="text-xl font-semibold mb-2">Advanced React Development</h3>
            <p className="text-gray-600 mb-4">Master React hooks and advanced patterns</p>
            <div className="flex justify-between items-center">
              <span className="text-2xl font-bold text-blue-600">$149</span>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                Enroll Now
              </button>
            </div>
          </div>

          {/* Course 3 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="w-full h-48 bg-gradient-to-br from-purple-100 to-pink-200 rounded-lg mb-4 flex items-center justify-center">
              <span className="text-purple-600 font-bold text-lg">Python Data</span>
            </div>
            <h3 className="text-xl font-semibold mb-2">Python for Data Science</h3>
            <p className="text-gray-600 mb-4">Learn data analysis with Python</p>
            <div className="flex justify-between items-center">
              <span className="text-2xl font-bold text-blue-600">$129</span>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                Enroll Now
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Home page component
  const HomePage = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <header className="text-center mb-16">
          <h1 className="text-6xl font-bold text-gray-900 mb-6">
            Welcome to{' '}
            <span className="text-blue-600">Course Creator</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            The ultimate platform for creating, sharing, and learning through professional online courses.
            Join thousands of instructors and students worldwide.
          </p>
          <div className="space-x-4">
            <button 
              onClick={() => navigateTo('courses')}
              className="bg-blue-600 text-white font-semibold text-lg px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Browse Courses
            </button>
            <button 
              onClick={() => navigateTo('teaching')}
              className="text-blue-600 border-2 border-blue-600 font-semibold text-lg px-8 py-3 rounded-lg hover:bg-blue-50 transition-colors"
            >
              Start Teaching
            </button>
          </div>
        </header>

        {/* System Status Card */}
        <div className="max-w-md mx-auto mb-12">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-2">System Status</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Frontend:</span>
                <span className="text-green-600">✅ Running</span>
              </div>
              <div className="flex justify-between">
                <span>Current Page:</span>
                <span className="text-blue-600 font-semibold">{currentPage}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-16">
          <div className="bg-white rounded-xl shadow-lg p-6 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Quality Content</h3>
            <p className="text-gray-600">Create and access high-quality courses from expert instructors worldwide.</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Community Learning</h3>
            <p className="text-gray-600">Connect with learners and instructors in a vibrant learning community.</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Certificates & Progress</h3>
            <p className="text-gray-600">Earn verified certificates and track your learning progress.</p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <div className="bg-blue-600 rounded-2xl p-12 text-white">
            <h2 className="text-3xl font-bold mb-4">Ready to Start Your Learning Journey?</h2>
            <p className="text-xl mb-8 opacity-90">Join our platform today and unlock your potential with expert-led courses.</p>
            <button 
              onClick={() => navigateTo('courses')}
              className="bg-white text-blue-600 font-semibold py-3 px-8 rounded-lg hover:bg-gray-100 transition-colors"
            >
              Get Started Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Teaching page component (placeholder)
  const TeachingPage = () => (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      <div className="container mx-auto px-4 py-16 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Start Teaching Today!</h1>
        <p className="text-xl text-gray-600 mb-8">Share your knowledge with the world</p>
        <button 
          onClick={() => navigateTo('home')}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
        >
          ← Back to Home
        </button>
      </div>
    </div>
  );

  // Render the appropriate page based on currentPage state
  if (currentPage === 'courses') {
    return <CoursesPage />;
  }
  
  if (currentPage === 'teaching') {
    return <TeachingPage />;
  }
  
  return <HomePage />;
}

export default App;
