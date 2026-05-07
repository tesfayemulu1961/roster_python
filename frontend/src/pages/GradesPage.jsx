import { useState, useEffect } from 'react';
import { gradeAPI, scoreAPI, rosterAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function GradesPage() {
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedGrade, setSelectedGrade] = useState(null);
  const [sections, setSections] = useState([]);
  const [scoreModalOpen, setScoreModalOpen] = useState(false);
  const [selectedSection, setSelectedSection] = useState(null);
  const [students, setStudents] = useState([]);
  const [scores, setScores] = useState({});
  const [scoreForm, setScoreForm] = useState({ subject: '', term: '', academic_year: '' });
  const [submitting, setSubmitting] = useState(false);
  const { hasRole } = useAuth();

  const canEnterScores = hasRole(['director', 'vice_director', 'supervisor', 'subject teacher', 'room teacher']);

  useEffect(() => {
    gradeAPI.getGrades()
      .then(res => setGrades(res.data.grades))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleGradeClick = async (grade) => {
    setSelectedGrade(grade.grade);
    try {
      const res = await gradeAPI.getSections(grade.grade);
      setSections(res.data.sections);
    } catch (e) {
      setSections([]);
    }
  };

  const openScoreEntry = async (section) => {
    setSelectedSection(section);
    setScoreForm({ subject: '', term: '', academic_year: new Date().getFullYear().toString() + '-' + (new Date().getFullYear() + 1).toString() });
    try {
      const res = await rosterAPI.getStudents({ grade: selectedGrade, section: section.section });
      setStudents(res.data.students);
      const initialScores = {};
      res.data.students.forEach(s => { initialScores[s.id] = ''; });
      setScores(initialScores);
      setScoreModalOpen(true);
    } catch (e) {
      setStudents([]);
    }
  };

  const handleSubmitScores = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const entries = students
        .filter(s => scores[s.id] !== '')
        .map(s => ({
          student_id: s.id,
          subject: scoreForm.subject,
          score: parseFloat(scores[s.id]),
          term: scoreForm.term,
          academic_year: scoreForm.academic_year,
        }));

      if (entries.length > 0) {
        await scoreAPI.bulkCreateScores({ scores: entries });
      }
      setScoreModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to save scores');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Grades & Sections</h1>
        <p className="text-gray-500">Manage grade levels and class sections</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-indigo-500 border-t-transparent"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm p-4">
              <h2 className="font-semibold text-gray-700 mb-3">Grades</h2>
              <div className="space-y-2">
                {grades.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-4">No grades found</p>
                ) : grades.map((g) => (
                  <button
                    key={g.grade}
                    onClick={() => handleGradeClick(g)}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition text-left ${
                      selectedGrade === g.grade
                        ? 'bg-indigo-100 text-indigo-700 border border-indigo-200'
                        : 'bg-gray-50 hover:bg-gray-100 border border-transparent'
                    }`}
                  >
                    <span className="font-medium capitalize">{g.grade}</span>
                    <span className="text-sm text-gray-500">{g.student_count} students</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            {selectedGrade ? (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h2 className="font-semibold text-gray-700 mb-4 capitalize">
                  {selectedGrade} - Sections
                </h2>
                {sections.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No sections found for this grade</p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {sections.map((s) => (
                      <div key={s.section} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-gray-800">Section {s.section}</h3>
                          <span className="text-sm text-gray-500">{s.student_count} students</span>
                        </div>
                        {s.teachers && s.teachers.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {s.teachers.map((t, i) => (
                              <p key={i} className="text-xs text-gray-500">
                                {t.subject || 'Homeroom'} - Teacher #{t.teacher_id}
                              </p>
                            ))}
                          </div>
                        )}
                        {canEnterScores && (
                          <button
                            onClick={() => openScoreEntry(s)}
                            className="mt-3 w-full bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-sm font-medium py-2 rounded-lg transition"
                          >
                            Enter Scores
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm p-12 text-center">
                <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <p className="text-gray-500">Select a grade to view its sections</p>
              </div>
            )}
          </div>
        </div>
      )}

      {scoreModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                Enter Scores - {selectedGrade} Section {selectedSection?.section}
              </h2>
              <button onClick={() => setScoreModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmitScores} className="p-6 space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subject *</label>
                  <input
                    type="text"
                    value={scoreForm.subject}
                    onChange={(e) => setScoreForm({...scoreForm, subject: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Term</label>
                  <select
                    value={scoreForm.term}
                    onChange={(e) => setScoreForm({...scoreForm, term: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                  >
                    <option value="">Select</option>
                    <option value="1st Quarter">1st Quarter</option>
                    <option value="2nd Quarter">2nd Quarter</option>
                    <option value="3rd Quarter">3rd Quarter</option>
                    <option value="4th Quarter">4th Quarter</option>
                    <option value="Midterm">Midterm</option>
                    <option value="Final">Final</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Academic Year *</label>
                  <input
                    type="text"
                    value={scoreForm.academic_year}
                    onChange={(e) => setScoreForm({...scoreForm, academic_year: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                    required
                  />
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-gray-600 font-medium">Student</th>
                      <th className="px-4 py-2 text-center text-gray-600 font-medium">Score (0-100)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((s) => (
                      <tr key={s.id} className="border-b border-gray-100">
                        <td className="px-4 py-2">{s.name}</td>
                        <td className="px-4 py-2">
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={scores[s.id] || ''}
                            onChange={(e) => setScores({...scores, [s.id]: e.target.value})}
                            className="w-24 mx-auto block px-3 py-1.5 border border-gray-300 rounded-lg text-center focus:ring-2 focus:ring-indigo-500 outline-none"
                            placeholder="-"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setScoreModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg disabled:bg-indigo-400 transition"
                >
                  {submitting ? 'Saving...' : 'Save Scores'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
