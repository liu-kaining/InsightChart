import * as echarts from 'echarts';
import type { ECharts, EChartsOption } from 'echarts';
import type { ChartConfig } from '@/types/api';
import type { ChartExportOptions, ChartTheme } from '@/types/chart';

export class ChartService {
  private chartInstances: Map<string, ECharts> = new Map();

  /**
   * 初始化图表
   */
  initChart(container: HTMLElement, chartId: string): ECharts {
    // 如果已存在实例，先销毁
    if (this.chartInstances.has(chartId)) {
      this.chartInstances.get(chartId)?.dispose();
    }

    const chart = echarts.init(container);
    this.chartInstances.set(chartId, chart);

    // 监听窗口大小变化
    const resizeHandler = () => {
      chart.resize();
    };
    window.addEventListener('resize', resizeHandler);

    // 存储resize处理器，用于后续清理
    (chart as any)._resizeHandler = resizeHandler;

    return chart;
  }

  /**
   * 渲染图表
   */
  renderChart(chartId: string, config: ChartConfig): void {
    const chart = this.chartInstances.get(chartId);
    if (!chart) {
      console.error(`Chart instance not found: ${chartId}`);
      return;
    }

    try {
      // 设置默认配置
      const defaultOption: EChartsOption = {
        backgroundColor: 'transparent',
        textStyle: {
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
        toolbox: {
          show: true,
          feature: {
            saveAsImage: {
              show: true,
              title: '下载图片',
              type: 'png',
              backgroundColor: '#ffffff',
              pixelRatio: 2,
            },
          },
          right: 10,
          top: 10,
        },
        animation: true,
        animationDuration: 1000,
      };

      // 合并配置
      const finalOption = this.mergeChartOptions(defaultOption, config.option);
      
      chart.setOption(finalOption, true);
    } catch (error) {
      console.error(`Error rendering chart ${chartId}:`, error);
    }
  }

  /**
   * 深度合并图表配置
   */
  private mergeChartOptions(defaultOption: EChartsOption, userOption: any): EChartsOption {
    // 简单的深度合并逻辑
    const merge = (target: any, source: any): any => {
      for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
          target[key] = target[key] || {};
          merge(target[key], source[key]);
        } else {
          target[key] = source[key];
        }
      }
      return target;
    };

    return merge({ ...defaultOption }, userOption);
  }

  /**
   * 导出图表
   */
  exportChart(chartId: string, options: Partial<ChartExportOptions> = {}): string | null {
    const chart = this.chartInstances.get(chartId);
    if (!chart) {
      console.error(`Chart instance not found: ${chartId}`);
      return null;
    }

    const defaultOptions: ChartExportOptions = {
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#ffffff',
      quality: 1,
    };

    const exportOptions = { ...defaultOptions, ...options };

    try {
      return chart.getDataURL({
        type: exportOptions.type,
        pixelRatio: exportOptions.pixelRatio,
        backgroundColor: exportOptions.backgroundColor,
      });
    } catch (error) {
      console.error(`Error exporting chart ${chartId}:`, error);
      return null;
    }
  }

  /**
   * 下载图表
   */
  downloadChart(chartId: string, filename?: string, options?: Partial<ChartExportOptions>): void {
    const dataURL = this.exportChart(chartId, options);
    if (!dataURL) return;

    const link = document.createElement('a');
    link.download = filename || `chart-${chartId}-${Date.now()}.png`;
    link.href = dataURL;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * 应用主题
   */
  applyTheme(chartId: string, theme: Partial<ChartTheme>): void {
    const chart = this.chartInstances.get(chartId);
    if (!chart) return;

    const currentOption = chart.getOption();
    const themedOption = {
      ...currentOption,
      backgroundColor: theme.backgroundColor,
      textStyle: {
        ...currentOption.textStyle,
        color: theme.textColor,
      },
      color: theme.colorPalette,
    };

    chart.setOption(themedOption, true);
  }

  /**
   * 获取图表实例
   */
  getChart(chartId: string): ECharts | undefined {
    return this.chartInstances.get(chartId);
  }

  /**
   * 销毁图表
   */
  destroyChart(chartId: string): void {
    const chart = this.chartInstances.get(chartId);
    if (chart) {
      // 移除resize监听器
      if ((chart as any)._resizeHandler) {
        window.removeEventListener('resize', (chart as any)._resizeHandler);
      }
      
      chart.dispose();
      this.chartInstances.delete(chartId);
    }
  }

  /**
   * 销毁所有图表
   */
  destroyAllCharts(): void {
    this.chartInstances.forEach((chart, chartId) => {
      this.destroyChart(chartId);
    });
    this.chartInstances.clear();
  }

  /**
   * 图表resize
   */
  resizeChart(chartId: string): void {
    const chart = this.chartInstances.get(chartId);
    if (chart) {
      chart.resize();
    }
  }

  /**
   * 获取预定义主题
   */
  getPresetThemes(): Record<string, ChartTheme> {
    return {
      default: {
        backgroundColor: '#ffffff',
        textColor: '#333333',
        colorPalette: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'],
      },
      dark: {
        backgroundColor: '#2c2c2c',
        textColor: '#ffffff',
        colorPalette: ['#dd6b66', '#759aa0', '#e69d87', '#8dc1a9', '#ea7e53', '#eedd78', '#73a373', '#73b9bc', '#7289ab'],
      },
      colorful: {
        backgroundColor: '#ffffff',
        textColor: '#333333',
        colorPalette: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd'],
      },
    };
  }
}

// 创建全局实例
export const chartService = new ChartService();