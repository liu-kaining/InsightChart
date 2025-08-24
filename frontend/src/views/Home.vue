<template>
  <div class="home-page">
    <!-- 主应用界面 -->
    <div class="main-section">
      <!-- 顶部导航 -->
      <header class="app-header">
        <div class="header-content">
          <div class="header-left">
            <h1 class="app-title">InsightChart AI</h1>
            <span class="app-subtitle">智能图表生成器</span>
          </div>
          
          <div v-if="hasCharts" class="header-right">
            <el-button 
              type="primary" 
              text 
              @click="startNewAnalysis"
              :icon="Plus"
            >
              新建分析
            </el-button>
          </div>
        </div>
      </header>
      
      <!-- 主要内容区域 -->
      <main class="app-main">
        <div class="main-content">
          <!-- 介绍和文件上传区域 -->
          <div v-if="!hasCharts" class="intro-section">
            <!-- 产品介绍 -->
            <div class="hero-section">
              <div class="hero-content">
                <h1 class="hero-title">AI 驱动的智能图表生成</h1>
                <p class="hero-subtitle">上传数据文件，让AI为您自动创建专业的数据可视化图表</p>
                
                <div class="features-grid">
                  <div class="feature-item">
                    <div class="feature-icon">📊</div>
                    <h3>智能分析</h3>
                    <p>AI自动分析数据特征，选择最合适的图表类型</p>
                  </div>
                  
                  <div class="feature-item">
                    <div class="feature-icon">🎨</div>
                    <h3>多样图表</h3>
                    <p>支持柱状图、折线图、饼图等多种专业图表</p>
                  </div>
                  
                  <div class="feature-item">
                    <div class="feature-icon">⚡</div>
                    <h3>快速生成</h3>
                    <p>几秒钟内生成8-20张精美图表，提升工作效率</p>
                  </div>
                  
                  <div class="feature-item">
                    <div class="feature-icon">🔒</div>
                    <h3>隐私安全</h3>
                    <p>数据仅用于图表生成，5分钟后自动清理</p>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 文件上传区域 -->
            <div class="upload-section">
              <div class="upload-intro">
                <h2>开始分析您的数据</h2>
                <p>支持Excel(.xlsx, .xls)和CSV文件，最大5MB</p>
              </div>
              
              <FileUpload
                @upload-success="handleUploadSuccess"
                @upload-error="handleUploadError"
                :require-auth="false"
              />
            </div>
          </div>
          
          <!-- 图表展示区域 -->
          <div v-else class="charts-section">
            <div class="charts-header">
              <h2>AI生成的图表分析</h2>
              <div class="charts-actions">
                <el-button 
                  type="default" 
                  text 
                  @click="showJsonViewer = true"
                  :icon="Document"
                >
                  查看JSON配置
                </el-button>
              </div>
            </div>
            
            <!-- 功能标签页 -->
            <div class="content-tabs">
              <el-tabs v-model="activeTab" class="analysis-tabs">
                <el-tab-pane label="图表展示" name="charts">
                  <ChartDisplay
                    :charts="charts"
                    :data-summary="dataSummary"
                    :session-id="sessionId"
                    @charts-updated="handleChartsUpdated"
                    @view-json="handleViewJson"
                  />
                </el-tab-pane>
                
                <el-tab-pane label="数据预览" name="data">
                  <DataPreview
                    :raw-data="rawData"
                    :data-summary="dataSummary"
                    :file-info="fileInfo"
                    :loading="dataPreviewLoading"
                    @refresh="refreshDataPreview"
                  />
                </el-tab-pane>
                
                <el-tab-pane label="处理详情" name="details">
                  <ProcessingDetails
                    :processing-details="processingDetails"
                    :charts="charts"
                  />
                </el-tab-pane>
              </el-tabs>
            </div>
          </div>
        </div>
      </main>
      
      <!-- 页脚 -->
      <footer class="app-footer">
        <div class="footer-content">
          <p>&copy; 2025 InsightChart AI. 基于大语言模型的智能图表生成器</p>
        </div>
      </footer>
    </div>
    
    <!-- 全局加载指示器 -->
    <div v-if="globalLoading" class="global-loading">
      <el-loading-service :visible="true" />
    </div>
    
    <!-- JSON配置查看器 -->
    <JsonViewer
      v-model:visible="showJsonViewer"
      :charts="charts"
      :default-chart-id="selectedChartIdForJson"
      @close="showJsonViewer = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Document } from '@element-plus/icons-vue';
import FileUpload from '@/components/FileUpload/FileUpload.vue';
import ChartDisplay from '@/components/ChartDisplay/ChartDisplay.vue';
import DataPreview from '@/components/DataPreview/DataPreview.vue';
import ProcessingDetails from '@/components/ProcessingDetails/ProcessingDetails.vue';
import JsonViewer from '@/components/JsonViewer/JsonViewer.vue';
import type { FileUploadResponse, ChartConfig, DataSummary, RawDataInfo, FileInfo, ProcessingDetails as ProcessingDetailsType } from '@/types/api';

// 响应式数据
const globalLoading = ref(false);
const hasCharts = ref(false);
const charts = ref<ChartConfig[]>([]);
const dataSummary = ref<DataSummary | undefined>();
const sessionId = ref<string>('');

// 新增的数据状态
const activeTab = ref('charts');
const showJsonViewer = ref(false);
const selectedChartIdForJson = ref<string>(''); // 用于默认选中的图表ID
const rawData = ref<RawDataInfo | undefined>();
const fileInfo = ref<FileInfo | undefined>();
const processingDetails = ref<ProcessingDetailsType | undefined>();
const dataPreviewLoading = ref(false);

// 处理文件上传成功
const handleUploadSuccess = (result: FileUploadResponse): void => {
  charts.value = result.charts;
  dataSummary.value = result.data_summary;
  sessionId.value = result.session_id || '';
  
  // 保存新增的数据
  fileInfo.value = result.file_info;
  rawData.value = result.raw_data;
  processingDetails.value = result.processing_details || {
    model_used: result.model_used,
    generation_time: result.processing_time,
    timestamp: new Date().toISOString(),
    prompt_used: '同步处理模式，无详细提示词',
    input_tokens: 0,
    output_tokens: 0,
    total_tokens: 0,
    start_time: 0,
    end_time: 0
  };
  
  hasCharts.value = true;
  activeTab.value = 'charts'; // 默认显示图表标签
  
  ElMessage.success(`成功生成了 ${result.charts.length} 张图表！`);
  
  // 滚动到图表区域
  setTimeout(() => {
    const chartsSection = document.querySelector('.charts-section');
    if (chartsSection) {
      chartsSection.scrollIntoView({ behavior: 'smooth' });
    }
  }, 500);
};
// 开始新的分析
const startNewAnalysis = async (): Promise<void> => {
  try {
    await ElMessageBox.confirm(
      '开始新的分析将清除当前图表，是否继续？',
      '确认新建分析',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    hasCharts.value = false;
    charts.value = [];
    dataSummary.value = undefined;
    sessionId.value = '';
    
    // 清除新增的数据状态
    rawData.value = undefined;
    fileInfo.value = undefined;
    processingDetails.value = undefined;
    activeTab.value = 'charts';
    showJsonViewer.value = false;
    
    // 滚动到上传区域
    setTimeout(() => {
      const uploadSection = document.querySelector('.upload-section');
      if (uploadSection) {
        uploadSection.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
    
  } catch (error) {
    // 用户取消，不做任何操作
  }
};

// 开始分析
const startAnalysis = (): void => {
  // 这里可以跳转到分析页面或显示上传组件
  ElMessage.info('开始分析功能');
};

// 处理文件上传错误
const handleUploadError = (error: string): void => {
  ElMessage.error(`上传失败: ${error}`);
};

// 处理图表更新
const handleChartsUpdated = (newCharts: ChartConfig[]): void => {
  charts.value = newCharts;
};

// 处理查看JSON配置
const handleViewJson = (chartId: string): void => {
  // 找到对应的图表
  const chart = charts.value.find(c => c.id === chartId);
  if (chart) {
    // 设置默认选中的图表ID
    selectedChartIdForJson.value = chartId;
    // 显示JSON查看器
    showJsonViewer.value = true;
  }
};

// 刷新数据预览
const refreshDataPreview = async (): Promise<void> => {
  if (!sessionId.value) {
    ElMessage.warning('没有有效的会话，无法刷新数据');
    return;
  }
  
  dataPreviewLoading.value = true;
  
  try {
    // 这里可以调用API重新获取数据
    ElMessage.success('数据刷新成功');
  } catch (error) {
    ElMessage.error('数据刷新失败');
  } finally {
    dataPreviewLoading.value = false;
  }
};
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.auth-section {
  flex: 1;
}

.main-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 顶部导航 */
.app-header {
  background: #ffffff;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.app-title {
  margin: 0;
  font-size: 20px;
  font-weight: bold;
  color: #2c3e50;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-subtitle {
  font-size: 12px;
  color: #7f8c8d;
}

/* 主要内容区域 */
.app-main {
  flex: 1;
  background: #f8f9fa;
  padding: 24px 0;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* 介绍区域 */
.intro-section {
  display: flex;
  flex-direction: column;
  gap: 48px;
}

/* Hero区域 */
.hero-section {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.hero-content {
  padding: 64px 48px;
  text-align: center;
  color: white;
}

.hero-title {
  margin: 0 0 16px 0;
  font-size: 48px;
  font-weight: 700;
  line-height: 1.2;
  background: linear-gradient(45deg, #ffffff, #f0f8ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  margin: 0 0 48px 0;
  font-size: 20px;
  line-height: 1.6;
  opacity: 0.9;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

/* 特性网格 */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 32px;
  margin-top: 24px;
}

.feature-item {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 32px 24px;
  text-align: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.2);
}

.feature-icon {
  font-size: 32px;
  margin-bottom: 16px;
  display: block;
}

.feature-item h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.feature-item p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  opacity: 0.9;
  color: white;
}

/* CTA区域 */
.cta-section {
  text-align: center;
  margin-top: 48px;
}

.cta-button {
  padding: 16px 48px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: white;
  transition: all 0.3s ease;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
}

.cta-subtitle {
  margin-top: 16px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
}

/* 上传区域 */
.upload-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.upload-intro {
  text-align: center;
  margin-bottom: 32px;
}

.upload-intro {
  margin-bottom: 48px;
}

.upload-intro h2 {
  margin: 0 0 12px 0;
  font-size: 28px;
  color: #2c3e50;
  font-weight: 600;
}

.upload-intro p {
  margin: 0;
  font-size: 16px;
  color: #7f8c8d;
  line-height: 1.6;
}

/* 图表区域 */
.charts-section {
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.charts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e0e0e0;
}

.charts-header h2 {
  margin: 0;
  font-size: 24px;
  color: #2c3e50;
  font-weight: 600;
}

.charts-actions {
  display: flex;
  gap: 12px;
}

/* 内容标签页 */
.content-tabs {
  margin-top: 16px;
}

.analysis-tabs {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.analysis-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: #fafafa;
  border-bottom: 1px solid #e4e7ed;
}

.analysis-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0 20px;
}

.analysis-tabs :deep(.el-tabs__item) {
  font-weight: 500;
  color: #606266;
  border: none;
}

.analysis-tabs :deep(.el-tabs__item.is-active) {
  color: #409eff;
  font-weight: 600;
}

.analysis-tabs :deep(.el-tabs__active-bar) {
  background-color: #409eff;
}

.analysis-tabs :deep(.el-tab-pane) {
  padding: 20px;
}

/* 页脚 */
.app-footer {
  background: #ffffff;
  border-top: 1px solid #e0e0e0;
  padding: 20px 0;
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  text-align: center;
}

.footer-content p {
  margin: 0;
  font-size: 12px;
  color: #95a5a6;
}

/* 全局加载 */
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
    height: 56px;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
  
  .app-title {
    font-size: 18px;
  }
  
  .main-content {
    padding: 0 16px;
  }
  
  /* Hero区域响应式 */
  .hero-content {
    padding: 48px 24px;
  }
  
  .hero-title {
    font-size: 32px;
  }
  
  .hero-subtitle {
    font-size: 16px;
    margin-bottom: 32px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .feature-item {
    padding: 24px 20px;
  }
  
  /* 上传区域响应式 */
  .upload-section {
    padding: 32px 24px;
    margin: 0 16px;
  }
  
  .upload-intro h2 {
    font-size: 24px;
  }
  
  .upload-intro p {
    font-size: 14px;
  }
  
  .charts-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .charts-header h2 {
    font-size: 20px;
  }
  
  .charts-actions {
    align-self: flex-end;
  }
}

@media (max-width: 480px) {
  .app-title {
    font-size: 16px;
  }
  
  .app-subtitle {
    font-size: 10px;
  }
  
  .hero-content {
    padding: 40px 20px;
  }
  
  .hero-title {
    font-size: 28px;
  }
  
  .hero-subtitle {
    font-size: 14px;
  }
  
  .upload-section {
    padding: 24px 16px;
    margin: 0 8px;
  }
  
  .upload-intro h2 {
    font-size: 20px;
  }
  
  .charts-header h2 {
    font-size: 18px;
  }
}
</style>