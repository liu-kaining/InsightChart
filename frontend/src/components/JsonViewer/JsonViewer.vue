<template>
  <div class="json-viewer-container">
    <el-dialog
      :model-value="visible"
      :title="dialogTitle"
      width="80%"
      :destroy-on-close="true"
      @update:model-value="(value: boolean) => emit('update:visible', value)"
      @close="handleClose"
      class="json-dialog"
    >
      <div class="json-viewer-content">
        <!-- 工具栏 -->
        <div class="toolbar">
          <div class="toolbar-left">
            <el-select 
              v-model="selectedChartId" 
              placeholder="选择图表"
              @change="onChartChange"
              style="width: 200px"
            >
              <el-option
                v-for="chart in charts"
                :key="chart.id"
                :label="chart.title"
                :value="chart.id"
              />
            </el-select>
            <el-divider direction="vertical" />
            <el-button-group size="small">
              <el-button 
                :type="viewMode === 'formatted' ? 'primary' : 'default'"
                @click="viewMode = 'formatted'"
              >
                格式化
              </el-button>
              <el-button 
                :type="viewMode === 'compact' ? 'primary' : 'default'"
                @click="viewMode = 'compact'"
              >
                紧凑
              </el-button>
              <el-button 
                :type="viewMode === 'tree' ? 'primary' : 'default'"
                @click="viewMode = 'tree'"
              >
                树形
              </el-button>
            </el-button-group>
          </div>
          
          <div class="toolbar-right">
            <el-tooltip content="复制JSON" placement="top">
              <el-button 
                type="primary" 
                :icon="CopyDocument" 
                size="small"
                @click="copyJson"
                :disabled="!currentChartConfig"
              />
            </el-tooltip>
            <el-tooltip content="下载JSON" placement="top">
              <el-button 
                type="default" 
                :icon="Download" 
                size="small"
                @click="downloadJson"
                :disabled="!currentChartConfig"
              />
            </el-tooltip>
            <el-tooltip content="验证配置" placement="top">
              <el-button 
                type="success" 
                :icon="Check" 
                size="small"
                @click="validateConfig"
                :disabled="!currentChartConfig"
              />
            </el-tooltip>
          </div>
        </div>

        <!-- JSON内容区域 -->
        <div class="json-content">
          <!-- 格式化视图 -->
          <div v-if="viewMode === 'formatted'" class="formatted-view">
            <div class="json-header">
              <h4>ECharts 配置 (格式化)</h4>
              <div class="json-stats">
                <el-tag size="small">{{ formatStats.lines }} 行</el-tag>
                <el-tag size="small" type="info">{{ formatStats.size }} 字符</el-tag>
                <el-tag size="small" type="warning">{{ formatStats.keys }} 个键</el-tag>
              </div>
            </div>
            <el-input
              v-model="formattedJson"
              type="textarea"
              :rows="20"
              readonly
              placeholder="请选择图表查看配置"
              class="json-textarea"
            />
          </div>

          <!-- 紧凑视图 -->
          <div v-else-if="viewMode === 'compact'" class="compact-view">
            <div class="json-header">
              <h4>ECharts 配置 (紧凑)</h4>
              <div class="json-stats">
                <el-tag size="small" type="info">{{ compactStats.size }} 字符</el-tag>
              </div>
            </div>
            <el-input
              v-model="compactJson"
              type="textarea"
              :rows="15"
              readonly
              placeholder="请选择图表查看配置"
              class="json-textarea"
            />
          </div>

          <!-- 树形视图 -->
          <div v-else-if="viewMode === 'tree'" class="tree-view">
            <div class="json-header">
              <h4>ECharts 配置 (树形结构)</h4>
              <div class="tree-controls">
                <el-button size="small" @click="expandAll">全部展开</el-button>
                <el-button size="small" @click="collapseAll">全部收起</el-button>
              </div>
            </div>
            <div class="tree-container">
              <JsonTreeNode
                v-if="currentChartConfig"
                :data="currentChartConfig.option"
                :level="0"
                :expanded="true"
                root-key="option"
              />
              <div v-else class="empty-tree">
                请选择图表查看配置
              </div>
            </div>
          </div>
        </div>

        <!-- 图表信息 -->
        <div v-if="currentChart" class="chart-info-section">
          <el-divider content-position="left">图表信息</el-divider>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="图表标题">
              {{ currentChart.title }}
            </el-descriptions-item>
            <el-descriptions-item label="图表类型">
              <el-tag>{{ currentChart.type }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="图表ID">
              <code>{{ currentChart.id }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="描述">
              {{ currentChart.description || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="数据来源" v-if="currentChart.metadata?.data_source">
              <el-tag 
                v-for="source in currentChart.metadata.data_source" 
                :key="source"
                size="small"
                class="source-tag"
              >
                {{ source }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="生成理由" v-if="currentChart.metadata?.chart_reasoning">
              {{ currentChart.metadata.chart_reasoning }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">关闭</el-button>
          <el-button 
            type="primary" 
            @click="copyJson"
            :disabled="!currentChartConfig"
          >
            复制配置
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { CopyDocument, Download, Check } from '@element-plus/icons-vue';
import type { ChartConfig } from '@/types/api';
import JsonTreeNode from './JsonTreeNode.vue';

// 定义props
interface Props {
  visible: boolean;
  charts: ChartConfig[];
  defaultChartId?: string;
}

const props = withDefaults(defineProps<Props>(), {
  charts: () => []
});

// 定义emit事件
const emit = defineEmits<{
  'update:visible': [value: boolean]
  close: []
}>();

// 响应式数据
const selectedChartId = ref<string>('');
const viewMode = ref<'formatted' | 'compact' | 'tree'>('formatted');

// 计算属性
const dialogTitle = computed(() => {
  return currentChart.value ? `JSON配置 - ${currentChart.value.title}` : 'JSON配置查看器';
});

const currentChart = computed(() => {
  return props.charts.find(chart => chart.id === selectedChartId.value);
});

const currentChartConfig = computed(() => {
  return currentChart.value;
});

const formattedJson = computed(() => {
  if (!currentChartConfig.value?.option) return '';
  try {
    return JSON.stringify(currentChartConfig.value.option, null, 2);
  } catch (error) {
    return '配置解析失败';
  }
});

const compactJson = computed(() => {
  if (!currentChartConfig.value?.option) return '';
  try {
    return JSON.stringify(currentChartConfig.value.option);
  } catch (error) {
    return '配置解析失败';
  }
});

const formatStats = computed(() => {
  const json = formattedJson.value;
  const lines = json.split('\n').length;
  const size = json.length;
  const keys = (json.match(/"\w+"\s*:/g) || []).length;
  
  return { lines, size, keys };
});

const compactStats = computed(() => {
  const json = compactJson.value;
  const size = json.length;
  
  return { size };
});

// 方法
const handleClose = () => {
  emit('update:visible', false);
  emit('close');
};

const onChartChange = () => {
  // 图表切换时的逻辑
};

const copyJson = async () => {
  if (!currentChartConfig.value?.option) {
    ElMessage.warning('暂无配置可复制');
    return;
  }
  
  try {
    const jsonText = viewMode.value === 'compact' ? compactJson.value : formattedJson.value;
    await navigator.clipboard.writeText(jsonText);
    ElMessage.success('JSON配置已复制到剪贴板');
  } catch (error) {
    ElMessage.error('复制失败');
  }
};

const downloadJson = () => {
  if (!currentChartConfig.value?.option) {
    ElMessage.warning('暂无配置可下载');
    return;
  }
  
  try {
    const jsonText = formattedJson.value;
    const blob = new Blob([jsonText], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentChart.value?.title || 'chart'}-config.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    ElMessage.success('JSON配置已下载');
  } catch (error) {
    ElMessage.error('下载失败');
  }
};

const validateConfig = () => {
  if (!currentChartConfig.value?.option) {
    ElMessage.warning('暂无配置可验证');
    return;
  }
  
  try {
    // 基本的ECharts配置验证
    const config = currentChartConfig.value.option;
    const warnings: string[] = [];
    
    // 检查必要字段
    if (!config.series) {
      warnings.push('缺少 series 配置');
    }
    
    if (!config.xAxis && !config.yAxis && !config.polar && !config.geo) {
      warnings.push('缺少坐标系配置 (xAxis/yAxis/polar/geo)');
    }
    
    if (warnings.length > 0) {
      ElMessage.warning(`配置验证警告: ${warnings.join(', ')}`);
    } else {
      ElMessage.success('配置验证通过');
    }
  } catch (error) {
    ElMessage.error('配置验证失败');
  }
};

const expandAll = () => {
  // 树形视图全部展开的逻辑
  ElMessage.info('功能开发中');
};

const collapseAll = () => {
  // 树形视图全部收起的逻辑
  ElMessage.info('功能开发中');
};

// 监听props变化
watch(() => props.visible, (newVisible) => {
  if (newVisible && props.charts.length > 0) {
    // 选择默认图表或第一个图表
    selectedChartId.value = props.defaultChartId || props.charts[0].id;
  }
});

watch(() => props.defaultChartId, (newId) => {
  if (newId) {
    selectedChartId.value = newId;
  }
});
</script>

<style scoped>
.json-dialog :deep(.el-dialog__body) {
  padding: 20px;
  max-height: 80vh;
  overflow-y: auto;
}

.json-viewer-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.json-content {
  flex: 1;
}

.json-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.json-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.json-stats,
.tree-controls {
  display: flex;
  gap: 8px;
}

.json-textarea {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
}

.tree-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  background: #fafafa;
  max-height: 500px;
  overflow-y: auto;
}

.empty-tree {
  text-align: center;
  color: #909399;
  padding: 40px;
}

.chart-info-section {
  margin-top: 16px;
}

.source-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

.dialog-footer {
  text-align: right;
}
</style>