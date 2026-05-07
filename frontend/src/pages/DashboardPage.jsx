import { useState, useEffect } from 'react';
import { dashboardAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const StatCard = ({ label, value, color }) => (
  <div className={`bg-white rounded-xl shadow-sm p-6 border-l-4 ${color}`}>
    <p className="text-sm text-gray-500">{label}</p>
    <p className="text-3xl font-bold text-gray-800 mt-1">{value}</p>
  </div>
);

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    dashboardAPI.getData()
      .then(res => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  const summary = data?.summary || {};
  const role = data?.role || user?.user_type || 'user';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 capitalize">
          {role.replace('_', ' ')} Dashboard
        </h1>
        <p className="text-gray-500 mt-1">Welcome back, {user?.username}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {summary.total_students != null && (
          <StatCard label="Total Students" value={summary.total_students} color="border-blue-500" />
        )}
        {summary.total_teachers != null && (
          <StatCard label="Total Teachers" value={summary.total_teachers} color="border-green-500" />
        )}
        {summary.total_users != null && (
          <StatCard label="Total Users" value={summary.total_users} color="border-purple-500" />
        )}
        {summary.today_logins != null && (
          <StatCard label="Today's Logins" value={summary.today_logins} color="border-amber-500" />
        )}
        {summary.total_assignments != null && (
          <StatCard label="Assignments" value={summary.total_assignments} color="border-cyan-500" />
        )}
        {summary.grades_covered != null && (
          <StatCard label="Grades Covered" value={summary.grades_covered} color="border-rose-500" />
        )}
        {summary.teachers_assigned != null && (
          <StatCard label="Teachers Assigned" value={summary.teachers_assigned} color="border-orange-500" />
        )}
        {summary.kg_students != null && (
          <StatCard label="KG Students" value={summary.kg_students} color="border-pink-500" />
        )}
      </div>

      {data?.students_by_grade && Object.keys(data.students_by_grade).length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Students by Grade</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {Object.entries(data.students_by_grade).map(([grade, count]) => (
              <div key={grade} className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-sm text-gray-500 capitalize">{grade}</p>
                <p className="text-2xl font-bold text-gray-800">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {data?.recent_activity && data.recent_activity.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Recent Activity</h2>
          <div className="space-y-2">
            {data.recent_activity.slice(0, 10).map((log) => (
              <div key={log.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    log.action?.includes('success') ? 'bg-green-500' :
                    log.action?.includes('failed') ? 'bg-red-500' : 'bg-blue-500'
                  }`} />
                  <div>
                    <p className="text-sm font-medium text-gray-700">{log.username || 'Unknown'}</p>
                    <p className="text-xs text-gray-500 capitalize">{log.action?.replace('_', ' ')}</p>
                  </div>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(log.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data?.assignments && data.assignments.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Your Assignments</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-gray-600">Grade</th>
                  <th className="px-4 py-2 text-left text-gray-600">Section</th>
                  <th className="px-4 py-2 text-left text-gray-600">Subject</th>
                  <th className="px-4 py-2 text-left text-gray-600">Academic Year</th>
                </tr>
              </thead>
              <tbody>
                {data.assignments.map((a) => (
                  <tr key={a.id} className="border-b border-gray-100">
                    <td className="px-4 py-2">{a.grade}</td>
                    <td className="px-4 py-2">{a.section || '-'}</td>
                    <td className="px-4 py-2">{a.subject || '-'}</td>
                    <td className="px-4 py-2">{a.academic_year}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data?.students && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            {role === 'student' ? 'Your Scores' : 'Students'}
          </h2>
          {data.scores ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-gray-600">Subject</th>
                    <th className="px-4 py-2 text-left text-gray-600">Score</th>
                    <th className="px-4 py-2 text-left text-gray-600">Grade</th>
                    <th className="px-4 py-2 text-left text-gray-600">Term</th>
                  </tr>
                </thead>
                <tbody>
                  {data.scores.map((s) => (
                    <tr key={s.id} className="border-b border-gray-100">
                      <td className="px-4 py-2">{s.subject}</td>
                      <td className="px-4 py-2 font-medium">{s.score}</td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          s.grade === 'A' ? 'bg-green-100 text-green-700' :
                          s.grade === 'B' ? 'bg-blue-100 text-blue-700' :
                          s.grade === 'C' ? 'bg-yellow-100 text-yellow-700' :
                          s.grade === 'D' ? 'bg-orange-100 text-orange-700' :
                          'bg-red-100 text-red-700'
                        }`}>{s.grade || '-'}</span>
                      </td>
                      <td className="px-4 py-2">{s.term || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-gray-600">Name</th>
                    <th className="px-4 py-2 text-left text-gray-600">Grade</th>
                    <th className="px-4 py-2 text-left text-gray-600">Section</th>
                  </tr>
                </thead>
                <tbody>
                  {data.students.map((s) => (
                    <tr key={s.id} className="border-b border-gray-100">
                      <td className="px-4 py-2">{s.name}</td>
                      <td className="px-4 py-2">{s.grade}</td>
                      <td className="px-4 py-2">{s.section}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
