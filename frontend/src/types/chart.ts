import type { ChartConfig } from './api';

// 图表展示状态
export interface ChartDisplayState {
  loading: boolean;
  error: string | null;
  charts: ChartConfig[];
}

// 图表导出选项
export interface ChartExportOptions {
  type: 'png' | 'jpeg' | 'svg';
  pixelRatio: number;
  backgroundColor: string;
  quality?: number;
}

// 图表主题配置
export interface ChartTheme {
  backgroundColor: string;
  textColor: string;
  colorPalette: string[];
}

// 图表生成选项
export interface ChartGenerationOptions {
  model?: string;
  maxCharts?: number;
  chartTypes?: string[];
}

// 图表操作类型
export type ChartAction = 'export' | 'regenerate' | 'delete' | 'edit';

// 图表状态枚举
export enum ChartStatus {
  LOADING = 'loading',
  SUCCESS = 'success',
  ERROR = 'error',
  EMPTY = 'empty'
}