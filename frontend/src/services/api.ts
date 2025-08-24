import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { authService } from './auth';
import type { 
  ApiResponse, 
  FileUploadResponse, 
  SessionData, 
  ModelInfo, 
  SystemHealth, 
  SystemInfo,
  ChartConfig
} from '@/types/api';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器：自动添加认证头
    this.client.interceptors.request.use(
      (config) => {
        const authHeaders = authService.getAuthHeader();
        if (config.headers) {
          Object.assign(config.headers, authHeaders);
        } else {
          config.headers = authHeaders as any;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器：处理认证失败
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          authService.logout();
          // 可以在这里触发重新登录逻辑
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * 上传文件并生成图表（同步处理）
   */
  async uploadFile(file: File, model?: string): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (model) {
      formData.append('model', model);
    }

    const response = await this.client.post<ApiResponse<FileUploadResponse>>(
      '/file/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 180000, // 延长超时时间到3分钟以处理复杂的图表生成
      }
    );

    if (response.data.success && response.data.data) {
      return response.data.data;
    } else {
      throw new Error(response.data.error?.message || '文件上传失败');
    }
  }

  /**
   * 获取会话图表数据
   */
  async getSessionCharts(sessionId: string): Promise<SessionData> {
    const response = await this.client.get<ApiResponse<SessionData>>(
      `/file/session/${sessionId}`
    );

    if (response.data.success && response.data.data) {
      return response.data.data;
    } else {
      throw new Error(response.data.error?.message || '获取会话数据失败');
    }
  }

  /**
   * 获取可用模型列表
   */
  async getAvailableModels(): Promise<ModelInfo[]> {
    const response = await this.client.get<ApiResponse<{ models: ModelInfo[] }>>(
      '/system/models'
    );

    if (response.data.success && response.data.data) {
      return response.data.data.models;
    } else {
      throw new Error(response.data.error?.message || '获取模型列表失败');
    }
  }

  /**
   * 系统健康检查
   */
  async healthCheck(): Promise<SystemHealth> {
    const response = await this.client.get<ApiResponse<SystemHealth>>(
      '/system/health'
    );

    if (response.data.success && response.data.data) {
      return response.data.data;
    } else {
      throw new Error(response.data.error?.message || '健康检查失败');
    }
  }

  /**
   * 获取清理服务状态
   */
  async getCleanupStatus(): Promise<any> {
    const response = await this.client.get<ApiResponse<any>>(
      '/cleanup/status'
    );

    if (response.data.success && response.data.data) {
      return response.data.data;
    } else {
      throw new Error(response.data.error?.message || '获取清理状态失败');
    }
  }

  /**
   * 获取清理配置
   */
  async getCleanupConfig(): Promise<any> {
    const response = await this.client.get<ApiResponse<any>>(
      '/cleanup/config'
    );

    if (response.data.success && response.data.data) {
      return response.data.data;
    } else {
      throw new Error(response.data.error?.message || '获取清理配置失败');
    }
  }

  /**
   * 强制清理文件
   */
  async forceCleanup(): Promise<any> {
    const response = await this.client.post<ApiResponse<any>>(
      '/cleanup/force'
    );

    if (response.data.success) {
      return response.data.data;
    } else {
      throw new Error(response.data.error?.message || '手动清理失败');
    }
  }

  /**
   * 清理指定会话
   */
  async cleanupSession(sessionId: string): Promise<any> {
    const response = await this.client.delete<ApiResponse<any>>(
      `/cleanup/session/${sessionId}`
    );

    if (response.data.success) {
      return response.data.data;
    } else {
      throw new Error(response.data.error?.message || '清理会话失败');
    }
  }

  /**
   * 批量下载图表为ZIP文件
   */
  async downloadChartsZip(charts: any[]): Promise<Blob> {
    const response = await this.client.post(
      '/file/download-charts-zip',
      { charts },
      {
        responseType: 'blob',
      }
    );

    return response.data;
  }

  /**
   * 通用GET请求
   */
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    } else {
      throw new Error(response.data.error?.message || '请求失败');
    }
  }

  /**
   * 通用POST请求
   */
  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    } else {
      throw new Error(response.data.error?.message || '请求失败');
    }
  }
}

// 创建全局实例
export const apiService = new ApiService();