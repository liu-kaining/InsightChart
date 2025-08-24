<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">InsightChart AI</h1>
        <p class="auth-subtitle">智能图表生成器</p>
      </div>
      
      <div class="auth-form">
        <el-form 
          @submit.prevent="handleLogin"
          :model="form" 
          :rules="rules" 
          ref="formRef"
          size="large"
        >
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入访问口令"
              show-password
              :disabled="loading"
              @keyup.enter="handleLogin"
              clearable
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              style="width: 100%"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '验证中...' : '进入系统' }}
            </el-button>
          </el-form-item>
        </el-form>
        
        <div v-if="error" class="auth-error">
          <el-alert 
            :title="error" 
            type="error" 
            show-icon 
            :closable="false"
          />
        </div>
      </div>
      
      <div class="auth-footer">
        <p class="auth-description">
          请输入访问口令以使用智能图表生成功能
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElLoading, type FormInstance, type FormRules } from 'element-plus';
import { Lock } from '@element-plus/icons-vue';
import { authService } from '@/services/auth';

// 定义emit事件
const emit = defineEmits<{
  authenticated: []
}>();

// 响应式数据
const formRef = ref<FormInstance>();
const loading = ref(false);
const error = ref('');

const form = reactive({
  password: ''
});

// 表单验证规则
const rules: FormRules = {
  password: [
    { required: true, message: '请输入访问口令', trigger: 'blur' },
    { min: 1, message: '口令不能为空', trigger: 'blur' }
  ]
};

// 处理登录
const handleLogin = async (): Promise<void> => {
  if (!formRef.value) return;
  
  try {
    // 验证表单
    const valid = await formRef.value.validate();
    if (!valid) return;
    
    loading.value = true;
    error.value = '';
    
    // 调用登录API
    await authService.login(form.password);
    
    ElMessage.success('认证成功！');
    
    // 触发认证成功事件
    emit('authenticated');
    
  } catch (err: any) {
    error.value = err.message || '认证失败，请检查口令是否正确';
    
    // 清空密码输入框
    form.password = '';
    
    // 聚焦到密码输入框
    setTimeout(() => {
      const passwordInput = document.querySelector('input[type="password"]') as HTMLInputElement;
      if (passwordInput) {
        passwordInput.focus();
      }
    }, 100);
    
  } finally {
    loading.value = false;
  }
};

// 检查是否已经认证
const checkExistingAuth = async (): Promise<void> => {
  if (authService.isAuthenticated()) {
    const isValid = await authService.verifyToken();
    if (isValid) {
      emit('authenticated');
    }
  }
};

// 组件挂载时检查认证状态
onMounted(() => {
  checkExistingAuth();
});
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.auth-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-title {
  font-size: 28px;
  font-weight: bold;
  color: #2c3e50;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.auth-subtitle {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0;
}

.auth-form {
  margin-bottom: 24px;
}

.auth-error {
  margin-top: 16px;
}

.auth-footer {
  text-align: center;
}

.auth-description {
  font-size: 12px;
  color: #95a5a6;
  margin: 0;
  line-height: 1.5;
}

:deep(.el-input__inner) {
  border-radius: 8px;
  height: 48px;
  font-size: 16px;
}

:deep(.el-button) {
  border-radius: 8px;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-alert) {
  border-radius: 8px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .auth-container {
    padding: 16px;
  }
  
  .auth-card {
    padding: 24px;
  }
  
  .auth-title {
    font-size: 24px;
  }
}
</style>