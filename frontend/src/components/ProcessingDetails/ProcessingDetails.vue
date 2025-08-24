<template>
  <div class="processing-details-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Setting /></el-icon>
            处理详情
          </span>
          <div class="actions">
            <el-tooltip content="复制提示词" placement="top">
              <el-button 
                type="primary" 
                :icon="CopyDocument" 
                size="small"
                @click="copyPrompt"
                :disabled="!processingDetails?.prompt_used"
              />
            </el-tooltip>
            <el-tooltip content="展开/收起" placement="top">
              <el-button 
                type="default" 
                :icon="expanded ? ArrowUp : ArrowDown" 
                size="small"
                @click="toggleExpanded"
              />
            </el-tooltip>
          </div>
        </div>
      </template>

      <div v-if="!expanded" class="summary-view">
        <div class="summary-info">
          <el-tag type="success" size="large">
            {{ processingDetails?.model_used || '未知模型' }}
          </el-tag>
          <span class="info-text">
            耗时: {{ formatDuration(processingDetails?.generation_time) }}
          </span>
          <span class="info-text">
            时间: {{ formatTimestamp(processingDetails?.timestamp) }}
          </span>
        </div>
      </div>

      <div v-else class="expanded-view">
        <!-- 基本信息 -->
        <div class="basic-info-section">
          <el-descriptions title="处理信息" :column="2" border>
            <el-descriptions-item label="使用模型">
              <el-tag type="success">{{ processingDetails?.model_used || '-' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="生成耗时">
              {{ formatDuration(processingDetails?.generation_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="处理时间">
              {{ formatTimestamp(processingDetails?.timestamp) }}
            </el-descriptions-item>
            <el-descriptions-item label="图表数量">
              {{ charts?.length || 0 }} 个
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 提示词展示 -->
        <div class="prompt-section">
          <div class="section-header">
            <h4>
              <el-icon><ChatLineSquare /></el-icon>
              大模型提示词
            </h4>
            <div class="actions">
              <el-button 
                type="primary" 
                size="small" 
                :icon="CopyDocument"
                @click="copyPrompt"
                :disabled="!processingDetails?.prompt_used"
              >
                复制
              </el-button>
              <el-button 
                type="default" 
                size="small" 
                :icon="Download"
                @click="downloadPrompt"
                :disabled="!processingDetails?.prompt_used"
              >
                下载
              </el-button>
            </div>
          </div>
          
          <div class="prompt-container">
            <el-input
              v-model="displayPrompt"
              type="textarea"
              :rows="promptRows"
              readonly
              placeholder="暂无提示词信息"
              class="prompt-textarea"
            />
            <div class="prompt-controls">
              <el-button-group size="small">
                <el-button 
                  :type="promptRows === 6 ? 'primary' : 'default'"
                  @click="promptRows = 6"
                >
                  收起
                </el-button>
                <el-button 
                  :type="promptRows === 12 ? 'primary' : 'default'"
                  @click="promptRows = 12"
                >
                  展开
                </el-button>
                <el-button 
                  :type="promptRows === 20 ? 'primary' : 'default'"
                  @click="promptRows = 20"
                >
                  全屏
                </el-button>
              </el-button-group>
              <div class="prompt-stats">
                字符数: {{ displayPrompt.length }} | 行数: {{ displayPrompt.split('\n').length }}
              </div>
            </div>
          </div>
        </div>

        <!-- 模型参数信息 -->
        <div class="model-params-section" v-if="modelParams">
          <div class="section-header">
            <h4>
              <el-icon><Setting /></el-icon>
              模型参数
            </h4>
          </div>
          
          <div class="params-grid">
            <el-card 
              v-for="(value, key) in modelParams" 
              :key="key"
              class="param-card"
              shadow="hover"
            >
              <div class="param-content">
                <div class="param-name">{{ formatParamName(key) }}</div>
                <div class="param-value">{{ formatParamValue(value) }}</div>
              </div>
            </el-card>
          </div>
        </div>

        <!-- 处理流程 -->
        <div class="workflow-section">
          <div class="section-header">
            <h4>
              <el-icon><Operation /></el-icon>
              处理流程
            </h4>
          </div>
          
          <el-timeline>
            <el-timeline-item 
              timestamp="步骤 1" 
              color="#409EFF"
              icon="Upload"
            >
              <div class="timeline-content">
                <h5>文件上传与解析</h5>
                <p>解析 Excel/CSV 文件，提取数据结构和内容</p>
              </div>
            </el-timeline-item>
            
            <el-timeline-item 
              timestamp="步骤 2" 
              color="#67C23A"
              icon="DataAnalysis"
            >
              <div class="timeline-content">
                <h5>数据分析</h5>
                <p>分析数据类型、统计信息，生成数据摘要</p>
              </div>
            </el-timeline-item>
            
            <el-timeline-item 
              timestamp="步骤 3" 
              color="#E6A23C"
              icon="ChatDotSquare"
            >
              <div class="timeline-content">
                <h5>大模型调用</h5>
                <p>使用 {{ processingDetails?.model_used || '大模型' }} 生成图表配置</p>
                <div class="model-info">
                  <el-tag type="warning" size="small">耗时: {{ formatDuration(processingDetails?.generation_time) }}</el-tag>
                  <el-tag 
                    v-if="processingDetails?.retry_count" 
                    :type="processingDetails.retry_count > 1 ? 'danger' : 'success'" 
                    size="small"
                  >
                    重试: {{ processingDetails.retry_count }}/{{ processingDetails.max_retries || 3 }}
                  </el-tag>
                </div>
              </div>
            </el-timeline-item>
            
            <el-timeline-item 
              timestamp="步骤 4" 
              color="#F56C6C"
              icon="PieChart"
            >
              <div class="timeline-content">
                <h5>图表渲染</h5>
                <p>生成 {{ charts?.length || 0 }} 个 ECharts 图表配置并渲染</p>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  Setting, 
  CopyDocument, 
  ArrowUp, 
  ArrowDown, 
  Download,
  ChatLineSquare,
  Operation
} from '@element-plus/icons-vue';
import type { ProcessingDetails, ChartConfig } from '@/types/api';

// 定义props
interface Props {
  processingDetails?: ProcessingDetails;
  charts?: ChartConfig[];
}

const props = withDefaults(defineProps<Props>(), {});

// 响应式数据
const expanded = ref(false);
const promptRows = ref(6);

// 计算属性
const displayPrompt = computed(() => {
  const prompt = props.processingDetails?.prompt_used;
  if (!prompt || prompt === '未知') {
    return '暂无提示词信息，可能模型调用失败或提示词未正确返回。';
  }
  return prompt;
});

const modelParams = computed(() => {
  // 这里可以从processingDetails中提取模型参数
  // 暂时返回一些示例参数
  if (!props.processingDetails) return null;
  
  return {
    temperature: 0.7,
    max_tokens: 2048,
    top_p: 0.9,
    frequency_penalty: 0.0
  };
});

// 方法
const toggleExpanded = () => {
  expanded.value = !expanded.value;
};

const copyPrompt = async () => {
  const prompt = props.processingDetails?.prompt_used;
  if (!prompt || prompt === '未知') {
    ElMessage.warning('暂无提示词可复制');
    return;
  }
  
  try {
    await navigator.clipboard.writeText(prompt);
    ElMessage.success('提示词已复制到剪贴板');
  } catch (error) {
    ElMessage.error('复制失败');
  }
};

const downloadPrompt = () => {
  const prompt = props.processingDetails?.prompt_used;
  if (!prompt || prompt === '未知') {
    ElMessage.warning('暂无提示词可下载');
    return;
  }
  
  const blob = new Blob([prompt], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `prompt-${Date.now()}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  ElMessage.success('提示词已下载');
};

const formatDuration = (seconds?: number): string => {
  if (!seconds) return '-';
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  return `${seconds.toFixed(2)}s`;
};

const formatTimestamp = (timestamp?: string): string => {
  if (!timestamp) return '-';
  return new Date(timestamp).toLocaleString('zh-CN');
};

const formatParamName = (key: string): string => {
  const nameMap: Record<string, string> = {
    temperature: '温度',
    max_tokens: '最大Token',
    top_p: 'Top-P',
    frequency_penalty: '频率惩罚'
  };
  return nameMap[key] || key;
};

const formatParamValue = (value: any): string => {
  if (typeof value === 'number') {
    return value.toString();
  }
  return String(value);
};
</script>

<style scoped>
.processing-details-container {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.actions {
  display: flex;
  gap: 8px;
}

.summary-view {
  padding: 12px 0;
}

.summary-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-text {
  color: #666;
  font-size: 14px;
}

.expanded-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.basic-info-section {
  margin-bottom: 16px;
}

.prompt-section,
.model-params-section,
.workflow-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.prompt-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prompt-textarea {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.prompt-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prompt-stats {
  color: #909399;
  font-size: 12px;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.param-card {
  border: 1px solid #ebeef5;
}

.param-content {
  padding: 8px;
  text-align: center;
}

.param-name {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.param-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.timeline-content h5 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.timeline-content p {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 13px;
  line-height: 1.5;
}

.model-info {
  margin-top: 8px;
}
</style>