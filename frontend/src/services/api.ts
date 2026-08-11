// API service layer using axios for DeceptiScan frontend
// Implements communication with Flask backend

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  AnalysisResult,
  ArticleInput,
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  AnalysisHistoryItem,
  PaginatedResponse,
  UserFeedback,
  User,
  ApiError,
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds for ML processing
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Clear token on unauthorized
          localStorage.removeItem('authToken');
          // Optionally redirect to login
        }
        return Promise.reject(error);
      }
    );
  }

  // Analysis endpoints
  async analyzeText(input: Partial<ArticleInput>): Promise<AnalysisResult> {
    try {
      const response: AxiosResponse<AnalysisResult> = await this.api.post('/analyze', {
        content: input.content,
        sourceUrl: input.sourceUrl,
        title: input.title,
        language: input.language || 'en',
        contentType: input.contentType || 'text',
      });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getAnalysis(id: string): Promise<AnalysisResult> {
    try {
      const response: AxiosResponse<AnalysisResult> = await this.api.get(`/analyze/${id}`);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async deleteAnalysis(id: string): Promise<void> {
    try {
      await this.api.delete(`/analyze/${id}`);
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // Authentication endpoints
  async register(request: RegisterRequest): Promise<AuthResponse> {
    try {
      const response: AxiosResponse<AuthResponse> = await this.api.post('/auth/register', request);
      const { token } = response.data;
      localStorage.setItem('authToken', token);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async login(request: LoginRequest): Promise<AuthResponse> {
    try {
      const response: AxiosResponse<AuthResponse> = await this.api.post('/auth/login', request);
      const { token } = response.data;
      localStorage.setItem('authToken', token);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout');
    } catch (error: any) {
      // Continue with local logout even if server request fails
      console.warn('Server logout failed:', error);
    } finally {
      localStorage.removeItem('authToken');
    }
  }

  async getCurrentUser(): Promise<User> {
    try {
      const response: AxiosResponse<User> = await this.api.get('/auth/me');
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async updateCurrentUser(data: { username?: string }): Promise<User> {
    try {
      const response: AxiosResponse<User> = await this.api.patch('/auth/me', data);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // History endpoints
  async getRecentAnalyses(limit = 5): Promise<AnalysisHistoryItem[]> {
    try {
      const response = await this.api.get('/analyses/recent', {
        params: { limit },
      });
      return response.data.items || [];
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getAnalysisHistory(page = 1, limit = 10): Promise<PaginatedResponse<AnalysisHistoryItem>> {
    try {
      const response = await this.api.get('/history', {
        params: { page, limit },
      });
      const resData = response.data;
      const itemsList = resData.data || resData.items || [];
      const paginationObj = resData.pagination || {
        page: resData.page || page,
        limit: resData.limit || limit,
        total: resData.total || 0,
        totalPages: resData.pages || resData.totalPages || 1,
      };
      return {
        data: itemsList,
        pagination: paginationObj,
      };
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getHistoryItem(id: string): Promise<AnalysisResult> {
    try {
      const response: AxiosResponse<AnalysisResult> = await this.api.get(`/history/${id}`);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // Feedback endpoints
  async submitFeedback(feedback: Omit<UserFeedback, 'id' | 'createdAt'>): Promise<{ feedbackId: string }> {
    try {
      const response: AxiosResponse<{ feedbackId: string }> = await this.api.post('/feedback', feedback);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // Health check
  async getHealth(): Promise<{ status: string; version: string; modelStatus: string }> {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // Utility methods
  isAuthenticated(): boolean {
    return !!localStorage.getItem('authToken');
  }

  private handleError(error: any): ApiError {
    if (error.response?.data?.error) {
      return error.response.data.error;
    }
    
    if (error.response?.status) {
      return {
        code: 'HTTP_ERROR',
        message: `Request failed with status ${error.response.status}`,
        details: { status: error.response.status },
      };
    }

    if (error.code === 'ECONNABORTED') {
      return {
        code: 'TIMEOUT',
        message: 'Request timed out. Please try again.',
      };
    }

    return {
      code: 'NETWORK_ERROR',
      message: 'Network error occurred. Please check your connection.',
    };
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;