<template>
  <div class="data-preview-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Document /></el-icon>
            数据预览
          </span>
          <div class="actions">
            <el-tooltip content="刷新数据" placement="top">
              <el-button 
                type="primary" 
                :icon="Refresh" 
                size="small"
                @click="refreshData"
                :loading="loading"
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
        <div class="file-info">
          <el-tag type="info" size="large">
            {{ fileInfo?.original_filename || '未知文件' }}
          </el-tag>
          <span class="info-text">
            {{ rawData?.total_rows || 0 }} 行 × {{ rawData?.total_columns || 0 }} 列
          </span>
        </div>
      </div>

      <div v-else class="expanded-view">
        <!-- 文件信息 -->
        <div class="file-details">
          <el-descriptions title="文件信息" :column="2" border>
            <el-descriptions-item label="文件名">
              {{ fileInfo?.original_filename || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="文件大小">
              {{ formatFileSize(fileInfo?.size) }}
            </el-descriptions-item>
            <el-descriptions-item label="文件类型">
              {{ fileInfo?.type || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="数据规模">
              {{ rawData?.total_rows || 0 }} 行 × {{ rawData?.total_columns || 0 }} 列
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 数据表格 -->
        <div class="data-table-section">
          <div class="section-header">
            <h4>数据预览 (前 {{ Math.min(displayRows, rawData?.total_rows || 0) }} 行)</h4>
            <el-button-group size="small">
              <el-button 
                :type="displayRows === 10 ? 'primary' : 'default'"
                @click="displayRows = 10"
              >
                10行
              </el-button>
              <el-button 
                :type="displayRows === 20 ? 'primary' : 'default'"
                @click="displayRows = 20"
              >
                20行
              </el-button>
              <el-button 
                :type="displayRows === 50 ? 'primary' : 'default'"
                @click="displayRows = 50"
              >
                50行
              </el-button>
            </el-button-group>
          </div>

          <div class="table-container">
            <el-table 
              :data="previewTableData" 
              border 
              stripe
              height="400"
              style="width: 100%"
              :loading="loading"
              empty-text="暂无数据"
            >
              <el-table-column 
                label="#" 
                type="index" 
                width="50" 
                fixed="left"
                :index="(index: number) => index + 1"
              />
              <el-table-column
                v-for="(column, index) in tableColumns"
                :key="index"
                :prop="column.prop"
                :label="column.label"
                :width="column.width"
                show-overflow-tooltip
              >
                <template #header>
                  <div class="column-header">
                    <span>{{ column.label }}</span>
                    <el-tag 
                      :type="getColumnTypeTag(column.type)" 
                      size="small"
                      class="column-type-tag"
                    >
                      {{ column.type }}
                    </el-tag>
                  </div>
                </template>
                <template #default="{ row }">
                  <span class="cell-content">{{ formatCellValue(row[column.prop]) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 列统计信息 -->
        <div class="column-stats-section">
          <div class="section-header">
            <h4>列统计信息</h4>
          </div>
          <div class="stats-grid">
            <el-card 
              v-for="(column, index) in tableColumns" 
              :key="index"
              class="stat-card"
              shadow="hover"
            >
              <div class="stat-content">
                <div class="stat-header">
                  <span class="column-name">{{ column.label }}</span>
                  <el-tag :type="getColumnTypeTag(column.type)" size="small">
                    {{ column.type }}
                  </el-tag>
                </div>
                <div class="stat-details">
                  <div class="stat-item" v-if="column.stats">
                    <span class="label">非空值:</span>
                    <span class="value">{{ column.stats.count || '-' }}</span>
                  </div>
                  <div class="stat-item" v-if="column.stats && column.stats.unique">
                    <span class="label">唯一值:</span>
                    <span class="value">{{ column.stats.unique }}</span>
                  </div>
                  <div class="stat-item" v-if="column.stats && column.stats.mean !== undefined">
                    <span class="label">平均值:</span>
                    <span class="value">{{ formatNumber(column.stats.mean) }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Document, Refresh, ArrowUp, ArrowDown } from '@element-plus/icons-vue';
import type { RawDataInfo, FileInfo, DataSummary } from '@/types/api';

// 定义props
interface Props {
  rawData?: RawDataInfo;
  dataSummary?: DataSummary;
  fileInfo?: FileInfo;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
});

// 定义emit事件
const emit = defineEmits<{
  refresh: []
}>();

// 响应式数据
const expanded = ref(false);
const displayRows = ref(10);

// 计算属性
const tableColumns = computed(() => {
  if (!props.dataSummary?.columns) return [];
  
  return props.dataSummary.columns.map((column, index) => ({
    prop: `col_${index}`,
    label: column,
    type: props.dataSummary?.column_types?.[column] || '未知',
    width: Math.max(120, Math.min(200, column.length * 12 + 50)),
    stats: props.dataSummary?.stats?.[column]
  }));
});

const previewTableData = computed(() => {
  if (!props.rawData?.preview_data) return [];
  
  const data = props.rawData.preview_data.slice(0, displayRows.value);
  return data.map(row => {
    const rowObj: Record<string, any> = {};
    row.forEach((cell, index) => {
      rowObj[`col_${index}`] = cell;
    });
    return rowObj;
  });
});

// 方法
const toggleExpanded = () => {
  expanded.value = !expanded.value;
};

const refreshData = () => {
  emit('refresh');
};

const formatFileSize = (bytes?: number): string => {
  if (!bytes) return '-';
  
  const sizes = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let size = bytes;
  
  while (size >= 1024 && i < sizes.length - 1) {
    size /= 1024;
    i++;
  }
  
  return `${size.toFixed(i === 0 ? 0 : 1)} ${sizes[i]}`;
};

const formatCellValue = (value: any): string => {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') return formatNumber(value);
  return String(value);
};

const formatNumber = (num: number): string => {
  if (Number.isInteger(num)) {
    return num.toLocaleString();
  }
  return num.toFixed(2);
};

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

// 监听rawData变化，自动展开
watch(() => props.rawData, (newData) => {
  if (newData && !expanded.value) {
    // 当有新数据时，可以选择自动展开
    // expanded.value = true;
  }
}, { immediate: true });
</script>

<style scoped>
.data-preview-container {
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

.file-info {
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
  gap: 20px;
}

.file-details {
  margin-bottom: 16px;
}

.data-table-section {
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
}

.table-container {
  border-radius: 6px;
  overflow: hidden;
}

.column-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
}

.column-type-tag {
  font-size: 10px !important;
  height: 16px !important;
  line-height: 14px !important;
}

.cell-content {
  color: #303133;
}

.column-stats-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.stat-card {
  border: 1px solid #ebeef5;
}

.stat-content {
  padding: 8px;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.column-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.stat-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.stat-item .label {
  color: #909399;
}

.stat-item .value {
  color: #303133;
  font-weight: 500;
}
</style>