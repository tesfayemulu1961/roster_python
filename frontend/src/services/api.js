import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
  refreshToken: () => api.post('/auth/refresh'),
};

export const rosterAPI = {
  getStudents: (params) => api.get('/roster/students', { params }),
  getStudent: (id) => api.get(`/roster/students/${id}`),
  createStudent: (data) => api.post('/roster/students', data),
  updateStudent: (id, data) => api.put(`/roster/students/${id}`, data),
  deleteStudent: (id) => api.delete(`/roster/students/${id}`),
  getParents: () => api.get('/roster/parents'),
  createParent: (data) => api.post('/roster/parents', data),
  getEnrollments: (params) => api.get('/roster/enrollments', { params }),
  createEnrollment: (data) => api.post('/roster/enrollments', data),
  getAssignments: (params) => api.get('/roster/assignments', { params }),
  createAssignment: (data) => api.post('/roster/assignments', data),
};

export const teacherAPI = {
  getTeachers: (params) => api.get('/teachers', { params }),
  getTeacher: (id) => api.get(`/teachers/${id}`),
  createTeacher: (data) => api.post('/teachers', data),
  updateTeacher: (id, data) => api.put(`/teachers/${id}`, data),
  deleteTeacher: (id) => api.delete(`/teachers/${id}`),
  getAssignments: (id) => api.get(`/teachers/${id}/assignments`),
  assignTeacher: (id, data) => api.post(`/teachers/${id}/assignments`, data),
  getStats: () => api.get('/teachers/stats'),
};

export const gradeAPI = {
  getGrades: () => api.get('/grades'),
  getSections: (grade) => api.get(`/grades/${grade}/sections`),
  getAllSections: (params) => api.get('/sections', { params }),
  getGradeDetail: (grade) => api.get(`/grades/${grade}`),
  getAcademicYears: () => api.get('/academic-years'),
};

export const scoreAPI = {
  getScores: (params) => api.get('/scores', { params }),
  getScore: (id) => api.get(`/scores/${id}`),
  createScore: (data) => api.post('/scores', data),
  updateScore: (id, data) => api.put(`/scores/${id}`, data),
  deleteScore: (id) => api.delete(`/scores/${id}`),
  bulkCreateScores: (data) => api.post('/scores/bulk', data),
  getStudentReport: (id, params) => api.get(`/scores/student/${id}/report`, { params }),
  getSummary: (params) => api.get('/scores/summary', { params }),
};

export const adminAPI = {
  getUsers: (params) => api.get('/admin/users', { params }),
  getUser: (id) => api.get(`/admin/users/${id}`),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  toggleUserStatus: (id) => api.post(`/admin/users/${id}/toggle-status`),
  getActivityLog: (params) => api.get('/admin/activity-log', { params }),
  getStats: () => api.get('/admin/stats'),
};

export const dashboardAPI = {
  getData: () => api.get('/dashboard/data'),
};

export default api;
