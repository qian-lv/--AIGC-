/**
 * 触摸手势处理模块
 * 提供移动端触摸体验优化功能
 */

class TouchGestureHandler {
    constructor() {
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.swipeThreshold = 50; // 滑动阈值
        this.longPressTimer = null;
        this.longPressDelay = 500; // 长按延迟（毫秒）
        this.isSwipeGesture = false;
        this.currentTouchTarget = null;
        
        this.init();
    }
    
    init() {
        // 为所有可点击元素添加触摸事件监听
        this.addTouchListeners();
        
        // 监听整个文档的触摸事件
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        
        console.log('触摸手势处理器已初始化');
    }
    
    handleTouchStart(e) {
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
        this.isSwipeGesture = false;
        this.currentTouchTarget = e.target;
        
        // 开始长按计时器
        if (this.currentTouchTarget && this.isClickable(this.currentTouchTarget)) {
            this.startLongPressTimer(e.touches[0]);
        }
    }
    
    handleTouchMove(e) {
        this.touchEndX = e.touches[0].clientX;
        this.touchEndY = e.touches[0].clientY;
        
        // 计算滑动距离
        const deltaX = this.touchEndX - this.touchStartX;
        const deltaY = this.touchEndY - this.touchStartY;
        
        // 如果移动距离超过阈值，判定为滑动
        if (Math.abs(deltaX) > 10 || Math.abs(deltaY) > 10) {
            this.isSwipeGesture = true;
            this.cancelLongPress();
        }
        
        // 如果是水平滑动，阻止默认滚动行为以实现页面过渡效果
        if (this.isSwipeGesture && Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 30) {
            e.preventDefault();
        }
    }
    
    handleTouchEnd(e) {
        this.cancelLongPress();
        
        if (this.isSwipeGesture) {
            const deltaX = this.touchEndX - this.touchStartX;
            const deltaY = this.touchEndY - this.touchStartY;
            
            // 检测水平滑动
            if (Math.abs(deltaX) > this.swipeThreshold && Math.abs(deltaX) > Math.abs(deltaY)) {
                if (deltaX > 0) {
                    this.onSwipeRight();
                } else {
                    this.onSwipeLeft();
                }
            }
        }
        
        this.isSwipeGesture = false;
    }
    
    startLongPressTimer(touch) {
        this.longPressTimer = setTimeout(() => {
            this.onLongPress(touch);
        }, this.longPressDelay);
    }
    
    cancelLongPress() {
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
    }
    
    onLongPress(touch) {
        console.log('检测到长按手势');
        
        // 创建长按菜单
        const menu = document.createElement('div');
        menu.className = 'long-press-menu active';
        menu.id = 'longPressMenu';
        menu.innerHTML = '<div>长按菜单</div>';
        
        // 设置菜单位置
        menu.style.left = touch.clientX + 'px';
        menu.style.top = touch.clientY + 'px';
        
        document.body.appendChild(menu);
        
        // 2秒后自动隐藏菜单
        setTimeout(() => {
            if (menu.parentNode) {
                menu.classList.remove('active');
                setTimeout(() => {
                    if (menu.parentNode) {
                        menu.parentNode.removeChild(menu);
                    }
                }, 200);
            }
        }, 2000);
        
        // 点击其他地方隐藏菜单
        const hideMenuHandler = (e) => {
            if (!menu.contains(e.target)) {
                menu.classList.remove('active');
                setTimeout(() => {
                    if (menu.parentNode) {
                        menu.parentNode.removeChild(menu);
                    }
                }, 200);
                document.removeEventListener('click', hideMenuHandler);
            }
        };
        
        setTimeout(() => {
            document.addEventListener('click', hideMenuHandler);
        }, 100);
    }
    
    onSwipeRight() {
        console.log('检测到右滑手势');

        // 触发返回按钮，使用浏览器的历史记录API
        history.back();
    }
    
    onSwipeLeft() {
        console.log('检测到左滑手势');
        // 可以实现前进功能或其他自定义行为
    }
    
    animatePageTransition(url, direction) {
        // 添加退出动画
        document.body.classList.add('page-transition-exit');
        
        setTimeout(() => {
            window.location.href = url;
        }, 150);
    }
    
    isClickable(element) {
        const clickableTags = ['A', 'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT'];
        const clickableTypes = ['button', 'submit', 'reset', 'checkbox', 'radio', 'file'];
        
        if (element.tagName && clickableTags.includes(element.tagName.toUpperCase())) {
            if (element.type && clickableTypes.includes(element.type)) {
                return false; // 这些是表单元素，不显示长按菜单
            }
            return true;
        }
        
        if (element.onclick || element.getAttribute('onclick')) {
            return true;
        }
        
        if (element.classList.contains('clickable') || element.classList.contains('interactive')) {
            return true;
        }
        
        // 检查父元素
        let parent = element.parentElement;
        while (parent) {
            if (parent.onclick || parent.getAttribute('onclick')) {
                return true;
            }
            if (parent.classList && (parent.classList.contains('clickable') || parent.classList.contains('interactive'))) {
                return true;
            }
            parent = parent.parentElement;
        }
        
        return false;
    }
    
    addTouchListeners() {
        // 为所有交互元素添加触摸反馈类
        const interactiveElements = document.querySelectorAll(
            'button, .btn, .nav-item, .back-button, .setting-card, ' +
            '.favorite-card, .more-card, .plan-card, .recommend-card, ' +
            '.card, a, .touch-lift, .interactive, .ripple'
        );
        
        interactiveElements.forEach(el => {
            // 添加可滚动容器的弹性滚动
            if (el.classList.contains('plan-cards') || 
                el.classList.contains('recommend-grid') ||
                el.classList.contains('content')) {
                el.classList.add('elastic-scroll');
            }
            
            // 添加触摸高亮效果
            el.classList.add('no-select');
        });
    }
}

/**
 * 页面过渡效果管理器
 */
class PageTransitionManager {
    constructor() {
        this.transitionDuration = 300;
    }
    
    /**
     * 页面滑入效果
     */
    slideIn(direction = 'right') {
        const page = document.body;
        page.classList.remove('page-enter', 'page-exit');
        
        // 强制重绘以触发动画
        void page.offsetWidth;
        
        if (direction === 'right') {
            page.classList.add('page-enter');
        } else {
            page.style.animation = 'slideInLeft 0.3s ease-out forwards';
        }
    }
    
    /**
     * 页面滑出效果
     */
    slideOut(direction = 'left') {
        const page = document.body;
        
        if (direction === 'left') {
            page.classList.add('page-exit');
        } else {
            page.style.animation = 'slideOutRight 0.3s ease-out forwards';
        }
    }
    
    /**
     * 页面淡入效果
     */
    fadeIn() {
        const page = document.body;
        page.style.animation = 'fadeIn 0.3s ease-out forwards';
    }
    
    /**
     * 页面淡出效果
     */
    fadeOut() {
        const page = document.body;
        page.style.animation = 'fadeOut 0.3s ease-out forwards';
    }
}

/**
 * 初始化触摸体验优化
 */
function initTouchExperience() {
    // 初始化触摸手势处理器
    window.touchHandler = new TouchGestureHandler();
    
    // 初始化页面过渡管理器
    window.pageTransition = new PageTransitionManager();
    
    // 添加页面加载完成后的触摸优化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.touchHandler.addTouchListeners();
        });
    } else {
        window.touchHandler.addTouchListeners();
    }
    
    console.log('触摸体验优化已启用');
}

// 如果在window对象上不存在则添加
if (typeof window.initTouchExperience !== 'function') {
    window.initTouchExperience = initTouchExperience;
}

// 自动初始化（可选，可以通过设置 window.touchAutoInit = false 来禁用）
if (window.touchAutoInit !== false) {
    // 延迟初始化以确保DOM完全加载
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTouchExperience);
    } else {
        setTimeout(initTouchExperience, 100);
    }
}