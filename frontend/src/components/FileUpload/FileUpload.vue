<template>
  <div class="file-upload-container">
    <div class="upload-area">
      <el-upload
        ref="uploadRef"
        class="upload-dragger"
        drag
        :show-file-list="false"
        :before-upload="handleBeforeUpload"
        :http-request="handleCustomUpload"
        :accept="acceptTypes"
        :disabled="uploading"
      >
        <div class="upload-content">
          <div v-if="!uploading" class="upload-icon">
            <el-icon><UploadFilled /></el-icon>
          </div>
          <div v-else class="upload-progress">
            <el-progress 
              type="circle" 
              :percentage="uploadProgress"
              :width="100"
              stroke-width="8"
              :stroke-linecap="'round'"
              :color="progressColor"
            >
              <template #default="{ percentage }">
                <span class="progress-text">
                  <div class="progress-percentage">{{ Math.round(percentage) }}%</div>
                  <div class="progress-status">{{ uploadingText }}</div>
                </span>
              </template>
            </el-progress>
          </div>
          
          <div class="upload-text">
            <p v-if="!uploading" class="upload-title">
              点击或拖拽文件到此区域上传
            </p>
            <p v-else class="upload-title">
              {{ uploadingText }}
            </p>
            
            <p class="upload-hint">
              支持 .xlsx、.xls、.csv 格式文件，大小不超过 {{ maxSizeMB }}MB
            </p>
          </div>
        </div>
      </el-upload>
    </div>
    
    <!-- 文件信息显示 -->
    <div v-if="selectedFile" class="file-info">
      <el-card shadow="never">
        <div class="file-details">
          <div class="file-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="file-meta">
            <h4 class="file-name">{{ selectedFile.name }}</h4>
            <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
          </div>
          <div class="file-actions">
            <el-button 
              v-if="!uploading"
              type="danger" 
              text 
              @click="clearFile"
              :icon="Delete"
            >
              移除
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 高级选项 -->
    <div v-if="showAdvancedOptions" class="advanced-options">
      <el-card shadow="never">
        <template #header>
          <span>高级选项</span>
        </template>
        
        <el-form label-width="80px">
          <el-form-item label="AI模型">
            <el-select 
              v-model="selectedModel" 
              placeholder="选择AI模型（可选）"
              clearable
              style="width: 100%"
            >
              <el-option
                v-for="model in availableModels"
                :key="model.type"
                :label="model.name"
                :value="model.type"
              >
                <span>{{ model.name }}</span>
                <span style="float: right; color: #8492a6; font-size: 12px">
                  {{ model.provider }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 操作按钮 -->
    <div class="upload-actions">
      <el-button 
        v-if="!showAdvancedOptions"
        type="primary" 
        text 
        @click="showAdvancedOptions = true"
      >
        显示高级选项
      </el-button>
      <el-button 
        v-else
        type="primary" 
        text 
        @click="showAdvancedOptions = false"
      >
        隐藏高级选项
      </el-button>
      
      <el-button
        type="primary"
        :disabled="!selectedFile || uploading"
        :loading="uploading"
        @click="startUpload"
      >
        {{ uploading ? '生成中...' : '开始分析' }}
      </el-button>
    </div>
    
    <!-- 认证弹窗 -->
    <el-dialog
      v-model="showAuthDialog"
      title="输入访问口令"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="true"
    >
      <el-form 
        ref="authFormRef"
        :model="authForm"
        :rules="authRules"
        label-width="0px"
      >
        <el-form-item prop="password">
          <el-input
            v-model="authForm.password"
            type="password"
            placeholder="请输入访问口令"
            show-password
            size="large"
            @keyup.enter="confirmAuth"
            autofocus
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelAuth">取消</el-button>
          <el-button 
            type="primary" 
            :loading="authLoading"
            @click="confirmAuth"
          >
            确认
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox, type UploadInstance, type UploadRequestOptions, type FormInstance } from 'element-plus';
import { UploadFilled, Document, Delete, Lock } from '@element-plus/icons-vue';
import { apiService } from '@/services/api';
import { authService } from '@/services/auth';
import type { FileUploadResponse, ModelInfo } from '@/types/api';

// 定义props
interface Props {
  maxSizeMB?: number;
  acceptTypes?: string;
  requireAuth?: boolean;  // 新增：是否需要认证
}

const props = withDefaults(defineProps<Props>(), {
  maxSizeMB: 5,
  acceptTypes: '.xlsx,.xls,.csv',
  requireAuth: false
});

// 定义emit事件
const emit = defineEmits<{
  uploadSuccess: [result: FileUploadResponse]
  uploadError: [error: string]
}>();

// 响应式数据
const uploadRef = ref<UploadInstance>();
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const uploadProgress = ref(0);
const uploadingText = ref('准备上传...');
const showAdvancedOptions = ref(false);
const selectedModel = ref<string>('');
const availableModels = ref<ModelInfo[]>([]);

// 认证相关的响应式数据
const showAuthDialog = ref(false);
const authLoading = ref(false);
const authFormRef = ref<FormInstance>();
const authForm = reactive({
  password: ''
});

// 认证表单验证规则
const authRules = {
  password: [
    { required: true, message: '请输入访问口令', trigger: 'blur' }
  ]
};

// 计算属性 - 进度条颜色
const progressColor = computed(() => {
  const progress = uploadProgress.value;
  if (progress < 30) {
    return '#67c23a'; // 绿色 - 开始阶段
  } else if (progress < 70) {
    return '#409eff'; // 蓝色 - 中间阶段
  } else if (progress < 100) {
    return '#e6a23c'; // 橙色 - 接近完成
  } else {
    return '#67c23a'; // 绿色 - 完成
  }
});

// 文件验证
const handleBeforeUpload = (file: File): boolean => {
  // 检查文件大小
  const maxSize = props.maxSizeMB * 1024 * 1024;
  if (file.size > maxSize) {
    ElMessage.error(`文件大小不能超过 ${props.maxSizeMB}MB`);
    return false;
  }
  
  // 检查文件类型
  const allowedTypes = props.acceptTypes.split(',').map(type => type.trim());
  const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
  
  if (!allowedTypes.includes(fileExt)) {
    ElMessage.error(`不支持的文件格式，请上传 ${props.acceptTypes} 格式的文件`);
    return false;
  }
  
  selectedFile.value = file;
  return false; // 阻止默认上传，使用自定义上传
};

// 自定义上传处理
const handleCustomUpload = (options: UploadRequestOptions): void => {
  // 这里不直接上传，而是存储文件，等待用户点击"开始分析"
  selectedFile.value = options.file;
};

// 开始上传
const startUpload = async (): Promise<void> => {
  if (!selectedFile.value) {
    ElMessage.error('请先选择文件');
    return;
  }
  
  await performUpload();
};

// 执行上传操作
const performUpload = async (): Promise<void> => {
  if (!selectedFile.value) {
    ElMessage.error('请先选择文件');
    return;
  }
  
  uploading.value = true;
  uploadProgress.value = 0;
  uploadingText.value = '正在上传文件...';
  
  try {
    // 模拟进度更新
    uploadProgress.value = 10;
    uploadingText.value = '正在解析文件...';
    
    // 调用同步上传API
    const uploadResult = await apiService.uploadFile(selectedFile.value, selectedModel.value || undefined);
    
    // 上传成功
    uploadProgress.value = 100;
    uploadingText.value = '图表生成完成！';
    
    // 延迟一下让用户看到完成状态
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 发送成功事件
    emit('uploadSuccess', uploadResult);
    
    // 重置状态
    uploading.value = false;
    uploadProgress.value = 0;
    uploadingText.value = '';
    selectedFile.value = null;
    
    ElMessage.success('图表生成成功！');
    
  } catch (error: any) {
    uploadProgress.value = 0;
    const errorMessage = error.message || '文件上传失败';
    ElMessage.error(errorMessage);
    emit('uploadError', errorMessage);
    uploading.value = false;
    uploadingText.value = '';
  }
};

// 清除文件
const clearFile = (): void => {
  selectedFile.value = null;
  uploadProgress.value = 0;
  uploadRef.value?.clearFiles();
};

// 认证相关方法
// 确认认证
const confirmAuth = async (): Promise<void> => {
  if (!authFormRef.value) return;
  
  const valid = await authFormRef.value.validate().catch(() => false);
  if (!valid) return;
  
  authLoading.value = true;
  
  try {
    await authService.login(authForm.password);
    showAuthDialog.value = false;
    authForm.password = ''; // 清空密码
    ElMessage.success('认证成功！');
    
    // 认证成功后开始上传
    await performUpload();
    
  } catch (error: any) {
    ElMessage.error(error.message || '认证失败');
  } finally {
    authLoading.value = false;
  }
};

// 取消认证
const cancelAuth = (): void => {
  showAuthDialog.value = false;
  authForm.password = '';
  authLoading.value = false;
};

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 加载可用模型
const loadAvailableModels = async (): Promise<void> => {
  try {
    availableModels.value = await apiService.getAvailableModels();
  } catch (error) {
    console.warn('Failed to load available models:', error);
    // 不显示错误，因为这是可选功能
  }
};

// 组件挂载时加载模型列表
onMounted(() => {
  loadAvailableModels();
});
</script>

<style scoped>
.file-upload-container {
  max-width: 600px;
  margin: 0 auto;
}

.upload-area {
  margin-bottom: 20px;
}

:deep(.upload-dragger) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  border-radius: 12px;
  border: 2px dashed #d9d9d9;
  background-color: #fafafa;
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background-color: #f0f9ff;
}

:deep(.el-upload-dragger.is-dragover) {
  border-color: #409eff;
  background-color: #e6f7ff;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-progress {
  margin-bottom: 16px;
}

.progress-text {
  text-align: center;
  font-size: 14px;
}

.progress-percentage {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.progress-status {
  font-size: 12px;
  color: #666;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 进度条动画优化 */
:deep(.el-progress-circle__path) {
  transition: stroke-dasharray 0.3s ease;
}

:deep(.el-progress__text) {
  color: #333 !important;
  font-size: 14px !important;
}

.upload-text {
  text-align: center;
}

.upload-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #333;
  font-weight: 500;
}

.upload-hint {
  margin: 0;
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

.file-info {
  margin-bottom: 20px;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 24px;
  color: #409eff;
}

.file-meta {
  flex: 1;
}

.file-name {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.file-size {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.advanced-options {
  margin-bottom: 20px;
}

.upload-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

/* 认证弹窗样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog__header) {
  padding: 20px 20px 10px 20px;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  padding: 10px 20px 20px 20px;
  border-top: 1px solid #ebeef5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .file-upload-container {
    margin: 0 16px;
  }
  
  :deep(.el-upload-dragger) {
    height: 160px;
  }
  
  .upload-icon {
    font-size: 36px;
  }
  
  .upload-title {
    font-size: 14px;
  }
  
  .upload-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>