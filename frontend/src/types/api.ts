// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: string;
  };
  message?: string;
  timestamp?: string;
}

// 认证相关类型
export interface LoginRequest {
  password: string;
}

export interface LoginResponse {
  token: string;
  expires_in: number;
}

export interface TokenVerifyResponse {
  valid: boolean;
  expires_at?: number;
  issued_at?: number;
}

// 文件上传类型
export interface FileUploadResponse {
  charts: ChartConfig[];
  model_used: string;
  file_info: FileInfo;
  data_summary: DataSummary;
  processing_time: number;
  session_id?: string;
  raw_data?: RawDataInfo;
  processing_details?: ProcessingDetails;
}

export interface DataSummary {
  columns: string[];
  row_count: number;
  column_types: Record<string, string>;
  stats?: Record<string, any>;
}

// 原始数据信息
export interface RawDataInfo {
  preview_data: any[][];  // 数据预览（前几行）
  total_rows: number;
  total_columns: number;
  file_info: FileInfo;
}

// 处理详情
export interface ProcessingDetails {
  model_used: string;
  prompt_used: string;  // 使用的提示词
  generation_time: number;  // 生成耗时（秒）
  timestamp: string;
  input_tokens: number;  // 输入token数
  output_tokens: number;  // 输出token数
  total_tokens: number;  // 总token数
  start_time: number;  // 开始时间戳
  end_time: number;  // 结束时间戳
  retry_count?: number;  // 实际重试次数
  max_retries?: number;  // 最大重试次数
}

// 图表配置类型
export interface ChartConfig {
  id: string;
  title: string;
  type: string;
  option: any; // ECharts配置对象
  description?: string;
  metadata?: ChartMetadata;  // 图表元数据
}

// 图表元数据
export interface ChartMetadata {
  data_source: string[];  // 数据来源列
  chart_reasoning?: string;  // 图表选择理由
  config_json?: string;  // 格式化的JSON配置
}

// 会话数据类型
export interface SessionData {
  session_id: string;
  charts: ChartConfig[];
  data_summary: DataSummary;
  file_info?: FileInfo;
  timestamp?: string;
  updated_at?: string;
  raw_data?: RawDataInfo;  // 原始数据
  processing_details?: ProcessingDetails;  // 处理详情
}

export interface FileInfo {
  original_filename: string;
  clean_filename: string;
  size: number;
  type: string;
}

// 系统信息类型
export interface ModelInfo {
  name: string;
  type: string;
  provider?: string;
  status: string;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  services?: any;
}

export interface SystemInfo {
  name: string;
  version: string;
  description: string;
  timestamp: string;
}

// 错误类型
export interface ApiError {
  code: string;
  message: string;
  details?: string;
}