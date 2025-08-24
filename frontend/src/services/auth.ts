import axios from 'axios';
import type { ApiResponse, LoginRequest, LoginResponse, TokenVerifyResponse } from '@/types/api';

const TOKEN_KEY = 'insightchart_token';
const TOKEN_EXPIRES_KEY = 'insightchart_token_expires';

export class AuthService {
  private token: string | null = null;
  private tokenExpires: number | null = null;

  constructor() {
    this.loadTokenFromStorage();
  }

  /**
   * 从localStorage加载token
   */
  private loadTokenFromStorage(): void {
    this.token = sessionStorage.getItem(TOKEN_KEY);
    const expiresStr = sessionStorage.getItem(TOKEN_EXPIRES_KEY);
    this.tokenExpires = expiresStr ? parseInt(expiresStr) : null;
  }

  /**
   * 保存token到localStorage
   */
  private saveTokenToStorage(token: string, expiresIn: number): void {
    const expiresAt = Date.now() + (expiresIn * 1000);
    
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(TOKEN_EXPIRES_KEY, expiresAt.toString());
    
    this.token = token;
    this.tokenExpires = expiresAt;
  }

  /**
   * 清除token
   */
  private clearToken(): void {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_EXPIRES_KEY);
    this.token = null;
    this.tokenExpires = null;
  }

  /**
   * 检查token是否已过期
   */
  private isTokenExpired(): boolean {
    if (!this.tokenExpires) return true;
    return Date.now() > this.tokenExpires;
  }

  /**
   * 用户登录
   */
  async login(password: string): Promise<LoginResponse> {
    try {
      const request: LoginRequest = { password };
      
      const response = await axios.post<ApiResponse<LoginResponse>>('/api/auth/login', request);
      
      if (response.data.success && response.data.data) {
        const { token, expires_in } = response.data.data;
        this.saveTokenToStorage(token, expires_in);
        return response.data.data;
      } else {
        throw new Error(response.data.error?.message || '登录失败');
      }
    } catch (error: any) {
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error.message);
      }
      throw new Error('登录请求失败，请检查网络连接');
    }
  }

  /**
   * 验证token
   */
  async verifyToken(): Promise<boolean> {
    if (!this.token || this.isTokenExpired()) {
      this.clearToken();
      return false;
    }

    try {
      const response = await axios.post<ApiResponse<TokenVerifyResponse>>(
        '/api/auth/verify',
        {},
        {
          headers: { Authorization: `Bearer ${this.token}` }
        }
      );

      if (response.data.success && response.data.data?.valid) {
        return true;
      } else {
        this.clearToken();
        return false;
      }
    } catch (error) {
      this.clearToken();
      return false;
    }
  }

  /**
   * 登出
   */
  logout(): void {
    this.clearToken();
  }

  /**
   * 获取当前token
   */
  getToken(): string | null {
    if (this.isTokenExpired()) {
      this.clearToken();
      return null;
    }
    return this.token;
  }

  /**
   * 检查是否已登录
   */
  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  /**
   * 获取认证头
   */
  getAuthHeader(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

// 创建全局实例
export const authService = new AuthService();