<template>
  <div class="cleanup-status-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Timer /></el-icon>
            文件清理服务
          </span>
          <div class="actions">
            <el-button 
              type="primary" 
              size="small" 
              :icon="Refresh"
              @click="refreshStatus"
              :loading="loading"
            >
              刷新状态
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              :icon="Delete"
              @click="forceCleanup"
              :loading="cleanupLoading"
            >
              立即清理
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="status" class="status-content">
        <!-- 服务状态 -->
        <div class="service-status">
          <el-descriptions title="服务状态" :column="2" border>
            <el-descriptions-item label="运行状态">
              <el-tag :type="status.running ? 'success' : 'danger'">
                {{ status.running ? '运行中' : '已停止' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="清理间隔">
              {{ status.cleanup_interval_minutes.toFixed(1) }} 分钟
            </el-descriptions-item>
            <el-descriptions-item label="工作线程">
              <el-tag :type="status.thread_alive ? 'success' : 'warning'">
                {{ status.thread_alive ? '活跃' : '非活跃' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="临时目录">
              {{ status.file_stats?.temp_dir || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 文件统计 -->
        <div class="file-stats">
          <h4>文件统计</h4>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-statistic 
                title="活跃会话数" 
                :value="status.file_stats?.active_sessions || 0"
                :value-style="{ color: '#3f6600' }"
              >
                <template #suffix>
                  <el-icon><FolderOpened /></el-icon>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="12">
              <el-statistic 
                title="图表文件数" 
                :value="status.file_stats?.total_chart_files || 0"
                :value-style="{ color: '#cf1322' }"
              >
                <template #suffix>
                  <el-icon><Document /></el-icon>
                </template>
              </el-statistic>
            </el-col>
          </el-row>
        </div>

        <!-- 清理配置 -->
        <div v-if="config" class="cleanup-config">
          <h4>清理配置</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="自动清理">
              {{ config.auto_cleanup_enabled ? '已启用' : '已禁用' }}
            </el-descriptions-item>
            <el-descriptions-item label="清理间隔">
              {{ config.cleanup_interval_minutes.toFixed(1) }} 分钟 
              ({{ config.cleanup_interval_seconds }} 秒)
            </el-descriptions-item>
            <el-descriptions-item label="存储目录">
              {{ config.temp_directory }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 最近清理结果 -->
        <div v-if="lastCleanupResult" class="last-cleanup">
          <h4>最近清理结果</h4>
          <el-alert
            :title="`清理完成：删除了 ${lastCleanupResult.sessions_cleaned} 个会话和 ${lastCleanupResult.charts_cleaned} 个图表文件`"
            type="success"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>清理前：{{ lastCleanupResult.stats_before.active_sessions }} 个会话，{{ lastCleanupResult.stats_before.total_chart_files }} 个图表文件</p>
              <p>清理后：{{ lastCleanupResult.stats_after.active_sessions }} 个会话，{{ lastCleanupResult.stats_after.total_chart_files }} 个图表文件</p>
            </template>
          </el-alert>
        </div>
      </div>

      <div v-else class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  Timer, 
  Refresh, 
  Delete, 
  FolderOpened, 
  Document 
} from '@element-plus/icons-vue';
import { apiService } from '@/services/api';

// 响应式数据
const loading = ref(false);
const cleanupLoading = ref(false);
const status = ref<any>(null);
const config = ref<any>(null);
const lastCleanupResult = ref<any>(null);

// 定时刷新
let refreshTimer: number | null = null;

// 刷新状态
const refreshStatus = async (): Promise<void> => {
  if (loading.value) return;
  
  loading.value = true;
  try {
    // 获取状态和配置
    const [statusRes, configRes] = await Promise.all([
      apiService.getCleanupStatus(),
      apiService.getCleanupConfig()
    ]);
    
    status.value = statusRes;
    config.value = configRes;
    
  } catch (error: any) {
    ElMessage.error(error.message || '获取清理状态失败');
  } finally {
    loading.value = false;
  }
};

// 强制清理
const forceCleanup = async (): Promise<void> => {
  if (cleanupLoading.value) return;
  
  try {
    await ElMessageBox.confirm(
      '确定要立即执行文件清理吗？这将删除所有超过5分钟的临时文件。',
      '确认清理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    cleanupLoading.value = true;
    
    const result = await apiService.forceCleanup();
    lastCleanupResult.value = result;
    
    ElMessage.success(result.message || '手动清理完成');
    
    // 刷新状态
    await refreshStatus();
    
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '手动清理失败');
    }
  } finally {
    cleanupLoading.value = false;
  }
};

// 开始定时刷新
const startAutoRefresh = (): void => {
  if (refreshTimer) return;
  
  refreshTimer = window.setInterval(() => {
    refreshStatus();
  }, 30000); // 每30秒刷新一次
};

// 停止定时刷新
const stopAutoRefresh = (): void => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
};

// 组件挂载
onMounted(async () => {
  await refreshStatus();
  startAutoRefresh();
});

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh();
});
</script>

<style scoped>
.cleanup-status-container {
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

.status-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.service-status,
.file-stats,
.cleanup-config,
.last-cleanup {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-stats h4,
.cleanup-config h4,
.last-cleanup h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.loading-state {
  padding: 20px;
}

/* 统计数字样式 */
:deep(.el-statistic) {
  text-align: center;
}

:deep(.el-statistic__head) {
  font-size: 14px;
  color: #666;
}

:deep(.el-statistic__content) {
  font-size: 24px;
  font-weight: bold;
}

/* 描述列表样式 */
:deep(.el-descriptions__label) {
  font-weight: 600;
}

/* 警告框样式 */
:deep(.el-alert__content) {
  line-height: 1.6;
}

:deep(.el-alert__description p) {
  margin: 4px 0;
  font-size: 13px;
  color: #666;
}
</style>