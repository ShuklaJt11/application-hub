/**
 * Dashboard Page Component
 * Main page for authenticated users
 */

const Dashboard = () => {
  return (
    <div className="bg-gradient-to-br from-primary-50 to-primary-100">
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-3xl font-bold text-primary-900 mb-4">Welcome to your Dashboard</h2>
          <p className="text-gray-600 mb-6">
            You are now logged in. This is your secure dashboard where you can manage your
            applications.
          </p>

          {/* Placeholder sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
            {/* Applications Section */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Applications</h3>
              <p className="text-gray-600">View and manage all your applications in one place.</p>
            </div>

            {/* Reminders Section */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Reminders</h3>
              <p className="text-gray-600">
                Set and track reminders for your important application milestones.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
