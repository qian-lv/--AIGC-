// 导航栈管理模块
class NavigationStack {
  constructor() {
    // 初始化导航栈
    this.stack = [];
    // 从localStorage恢复栈状态
    this.restoreFromStorage();
    console.log('导航栈初始化:', this.stack);
  }

  // 压入新页面
  push(url) {
    // 避免重复压入相同的页面
    if (this.stack.length > 0 && this.stack[this.stack.length - 1] === url) {
      console.log('页面已在栈顶，无需重复压入:', url);
      return;
    }
    // 限制栈的最大长度为10
    if (this.stack.length >= 10) {
      this.stack.shift(); // 移除最早的页面
    }
    this.stack.push(url);
    // 存储到localStorage以持久化
    localStorage.setItem('navigationStack', JSON.stringify(this.stack));
    console.log('压入页面:', url, '当前栈:', this.stack);
  }

  // 弹出页面（返回）
  pop() {
    if (this.stack.length > 1) {
      // 弹出当前页面
      this.stack.pop();
      // 获取新的栈顶页面
      const previousUrl = this.stack[this.stack.length - 1];
      // 存储到localStorage
      localStorage.setItem('navigationStack', JSON.stringify(this.stack));
      console.log('弹出页面，返回:', previousUrl, '当前栈:', this.stack);
      return previousUrl;
    }
    console.log('栈为空或只有一个页面，无法返回');
    return null; // 栈为空或只有一个页面
  }

  // 获取当前栈
  getStack() {
    return this.stack;
  }

  // 从localStorage恢复栈
  restoreFromStorage() {
    const storedStack = localStorage.getItem('navigationStack');
    if (storedStack) {
      try {
        this.stack = JSON.parse(storedStack);
        console.log('从localStorage恢复导航栈:', this.stack);
      } catch (error) {
        console.error('恢复导航栈失败:', error);
        this.stack = [];
      }
    }
  }
  
  // 清空导航栈
  clear() {
    this.stack = [];
    localStorage.removeItem('navigationStack');
    console.log('导航栈已清空');
  }
}

// 创建单例实例
const navigationStack = new NavigationStack();

// 导出实例
if (typeof module !== 'undefined' && module.exports) {
  module.exports = navigationStack;
} else if (typeof window !== 'undefined') {
  // 确保window.navigationStack是一个NavigationStack实例
  window.navigationStack = navigationStack;
  // 确保clear方法存在
  if (!window.navigationStack.clear) {
    window.navigationStack.clear = function() {
      this.stack = [];
      localStorage.removeItem('navigationStack');
      console.log('导航栈已清空');
    };
  }
  // 确保push方法存在
  if (!window.navigationStack.push) {
    window.navigationStack.push = function(url) {
      if (this.stack.length > 0 && this.stack[this.stack.length - 1] === url) {
        console.log('页面已在栈顶，无需重复压入:', url);
        return;
      }
      if (this.stack.length >= 10) {
        this.stack.shift();
      }
      this.stack.push(url);
      localStorage.setItem('navigationStack', JSON.stringify(this.stack));
      console.log('压入页面:', url, '当前栈:', this.stack);
    };
  }
  // 确保pop方法存在
  if (!window.navigationStack.pop) {
    window.navigationStack.pop = function() {
      if (this.stack.length > 1) {
        this.stack.pop();
        const previousUrl = this.stack[this.stack.length - 1];
        localStorage.setItem('navigationStack', JSON.stringify(this.stack));
        console.log('弹出页面，返回:', previousUrl, '当前栈:', this.stack);
        return previousUrl;
      }
      console.log('栈为空或只有一个页面，无法返回');
      return null;
    };
  }
  // 确保getStack方法存在
  if (!window.navigationStack.getStack) {
    window.navigationStack.getStack = function() {
      return this.stack;
    };
  }
}