<template>
  <div class="chart-display-container">
    <!-- 数据摘要信息 -->
    <div v-if="dataSummary" class="data-summary">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>数据概览</span>
            <el-button 
              type="primary" 
              text 
              @click="toggleSummaryDetails"
              :icon="summaryExpanded ? ArrowUp : ArrowDown"
            >
              {{ summaryExpanded ? '收起' : '详情' }}
            </el-button>
          </div>
        </template>
        
        <div class="summary-basic">
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="summary-item">
                <div class="summary-label">数据行数</div>
                <div class="summary-value">{{ dataSummary.row_count.toLocaleString() }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-item">
                <div class="summary-label">字段数量</div>
                <div class="summary-value">{{ dataSummary.columns.length }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-item">
                <div class="summary-label">生成图表</div>
                <div class="summary-value">{{ charts.length }}</div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <div v-if="summaryExpanded" class="summary-details">
          <el-divider />
          <div class="columns-info">
            <h4>字段信息</h4>
            <div class="columns-grid">
              <div 
                v-for="column in dataSummary.columns" 
                :key="column"
                class="column-item"
              >
                <el-tag 
                  :type="getColumnTypeTag(dataSummary.column_types[column])"
                  size="small"
                >
                  {{ column }}
                </el-tag>
                <span class="column-type">{{ dataSummary.column_types[column] }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 图表网格 -->
    <div v-if="charts.length > 0" class="charts-grid">
      <div 
        v-for="chart in charts" 
        :key="chart.id"
        class="chart-item"
      >
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="chart-header">
              <div class="chart-title">
                <h3>{{ chart.title }}</h3>
                <p v-if="chart.description" class="chart-description">
                  {{ chart.description }}
                </p>
              </div>
              <div class="chart-actions">
                <el-dropdown @command="handleChartAction">
                  <el-button type="primary" text>
                    更多
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item 
                        :command="{ action: 'download', chartId: chart.id }"
                        :icon="Download"
                      >
                        下载PNG
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{ action: 'downloadJPG', chartId: chart.id }"
                        :icon="Download"
                      >
                        下载JPG
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{ action: 'copy', chartId: chart.id }"
                        :icon="CopyDocument"
                      >
                        复制图片
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{ action: 'fullscreen', chartId: chart.id }"
                        :icon="FullScreen"
                      >
                        全屏查看
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{ action: 'viewJson', chartId: chart.id }"
                        :icon="Document"
                        divided
                      >
                        查看JSON配置
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </template>
          
          <div class="chart-container">
            <div 
              :ref="(el) => setChartRef(chart.id, el)"
              :id="`chart-${chart.id}`"
              class="chart-wrapper"
              v-loading="chartLoading[chart.id]"
            ></div>
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty 
        description="暂无图表数据"
        :image-size="100"
      >
        <template #image>
          <el-icon size="100" color="#e6e8eb"><PieChart /></el-icon>
        </template>
      </el-empty>
    </div>
    
    <!-- 操作工具栏 -->
    <div v-if="charts.length > 0" class="chart-toolbar">
      <el-card shadow="never">
        <div class="toolbar-content">
          <div class="toolbar-left">
            <el-button 
              type="primary"
              :icon="Refresh"
              :loading="regenerating"
              @click="handleRegenerate"
            >
              {{ regenerating ? '重新生成中...' : '重新生成图表' }}
            </el-button>
          </div>
          
          <div class="toolbar-right">
            <el-button 
              type="default"
              :icon="Download"
              @click="handleDownloadAll"
            >
              批量下载
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 全屏预览对话框 -->
    <el-dialog
      v-model="fullscreenVisible"
      title="图表预览"
      width="90%"
      :destroy-on-close="true"
      @close="handleFullscreenClose"
    >
      <div 
        v-if="fullscreenChart"
        :id="`fullscreen-chart-${fullscreenChart.id}`"
        class="fullscreen-chart"
      ></div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  ArrowDown, 
  ArrowUp, 
  Download, 
  CopyDocument, 
  FullScreen, 
  Refresh, 
  PieChart,
  Document
} from '@element-plus/icons-vue';
import { chartService } from '@/services/chart';
import { apiService } from '@/services/api';
import type { ChartConfig, DataSummary } from '@/types/api';

// 定义props
interface Props {
  charts: ChartConfig[];
  dataSummary?: DataSummary;
  sessionId?: string;
}

const props = withDefaults(defineProps<Props>(), {
  charts: () => [],
});

// 定义emit事件
const emit = defineEmits<{
  chartsUpdated: [charts: ChartConfig[]]
  viewJson: [chartId: string]
}>();

// 响应式数据
const chartRefs = ref<Record<string, HTMLElement>>({});
const chartLoading = reactive<Record<string, boolean>>({});
const summaryExpanded = ref(false);
const regenerating = ref(false);
const fullscreenVisible = ref(false);
const fullscreenChart = ref<ChartConfig | null>(null);

// 设置图表DOM引用
const setChartRef = (chartId: string, el: any): void => {
  if (el && el instanceof HTMLElement) {
    chartRefs.value[chartId] = el;
  }
};

// 初始化图表
const initializeCharts = async (): Promise<void> => {
  await nextTick();
  
  for (const chart of props.charts) {
    const container = chartRefs.value[chart.id];
    if (container) {
      chartLoading[chart.id] = true;
      
      try {
        // 初始化图表实例
        chartService.initChart(container, chart.id);
        
        // 渲染图表
        chartService.renderChart(chart.id, chart);
        
      } catch (error) {
        console.error(`Error initializing chart ${chart.id}:`, error);
        ElMessage.error(`图表 "${chart.title}" 渲染失败`);
      } finally {
        chartLoading[chart.id] = false;
      }
    }
  }
};

// 获取列类型标签样式
const getColumnTypeTag = (type: string): string => {
  const typeMap: Record<string, string> = {
    '数值': 'primary',
    '整数': 'success',
    '小数': 'success',
    '文本': 'info',
    '日期': 'warning',
    '分类': 'danger',
  };
  return typeMap[type] || 'default';
};

// 切换摘要详情显示
const toggleSummaryDetails = (): void => {
  summaryExpanded.value = !summaryExpanded.value;
};

// 处理图表操作
const handleChartAction = async (command: { action: string; chartId: string }): Promise<void> => {
  const { action, chartId } = command;
  
  switch (action) {
    case 'download':
      chartService.downloadChart(chartId);
      break;
      
    case 'downloadJPG':
      chartService.downloadChart(chartId, undefined, { type: 'jpeg' });
      break;
      
    case 'copy':
      await copyChartToClipboard(chartId);
      break;
      
    case 'fullscreen':
      showFullscreenChart(chartId);
      break;
      
    case 'viewJson':
      emit('viewJson', chartId);
      break;
  }
};

// 复制图表到剪贴板
const copyChartToClipboard = async (chartId: string): Promise<void> => {
  try {
    const dataURL = chartService.exportChart(chartId);
    if (!dataURL) {
      ElMessage.error('图表导出失败');
      return;
    }
    
    // 将dataURL转换为Blob
    const response = await fetch(dataURL);
    const blob = await response.blob();
    
    // 复制到剪贴板
    await navigator.clipboard.write([
      new ClipboardItem({ 'image/png': blob })
    ]);
    
    ElMessage.success('图表已复制到剪贴板');
  } catch (error) {
    console.error('Copy to clipboard failed:', error);
    ElMessage.error('复制失败，请使用下载功能');
  }
};

// 全屏显示图表
const showFullscreenChart = (chartId: string): void => {
  const chart = props.charts.find(c => c.id === chartId);
  if (!chart) return;
  
  fullscreenChart.value = chart;
  fullscreenVisible.value = true;
  
  // 等待对话框渲染完成后初始化图表
  nextTick(() => {
    const container = document.getElementById(`fullscreen-chart-${chartId}`);
    if (container) {
      const fullscreenChartId = `fullscreen-${chartId}`;
      chartService.initChart(container, fullscreenChartId);
      chartService.renderChart(fullscreenChartId, chart);
    }
  });
};

// 关闭全屏预览
const handleFullscreenClose = (): void => {
  if (fullscreenChart.value) {
    chartService.destroyChart(`fullscreen-${fullscreenChart.value.id}`);
    fullscreenChart.value = null;
  }
};

// 重新生成图表
const handleRegenerate = async (): Promise<void> => {
  if (!props.sessionId) {
    ElMessage.error('会话信息丢失，无法重新生成图表');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      '重新生成将覆盖当前所有图表，是否继续？',
      '确认重新生成',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    regenerating.value = true;
    
    // 销毁当前图表
    props.charts.forEach(chart => {
      chartService.destroyChart(chart.id);
    });
    
    // 提示用户需要重新上传文件
    ElMessage.info('请重新上传文件来生成新的图表');
    
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败');
    }
  } finally {
    regenerating.value = false;
  }
};

// 批量下载所有图表
const handleDownloadAll = async (): Promise<void> => {
  try {
    // 调用后端ZIP下载API
    const blob = await apiService.downloadChartsZip(props.charts);
    
    // 创建下载链接
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `图表集合-${new Date().toISOString().slice(0, 10)}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    ElMessage.success(`成功下载 ${props.charts.length} 个图表到ZIP文件`);
  } catch (error) {
    console.error('ZIP download failed:', error);
    ElMessage.error('批量下载失败，请重试');
  }
};

// 监听charts变化，重新初始化图表
watch(() => props.charts, async (newCharts) => {
  if (newCharts.length > 0) {
    // 清理旧的加载状态
    Object.keys(chartLoading).forEach(key => {
      delete chartLoading[key];
    });
    
    // 初始化新图表
    await initializeCharts();
  }
}, { immediate: true });

// 组件挂载时初始化图表
onMounted(() => {
  if (props.charts.length > 0) {
    initializeCharts();
  }
});

// 组件卸载时清理图表
onUnmounted(() => {
  chartService.destroyAllCharts();
});
</script>

<style scoped>
.chart-display-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.data-summary {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-basic {
  margin-bottom: 16px;
}

.summary-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.summary-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.summary-details {
  padding-top: 16px;
}

.columns-info h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
}

.columns-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}

.column-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.column-type {
  font-size: 12px;
  color: #666;
}

.charts-grid {
  display: flex;
  flex-direction: column;
  gap: 32px;
  margin-bottom: 24px;
}

.chart-card {
  width: 100%;
  height: auto;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.chart-title h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #333;
}

.chart-description {
  margin: 0;
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.chart-container {
  position: relative;
}

.chart-wrapper {
  width: 100%;
  height: 400px;
  min-height: 400px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.chart-toolbar {
  position: sticky;
  bottom: 20px;
  z-index: 10;
}

.toolbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.fullscreen-chart {
  width: 100%;
  height: 500px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-display-container {
    padding: 16px;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .chart-wrapper {
    height: 250px;
    min-height: 250px;
  }
  
  .summary-basic .el-row {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .columns-grid {
    grid-template-columns: 1fr;
  }
  
  .toolbar-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .toolbar-left,
  .toolbar-right {
    width: 100%;
  }
  
  .toolbar-left .el-button,
  .toolbar-right .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .chart-header {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .chart-actions {
    align-self: flex-end;
  }
}
</style>