<template>
  <div class="json-tree-node" :style="{ paddingLeft: `${level * 20}px` }">
    <div class="node-content" @click="toggleExpanded">
      <div class="node-header">
        <el-icon v-if="hasChildren" class="expand-icon" :class="{ expanded: isExpanded }">
          <ArrowRight />
        </el-icon>
        <span v-else class="leaf-icon">•</span>
        
        <span class="node-key">{{ displayKey }}</span>
        <span class="node-type">{{ nodeType }}</span>
        
        <span v-if="!hasChildren" class="node-value">{{ displayValue }}</span>
        <span v-else class="node-summary">{{ nodeSummary }}</span>
      </div>
    </div>
    
    <div v-if="hasChildren && isExpanded" class="node-children">
      <JsonTreeNode
        v-for="(value, key) in childData"
        :key="key"
        :data="value"
        :level="level + 1"
        :expanded="false"
        :root-key="String(key)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ArrowRight } from '@element-plus/icons-vue';

interface Props {
  data: any;
  level: number;
  expanded?: boolean;
  rootKey?: string;
}

const props = withDefaults(defineProps<Props>(), {
  expanded: false,
  rootKey: ''
});

const isExpanded = ref(props.expanded);

const displayKey = computed(() => {
  return props.rootKey || 'root';
});

const nodeType = computed(() => {
  const data = props.data;
  
  if (data === null) return 'null';
  if (data === undefined) return 'undefined';
  if (Array.isArray(data)) return `array[${data.length}]`;
  if (typeof data === 'object') return `object{${Object.keys(data).length}}`;
  if (typeof data === 'string') return 'string';
  if (typeof data === 'number') return 'number';
  if (typeof data === 'boolean') return 'boolean';
  
  return typeof data;
});

const hasChildren = computed(() => {
  const data = props.data;
  return (Array.isArray(data) && data.length > 0) || 
         (typeof data === 'object' && data !== null && Object.keys(data).length > 0);
});

const childData = computed(() => {
  if (!hasChildren.value) return {};
  return props.data;
});

const displayValue = computed(() => {
  const data = props.data;
  
  if (data === null) return 'null';
  if (data === undefined) return 'undefined';
  if (typeof data === 'string') {
    // 截断长字符串
    return data.length > 100 ? `"${data.substring(0, 100)}..."` : `"${data}"`;
  }
  if (typeof data === 'number' || typeof data === 'boolean') {
    return String(data);
  }
  
  return '';
});

const nodeSummary = computed(() => {
  const data = props.data;
  
  if (Array.isArray(data)) {
    return `${data.length} items`;
  }
  
  if (typeof data === 'object' && data !== null) {
    const keys = Object.keys(data);
    return `${keys.length} properties`;
  }
  
  return '';
});

const toggleExpanded = () => {
  if (hasChildren.value) {
    isExpanded.value = !isExpanded.value;
  }
};
</script>

<style scoped>
.json-tree-node {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
}

.node-content {
  cursor: pointer;
  user-select: none;
}

.node-content:hover {
  background-color: #f0f9ff;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 4px;
  border-radius: 3px;
}

.expand-icon {
  transition: transform 0.2s ease;
  color: #909399;
  font-size: 12px;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.leaf-icon {
  color: #c0c4cc;
  font-size: 8px;
  width: 12px;
  text-align: center;
}

.node-key {
  color: #e91e63;
  font-weight: 600;
}

.node-type {
  color: #9c27b0;
  font-size: 10px;
  background: #f3e5f5;
  padding: 1px 4px;
  border-radius: 2px;
  margin-left: 4px;
}

.node-value {
  color: #2196f3;
  margin-left: 8px;
}

.node-summary {
  color: #666;
  font-style: italic;
  margin-left: 8px;
}

.node-children {
  margin-top: 2px;
}
</style>