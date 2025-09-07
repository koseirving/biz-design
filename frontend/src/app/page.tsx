export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      <main className="text-center space-y-8 p-8">
        <h1 className="text-6xl font-bold text-blue-600 dark:text-blue-400 mb-4">
          Biz Design
        </h1>
        <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-200">
          AI-powered Business Framework Learning Platform
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Hello World from Biz Design Frontend! Transform your business thinking with AI-guided framework learning.
        </p>
        <div className="bg-green-100 dark:bg-green-900 border border-green-400 text-green-700 dark:text-green-300 px-4 py-3 rounded-lg inline-block">
          🎉 Frontend service is running successfully!
        </div>
      </main>
      <footer className="absolute bottom-4 text-sm text-gray-500">
        Biz Design v1.0.0 - Powered by Next.js & FastAPI
      </footer>
    </div>
  );
}
